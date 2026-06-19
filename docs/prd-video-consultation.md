# PRD — AI 視頻診症系統

**Product:** 陳芷晴中醫師 AI 視頻診症助理
**Platform:** Web (mobile-first, works on desktop)
**Last updated:** 2026-06-19
**Status:** Live on `https://tcm-jessica.onrender.com`

---

## 1. Overview

Patient connects to a browser-based video call. The AI (Chloe 陳芷晴) acts as the practitioner — listening, observing through the camera, asking TCM diagnostic questions, and sending a structured summary back to the patient's DM after the call ends.

No app install. No account. One link, one tap.

---

## 2. Entry Flow

### 2.1 Trigger

A consultation room is created when a patient sends a booking intent DM to the Instagram or Facebook page.

**Booking intent keywords (regex-matched):**
`約診 / 預約 / 睇診 / 睇醫生 / 診症 / 視頻診症 / video call / book / consultation / 想約`

**Flow:**
1. Patient DMs Kevin's IG/FB: *"我想約診"*
2. Chloe detects booking intent → calls `POST /api/consultation/create` with the patient's `crm_key`
3. Chloe sends the `patient_url` back to the patient's DM

### 2.2 Room Creation API

```
POST /api/consultation/create
Content-Type: application/json

{
  "crm_key": "ig_<igsid>" | "fb_<psid>",
  "preferred_time": ""
}

→ 200 OK
{
  "room_id": "abc123def456",
  "patient_url": "https://tcm-jessica.onrender.com/consult/abc123def456?role=patient",
  "practitioner_url": "https://tcm-jessica.onrender.com/consult/abc123def456?role=practitioner",
  "status": "pending"
}
```

`crm_key` encodes the patient's origin platform. Used at end of call to route the post-call summary back to the correct DM channel.

---

## 3. Connection Flow

### 3.1 Welcome Splash (pre-call gate)

On page load, patient sees a full-screen splash before any media permissions are requested:

- Clinic branding: 🌿 陳芷晴中醫師
- Subtitle: AI 視頻診症助理
- Instruction to allow microphone and camera
- Single CTA button: **接通診症**

The splash gates all media permission prompts — browser does not ask until the patient explicitly taps.

### 3.2 Startup Sequence (after tap)

```
Patient taps "接通診症"
  ↓
setupMedia()
  Request getUserMedia({ audio: true, video: { facingMode: 'user' } })
  If camera denied → mic-only mode, selfView hidden
  Build AudioContext + AnalyserNode from mic stream
  ↓
connect()
  Open WebSocket to wss://tcm-jessica.onrender.com/ws/voice/{room_id}
  ↓
Server: send welcome audio (pre-cached at startup, zero latency)
  {type: "response", text: "你好，歡迎嚟到...", audio_b64: "..."}
  Chloe speaks her opening lines
  {type: "ready"}
  ↓
calibrateNoise()
  Sample 1.2s ambient noise → set dynamic VAD threshold
  ↓
startVAD() + startLiveRecog()
  Patient can now speak
```

### 3.3 Server-side Startup (lifespan)

At server startup, `warmup_welcome_audio()` pre-generates the welcome TTS and caches it in memory. First patient gets instant audio with zero TTS latency.

---

## 4. Voice Activity Detection (VAD)

Client-side, energy-based, using Web Audio API `AnalyserNode` (bins 2–79, covering ~86 Hz–3.4 kHz speech range).

### 4.1 Parameters

| Constant | Value | Purpose |
|----------|-------|---------|
| `VAD_THRESHOLD` | 14 | Minimum floor (overridden by calibration) |
| `SPEECH_START_MS` | 280ms | Must detect voice continuously before recording starts |
| `SILENCE_END_MS` | 850ms | Silence duration that ends the recording |
| `MIN_AUDIO_MS` | 400ms | Clips shorter than this are discarded |
| `MAX_AUDIO_MS` | 8000ms | Hard safety cap |
| `BARGE_IN_MS` | 600ms | Patient speaking this long while Chloe talks → interrupt |

### 4.2 Calibration

On each connection, samples 1.2s of ambient noise:
```
dynamicThreshold = min(max(VAD_THRESHOLD, p75 × 1.3), 80)
```
Handles noisy environments (fans, AC, street noise) without the threshold being unreachable.

### 4.3 Silence Detection

Uses `lastSpeechAt` approach: recording stops when `now - lastSpeechAt > SILENCE_END_MS`. Avoids the ambiguous zone problem of hysteresis-based silence detection.

### 4.4 Browser Compatibility

`getSupportedMimeType()` tries MIME types in order:
1. `audio/webm;codecs=opus` (Chrome)
2. `audio/webm`
3. `audio/mp4;codecs=mp4a.40.2` (Safari)
4. `audio/mp4`
5. `audio/ogg;codecs=opus`
6. `audio/ogg`

Server detects the actual format from magic bytes and sets the correct filename hint for Whisper:
- `0x1A45DFA3` → `.webm`
- bytes 4–8 = `ftyp` → `.mp4`
- `OggS` → `.ogg`

---

## 5. Per-Turn Pipeline

### 5.1 Client → Server

When patient finishes speaking:

```
1. captureFrame()
   Draw selfVideo to hidden 320×240 canvas
   Encode as JPEG (quality 0.65) → raw base64 (no data-URI prefix)
   Note: drawImage() reads the raw MediaStream, ignoring CSS scaleX(-1) mirror

2. WS send JSON (before audio):
   { type: "vision_frame", image_b64: "..." }
   OR if camera is off:
   { type: "vision_frame", camera_off: true }

3. WS send binary:
   audio blob (WebM or MP4, from MediaRecorder)
```

### 5.2 Server Processing

```
Receive vision_frame JSON
  → camera_available = true / false
  → if image: asyncio.create_task(analyze_vision_frame(...))  ← runs concurrently

Receive audio binary
  → Whisper STT  (~1–2s)
     while Whisper runs, vision task is completing in background

await vision_task (timeout 3s)
  → collect vision_notes

ChloeAgent._generate(
    voice_call=True,
    vision_notes=vision_notes,
    camera_available=camera_available
)
  → Anthropic LLM call

MiniMax TTS
  → model: speech-2.8-hd
  → voice: Cantonese_GentleLady
  → pitch: +1, speed: 1.0

Send to client:
  {type: "transcript", text: "..."}     ← patient's transcribed words
  {type: "response", text: "...", audio_b64: "..."}
```

Vision analysis runs **concurrently** with STT — zero added latency to the response time.

---

## 6. TCM 望診 (Visual Inspection)

### 6.1 What Is Captured

Every patient turn, a 320×240 JPEG is sent to GPT-4o Vision with this TCM inspection prompt:

> 請用繁體中文，以條列方式輸出觀察到的資訊：
> - 面色 (complexion)
> - 眼神 (eyes / dark circles / eye bags)
> - 脣色 (lip colour)
> - 舌象 (tongue colour & coating, if visible)
> - 整體神態 (overall vitality)

GPT-4o Vision is called with `detail: low` for speed and cost.

### 6.2 Three Camera States

| State | Detection | Chloe Behaviour |
|-------|-----------|----------------|
| Camera on, face visible | `vision_notes` ≥ 20 chars | Uses observations to ask targeted questions (e.g. 面色偏白 → 詢問是否怕冷) |
| Camera on, frame unclear | `camera_available=True` but `vision_notes` empty | Asks patient to adjust angle, show tongue to camera |
| Camera off | `camera_off: true` from browser | Proactively asks patient to enable camera, explains 望診 is required — does not accept verbal description as substitute |

### 6.3 Voice Call Mode Override

When `voice_call=True`, a preamble is prepended to Chloe's persona system prompt:

- Establishes she is on a **video call**, not an IG DM
- She can see the patient — never ask for photos
- To perform 望診: ask patient to face camera / show tongue directly
- Natural spoken language (no bullet points, no markdown, no IG emoji cadence)
- WhatsApp CTA suppressed entirely
- Deeper clinical questions permitted

---

## 7. Barge-in & Audio Control

**Barge-in:** VAD continues running while Chloe is talking. If patient speaks for `BARGE_IN_MS` (600ms) continuously, `currentSource.stop()` is called immediately. Chloe stops mid-sentence. Subtitle queue is cleared. VAD resumes.

**End call:** Same mechanism. `currentSource.stop()` called instantly on tap of 結束 button.

Both operations act on the `AudioBufferSourceNode` ref (`currentSource`), which is the only reliable cross-browser way to stop Web Audio playback immediately.

---

## 8. Subtitles

Movie-style chunked display:

1. Text split into chunks ≤ 18 Chinese characters, breaking on sentence-ending punctuation (`。！？…`) then mid-sentence (`，；、：`)
2. Total audio duration obtained from `AudioContext.decodeAudioData()` before playback starts
3. Hold time per chunk: `max(700ms, (chunk_chars / total_chars) × (audio_duration - 600ms))`
4. Last chunk fades 1.2s after the final chunk shows

Patient's own speech shown as dimmed italic (`你：...`) for 5s, replaced by Chloe's subtitles when response arrives.

---

## 9. Live Transcript

Web Speech API (`SpeechRecognition`, lang `zh-HK`) provides real-time interim results as the patient speaks. Displays below Chloe. Paused while Chloe is speaking. Auto-restarts on `onend` / `onerror` if VAD is still active. Gracefully absent if browser doesn't support it (no error).

---

## 10. Post-Call Summary

Triggered in the WebSocket handler's `finally` block on disconnect.

### 10.1 Generation

```python
gpt-4o-mini call with conversation history

Output format:
【問診總結】

📋 主訴：（1–2 sentences）
💡 討論要點：（1–3 sentences）
📝 建議：（1–3 sentences）

—— 陳芷晴中醫師 AI 問診助理
```

Requires at least 1 patient turn. Empty history → skipped.

### 10.2 Routing

```
crm_key prefix → platform

ig_<igsid>   → Instagram DM  (Graph API POST /me/messages)
fb_<psid>    → Messenger DM  (Graph API POST /me/messages)
<other>      → skipped (no platform to send to)
```

Uses `META_GRAPH_BASE=https://graph.instagram.com`, `META_GRAPH_VERSION=v23.0`.

---

## 11. In-Call Controls

| Button | Action |
|--------|--------|
| 🎙️ 靜音 | Toggle mic track enabled/disabled. Aborts current recording if active. |
| 📷 鏡頭 | Toggle camera track. Dims selfView to 0.3 opacity. |
| 📵 結束 | Stops VAD, kills audio, closes WebSocket (without reconnect), stops all media tracks, closes AudioContext. Renders 診症完畢 screen. |

---

## 12. UI Layout

```
┌─────────────────────────────────┐
│                                 │ ← Chloe full-screen photo
│   Status pill (top-centre)      │   object-position: center 18%
│                                 │
│   Green glow border when        │
│   Chloe is speaking             │
│                                 │
│                        ┌──────┐ │
│                        │ you  │ │ ← Patient PiP 88×120px
│                        └──────┘ │   bottom-right, mirrored
│                                 │
│   Subtitle text (bottom)        │
│                                 │
│  🎙️ 靜音   📷 鏡頭   📵 結束   │ ← Controls bar
└─────────────────────────────────┘
```

Visual states on Chloe's photo:
- **Speaking:** green glow border, `speakPulse` animation
- **Thinking:** brightness 0.88 dim
- **Idle:** no overlay

---

## 13. Infrastructure

| Component | Technology |
|-----------|-----------|
| Server | FastAPI + uvicorn |
| WebSocket | FastAPI native WebSocket |
| STT | OpenAI Whisper (`whisper-1`) |
| LLM | Anthropic Claude via ChloeAgent |
| TTS | MiniMax `speech-2.8-hd`, `Cantonese_GentleLady`, pitch +1 |
| Vision | OpenAI GPT-4o, `detail: low` |
| Post-call routing | Meta Graph API v23.0 |
| Hosting | Render Singapore, Starter plan |
| Database | Postgres (production) / SQLite (local dev) |
| Environment | `CONSULT_BASE_URL`, `IG_PAGE_ACCESS_TOKEN`, `OPENAI_API_KEY`, `MINIMAX_API_KEY`, `META_APP_SECRET`, `META_VERIFY_TOKEN` |

---

## 14. Conversation State

In-memory per WebSocket connection (not persisted to CRM):
- `history: list[ConversationMessage]` — capped at last 20 turns
- `vision_notes: str` — latest TCM observation, replaced each turn
- `camera_available: bool` — tracks camera state
- `vision_task: asyncio.Task` — concurrent vision analysis handle

Persisted to DB:
- Consultation room record (`id`, `crm_key`, `status`, `created_at`)

---

## 15. Known Limitations & Roadmap

| Item | Priority | Notes |
|------|----------|-------|
| Silero VAD (neural end-of-speech) | High | More precise than energy threshold; eliminates false triggers from breath/ambient noise |
| PTT (push-to-talk) fallback | Medium | For environments where VAD is unreliable |
| WhatsApp post-call summary | Medium | Different send path — needs WA client, not Graph API |
| Tongue detection prompt | Medium | Dedicated "show tongue" prompt mid-consultation |
| Real practitioner join | Low | Architecture (signaling hub) exists, not wired to UI |
| Multi-language (Mandarin / English) | Low | Not scoped |
| Session recording / replay | Not scoped | Privacy implications |
