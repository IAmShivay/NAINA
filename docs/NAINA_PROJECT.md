# NAINA — Master Project Document
**Version:** 2.1 | **Last Updated:** 2026-04-20 | **Status:** Active Development

---

## What Is Naina

Naina is a Jarvis-style personal AI assistant that:
- Runs as `naina.exe` on Windows, auto-starts on boot (no admin)
- Listens for wake word **"Hey Naina"** (<1 second detection)
- Speaks and understands Hindi, English, Hinglish naturally
- Uses **Ollama llama3.2:3b** as the local default brain (100% offline)
- Falls back to **Groq llama3-70b** only when Ollama times out/fails
- Has 80+ tools across 15 categories (no fixed syntax — just talk naturally)
- Has a **Three.js Jarvis holographic GUI** controllable by hand gestures (MediaPipe)
- Is accessible from mobile via Cloudflare Tunnel (permanent free HTTPS URL)
- **Never says "I can't"** — falls back to CodeGen (writes + runs Python) for unknown tasks

---

## Project Phases

| Phase | Focus | Status |
|---|---|---|
| 1 | Foundation: structure, FastAPI, Ollama brain, STT/TTS, wake word, system tray, Three.js Jarvis GUI + hand gestures | **In Progress** |
| 2 | Core Tools: system control, productivity, entertainment, files, web info, basic coding | Planned |
| 3 | Communication: contacts, WhatsApp URI, email, SMS (ADB), calls | Planned |
| 4 | Health (ADB/FitCloud screen scrape + Google Fit), CodeGen fallback, Finance | Planned |
| 5 | Learning/Growth: pattern detection, tool promotion, hot-reload | Planned |

---

## Tech Stack

| Component | Technology | Notes |
|---|---|---|
| Language | Python 3.11 | All backend |
| Packaging | PyInstaller | Builds naina.exe |
| System tray | pystray + Pillow | Tray icon & menu |
| Wake word | openWakeWord | "Hey Naina" |
| STT (online) | Google Speech Recognition | `speech_recognition` lib |
| STT (offline) | Vosk | Fallback, no internet |
| TTS | edge-tts | `hi-IN-SwaraNeural` (Hindi), `en-IN-NeerjaNeural` (English) |
| LLM (default) | Ollama — llama3.2:3b | Local, always-on, 100% offline |
| LLM (fallback) | Groq — llama3-70b | Cloud, only on Ollama failure/timeout |
| Agent | Custom ReAct tool-calling loop | Multi-step sequential tool calls |
| CodeGen | Python + subprocess sandbox | Unknown tasks → write + run program |
| Contacts | rapidfuzz (WRatio scorer) | Fuzzy name/tag/phone matching |
| Web backend | FastAPI | REST + WebSocket |
| 3D GUI | Three.js r148 | Jarvis holographic UI (browser) |
| Gesture | MediaPipe Hands (JS) | Pinch=zoom, swipe=navigate, fist=select |
| PWA | HTML + Vanilla JS | Mobile-first, installable |
| Tunnel | Cloudflare Tunnel (cloudflared) | Permanent free HTTPS URL |
| Windows startup | Registry HKCU\...\Run | No admin required |
| Scheduler | APScheduler | Alarms, reminders, timers |
| Health (primary) | ADB WiFi + uiautomator dump | Screen scrape FitCloud app |
| Health (fallback) | Google Fit REST API | OAuth, free |
| Pattern learning | watchdog + custom detector | Detects repeated sequences |
| Contact fuzzy | rapidfuzz | WRatio scorer, cutoff 60 |

---

## Coding Conventions

- **Python 3.11** — use `match` statements, `|` union types, `async/await` throughout
- **All async** — FastAPI routes are `async def`, tools are sync but wrapped properly
- **Type hints everywhere** — every function signature has types
- **Logging** — use `loguru` for all logging → `naina.log`
- **Config** — all secrets/settings in `config.py`, never hardcoded
- **No print statements** — use `logger.info/debug/warning/error`
- **Error handling** — every tool catches its own exceptions, returns error dict
- **Tool return format:**
  ```python
  {"success": True/False, "result": "...", "error": "..." }
  ```
- **Hinglish responses** — Naina addresses user as "Boss", mixes Hindi/English naturally
- **Never refuse** — if no tool, trigger CodeGen fallback
- **JS** — vanilla JS only (no React/Vue), ES2022 modules, no build step
- **CSS** — CSS custom properties for theming, mobile-first

---

## File Structure

```
naina/
├── main.py                        # Entry: tray app, startup, orchestration
├── config.py                      # All settings, API keys, timeouts
├── requirements.txt
├── build.py                       # PyInstaller → naina.exe
│
├── agent/
│   ├── __init__.py
│   ├── brain.py                   # Ollama → Groq fallback LLM wrapper
│   ├── loop.py                    # ReAct agent loop (think→act→observe)
│   ├── dispatcher.py              # Tool dispatcher + intent matching
│   └── memory.py                  # memory.json read/write
│
├── voice/
│   ├── __init__.py
│   ├── wake_word.py               # openWakeWord "Hey Naina"
│   ├── stt.py                     # Google STT / Vosk offline
│   └── tts.py                     # edge-tts Swara/Neerja
│
├── api/
│   ├── __init__.py
│   ├── server.py                  # FastAPI app factory
│   ├── routes.py                  # /chat /voice /status /health /contacts
│   └── ws.py                      # WebSocket for real-time voice streaming
│
├── tools/
│   ├── __init__.py
│   ├── base.py                    # Tool base class + registry
│   ├── communication.py           # WhatsApp URI, mailto, ADB SMS, tel URI
│   ├── contacts.py                # Contact resolver, fuzzy matcher, sync
│   ├── entertainment.py           # YouTube, Spotify URI, jokes, quiz
│   ├── productivity.py            # Alarms, reminders, calendar, todos, notes
│   ├── system_control.py          # Shutdown, volume, brightness, screenshot
│   ├── files.py                   # File + folder operations
│   ├── web_info.py                # Search, weather, news, stocks, crypto
│   ├── coding.py                  # Code gen, debug, explain, run
│   ├── finance.py                 # Stocks, crypto, expense tracker
│   ├── health.py                  # FitCloud ADB scrape + Google Fit fallback
│   ├── ai_features.py             # Image gen, summarize, remember/recall
│   ├── mobile_control.py          # ADB + ntfy.sh Android control
│   └── user_tools.py              # Hot-reloaded user-generated tools
│
├── codegen/
│   ├── __init__.py
│   ├── generator.py               # write_and_run_program logic
│   ├── runner.py                  # Sandboxed subprocess executor
│   └── registry.py                # tool_registry.json management
│
├── learning/
│   ├── __init__.py
│   ├── pattern_detector.py        # Detects repeated command sequences
│   └── tool_promoter.py           # Promotes CodeGen scripts to permanent tools
│
├── web/
│   ├── index.html                 # Three.js Jarvis GUI (main PWA)
│   ├── manifest.json
│   ├── sw.js                      # Service worker
│   └── static/
│       ├── css/
│       │   └── jarvis.css         # Holographic dark UI styles
│       ├── js/
│       │   ├── three-scene.js     # Three.js holographic scene
│       │   ├── gesture.js         # MediaPipe hand gesture controller
│       │   ├── voice.js           # Web Speech API (STT + TTS)
│       │   └── app.js             # Main app logic, API calls, state
│       └── icons/
│           ├── icon-192.png
│           └── icon-512.png
│
├── tunnel/
│   └── cloudflare.py              # Starts cloudflared subprocess
│
└── data/
    ├── contacts.json              # Merged contact cache
    ├── notes.txt
    ├── todos.json
    ├── expenses.json
    ├── memory.json                # User name, preferences
    ├── tool_registry.json         # All tools (built-in + generated)
    ├── learned_patterns.json      # Detected usage sequences
    └── generated_scripts/         # Every CodeGen script with timestamp
```

---

## LLM Strategy

```
Request arrives
    │
    ▼
Ollama (llama3.2:3b, local)
    │
    ├─ responds within 8s ──────────────────────────► Use response ✅
    │
    └─ timeout / connection error
            │
            ▼
        Groq (llama3-70b, cloud)
            │
            ├─ responds ────────────────────────────► Use response ✅
            │
            └─ fails (no internet)
                    │
                    ▼
                Offline-only tools + CodeGen fallback
```

---

## Agent ReAct Loop

```
User text
    │
    ▼
LLM (with tool list in system prompt)
    │
    ▼
Parse output for: TOOL: name | INPUT: {...}
    │
    ├─ Tool found ──► Execute ──► Result ──► LLM ──► Next step / final response
    │
    └─ No tool ────► CodeGen fallback (write_and_run_program)
```

**Max iterations:** 10 per request. If still no final response after 10 tool calls, summarize what was done.

---

## Jarvis GUI — Three.js + MediaPipe Hand Gestures

### Visual Design
- **Background:** Deep black (`#000814`)
- **Primary accent:** Electric cyan (`#00d4ff`)
- **Secondary accent:** Deep blue (`#0055ff`)
- **Glow:** Cyan box/text shadows throughout
- **Font:** `Orbitron` (Google Fonts) — sci-fi monospace feel

### Three.js Scene Elements
1. **Central Orb** — rotating wireframe icosahedron, glowing cyan
2. **Floating Panels** — 5 panels orbit the orb: Chat, Health, Todos, Music, System
3. **Voice Ring** — ring geometry around orb, pulses on voice activity
4. **Particle Field** — 2000 floating particles, ambient "thinking" effect
5. **Arc Reactor Grid** — hexagonal grid behind everything, subtle glow

### MediaPipe Hand Gestures
| Gesture | Detection | Action |
|---|---|---|
| Pinch (thumb+index close, distance < 40px) | Both fingers tracked | Zoom in on current panel |
| Spread (thumb+index far, distance > 120px) | Both fingers tracked | Zoom out / overview |
| Swipe Right (wrist moves +200px in 0.3s) | Wrist velocity | Previous panel |
| Swipe Left (wrist moves -200px in 0.3s) | Wrist velocity | Next panel |
| Open Palm (all 5 tips extended) | Finger tip positions | Show overview, stop speaking |
| Fist (all fingers curled) | Finger curl angles | Select / confirm |
| Point Up (only index extended, tip above base) | Single finger | Scroll up |
| Point Down (only index extended, tip below base) | Single finger | Scroll down |

### Gesture Implementation
```js
// Pinch detection
const thumbTip = landmarks[4];
const indexTip = landmarks[8];
const dist = Math.hypot(thumbTip.x - indexTip.x, thumbTip.y - indexTip.y);
if (dist < 0.05) { /* PINCH */ }

// Swipe detection
const wrist = landmarks[0];
const velX = wrist.x - prevWrist.x;
if (Math.abs(velX) > 0.15) { /* SWIPE */ }
```

---

## Health Data Flow (Phase 4)

```
FitCloud phone app → ADB WiFi → uiautomator dump → XML parse → Ollama summary → Hinglish speech
                          ↓ (fallback if ADB fails)
                     Google Fit REST API → same summary flow
```

---

## CodeGen Fallback Flow

```
Unknown task
    │
    ▼
LLM generates Python/PowerShell script
    │
    ▼
Save to data/generated_scripts/task_YYYYMMDD_HHMMSS.py
    │
    ▼
subprocess.run(timeout=60)
    │
    ├─ success ──► parse output ──► LLM summarizes ──► Naina speaks
    │
    └─ error ───► send stderr back to LLM for one self-debug attempt
                      │
                      ├─ fixed ──► retry ──► success/fail
                      └─ still fails ──► "Boss, yeh kaam nahi hua, script save kar li hai"
```

---

## Contact Selection Logic

```
query: "Rahul ko WhatsApp bhejo"
    │
    ▼
rapidfuzz WRatio search in contacts.json (cutoff: 60)
    │
    ├─ 0 matches ──► "Boss, yeh contact nahi mila. Dobara boliye?"
    ├─ 1 match ───► proceed silently
    ├─ 2-5 matches ► voice: "Rahul naam ke N contacts hain Boss..." + visual cards
    └─ 6+ matches ─► "Bahut saare results hain — thoda aur specific boliye"
```

---

## Key Config Values (config.py)

```python
OLLAMA_BASE_URL    = "http://localhost:11434"
OLLAMA_MODEL       = "llama3.2:3b"
OLLAMA_TIMEOUT     = 8          # seconds before Groq fallback
GROQ_API_KEY       = ""         # optional
GROQ_MODEL         = "llama3-70b-8192"
FASTAPI_PORT       = 8000
WAKE_WORD          = "hey naina"
TTS_HINDI_VOICE    = "hi-IN-SwaraNeural"
TTS_ENGLISH_VOICE  = "en-IN-NeerjaNeural"
USER_NAME          = "Boss"
PHONE_IP           = ""         # auto-detected
ADB_PORT           = 5555
CODEGEN_TIMEOUT    = 60         # seconds
PATTERN_THRESHOLD  = 7          # repetitions before suggesting automation
FUZZY_CUTOFF       = 60         # rapidfuzz WRatio cutoff
```

---

## Error Handling Conventions

Every tool function must:
```python
def my_tool(args) -> dict:
    try:
        # do work
        return {"success": True, "result": "..."}
    except SpecificError as e:
        logger.error(f"my_tool failed: {e}")
        return {"success": False, "error": str(e)}
```

Naina's spoken error responses (in brain.py):
- Tool failure → LLM generates recovery response in Hinglish
- All errors → `naina.log` with full stack trace

---

## PWA / Mobile

- Service worker caches app shell for offline
- `manifest.json` allows "Add to Home Screen" on Android/iOS
- Web Speech API for mic input (Hindi + English)
- `navigator.contacts.select()` for contact picker on mobile
- All API calls go to Cloudflare Tunnel HTTPS URL

---

## Windows Startup

```python
# In main.py on first run:
import winreg
key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
    r"Software\Microsoft\Windows\CurrentVersion\Run",
    0, winreg.KEY_SET_VALUE)
winreg.SetValueEx(key, "Naina", 0, winreg.REG_SZ, str(exe_path))
```

No admin required — HKCU not HKLM.

---

## Personality & Voice

- **Name:** Naina | **Gender:** Female
- **Hindi voice:** `hi-IN-SwaraNeural` | **English:** `en-IN-NeerjaNeural`
- **Addresses user as:** "Boss" (or saved name from memory.json)
- **Style:** Warm, smart, slight humor, natural Hinglish
- **Never says:** "I can't do that" / "I don't know how"
- **Always says:** Something helpful, even if it's just starting CodeGen

### Example Responses
- `"Haan Boss, YouTube pe Arijit Singh laga rahi hoon!"`
- `"Done! Alarm set for 7 AM. Kal subah uthna mat bhoolna!"`
- `"Rahul naam ke 2 contacts hain Boss — kaun sa bhejun?"`
- `"Koi built-in tool nahi tha, toh maine ek program likh ke chalaya — yeh raha result Boss!"`
