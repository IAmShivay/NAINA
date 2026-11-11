# naina/tools/system_control.py
import os
import subprocess
import datetime
import psutil
from loguru import logger
from naina.tools.base import ToolResult, register_tool
from naina.config import DATA_DIR

try:
    import pyautogui
    PYAUTOGUI_OK = True
except Exception:
    PYAUTOGUI_OK = False

@register_tool(
    "get_system_stats",
    "Get CPU, RAM, disk usage stats",
    ["system status", "cpu", "ram", "disk", "system stats"]
)
def get_system_stats() -> ToolResult:
    try:
        cpu   = psutil.cpu_percent(interval=1)
        ram   = psutil.virtual_memory()
        disk  = psutil.disk_usage("/")
        return ToolResult(success=True, result={
            "cpu_percent": cpu,
            "ram_used_gb": round(ram.used / 1e9, 1),
            "ram_total_gb": round(ram.total / 1e9, 1),
            "ram_percent": ram.percent,
            "disk_used_gb": round(disk.used / 1e9, 1),
            "disk_total_gb": round(disk.total / 1e9, 1),
            "disk_percent": disk.percent,
        })
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool(
    "get_battery_status",
    "Get battery percentage and charging status",
    ["battery", "charge", "battery status"]
)
def get_battery_status() -> ToolResult:
    try:
        batt = psutil.sensors_battery()
        if batt is None:
            return ToolResult(success=True, result={"percent": 100, "plugged": True, "note": "No battery — desktop PC"})
        return ToolResult(success=True, result={
            "percent": round(batt.percent, 1),
            "plugged": batt.power_plugged,
            "seconds_left": batt.secsleft if batt.secsleft != psutil.POWER_TIME_UNLIMITED else None,
        })
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool(
    "take_screenshot",
    "Take a screenshot and save it",
    ["screenshot", "screen capture", "screen shot"]
)
def take_screenshot(filename: str = "") -> ToolResult:
    try:
        if not PYAUTOGUI_OK:
            return ToolResult(success=False, error="pyautogui not available")
        if not filename:
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = DATA_DIR / filename
        img = pyautogui.screenshot()
        img.save(str(path))
        return ToolResult(success=True, result=str(path))
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool(
    "set_volume",
    "Set system volume 0-100",
    ["volume", "set volume", "volume set", "awaaz"]
)
def set_volume(level: int) -> ToolResult:
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        scalar = max(0.0, min(1.0, level / 100))
        volume.SetMasterVolumeLevelScalar(scalar, None)
        return ToolResult(success=True, result=f"Volume set to {level}%")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool(
    "shutdown_pc",
    "Shutdown the PC",
    ["shutdown", "band karo", "pc band"]
)
def shutdown_pc() -> ToolResult:
    try:
        os.system("shutdown /s /t 5")
        return ToolResult(success=True, result="Shutting down in 5 seconds Boss...")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool(
    "restart_pc",
    "Restart the PC",
    ["restart", "reboot", "restart karo"]
)
def restart_pc() -> ToolResult:
    try:
        os.system("shutdown /r /t 5")
        return ToolResult(success=True, result="Restarting in 5 seconds Boss...")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool(
    "lock_screen",
    "Lock the Windows screen",
    ["lock", "lock screen", "screen lock"]
)
def lock_screen() -> ToolResult:
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return ToolResult(success=True, result="Screen locked Boss!")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool(
    "open_app",
    "Open a Windows application by name or path",
    ["open", "launch", "start", "kholo"]
)
def open_app(name: str) -> ToolResult:
    try:
        os.startfile(name)
        return ToolResult(success=True, result=f"Opening {name}...")
    except Exception:
        try:
            subprocess.Popen(name)
            return ToolResult(success=True, result=f"Launched {name}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

@register_tool(
    "open_browser",
    "Open a URL in the default browser",
    ["open url", "browser", "website", "open website"]
)
def open_browser(url: str) -> ToolResult:
    try:
        import webbrowser
        webbrowser.open(url)
        return ToolResult(success=True, result=f"Opened {url}")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

_MUSIC_EXTS = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma', '.opus'}

@register_tool(
    "play_music",
    "Play a song from the local music folder. Searches by filename match. Input: {\"query\": \"song name\"}",
    ["play", "music", "song", "play song", "play music"]
)
def play_music(query: str) -> ToolResult:
    """Search local MUSIC_DIR for best matching file and open it."""
    from pathlib import Path
    from naina.config import MUSIC_DIR

    music_path = Path(MUSIC_DIR)
    if not music_path.exists():
        return ToolResult(success=False, error=f"Music folder not found: {MUSIC_DIR}. Set MUSIC_DIR in config.py.")

    q_words = set(query.lower().split())
    candidates = []
    for f in music_path.rglob("*"):
        if f.suffix.lower() not in _MUSIC_EXTS:
            continue
        name_lower = f.stem.lower()
        score = sum(1 for w in q_words if w in name_lower)
        if score > 0:
            candidates.append((score, f))

    if not candidates:
        return ToolResult(success=False, error=f"No local song found matching '{query}' in {MUSIC_DIR}.")

    best = sorted(candidates, key=lambda x: -x[0])[0][1]
    try:
        os.startfile(str(best))
        return ToolResult(success=True, result=f"Playing: {best.name}")
    except Exception as e:
        return ToolResult(success=False, error=str(e))
