# naina/api/routes.py
import os
import tempfile
import asyncio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from loguru import logger
from naina.agent.loop import run as agent_run
from naina.agent.memory import get_user_name

router = APIRouter()

class ChatRequest(BaseModel):
    text: str
    speak_response: bool = False

class ChatResponse(BaseModel):
    response: str
    source: str = "ollama"

@router.get("/status")
async def status():
    return {"status": "online", "user": get_user_name(), "version": "1.0.0"}

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    logger.info(f"Chat: {req.text}")
    try:
        response = await agent_run(req.text)
        if req.speak_response:
            from naina.voice.tts import speak
            speak(response)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    return {"status": "healthy"}

@router.get("/ai/status")
async def ai_status():
    """Check whether Ollama and Groq are reachable and configured."""
    import httpx
    from naina.config import OLLAMA_BASE_URL, OLLAMA_MODEL, GROQ_API_KEY, GROQ_MODEL

    # --- Ollama ---
    ollama = {"reachable": False, "model_loaded": False, "model": OLLAMA_MODEL, "error": ""}
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                ollama["reachable"] = True
                names = [m.get("name", "") for m in r.json().get("models", [])]
                ollama["model_loaded"] = any(OLLAMA_MODEL in n for n in names)
                ollama["available_models"] = names
            else:
                ollama["error"] = f"HTTP {r.status_code}"
    except Exception as e:
        ollama["error"] = str(e)

    # --- Groq ---
    groq = {"configured": bool(GROQ_API_KEY), "reachable": False, "model": GROQ_MODEL, "error": ""}
    if GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
                )
                if r.status_code == 200:
                    groq["reachable"] = True
                    model_ids = [m["id"] for m in r.json().get("data", [])]
                    groq["model_available"] = GROQ_MODEL in model_ids
                else:
                    groq["error"] = f"HTTP {r.status_code} — check API key"
        except Exception as e:
            groq["error"] = str(e)
    else:
        groq["error"] = "GROQ_API_KEY not set in config.py"

    return {"ollama": ollama, "groq": groq}

@router.get("/tts")
async def tts(text: str = Query(...)):
    """Stream speech via edge-tts — first audio chunk arrives in ~300ms."""
    import edge_tts
    from fastapi.responses import StreamingResponse
    from naina.config import TTS_ENGLISH_VOICE
    voice = TTS_ENGLISH_VOICE

    async def _audio_chunks():
        try:
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            logger.error(f"edge-tts stream failed: {e}")

    return StreamingResponse(
        _audio_chunks(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )

@router.get("/livereload")
async def livereload():
    """Returns a hash of all web static file mtimes — browser polls this to auto-reload."""
    import hashlib
    from naina.config import WEB_DIR
    h = hashlib.md5()
    for f in sorted(WEB_DIR.rglob("*")):
        if f.is_file() and not f.name.startswith('.'):
            try:
                h.update(f"{f.name}:{f.stat().st_mtime_ns}".encode())
            except OSError:
                pass
    return {"v": h.hexdigest()[:10]}

@router.get("/tools")
async def list_tools():
    from naina.tools.base import TOOL_REGISTRY
    return {"tools": list(TOOL_REGISTRY.keys())}

# ── Music ────────────────────────────────────────────────────────────────────
_MUSIC_EXTS = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma', '.opus'}

@router.get("/music/list")
async def music_list(q: str = Query(default="")):
    """List all songs in MUSIC_DIR, optionally filtered by query string."""
    from pathlib import Path
    from naina.config import MUSIC_DIR
    music_path = Path(MUSIC_DIR)
    if not music_path.exists():
        return {"songs": [], "music_dir": MUSIC_DIR, "error": "Music folder not found. Set MUSIC_DIR in config.py."}
    q_lower = q.lower()
    songs = []
    for f in sorted(music_path.rglob("*"), key=lambda x: x.name.lower()):
        if f.suffix.lower() not in _MUSIC_EXTS:
            continue
        if q_lower and q_lower not in f.stem.lower():
            continue
        songs.append({"name": f.stem, "file": f.name, "path": str(f), "ext": f.suffix.lower()})
    return {"songs": songs, "music_dir": MUSIC_DIR}

@router.get("/music/play")
async def music_play(path: str = Query(...)):
    """Stream a local audio file to the browser."""
    from pathlib import Path
    p = Path(path)
    if not p.exists() or not p.is_file() or p.suffix.lower() not in _MUSIC_EXTS:
        raise HTTPException(status_code=404, detail="File not found or not a supported audio format")
    import mimetypes
    mime = mimetypes.guess_type(str(p))[0] or "audio/mpeg"
    return FileResponse(str(p), media_type=mime, headers={"Cache-Control": "no-store", "Accept-Ranges": "bytes"})

# ── File browser ──────────────────────────────────────────────────────────────
import os, base64, mimetypes
from pathlib import Path
from fastapi import Query

_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico', '.svg'}

@router.get("/files")
async def list_files(path: str = Query(default=None)):
    """List directory contents for the file browser panel."""
    p = Path(path) if path else Path.home()
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")
    items = []
    try:
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "ext": item.suffix.lower(),
                    "is_image": item.suffix.lower() in _IMAGE_EXTS,
                })
            except PermissionError:
                pass
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"path": str(p), "parent": str(p.parent) if str(p.parent) != str(p) else None, "items": items}

@router.get("/file/image")
async def get_image(path: str = Query(...)):
    """Return an image as a base64 data URL."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if p.suffix.lower() not in _IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="Not a supported image")
    mime = mimetypes.guess_type(str(p))[0] or "image/jpeg"
    with open(p, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return {"data_url": f"data:{mime};base64,{data}", "name": p.name}
