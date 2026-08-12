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


def build_prompt(persona: str, visual: str, talking: bool = False) -> str:
    """One shot = ONE single frame. Setting is derived from the visual description —
    not hardcoded. Street/outdoor shots use natural light; clinic shots use clinic light.
    People (patient, guest, bystander) appear only when the scene explicitly describes them.

    `talking` added 2026-07-16: when the shot has spoken dialogue, the STILL
    that feeds 即梦's multimodal2video must be a lip-syncable talking head —
    single person, face near-frontal to camera, eyes OPEN, mouth visible.
    Root-caused on Phone Neck Shot 3: the shot guide was a demo beat ("neck
    roll, eyes closed" + a second person in frame), gpt-image-2 faithfully
    produced a two-person, eyes-closed, head-down image, and multimodal2video
    then hung forever (both documented triggers: two faces + no frontal
    speaking face → silent lip-sync failure). For a dialogue shot the
    talking-head framing OVERRIDES the demo posture — the words are the point,
    the technique is narrated, not silently performed."""
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
    if talking:
        # A lip-syncable talking head overrides any demo posture in the beat.
        lines.append(
            "IMPORTANT — this is a talking-to-camera shot: exactly ONE person "
            "in frame, alone, facing the camera near-frontally, eyes OPEN and "
            "looking at the camera, mouth clearly visible mid-speech. Any "
            "demonstration is shown by the single presenter facing camera "
            "(gesturing / holding a prop), NEVER by turning away, closing the "
            "eyes, tilting the head down, or adding a second person.")
    if has_doctor or talking:
        lines.append(f"The main character must be the EXACT same person as the reference photo "
                     f"({persona}) — same face, hair, age, ethnicity.")
    lines.append("Include only the people explicitly described in the scene. "
                 "No extra faces, no on-screen text, no watermark.")
    return "\n".join(lines)


JIMENG_DISCLAIMER = "请注意，这些都是 AI 数字人，不是真人。没有真人也可以直接生成影片。"


def _jimeng_camera(title: str, visual: str = "", lang: str = "") -> str:
    """Camera/运镜 keyed off the shot BEAT (the title), not the visual text — so a word
    like 'gesturing' in one shot can't leak its camera into another.

    Language-aware as of 2026-07-16: this function used to return Chinese
    UNCONDITIONALLY regardless of the IP's language — meaning an otherwise
    all-English Jackie prompt still had one Chinese-language clause sitting
    inside its 【Camera】 line. Per Seedance's own audio-guide skill, language
    strength is uneven and Mandarin-weighted in training; a prompt that mixes
    languages gives the model less reason to lock onto the uploaded audio's
    actual (English) language rather than drifting to its strongest-trained
    one. English/Cantonese-tagged IPs now get an English camera direction —
    only genuinely Chinese-language IPs (Mandarin) keep the Chinese phrasing,
    since 运镜 vocabulary in Chinese is native/correct for that case, not a
    leftover default."""
    t = title.lower()
    if lang not in ("", "普通话"):  # English, Cantonese, and every other non-Mandarin IP language
        if "hook" in t:
            return "Slow push-in, drawing the viewer in"
        if "cta" in t:
            return "Slow push-in to the face, warm and personal close"
        if any(k in t for k in ("quick", "win", "demo", "method", "try", "remedy", "recipe")):
            return "Medium shot, camera naturally follows the hand action, slight handheld feel"
        if any(k in t for k in ("safety", "principle", "caution", "root")):
            return "Stable frame, slight push-in, serious expression"
        return "Subject centered, slow gentle push-in, natural breathing and blinking"
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
    # Anatomy + acupoint vocabulary (added 2026-07-16 after Phone Neck Shot 3
    # hung 3/3 consecutive multimodal attempts — ~9% odds if pure hang-lottery
    # — with "base of your skull" in the quoted dialogue and "風池穴 ... at
    # skull base" in the shot guide; same medical-content-review trigger
    # class as the 07-10 root cause):
    (re.compile(r"\bskull\b", re.I), "head"),
    (re.compile(r"[一-鿿]{1,3}穴"), "acupressure point"),
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


def build_jimeng_prompt(title: str, visual: str = "", lang: str = "", dialogue: str = "") -> str:
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
         uploaded reference image / audio") instead of {{图片}}/{{对白}} tokens.

    【Speech】 + 【Camera】 rewritten 2026-07-16 after Shivonne reported videos
    for English-configured shots kept coming back with Chinese script/voice.
    Root-caused via the seedance-20 skill's audio-guide.md (field-observed
    community testing, not guesswork): an uploaded audio reference is NOT
    automatically treated as "these are the exact words, in this exact
    language" — surfaces default to treating it as a rhythm/mood reference
    unless the prompt explicitly assigns it the stronger role, and the
    underlying model is Mandarin-weighted by training, so an under-specified
    audio role lets it drift toward synthesizing its own (Mandarin) speech
    instead of strictly lip-syncing the uploaded track. Compounding factor
    found in THIS codebase: _jimeng_camera() returned Chinese unconditionally
    regardless of IP language, so an English shot's prompt was English text
    with one Chinese clause sitting in the middle of it — a mixed-language
    prompt gives the model less signal to lock onto English. Fix: (a)
    _jimeng_camera() is now language-aware (English camera direction for
    non-Mandarin IPs), (b) 【Speech】 assigns the uploaded audio the "exact
    spoken words" role.

    【Speech】 rewritten AGAIN same day (second pass) after the first version
    made things categorically worse — EVERY shot stopped using the uploaded
    voice at all, not just the wrong-language subset. Root cause: the first
    version leaned on negation to lock the role ("Do NOT synthesize new
    speech. Do NOT invent dialogue. Do NOT translate or switch language."),
    plus stated the locked language twice. Per model-mechanics.md's mechanism
    #3 ("there is no NOT" — text conditioning moves probability TOWARD every
    concept it names; negation is weak grammar wrapped around a strong
    activation, so telling the model "do not synthesize new speech" still
    primes it toward synthesizing new speech) and mechanism #1 (attention is
    a finite budget; short dense prompts beat long repetitive ones). The
    ORIGINAL 07-10 template — which Shivonne confirmed worked — used exactly
    ONE short positive sentence for the read-aloud instruction and no
    negation at all. That pattern is restored here: state the audio's role
    positively (it IS the dialogue, lip-sync to it) instead of listing what
    it must not become.

    `dialogue` param added same day (third pass) after Shivonne reported the
    positive-only rewrite STILL wasn't strictly following the uploaded voice.
    Real gap found: this function never had a way to receive the shot's
    actual voice-script text in the first place — 【Speech】 only ever
    gestured at "the uploaded audio" in the abstract, never quoted the words
    being said. Per seedance-troubleshoot's diagnostic tree, "Lip-sync poor"
    lists "unassigned speaker" as a documented cause, and audio-guide.md's
    Dialogue section says explicitly: "Put spoken dialogue in quotes. Assign
    the speaker by tag." — i.e. the model wants the literal line as text,
    not just an audio waveform to imitate. When `dialogue` is supplied,
    【Speech】 now quotes it with an assigned speaker tag; the audio
    reference is framed as "how it sounds", the quoted text as "what is
    said" — the two channels reinforcing each other instead of the video
    channel having zero textual signal about the actual words."""
    visual_clean = sanitize_for_jimeng(visual or "")
    lang_en = _LANG_EN.get(lang, lang)
    # The quoted dialogue must pass content review too — quoting the RAW voice
    # script leaked unsanitized medical vocabulary straight into the prompt
    # (found 2026-07-16: "base of your skull" in a quoted line → 3/3 hangs).
    # The audio still carries the true verbatim words; the quote is the text
    # hint, so a safety-substituted word in it costs almost nothing.
    dialogue = sanitize_for_jimeng((dialogue or "").strip())
    lang_word = f" in {lang_en}" if lang_en else ""
    # Dialogue shots: 【Speech】 comes FIRST (right after the header) and the
    # Shot Guide gets a harmonizing clause. Added 2026-07-16 (fourth pass)
    # after a verified-correct-voice generation still played the audio as
    # VOICEOVER — mouth not moving — because the Shot Guide directed the
    # presenter to tilt her head down at a phone + cut to an insert, actions
    # that hide the face and physically preclude lip-sync. Per the seedance
    # skill: mechanism #1 (earlier clauses win more conditioning influence —
    # so speaking-to-camera must outrank the action beats) and audio-guide's
    # lip-sync rules ("use stable framing for lip-sync; avoid head turns,
    # large face movement... while mouth accuracy matters"). The harmonizing
    # clause resolves the guide-vs-lip-sync conflict positively (what IS:
    # face stays toward camera while speaking) instead of deleting the
    # creative beats.
    if dialogue:
        speech = (
            "The presenter speaks directly to camera for the entire clip — face "
            "frontal, mouth clearly visible, lips moving in precise sync with the "
            f'uploaded audio from the first word to the last. The exact line: "{dialogue}" '
            f"— this is the uploaded audio, spoken{lang_word}. Comfortable pace, "
            "occasional natural blinking and breathing."
        )
        guide_body = (
            f"{visual_clean.rstrip('。.; ')}. Throughout every beat the presenter "
            "keeps facing the camera, mouth visible, speaking the line."
        ) if visual_clean else ""
    else:
        speech = (
            f"Lip-sync to the uploaded audio reference — it is the dialogue"
            f"{lang_word}, lips moving in precise sync with the uploaded audio from "
            "the first word to the last. Comfortable pace, occasional natural "
            "blinking and breathing."
        )
        guide_body = visual_clean
    shot_guide = f"【Shot Guide】{guide_body}\n" if guide_body else ""
    speech_sec = f"【Speech】{speech}\n"
    character_sec = (
        "【Character】AI virtual presenter. Use the uploaded reference image as the "
        "appearance reference. Keep the same hairstyle, clothing, facial features, "
        "age and expression. Consistent identity throughout the video.\n"
    )
    # Speaking shots: Speech outranks the Shot Guide. Silent shots: original order.
    body = (speech_sec + shot_guide + character_sec) if dialogue else (shot_guide + character_sec + speech_sec)
    return (
        "音频驱动（Audio Native）数字人视频。\n"
        f"{body}"
        "【Style】Educational wellness presentation. Calm. Friendly. Professional. "
        "Natural. No dramatic acting. No exaggerated gestures.\n"
        f"【Camera】{_jimeng_camera(title, visual, lang)}。Maintain 9:16 vertical composition. "
        "Warm soft natural lighting.\n"
        "【Important】This is an AI-generated virtual presenter for educational "
        "purposes. No patient. No treatment. No doctor. No diagnosis. No medical "
        "advice. No medical procedures. No surgery. No injections. No blood. "
        "NO glow. NO halo. NO light effects. NO magical particles. "
        "Textless plate: NO subtitles. NO captions. NO burned-in text of any kind, "
        "in any language. No lyrics text. "
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


# Actual emoji Unicode blocks only — NOT a blanket non-ASCII strip, since
# Chloe's titles are Cantonese/CJK and must survive. Image-generation models
# reliably render emoji as garbled glyphs/tofu boxes when told to render
# literal text containing them (same failure mode fixed for the PIL cover
# overlay on 2026-07-14 — this is the AI-native-text equivalent).
_EMOJI_RE = re.compile(
    "[" "\U0001F300-\U0001FAFF" "\U00002600-\U000027BF" "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF" "\U00002B00-\U00002BFF" "\U0000FE0F" "]+"
)


def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()


def build_cover_prompt(persona: str, title: str, hook_visual: str = "") -> str:
    """Cover/thumbnail prompt — viral YouTube-thumbnail style with the title
    baked directly into the image by gpt-image-2.

    Rewritten 2026-07-16 after Shivonne flagged that recent covers ("plain
    text + IP photo") looked much worse than the early hand-crafted ones
    (Tonsil Stone, Detox Juice, Constant Anxiety — all published, all still
    live in Notion). Root cause found by pulling those actual images: they
    were never generated by this function — build_cover_prompt() didn't
    exist yet when they were made (git-blamed to a single commit, no prior
    history), and their Content Library pages have no cover prompt of any
    kind. They were bespoke, one-off prompts typed directly into an image
    tool, never captured in code. This version reverse-engineers their
    consistent visual template from the actual published images (all 3
    independently confirm the same pattern) instead of guessing:
      - Bold condensed "Impact"-style font, ALL text inside a black
        rough/marker-edged highlight box
      - 1-3 punchy words picked out in bright yellow, the rest in white
      - A small yellow "attention burst" accent mark near the headline
      - Subject with an exaggerated reaction (shocked/intrigued), gesturing,
        positioned below/beside the text block, holding a topic-relevant prop
      - Warm, detailed TCM clinic background (herb jars, wooden cabinets,
        calligraphy signage) — never a plain/empty backdrop
    The previous version explicitly said "No on-screen text" (correct for
    SHOT prompts, where small dialogue captions render as garbled — wrong
    here: short, huge, high-contrast headline text is exactly what
    gpt-image-2 handles well, as the reference examples prove). Because the
    title is now baked in by the model, generate_cover.py no longer runs its
    PIL text-overlay pass on top — that would double the text.
    """
    title = _strip_emoji(title)
    topic_hint = f" Include one clear visual element from the hook scene: {hook_visual}" if hook_visual else ""
    return (
        "One single photorealistic vertical 9:16 COVER IMAGE for a short-video "
        "thumbnail — viral YouTube-thumbnail style. A single moment, no split "
        "screen, no collage, no panels.\n"
        f"The main character must be the EXACT same person as the reference photo "
        f"({persona}) — same face, hair, age, ethnicity.\n"
        "TEXT (render this directly in the image, large and bold):\n"
        f'"{title}"\n'
        "Typography: bold condensed sans-serif ('Impact'/poster style), all-caps "
        "energy, set inside a black rough-edged marker/brush-stroke highlight box "
        "that hugs the text tightly. Pick out the 1-3 most attention-grabbing words "
        "(the pain point, the surprising fact, or the question word) in bright "
        "saturated YELLOW — every other word in WHITE. Add one small yellow "
        "spark/burst accent mark near a top corner of the text block, like a "
        "hand-drawn '!' emphasis mark. Text block sits in the upper portion of the "
        "frame, sized to be readable at thumbnail scale on a phone screen.\n"
        "Subject: positioned below or beside the text block, expression exaggerated "
        "and scroll-stopping (shocked / concerned / intrigued), direct eye contact "
        "with the camera, one hand gesturing or pointing, the other holding a "
        f"prop directly relevant to the topic.{topic_hint}\n"
        "Background: warm, detailed, in-focus traditional Chinese medicine clinic — "
        "wooden herb cabinets, glass jars of herbs, calligraphy signage plaque — "
        "never a plain or empty backdrop.\n"
        f"TOPIC: {title}.\n"
        "Punchy color grading, crisp lighting, high contrast, professional "
        "thumbnail-designer composition. No watermark."
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
        # Guard: never feed the placeholder text itself to build_jimeng_prompt as
        # spoken dialogue — that would literally quote "<add to the Script...>"
        # as the presenter's line.
        dialogue_for_jimeng = "" if voice_line.startswith("<add to") else voice_line
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
            "rich_text": _rt(build_jimeng_prompt(s["title"], s["visual"], lang, dialogue_for_jimeng)),
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
                "rich_text": _rt(build_jimeng_prompt(title, dialogue=dialogue)), "language": "plain text"}},
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
                "rich_text": _rt(build_jimeng_prompt(s["title"], s["scene"], lang, s["dialogue"])),
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
