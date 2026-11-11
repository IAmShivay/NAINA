# naina/main.py
"""
Naina AI Assistant — Main Orchestrator
Starts: FastAPI server, Cloudflare tunnel, wake word listener, system tray
"""
import sys
import threading
import webbrowser
from pathlib import Path

import uvicorn
import pystray
from PIL import Image, ImageDraw
from loguru import logger

from naina.logger_setup import setup_logger
from naina.config import FASTAPI_HOST, FASTAPI_PORT, BASE_DIR
from naina.api.server import create_app
from naina.tunnel.cloudflare import start_tunnel, get_url
from naina.tunnel.tailscale import detect_and_log as tailscale_detect, get_url as tailscale_url
from naina.agent.memory import get_user_name
from naina.voice.tts import speak
from naina.voice.wake_word import WakeWordListener
from naina.voice.stt import listen_once
from naina.agent.loop import run as agent_run

setup_logger()

_app = create_app()

# ── Tray icon ─────────────────────────────────────────────────────────────────

def _make_icon() -> Image.Image:
    """Cyan 'N' on dark background for system tray."""
    img  = Image.new('RGBA', (64, 64), (0, 8, 20, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([3, 3, 61, 61], outline=(0, 212, 255, 255), width=3)
    lw = 4
    m  = 14
    draw.line([(m, m), (m, 64-m)],          fill=(0, 212, 255, 255), width=lw)
    draw.line([(m, m), (64-m, 64-m)],       fill=(0, 212, 255, 255), width=lw)
    draw.line([(64-m, m), (64-m, 64-m)],    fill=(0, 212, 255, 255), width=lw)
    return img

def _open_ui(_icon=None, _item=None):
    webbrowser.open(f"http://localhost:{FASTAPI_PORT}")

def _restart(_icon=None, _item=None):
    logger.info("Restarting Naina...")
    import os
    os.execv(sys.executable, [sys.executable] + sys.argv)

def _exit_app(icon, _item=None):
    icon.stop()
    sys.exit(0)

# ── Server ────────────────────────────────────────────────────────────────────

def _start_server() -> None:
    uvicorn.run(_app, host=FASTAPI_HOST, port=FASTAPI_PORT, log_level="error")

# ── Windows startup registration ──────────────────────────────────────────────

def _register_startup() -> None:
    """Add Naina to Windows startup (HKCU — no admin needed)."""
    try:
        import winreg
        exe = sys.executable
        script = str(Path(sys.argv[0]).resolve())
        value  = f'"{exe}" "{script}"'
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "Naina", 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        logger.info("Windows startup registered")
    except Exception as e:
        logger.warning(f"Could not register startup: {e}")

# ── Wake word handler ─────────────────────────────────────────────────────────

def _on_wake_word() -> None:
    """Called when 'Hey Naina' detected — listen, process, respond."""
    speak("Haan Boss?")
    text = listen_once(timeout=8)
    if not text:
        speak("Kuch suna nahi Boss, dobara boliye?")
        return
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(agent_run(text))
    finally:
        loop.close()
    speak(response)

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("Naina starting up...")

    # Register Windows startup
    _register_startup()

    # Start FastAPI in background thread
    server_thread = threading.Thread(target=_start_server, daemon=True)
    server_thread.start()
    logger.info(f"FastAPI started → http://localhost:{FASTAPI_PORT}")

    # Start Cloudflare tunnel (public HTTPS)
    start_tunnel()

    # Detect Tailscale private tunnel (no process needed — just reads the IP)
    tailscale_detect()

    # Start wake word listener
    wake = WakeWordListener(on_detected=_on_wake_word)
    wake.start()

    # Greeting
    user = get_user_name()
    speak(f"Namaste {user}! Naina ready hai. Local server chal raha hai.")

    # Open browser after short delay (let server boot)
    threading.Timer(1.5, _open_ui).start()

    # System tray (blocking — runs until user exits)
    icon = pystray.Icon(
        "Naina",
        _make_icon(),
        "Naina — Personal AI",
        menu=pystray.Menu(
            pystray.MenuItem("Open Naina UI", _open_ui, default=True),
            pystray.MenuItem("Restart", _restart),
            pystray.MenuItem("Exit", _exit_app),
        )
    )
    logger.info("System tray active. Right-click for menu.")
    icon.run()

if __name__ == "__main__":
    main()
