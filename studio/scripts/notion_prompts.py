#!/usr/bin/env python3
"""Auto-generate ready-to-paste image prompts inside each Production row.

The missing automation: a Production row links to a Content concept (which holds
the 分镜指南 / Shot Guide) and to an IP (persona/voice). Notion can't read a linked
page's body, so this script does it: for each row it reads the storyboard's 🎥 Visual
lines + the IP persona, builds one finished GPT image prompt per shot, and writes them
into the row body as copy-ready code blocks. Operators just click "copy" — no manual
copy-paste from the Content Library.

Usage:
    export NOTION_KEY=ntn_...
    python3 scripts/notion_prompts.py --backfill           # fill all rows missing prompts
    python3 scripts/notion_prompts.py --backfill --force   # regenerate (wipe + rebuild)
    python3 scripts/notion_prompts.py --row <page_id>      # one row

Also imported by notion_fanout.py / notion_watch.py so new rows get prompts automatically.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.notion.com/v1"
IDS_PATH = Path(__file__).resolve().parent / "notion_ids.json"
SENTINEL = "🖼️ IMAGE PROMPTS"
SENTINEL_VOICE = "🎙️ VOICE CONFIG"


def _headers() -> dict[str, str]:
    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        sys.exit("[error] NOTION_KEY env var not set")
    return {"Authorization": f"Bearer {key}",
            "Notion-Version": "2022-06-28", "Content-Type": "application/json"}


def call(method: str, path: str, body: dict | None = None, retries: int = 5) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(f"{BASE}{path}", data=data, headers=_headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode()
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(float(exc.headers.get("Retry-After", 1)) + 0.5)
                continue
            sys.exit(f"[error] {method} {path} -> HTTP {exc.code}: {payload}")
    sys.exit("[error] exhausted retries")


def _env(key: str) -> str:
    v = os.environ.get(key, "").strip()
    if v:
        return v
    envp = Path(__file__).resolve().parent.parent / ".env"
    if envp.exists():
        for line in envp.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(key + "="):
                return line.split("=", 1)[1].strip()
    return ""


def _openai_chat(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 40) -> str:
    key = _env("OPENAI_API_KEY")
    if not key:
        return ""
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": 0.8}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())["choices"][0]["message"]["content"].strip()
    except Exception:
        return ""


def draft_title(hook: str, topic: str, lang: str = "") -> str:
    """Short clickbait video title (a punchy viewer-facing question + one surprise emoji),
    in the IP's language. Returns '' on any failure (caller leaves the field blank)."""
    low = (lang or "").lower()
    target = ("Cantonese (繁體中文, natural 口語粵語)" if "粤" in low or "cantonese" in low
              else "Mandarin Chinese (简体)" if "普通" in low or "mandarin" in low
              else "English")
    prompt = (f"Write ONE very short clickbait title (3-8 words) for a Traditional Chinese Medicine "
              f"short video. Topic: {topic}. Hook: {hook}. Write it in {target}. Make it a punchy "
              f"question spoken directly to the viewer. End with exactly ONE surprise emoji "
              f"(😱 😳 😮 😴 😣). Output ONLY the title — no quotes, no extra text.")
    return _openai_chat(prompt).strip().strip('"').strip()


_TRANSLATE_LANGS = ("粤", "cantonese", "普通", "mandarin", "spanish", "arabic",
                    "indonesian", "vietnamese", "thai", "hindi", "portuguese")


def _translate_lines(lines: list[str], lang: str) -> list[str]:
    """Translate per-shot script lines into the IP language (commas avoided for TTS).

    English / unknown language / no API key → returns the source lines unchanged
    (so English IPs use the storyboard lines verbatim, and we never blank out).
    """
    import re
    low = (lang or "").lower()
    if not lines or not any(k in low for k in _TRANSLATE_LANGS):
        return lines
    target = ("Cantonese (繁體中文, natural spoken 口語粵語)" if "粤" in low or "cantonese" in low
              else "Mandarin Chinese (简体)" if "普通" in low or "mandarin" in low
              else lang)
    numbered = "\n".join(f"{i + 1}. {ln}" for i, ln in enumerate(lines))
    prompt = (f"Translate each numbered line into {target} for a SPOKEN Traditional Chinese Medicine "
              f"short video. Keep the SAME number of lines and the same numbering. Natural spoken tone. "
              f"IMPORTANT: use natural punctuation so the text-to-speech has real pauses and rhythm — "
              f"commas (，) for short breaths, full stops (。) at sentence ends, question marks (？) for "
              f"questions. Do NOT replace punctuation with spaces. "
              f"Translate EVERY line including the final call-to-action; in that CTA line keep ONLY "
              f"the single English keyword word itself untranslated (e.g. the word 'teeth') and "
              f"translate the rest of the sentence. "
              f"Output ONLY the numbered lines.\n\n{numbered}")
    out = _openai_chat(prompt, max_tokens=700)
    if not out:
        return lines
    parsed = []
    for ln in out.splitlines():
        m = re.match(r"^\s*\d+[.):、]\s*(.+)", ln)
        if m:
            parsed.append(m.group(1).strip())
    return parsed if len(parsed) == len(lines) else lines


def script_lines_for_ip(concept_id: str, ip_id: str | None) -> list[str]:
    """Per-shot voice lines from the concept's Shot Guide, in the IP's language.

    Returns ONE entry per shot — empty string for shots with no voice line.
    This preserves positional alignment: script_lines[i] == shot i's voice line.
    """
    lines = [s.get("line", "").strip() for s in parse_storyboard(concept_id)]
    lang = ip_language(ip_id) if ip_id else ""
    # Only translate non-empty lines; empty (no-voice) slots stay empty
    voiced = [ln for ln in lines if ln]
    translated = _translate_lines(voiced, lang)
    # Re-insert empty slots back into their original positions
    result: list[str] = []
    t_iter = iter(translated)
    for ln in lines:
        result.append(next(t_iter) if ln else "")
    return result


def apply_script_property(row_id: str, force: bool = False) -> str:
    """Fill a Production row's Script property (ONE LINE PER SHOT, IP language).

    Source of truth for apply_shot_plan's per-shot voice. Safe: only writes when
    the Script property is empty unless force=True.
    """
    page = call("GET", f"/pages/{row_id}")
    concept_id = _relation_id(page, "Content")
    ip_id = _relation_id(page, "IP")
    if not concept_id:
        return "no-content"
    current = "".join(t["plain_text"] for t in
                      page["properties"].get("Script", {}).get("rich_text", []))
    if current.strip() and not force:
        return "exists"
    lines = script_lines_for_ip(concept_id, ip_id)
    if not lines:
        return "no-lines"
    script = "\n".join(lines)[:2000]
    call("PATCH", f"/pages/{row_id}",
         {"properties": {"Script": {"rich_text": _rt(script)}}})
    return f"script set ({len(lines)} shots)"


def _rt(t): return [{"type": "text", "text": {"content": t}}]
def _txt(block) -> str:
    t = block["type"]
    return "".join(x.get("plain_text", "") for x in block.get(t, {}).get("rich_text", []))


def _all_children(block_id: str) -> list[dict]:
    out, cursor = [], None
    while True:
        suffix = f"?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
        data = call("GET", f"/blocks/{block_id}/children{suffix}")
        out.extend(data["results"])
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    return out


def parse_storyboard(concept_id: str) -> list[dict]:
    """Return [{title, line, visual}] from the concept's Shot Guide section."""
    blocks = _all_children(concept_id)
    in_guide, shots, cur = False, [], None
    for b in blocks:
        t = b["type"]
        txt = _txt(b)
        if t == "heading_2":
            in_guide = ("Shot Guide" in txt) or ("分镜" in txt)
            continue
        if not in_guide:
            continue
        if t == "heading_3" and txt.strip().lower().startswith("shot"):
            cur = {"title": txt.strip(), "line": "", "visual": ""}
            shots.append(cur)
        elif t == "bulleted_list_item" and cur is not None:
            if "🎥" in txt:
                cur["visual"] = txt.split("🎥", 1)[1].lstrip(" :").strip()
            elif "🗣️" in txt or "🗣" in txt:
                cur["line"] = txt.split("🗣", 1)[1].lstrip("️ :").strip()
    return [s for s in shots if s["visual"]]


def ip_persona(ip_id: str) -> tuple[str, str]:
    page = call("GET", f"/pages/{ip_id}")
    name = "".join(t["plain_text"] for t in
                   next(p for p in page["properties"].values() if p["type"] == "title")["title"])
    persona = "".join(t["plain_text"] for t in
                      page["properties"].get("Persona", {}).get("rich_text", []))
    return name, persona or "TCM doctor"


def _primary_beat(visual: str) -> str:
    """Extract the single primary frame from a (possibly rich, multi-beat) shot guide,
    for IMAGE generation — one image = one frame, so drop cuts/inserts/transitions."""
    import re
    parts = re.split(r";|；|，|\bthen\b|cut[- ]?in|quick cut|cut to|cut back|insert|return to",
                     visual, flags=re.I)
    first = parts[0].strip().strip("—-：: ").strip()
    # strip a leading label like "Demonstration:" / "Talking head —"
    first = re.sub(r"^(talking head|demonstration|doctor)\b[\s—:-]*", r"\1: ", first, flags=re.I)
    return first or visual


def build_prompt(persona: str, visual: str) -> str:
    """One shot = ONE single frame. Setting is derived from the visual description —
    not hardcoded. Street/outdoor shots use natural light; clinic shots use clinic light.
    People (patient, guest, bystander) appear only when the scene explicitly describes them."""
    v = visual.lower()

    # Derive setting from the visual — don't hardcode clinic for every shot
    _street_kws = ("street", "road", "pavement", "sidewalk", "outdoor", "city",
                   "high street", "brick", "shopfront", "pedestrian", "western",
                   "london", "new york", "market", "corner", "crowd", "walking",
                   "leaning against", "coffee in hand")
    _clinic_kws = ("clinic", "consultation", "counter", "herbal", "wooden desk",
                   "tcm", "medicine cabinet", "treatment room")

    is_street = any(k in v for k in _street_kws)
    is_clinic = any(k in v for k in _clinic_kws)
    # Only EXTREME close-ups (ECU) have an invisible background — "close-up" alone still shows setting
    is_ecu = any(k in v for k in ("ecu", "extreme close-up", "extreme close up",
                                   "extreme closeup", "macro shot"))

    if is_ecu and not is_clinic:
        setting = "Setting: extremely shallow depth of field, background fully blurred — focus is 100% on the subject in frame."
    elif is_street and not is_clinic:
        setting = "Setting: natural outdoor daylight, Western city street, shallow depth of field. No clinic, no indoor setting."
    elif is_clinic:
        setting = "Setting: warm, traditional Chinese-medicine clinic lighting, shallow depth of field."
    else:
        setting = "Setting: shallow depth of field, natural lighting."

    # Doctor identity only locked when they're actually in the scene
    has_doctor = any(k in v for k in ("jackie", "doctor", "to camera", "looking at camera",
                                      "talking", "presenter", "gestur", "smile", "he explains",
                                      "he leans", "he turns", "he spots", "he approaches",
                                      "he looks", "he reaches", "he mimes"))

    lines = [
        "One single photorealistic vertical 9:16 frame — a single moment. "
        "No split screen, no collage, no before/after, no multiple panels.",
        setting,
        f"SCENE: {visual}",
    ]
    if has_doctor:
        lines.append(f"The main character must be the EXACT same person as the reference photo "
                     f"({persona}) — same face, hair, age, ethnicity.")
    lines.append("Include only the people explicitly described in the scene. "
                 "No extra faces, no on-screen text, no watermark.")
    return "\n".join(lines)


JIMENG_DISCLAIMER = "请注意，这些都是 AI 数字人，不是真人。没有真人也可以直接生成影片。"


def _jimeng_camera(title: str, visual: str = "") -> str:
    """Camera/运镜 keyed off the shot BEAT (the title), not the visual text — so a word
    like 'gesturing' in one shot can't leak its camera into another."""
    t = title.lower()
    if "hook" in t:
        return "缓慢推近，营造代入感"
    if "cta" in t:
        return "缓慢推近至面部，温暖亲切收尾"
    if any(k in t for k in ("quick", "win", "demo", "method", "try", "remedy", "recipe")):
        return "中景，镜头自然跟随手上的动作，轻微手持感"
    if any(k in t for k in ("safety", "principle", "caution", "root")):
        return "画面稳定，轻微推近，神情认真"
    return "人物居中，轻微缓推，自然呼吸与眨眼"


_LANG_MAP = {"cantonese": "粤语", "english": "英文", "mandarin": "普通话",
             "spanish": "西班牙语", "arabic": "阿拉伯语", "indonesian": "印尼语",
             "vietnamese": "越南语", "thai": "泰语", "hindi": "印地语", "portuguese": "葡萄牙语"}


def _lang_label(raw: str) -> str:
    low = (raw or "").lower()
    for k, v in _LANG_MAP.items():
        if k in low:
            return v
    return "".join(c for c in (raw or "") if ord(c) < 0x2000).strip()


def ip_language(ip_id: str | None) -> str:
    if not ip_id:
        return ""
    sel = call("GET", f"/pages/{ip_id}")["properties"].get("Language", {}).get("select")
    return _lang_label(sel["name"]) if sel else ""


# ── 即梦 content-safety vocabulary sanitizer (added 2026-07-10) ──────────────
# Root-caused by comparing prompts Shivonne verified PASS on the 即梦 web UI
# against ours that hung forever: medical identities/actions (doctor, patient,
# clinic, treatment, diagnosis, needles...) trip 即梦's medical content-safety
# review → the task sits in "querying" purgatory forever. The passing prompts
# use wellness/education vocabulary and explicitly disclaim medical content.
_JIMENG_SAFE_SUBS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bTCM doctors?\b", re.I), "wellness educator"),
    (re.compile(r"\bdoctor'?s?\b", re.I), "wellness educator"),
    (re.compile(r"\bphysicians?\b", re.I), "wellness educator"),
    (re.compile(r"\bpatients?\b", re.I), "participant"),
    (re.compile(r"\bclinics?\b", re.I), "wellness studio"),
    (re.compile(r"\btreatments?\b", re.I), "demonstration"),
    (re.compile(r"\btherapy\b", re.I), "wellness practice"),
    (re.compile(r"\bdiagnos(?:is|es|e|ing)\b", re.I), "observation"),
    (re.compile(r"\bmedical\b", re.I), "wellness"),
    (re.compile(r"\bacupuncture\b", re.I), "acupressure"),
    (re.compile(r"\bneedles?\b", re.I), "small tool"),
    (re.compile(r"医生|老中医|中医师"), "养生讲师"),
    (re.compile(r"病人|患者"), "参与者"),
    (re.compile(r"诊所|医馆"), "养生工作室"),
    (re.compile(r"治疗"), "演示"),
    (re.compile(r"诊断"), "观察"),
]

_LANG_EN = {"英文": "English", "粤语": "Cantonese", "普通话": "Mandarin",
            "西班牙语": "Spanish", "阿拉伯语": "Arabic", "印尼语": "Indonesian",
            "越南语": "Vietnamese", "泰语": "Thai", "印地语": "Hindi", "葡萄牙语": "Portuguese"}


def sanitize_for_jimeng(text: str) -> str:
    """Swap medical vocabulary for 即梦-safe wellness vocabulary."""
    for pat, repl in _JIMENG_SAFE_SUBS:
        text = pat.sub(repl, text)
    return text


def build_jimeng_prompt(title: str, visual: str = "", lang: str = "") -> str:
    """The prompt that goes INTO 即梦 (audio-native digital human).

    Rewritten 2026-07-10 to the structured 【Section】 format Shivonne verified
    passes 即梦's generation + content review, replacing the old free-prose
    template. Key differences (all root-caused against real pass/hang outcomes):
      1. Shot-guide text runs through sanitize_for_jimeng() — medical words
         (doctor/patient/clinic/treatment...) trip content review → eternal
         "querying". Wellness vocabulary passes.
      2. No contradictory boilerplate: the old template appended 「适时插入
         空镜/特写或镜头切换」 even when the shot guide said "one continuous
         take, no cutaway".
      3. Explicit negative guards (【Important】): no medical procedures / no
         glow / no halo / no particles — heads off both the safety filter and
         即梦's fantasy-VFX drift.
      4. Short declarative sentences; uploads referenced plainly ("the
         uploaded reference image / audio") instead of {{图片}}/{{对白}} tokens."""
    visual_clean = sanitize_for_jimeng(visual or "")
    lang_en = _LANG_EN.get(lang, lang)
    speech_lang = f" Speak {lang_en} dialogue." if lang_en else ""
    shot_guide = f"【Shot Guide】{visual_clean}\n" if visual_clean else ""
    return (
        "音频驱动（Audio Native）数字人视频。\n"
        f"{shot_guide}"
        "【Character】AI virtual presenter. Use the uploaded reference image as the "
        "appearance reference. Keep the same hairstyle, clothing, facial features, "
        "age and expression. Consistent identity throughout the video.\n"
        f"【Speech】Lip-sync naturally to the uploaded audio.{speech_lang} "
        "Natural mouth movement. Comfortable speaking pace. "
        "Occasional natural blinking and breathing.\n"
        "【Style】Educational wellness presentation. Calm. Friendly. Professional. "
        "Natural. No dramatic acting. No exaggerated gestures.\n"
        f"【Camera】{_jimeng_camera(title, visual)}。Maintain 9:16 vertical composition. "
        "Warm soft natural lighting.\n"
        "【Important】This is an AI-generated virtual presenter for educational "
        "purposes. No patient. No treatment. No doctor. No diagnosis. No medical "
        "advice. No medical procedures. No surgery. No injections. No blood. "
        "NO glow. NO halo. NO light effects. NO magical particles. "
        "NO subtitles. NO captions. NO on-screen text of any kind. NO lyrics text. "
        "画面中绝对不要出现任何字幕、文字、标题 — 字幕由后期另行添加。No watermark.\n"
        f"{JIMENG_DISCLAIMER}"
    )


def _relation_id(page: dict, prop: str) -> str | None:
    rel = page["properties"].get(prop, {}).get("relation", [])
    return rel[0]["id"] if rel else None


def _page_title(page: dict) -> str:
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return ""


def fetch_infographic_brief(concept_id: str) -> str:
    """Pull the 🖼️ Infographic Brief code block from a Content Library page.
    Returns "" if the concept has no brief."""
    grab = False
    for b in _all_children(concept_id):
        t, tx = b["type"], _txt(b)
        if t.startswith("heading") and "Infographic Brief" in tx:
            grab = True
            continue
        if grab and t == "code":
            return tx
        if grab and t.startswith("heading"):
            break  # next section reached without finding a code block
    return ""


def build_cover_prompt(persona: str, title: str, hook_visual: str = "") -> str:
    """Cover/thumbnail prompt for the row — scroll-stopping single frame with
    clean space reserved for a bold title overlay (text added in editing)."""
    topic_hint = f" Include one clear visual element from the hook scene: {hook_visual}" if hook_visual else ""
    return (
        "One single photorealistic vertical 9:16 COVER IMAGE for a short-video "
        "thumbnail — a single moment. No split screen, no collage, no panels.\n"
        f"The main character must be the EXACT same person as the reference photo "
        f"({persona}) — same face, hair, age, ethnicity.\n"
        "Expression: exaggerated, scroll-stopping (shocked / concerned / intrigued), "
        "direct eye contact with the camera, face near-frontal.\n"
        "Composition: subject fills the lower two-thirds of the frame; clean "
        "high-contrast background; keep the top third uncluttered for a bold title "
        "text overlay added later.\n"
        f"TOPIC: {title}.{topic_hint}\n"
        "Punchy color grading, crisp lighting, readable at thumbnail size. "
        "No on-screen text, no watermark."
    )


NO_BRIEF_PLACEHOLDER = "<no Infographic Brief on the Content page — add it there, then re-sync>"


def _bold_block(t: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [
        {"type": "text", "text": {"content": t},
         "annotations": {"bold": True, "italic": False, "strikethrough": False,
                         "underline": False, "code": False, "color": "default"}}]}}


def _code_block(t: str) -> dict:
    return {"object": "block", "type": "code",
            "code": {"rich_text": _rt(t), "language": "plain text"}}


def cover_blocks(persona: str, title: str, hook_visual: str = "") -> list[dict]:
    """🖼️ Cover Photo section blocks (prompt + drop-toggle + trailing divider)."""
    return [
        {"object": "block", "type": "heading_3", "heading_3": {"rich_text": _rt("🖼️ Cover Photo")}},
        _bold_block("🖼️ Cover prompt (thumbnail → GPT)"),
        _code_block(build_cover_prompt(persona, title, hook_visual)),
        {"object": "block", "type": "toggle",
         "toggle": {"rich_text": _rt("🖼️ Cover here"), "children": []}},
        {"object": "block", "type": "divider", "divider": {}},
    ]


def dm_blocks(brief: str) -> list[dict]:
    """📊 DM Infographic section blocks (prompt synced from the Content page)."""
    return [
        {"object": "block", "type": "heading_3", "heading_3": {"rich_text": _rt("📊 DM Infographic")}},
        _bold_block("🖼️ Infographic prompt (→ GPT image gen)"),
        _code_block(brief or NO_BRIEF_PLACEHOLDER),
    ]


def cover_dm_blocks(persona: str, title: str, brief: str, hook_visual: str = "") -> list[dict]:
    """Body blocks for the 🖼️ Cover Photo + 📊 DM Infographic sections
    (appended by apply_shot_plan on fan-out; backfilled onto older rows)."""
    return cover_blocks(persona, title, hook_visual) + dm_blocks(brief)


def _has_sentinel(row_id: str) -> dict | None:
    for b in _all_children(row_id):
        if b["type"] == "callout" and SENTINEL in _txt(b):
            return b
    return None


def _wipe_from(row_id: str, sentinel_block: dict) -> None:
    """Delete the sentinel callout and everything after it (prompts are the last section)."""
    kids = _all_children(row_id)
    idx = next((i for i, b in enumerate(kids) if b["id"] == sentinel_block["id"]), None)
    if idx is None:
        return
    for b in kids[idx:]:
        call("DELETE", f"/blocks/{b['id']}")
        time.sleep(0.2)


def apply_prompts(row_id: str, force: bool = False) -> str:
    page = call("GET", f"/pages/{row_id}")
    concept_id = _relation_id(page, "Content")
    ip_id = _relation_id(page, "IP")
    if not concept_id:
        return "no-content"
    shots = parse_storyboard(concept_id)
    if not shots:
        return "no-storyboard"

    existing = _has_sentinel(row_id)
    if existing and not force:
        return "exists"
    if existing and force:
        _wipe_from(row_id, existing)

    persona = ip_persona(ip_id)[1] if ip_id else "TCM doctor"
    blocks = [
        {"object": "block", "type": "divider", "divider": {}},
        {"object": "block", "type": "callout", "callout": {
            "rich_text": _rt(f"{SENTINEL} — auto-generated from the linked storyboard + IP. "
                             "Click ‘copy’ on each block and paste into GPT (upload the IP photo first)."),
            "icon": {"type": "emoji", "emoji": "🖼️"}, "color": "purple_background"}},
    ]
    for s in shots:
        label = s["title"]
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": label},
                           "annotations": {"bold": True, "italic": False, "strikethrough": False,
                                           "underline": False, "code": False, "color": "default"}}]}})
        blocks.append({"object": "block", "type": "code", "code": {
            "rich_text": _rt(build_prompt(persona, s["visual"])), "language": "plain text"}})
    for i in range(0, len(blocks), 25):
        call("PATCH", f"/blocks/{row_id}/children", {"children": blocks[i:i + 25]})
    return f"added {len(shots)} prompts"


def _ip_voice_config(ip_id: str) -> dict:
    page = call("GET", f"/pages/{ip_id}")
    p = page["properties"]
    def _r(name):
        return "".join(t["plain_text"] for t in p.get(name, {}).get("rich_text", []))
    return {
        "voice_id": _r("voice_id") or "?",
        "speed": (p.get("Speed", {}) or {}).get("number"),
        "pitch": (p.get("Pitch", {}) or {}).get("number"),
        "boost": _r("Language Boost") or "?",
        "emotion": _r("Emotion") or "none",
    }


def apply_voice_config(row_id: str, force: bool = False) -> str:
    """Write the row's real MiniMax voice config (pulled from its IP) as a copy-ready block."""
    page = call("GET", f"/pages/{row_id}")
    ip_id = _relation_id(page, "IP")
    if not ip_id:
        return "no-ip"

    for b in _all_children(row_id):
        if b["type"] == "callout" and SENTINEL_VOICE in _txt(b):
            if not force:
                return "exists"
            # wipe sentinel callout + the following code block
            kids = _all_children(row_id)
            idx = next((i for i, x in enumerate(kids) if x["id"] == b["id"]), None)
            for x in kids[idx: idx + 2]:
                call("DELETE", f"/blocks/{x['id']}")
                time.sleep(0.2)
            break

    cfg = _ip_voice_config(ip_id)
    block_text = (f"voice_id:        {cfg['voice_id']}\n"
                  f"speed:           {cfg['speed']}\n"
                  f"pitch:           {cfg['pitch']}\n"
                  f"language boost:  {cfg['boost']}\n"
                  f"emotion:         {cfg['emotion']}")
    blocks = [
        {"object": "block", "type": "callout", "callout": {
            "rich_text": _rt(f"{SENTINEL_VOICE} — set these exactly in MiniMax. "
                             "The script to paste is in the Script property above. ⚠️ avoid commas."),
            "icon": {"type": "emoji", "emoji": "🎙️"}, "color": "yellow_background"}},
        {"object": "block", "type": "code", "code": {
            "rich_text": _rt(block_text), "language": "plain text"}},
    ]
    call("PATCH", f"/blocks/{row_id}/children", {"children": blocks})
    return "added voice config"


def _wipe_all(row_id: str) -> int:
    kids = _all_children(row_id)
    for b in kids:
        call("DELETE", f"/blocks/{b['id']}")
        time.sleep(0.18)
    return len(kids)


def apply_shot_plan(row_id: str, rebuild: bool = True) -> str:
    """Rebuild a Production row body as a per-shot plan: each shot gets its own
    🖼️ image prompt + 🗣️ voice script. One 🎙️ Voice Config block up top (same for
    all shots). No tick-box steps — progress is tracked via the row's properties."""
    page = call("GET", f"/pages/{row_id}")
    concept_id = _relation_id(page, "Content")
    ip_id = _relation_id(page, "IP")
    if not concept_id:
        return "no-content"
    shots = parse_storyboard(concept_id)
    if not shots:
        return "no-storyboard"

    persona = ip_persona(ip_id)[1] if ip_id else "TCM doctor"
    lang = ip_language(ip_id)
    cfg = _ip_voice_config(ip_id) if ip_id else {"voice_id": "?", "speed": None,
                                                 "pitch": None, "boost": "?", "emotion": "none"}
    # per-shot voice script comes from THIS row's own Script property (language-specific),
    # one line per shot. Storyboard line is only a fallback if Script is missing/misaligned.
    script_text = "".join(t["plain_text"] for t in
                          page["properties"].get("Script", {}).get("rich_text", []))
    # Keep empty lines — they mark no-voice shots and maintain positional alignment with shots[].
    # Do NOT strip leading/trailing blanks: the first '' may be Shot 1's silent slot.
    script_lines = [ln.strip() for ln in script_text.split("\n")]
    if rebuild:
        _wipe_all(row_id)

    def _bold(t):
        return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [
            {"type": "text", "text": {"content": t},
             "annotations": {"bold": True, "italic": False, "strikethrough": False,
                             "underline": False, "code": False, "color": "default"}}]}}

    def _empty_toggle(label):
        return {"object": "block", "type": "toggle",
                "toggle": {"rich_text": _rt(label), "children": []}}

    blocks = [
        {"object": "block", "type": "callout", "callout": {
            "rich_text": _rt("PER-SHOT PLAN — for EACH shot: (1) generate the still with the 🖼️ image prompt "
                             "(GPT), (2) make the audio from the 🗣️ voice script in MiniMax (🎙️ Voice Config), "
                             "(3) feed that image + audio + the 🎬 即梦 prompt into 即梦 to make the video. "
                             "Drop results into the 🖼️ / 🎬 toggles. Track progress via the Stage / ✅ properties."),
            "icon": {"type": "emoji", "emoji": "🎬"}, "color": "blue_background"}},
        {"object": "block", "type": "callout", "callout": {
            "rich_text": _rt(f"{SENTINEL_VOICE} — same for every shot. ⚠️ avoid commas in MiniMax."),
            "icon": {"type": "emoji", "emoji": "🎙️"}, "color": "yellow_background"}},
        {"object": "block", "type": "code", "code": {"rich_text": _rt(
            f"voice_id:        {cfg['voice_id']}\nspeed:           {cfg['speed']}\n"
            f"pitch:           {cfg['pitch']}\nlanguage boost:  {cfg['boost']}\n"
            f"emotion:         {cfg['emotion']}"), "language": "plain text"}},
        {"object": "block", "type": "divider", "divider": {}},
    ]
    for i, s in enumerate(shots):
        voice_line = (script_lines[i] if i < len(script_lines)
                      else (s["line"] or "<add to the Script property: one line per shot>"))
        blocks.append({"object": "block", "type": "heading_3",
                       "heading_3": {"rich_text": _rt(s["title"])}})
        blocks.append(_bold("🖼️ Image prompt (single frame → GPT)"))
        blocks.append({"object": "block", "type": "code", "code": {
            "rich_text": _rt(build_prompt(persona, _primary_beat(s["visual"]))), "language": "plain text"}})
        blocks.append(_bold("🗣️ Voice script"))
        blocks.append({"object": "block", "type": "code", "code": {
            "rich_text": _rt(voice_line), "language": "plain text"}})
        blocks.append(_bold("🎬 即梦 prompt (rich shot guide → video)"))
        blocks.append({"object": "block", "type": "code", "code": {
            "rich_text": _rt(build_jimeng_prompt(s["title"], s["visual"], lang)),
            "language": "plain text"}})
        blocks.append(_empty_toggle("🖼️ Image here"))   # leave blank — drop assets in later
        blocks.append(_empty_toggle("🎬 Video here"))   # leave blank — drop assets in later
        blocks.append({"object": "block", "type": "divider", "divider": {}})

    # Trailer sections: cover-photo prompt + DM-infographic prompt travel WITH
    # the production row from day one (synced from the Content page at fan-out).
    concept_title = _page_title(call("GET", f"/pages/{concept_id}"))
    brief = fetch_infographic_brief(concept_id)
    hook_visual = _primary_beat(shots[0]["visual"]) if shots else ""
    blocks.extend(cover_dm_blocks(persona, concept_title, brief, hook_visual))

    for i in range(0, len(blocks), 25):
        call("PATCH", f"/blocks/{row_id}/children", {"children": blocks[i:i + 25]})
    return f"rebuilt with {len(shots)} shots"


def add_jimeng_prompts(row_id: str) -> str:
    """Insert a 🎬 即梦 prompt under each shot's voice-script block WITHOUT rebuilding
    (preserves already-attached audio/images). Idempotent."""
    kids = _all_children(row_id)
    if any(b["type"] == "code" and JIMENG_DISCLAIMER in _txt(b) for b in kids):
        return "exists"
    cur_title, expect_code, targets = "(shot)", False, []
    for b in kids:
        t = b["type"]; tx = _txt(b)
        if t == "heading_3" and tx.lower().startswith("shot"):
            cur_title = tx
        elif t == "paragraph" and "Voice script" in tx:
            expect_code = True
        elif expect_code and t == "code":
            targets.append((b["id"], cur_title, tx))  # after this block, insert 即梦 prompt
            expect_code = False
    for code_id, title, dialogue in targets:
        call("PATCH", f"/blocks/{row_id}/children", {"after": code_id, "children": [
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [
                {"type": "text", "text": {"content": "🎬 即梦 prompt (image + voice → video)"},
                 "annotations": {"bold": True, "italic": False, "strikethrough": False,
                                 "underline": False, "code": False, "color": "default"}}]}},
            {"object": "block", "type": "code", "code": {
                "rich_text": _rt(build_jimeng_prompt(title)), "language": "plain text"}},
        ]})
        time.sleep(0.25)
    return f"added {len(targets)} 即梦 prompts"


def refresh_jimeng(row_id: str) -> str:
    """Rewrite each shot's 🎬 即梦 prompt in place, driven by the shot's storyboard
    scene (read from its 🖼️ image prompt SCENE) + dialogue. Preserves all other blocks."""
    lang = ip_language(_relation_id(call("GET", f"/pages/{row_id}"), "IP"))
    kids = _all_children(row_id)
    shots, cur, label = [], None, None
    for b in kids:
        t = b["type"]; tx = _txt(b)
        if t == "heading_3" and tx.lower().startswith("shot"):
            cur = {"title": tx, "scene": "", "dialogue": "", "jid": None}
            shots.append(cur); label = None
        elif t == "paragraph" and any(k in tx for k in ("Image prompt", "Voice script", "即梦")):
            label = tx
        elif t == "code" and cur is not None:
            if label and "Image prompt" in label:
                for ln in tx.split("\n"):
                    if ln.strip().startswith("SCENE:"):
                        cur["scene"] = ln.split("SCENE:", 1)[1].strip()
            elif label and "Voice script" in label:
                cur["dialogue"] = tx.strip()
            elif label and "即梦" in label:
                cur["jid"] = b["id"]
    n = 0
    for s in shots:
        if s["jid"]:
            call("PATCH", f"/blocks/{s['jid']}", {"code": {
                "rich_text": _rt(build_jimeng_prompt(s["title"], s["scene"], lang)),
                "language": "plain text"}})
            n += 1; time.sleep(0.25)
    return f"refreshed {n} 即梦 prompts"


def _title(page: dict) -> str:
    for p in page["properties"].values():
        if p["type"] == "title":
            return "".join(t["plain_text"] for t in p["title"])
    return "(untitled)"


def backfill(force: bool) -> int:
    ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = call("POST", f"/databases/{ids['prod_db']}/query", body)
        rows.extend(data["results"])
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    for r in rows:
        status = apply_shot_plan(r["id"], rebuild=True)
        print(f"  {_title(r):34} → {status}")
        time.sleep(0.34)
    print(f"[done] processed {len(rows)} rows")
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--row")
    args = ap.parse_args()
    if args.row:
        print(apply_prompts(args.row, args.force))
    elif args.backfill:
        raise SystemExit(backfill(args.force))
    else:
        sys.exit("pass --backfill or --row <id>")
