# naina/config.py
import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data"
SCRIPTS_DIR = DATA_DIR / "generated_scripts"
WEB_DIR    = BASE_DIR / "web"

# ── LLM ──────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL  = "http://localhost:11434"
OLLAMA_MODEL     = "llama3.2:3b"
OLLAMA_TIMEOUT   = 8          # seconds before Groq fallback

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL       = "llama-3.3-70b-versatile"

# ── API Server ────────────────────────────────────────────────────────────────
FASTAPI_HOST     = "0.0.0.0"
FASTAPI_PORT     = 8000

# ── Music ─────────────────────────────────────────────────────────────────────
MUSIC_DIR        = str(Path.home() / "Music")   # change to your music folder path

# ── Voice ─────────────────────────────────────────────────────────────────────
WAKE_WORD        = "hey naina"
TTS_HINDI_VOICE  = "hi-IN-SwaraNeural"
TTS_ENGLISH_VOICE = "en-IN-NeerjaNeural"
STT_LANGUAGE     = "hi-IN"    # primary; falls back to en-IN

# ── User ──────────────────────────────────────────────────────────────────────
USER_NAME        = "Shivay"   # overridden by memory.json

# ── Mobile / ADB ─────────────────────────────────────────────────────────────
PHONE_IP         = ""         # auto-detected on LAN
ADB_PORT         = 5555
FITCLOUD_PKG     = "com.fitcloud.cb"

# ── CodeGen ───────────────────────────────────────────────────────────────────
CODEGEN_TIMEOUT  = 60         # subprocess timeout (seconds)
CODEGEN_DANGEROUS_OPS = ["os.remove", "shutil.rmtree", "subprocess.run", "socket."]

# ── Learning ──────────────────────────────────────────────────────────────────
PATTERN_THRESHOLD = 7         # repeated sequences before suggesting automation

# ── Contacts ─────────────────────────────────────────────────────────────────
FUZZY_CUTOFF     = 60         # rapidfuzz WRatio cutoff

# ── External APIs (free tiers) ───────────────────────────────────────────────
OPENWEATHER_KEY  = ""
NEWSAPI_KEY      = ""
OMDB_KEY         = ""
GOOGLE_CAL_TOKEN = DATA_DIR / "gcal_token.json"
GFIT_TOKEN       = DATA_DIR / "gfit_token.json"

# ── Notifications ─────────────────────────────────────────────────────────────
NTFY_TOPIC       = "naina-boss"   # ntfy.sh topic for mobile push

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE         = BASE_DIR.parent / "logs" / "naina.log"
LOG_LEVEL        = "DEBUG"
