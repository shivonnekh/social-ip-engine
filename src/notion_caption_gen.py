"""notion_caption_gen.py — burn karaoke captions onto a Production row's
"Raw Video" and upload the finished cut to "Production Video".

WHY THIS EXISTS
---------------
This is the SECOND (and final) piece of "auto-finish a Production Tracker
row the moment ``Stage`` flips to 🟢 Ready to Publish" — ``notion_cover_gen.py``
is the first (Reels cover generation). ``studio/scripts/notion_video.py``
already uploads the merged-but-uncaptioned video to a new "Raw Video" page
property (deliberately separate from "Production Video" — see that script's
``upload_raw_video_property``); this module is what turns "Raw Video" into a
captioned "Production Video" without a human ever running
``add_karaoke_captions.py`` by hand.

Structure mirrors ``src/notion_cover_gen.py`` exactly (same problem shape:
find something on the row -> do the expensive work -> upload the result,
never-raise contract, dependency-injection-for-testing style):

1. ``find_raw_video_url`` — pure, given an already-fetched Notion page
   dict. Mirrors ``notion_publish.py::_extract_video_url`` exactly, reading
   a different property name.
2. ``upload_production_video`` — the default ``upload_fn``: POST
   /file_uploads -> PUT -> PATCH the row's "Production Video" page
   PROPERTY. Mirrors ``notion_cover_gen.upload_cover_to_toggle``'s
   file-upload dance and ``studio/scripts/add_karaoke_captions.py
   ::upload_final_video_property``'s exact property-PATCH shape (just
   working from an in-memory path instead of assuming a local script run).
3. ``burn_captions_for_row`` — the single-row orchestrator. NEVER raises
   (catches everything, returns a warning string or ``None`` on success),
   same contract as ``notion_cover_gen.generate_and_upload_cover`` — this
   function is dispatched from a detached ``asyncio.create_task`` in
   ``web.py`` with NOTHING awaiting its result directly, so an unhandled
   exception here would only ever surface as an ugly "Task exception was
   never retrieved" log line instead of a clean, actionable warning.

FAIL-CLOSED DESIGN (why "Raw Video" and "Production Video" are separate)
---------------------------------------------------------------------------
``src/notion_publish.py`` already treats an empty "Production Video" as
"not ready yet, retry later" — zero new code needed there. An unfinished or
failed caption job simply never populates "Production Video", so a partial
or crashed run can never accidentally publish an uncaptioned (or
half-rendered) video live to Instagram.

THE CPU-BOUND STEP MUST NEVER BLOCK THE EVENT LOOP
-------------------------------------------------------
``notion_caption_render.render()`` does synchronous, CPU-bound moviepy
compositing + ffmpeg encoding — easily 10-60+ seconds for a short Reel.
Calling it directly inside this async function would freeze the ENTIRE
FastAPI process (live Instagram DM replies, comment webhooks) for the
whole render. ``burn_captions_for_row`` offloads it via
``asyncio.to_thread`` — non-negotiable, see the call site below.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import tempfile
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import AsyncOpenAI

from src.notion_caption_render import group_words, render
from src.notion_publish_media import _is_safe_download_url
from src.notion_transcribe_words import transcribe_words

logger = logging.getLogger("notion_caption_gen")

UploadFn = Callable[[str, Path], None]

_DOWNLOAD_TIMEOUT_S = 120  # videos are much larger than the cover images notion_cover_gen fetches
_UPLOAD_TIMEOUT_S = 120
_NOTION_API = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"
_RAW_VIDEO_PROP = "Raw Video"
_PRODUCTION_VIDEO_PROP = "Production Video"

# HIGH (security review, 2026-07-08): with no cap, an accidentally huge file
# landing in "Raw Video" (today's only writer is Shivonne's own studio
# pipeline, but a bug there is still realistic) gets fully buffered into
# memory on the SAME process serving live Instagram traffic. 250MB comfortably
# covers a real ~30-90s vertical Reel (studio's own _maybe_compress_video
# already targets well under Notion's single-part upload cap) with headroom,
# while still bounding worst-case memory use.
_MAX_VIDEO_BYTES = 250 * 1024 * 1024
_DOWNLOAD_CHUNK_BYTES = 1024 * 1024

# HIGH (security review, 2026-07-08): asyncio.to_thread() always runs on the
# process-wide DEFAULT executor — the SAME pool notion_publish_runner.py /
# notion_publish_fb_runner.py already use for their own to_thread git-push
# calls. A stuck/pathological render (moviepy/ffmpeg hang on a malformed
# video) would otherwise pin a thread in that shared pool indefinitely,
# eventually starving unrelated background work in this same live-traffic
# process. A small, DEDICATED executor confines that blast radius to this
# feature's own thread(s) — max_workers matches the default caption-render
# cap (NOTION_SYNC_MAX_CAPTION_RENDERS=1) so normal operation never queues.
_RENDER_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="caption-render")

# HIGH (security review, 2026-07-08): asyncio.wait_for cannot force-kill an
# OS thread/subprocess already in flight (Python threads aren't preemptible),
# but it DOES guarantee this async orchestrator itself always returns within
# a bounded time instead of hanging forever on a detached asyncio.create_task
# that nothing is awaiting — the more severe half of the original gap (a
# stuck render being invisible forever, never even reported as a warning).
# 10 minutes comfortably exceeds any real ~30-90s Reel's expected render time.
_RENDER_TIMEOUT_S = 600


class CaptionGenError(RuntimeError):
    """Raised by this module's internal helpers on failure. Never escapes
    ``burn_captions_for_row`` — that function's whole contract is to catch
    everything (including this) and return a warning string instead."""


def find_raw_video_url(
    row_id: str, children_fn_unused: Callable[[str], list[dict]] | None = None, *, page: dict
) -> str | None:
    """Extract the row's "Raw Video" page PROPERTY's file URL from an
    already-fetched Notion ``page`` dict, or ``None`` if missing/empty.

    Mirrors ``notion_publish.py::_extract_video_url`` exactly (same
    file/external URL handling), just reading a different property name.
    ``children_fn_unused`` exists only to keep this function's call
    signature consistent with the other ``find_*`` helpers in this codebase
    (e.g. ``notion_cover_gen.find_cover_prompt``) that take a
    ``(row_id, children_fn)`` pair — "Raw Video" is a page PROPERTY, not a
    body block, so no body-walk (and no extra Notion round-trip) is needed
    here; the parameter is accepted but never called.
    """
    files = page.get("properties", {}).get(_RAW_VIDEO_PROP, {}).get("files") or []
    if not files:
        return None
    file_obj = files[0]
    kind = file_obj.get("type", "")
    url = str((file_obj.get(kind) or {}).get("url", "")).strip()
    return url or None


def _download_video(url: str, dest: Path) -> None:
    """Download ``url`` to ``dest``, streamed in bounded chunks (never a
    single ``resp.read()`` of the whole body — see ``_MAX_VIDEO_BYTES``).
    Raises ``CaptionGenError`` on any failure, including exceeding the size
    cap (checked against both a declared ``Content-Length`` header AND the
    actual bytes read, since a missing or lying header must not bypass the
    cap). Callers MUST check ``_is_safe_download_url`` before calling this —
    mirrors ``notion_publish_media._download_image``'s split between the
    SSRF check and the download itself, kept as two steps so the guard is
    checked exactly once, at the top of ``burn_captions_for_row``, rather
    than duplicated here."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "social-ip-engine/notion-caption-gen"}
    )
    try:
        with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT_S) as resp:
            # getattr, not a bare attribute access: real urllib responses
            # always carry .headers, but this repo's test doubles fake
            # urlopen() with a plain io.BytesIO (no .headers) — matching the
            # existing test style rather than requiring every test fixture
            # in this file to grow a fake headers object just for this cap.
            headers = getattr(resp, "headers", None)
            declared_length = headers.get("Content-Length") if headers is not None else None
            if declared_length is not None:
                try:
                    if int(declared_length) > _MAX_VIDEO_BYTES:
                        raise CaptionGenError(
                            f"video at {url} declares {declared_length} bytes, "
                            f"exceeds cap of {_MAX_VIDEO_BYTES} bytes"
                        )
                except ValueError:
                    pass  # malformed header — fall through to the streamed cap below
            total = 0
            with dest.open("wb") as f:
                while True:
                    chunk = resp.read(_DOWNLOAD_CHUNK_BYTES)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > _MAX_VIDEO_BYTES:
                        raise CaptionGenError(
                            f"video at {url} exceeded cap of {_MAX_VIDEO_BYTES} bytes "
                            f"while streaming — aborted"
                        )
                    f.write(chunk)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise CaptionGenError(f"video download failed for {url}: {exc}") from exc
    if total == 0:
        raise CaptionGenError(f"video download returned empty body for {url}")


def _notion_call(method: str, path: str, api_key: str, body: dict | None = None) -> dict:
    """POST/PATCH/GET against the Notion API. Raises ``CaptionGenError`` on
    any transport failure or malformed response — mirrors
    ``notion_cover_gen._notion_call`` exactly (deliberately reimplemented
    here rather than imported, keeping this module independently movable,
    same convention already established between ``notion_publish_media.py``
    and ``notion_sync_media.py``)."""
    headers = {"Authorization": f"Bearer {api_key}", "Notion-Version": _NOTION_VERSION}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    url = f"{_NOTION_API}{path}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=_UPLOAD_TIMEOUT_S) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise CaptionGenError(f"notion API {method} {path} failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CaptionGenError(f"notion API {method} {path} returned invalid JSON: {exc}") from exc


def upload_production_video(
    row_id: str, video_path: Path, *, api_key: str | None = None
) -> None:
    """Default ``upload_fn``: ``POST /file_uploads`` -> the returned
    multipart ``upload_url`` PUT -> ``PATCH /pages/{row_id}`` setting the
    "Production Video" page PROPERTY. Mirrors
    ``studio/scripts/add_karaoke_captions.py::upload_final_video_property``'s
    exact property-PATCH shape (Files & media property, not a body block —
    the same property ``src/notion_publish.py::_extract_video_url`` reads).
    Raises ``CaptionGenError`` on failure -- callers
    (``burn_captions_for_row``) own the catch.
    """
    resolved_key = (api_key or os.environ.get("NOTION_KEY", "")).strip()
    if not resolved_key:
        raise CaptionGenError("NOTION_KEY not set")

    filename = video_path.name or "captioned.mp4"
    upload = _notion_call(
        "POST", "/file_uploads", resolved_key, {"filename": filename, "content_type": "video/mp4"}
    )
    try:
        upload_url = upload["upload_url"]
        upload_id = upload["id"]
    except (KeyError, TypeError) as exc:
        raise CaptionGenError(f"unexpected file_uploads response: {exc}") from exc

    boundary = "----cap" + uuid.uuid4().hex
    video_bytes = video_path.read_bytes()
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{filename}"\r\nContent-Type: video/mp4\r\n\r\n'
    ).encode() + video_bytes + f"\r\n--{boundary}--\r\n".encode()
    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    request = urllib.request.Request(upload_url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=_UPLOAD_TIMEOUT_S) as response:
            response.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise CaptionGenError(f"notion file upload PUT failed: {exc}") from exc

    file_ref = {"type": "file_upload", "file_upload": {"id": upload_id}, "name": filename}
    _notion_call(
        "PATCH", f"/pages/{row_id}", resolved_key,
        {"properties": {_PRODUCTION_VIDEO_PROP: {"files": [file_ref]}}},
    )


async def burn_captions_for_row(
    row_id: str,
    video_url: str,
    *,
    api_key: str | None = None,
    upload_fn: UploadFn | None = None,
) -> str | None:
    """Single-row orchestrator: download the row's Raw Video, transcribe it
    for word-level timings, burn karaoke captions, upload the result to
    "Production Video". NEVER raises (catches everything, returns a
    warning string or ``None`` on success) — see module docstring for why
    this contract is non-negotiable for a task dispatched via a detached
    ``asyncio.create_task``.

    ``api_key`` is the OpenAI key used for transcription (``transcribe_words``
    falls back to ``OPENAI_API_KEY`` from the environment when unset, same
    as every other OpenAI call in this codebase). ``upload_fn`` defaults to
    ``upload_production_video`` (reads ``NOTION_KEY`` from the environment)
    and is injectable purely for testing, same DI pattern as
    ``notion_cover_gen.generate_and_upload_cover``'s ``upload_fn`` parameter.
    """
    resolved_upload: UploadFn = upload_fn if upload_fn is not None else upload_production_video
    tmp_dir: str | None = None

    try:
        if not _is_safe_download_url(video_url):
            return f"no_captions: '{row_id}' — refusing non-https video URL"

        tmp_dir = tempfile.mkdtemp(prefix="notion-caption-")
        video_path = Path(tmp_dir) / "raw.mp4"
        out_path = Path(tmp_dir) / "captioned.mp4"

        try:
            _download_video(video_url, video_path)
        except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
            return f"caption_download_failed: '{row_id}' — {exc}"

        # whisper-1 reads the audio track straight out of a common video
        # container (mp4) — no separate ffmpeg/moviepy audio-extraction step
        # needed. If this assumption ever proves wrong for a real video
        # (unusual codec/container), the failure surfaces as a normal
        # transcription failure below (zero words -> "no_captions" warning),
        # not a crash — safe to try directly first.
        try:
            video_bytes = video_path.read_bytes()
        except OSError as exc:
            return f"caption_failed: '{row_id}' — could not read downloaded video: {exc}"

        client = AsyncOpenAI(api_key=api_key) if api_key else None
        words = await transcribe_words(video_bytes, filename_hint=video_path.name, client=client)
        if not words:
            return f"no_captions: '{row_id}' — transcription produced zero words"

        chunks = group_words(words)

        try:
            # THE one CPU-bound step — moviepy's TextClip compositing +
            # ffmpeg export is synchronous Python. Offloaded to a DEDICATED
            # worker pool (not asyncio.to_thread's shared default executor —
            # see _RENDER_EXECUTOR's docstring above, HIGH finding 2026-07-08)
            # so it never freezes the event loop AND a stuck render can never
            # starve unrelated background work sharing the default pool.
            # asyncio.wait_for can't force-kill a hung OS thread, but it does
            # guarantee THIS function always returns within a bounded time
            # instead of hanging forever on a task nothing else is awaiting.
            loop = asyncio.get_running_loop()
            await asyncio.wait_for(
                loop.run_in_executor(_RENDER_EXECUTOR, render, video_path, chunks, out_path),
                timeout=_RENDER_TIMEOUT_S,
            )
        except TimeoutError:
            return f"caption_render_timeout: '{row_id}' — exceeded {_RENDER_TIMEOUT_S}s"
        except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
            return f"caption_render_failed: '{row_id}' — {exc}"

        try:
            resolved_upload(row_id, out_path)
        except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
            return f"caption_upload_failed: '{row_id}' — {exc}"

        return None
    except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
        return f"caption_failed: '{row_id}' — {exc}"
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)
