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


def build_prompt(persona: str, visual: str) -> str:
    """One shot = ONE single frame. The doctor's identity is locked only when the
    doctor is in the frame. Other people (e.g. a patient) appear when the scene
    calls for it — we never blanket-ban extra people."""
    v = visual.lower()
    has_doctor = any(k in v for k in ("doctor", "to camera", "looking at camera",
                                      "talking", "presenter", "gestur", "smile"))
    lines = [
        "One single photorealistic vertical 9:16 frame — a single moment. "
        "No split screen, no collage, no before/after, no multiple panels.",
        "Setting: warm, traditional Chinese-medicine clinic lighting, shallow depth of field.",
        f"SCENE: {visual}",
    ]
    if has_doctor:
        lines.append(f"The doctor must be the EXACT same person as the reference photo "
                     f"({persona}) — same face, hair, age.")
    lines.append("Include only the people the scene describes (a patient may appear when the "
                 "scene needs one). No on-screen text, no watermark.")
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


def build_jimeng_prompt(title: str, visual: str = "", lang: str = "") -> str:
    """The prompt that goes INTO 即梦 (audio-native). Everything that gets UPLOADED is a
    variable: the image (画面+人物) = {{图片}}, the dialogue audio = {{对白}}. We only
    author the read-language (from the row's IP) + camera (运镜, derived from the
    storyboard shot) + the AI-digital-human disclaimer."""
    scene = f"画面 / 动作（按分镜）：{visual}\n" if visual else ""
    read = "人物對口型朗读" + (f"{lang}对白" if lang else "对白") + "：{{对白}}（以上传音频为准）\n"
    return ("音频驱动（Audio Native）数字人视频。\n"
            f"{scene}"
            "图片：{{图片}}（以上传图片为准）\n"
            f"{read}"
            f"运镜：{_jimeng_camera(title, visual)}。保持 9:16 竖屏、自然光。\n"
            f"{JIMENG_DISCLAIMER}")


def _relation_id(page: dict, prop: str) -> str | None:
    rel = page["properties"].get(prop, {}).get("relation", [])
    return rel[0]["id"] if rel else None


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
    script_lines = [ln.strip() for ln in script_text.split("\n") if ln.strip()]
    if rebuild:
        _wipe_all(row_id)

    def _bold(t):
        return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [
            {"type": "text", "text": {"content": t},
             "annotations": {"bold": True, "italic": False, "strikethrough": False,
                             "underline": False, "code": False, "color": "default"}}]}}

    blocks = [
        {"object": "block", "type": "callout", "callout": {
            "rich_text": _rt("PER-SHOT PLAN — upload the IP photo to GPT once. Then for EACH shot below: "
                             "copy the 🖼️ image prompt into GPT, and the 🗣️ voice script into MiniMax "
                             "(settings in 🎙️ Voice Config). Lip-sync image + audio in 即梦. "
                             "Track progress with the Stage / ✅ properties above."),
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
        blocks.append(_bold("🖼️ Image prompt"))
        blocks.append({"object": "block", "type": "code", "code": {
            "rich_text": _rt(build_prompt(persona, s["visual"])), "language": "plain text"}})
        blocks.append(_bold("🗣️ Voice script"))
        blocks.append({"object": "block", "type": "code", "code": {
            "rich_text": _rt(voice_line), "language": "plain text"}})
        blocks.append(_bold("🎬 即梦 prompt (image + voice → video)"))
        blocks.append({"object": "block", "type": "code", "code": {
            "rich_text": _rt(build_jimeng_prompt(s["title"], s["visual"], lang)),
            "language": "plain text"}})
        blocks.append({"object": "block", "type": "divider", "divider": {}})

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
