# build.py — run from project root: python build.py
"""
PyInstaller build script → dist/Naina.exe
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name", "Naina",
    "--onefile",
    "--windowed",                        # no console window
    "--icon", str(ROOT / "naina/web/static/icons/icon-192.png"),
    "--add-data", f"{ROOT / 'naina/web'};web",
    "--add-data", f"{ROOT / 'naina/data'};data",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.lifespan",
    "--hidden-import", "uvicorn.lifespan.off",
    "--hidden-import", "uvicorn.protocols",
    "--hidden-import", "uvicorn.protocols.http",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "uvicorn.protocols.websockets",
    "--hidden-import", "uvicorn.protocols.websockets.auto",
    "--hidden-import", "edge_tts",
    "--hidden-import", "pystray._win32",
    "--hidden-import", "naina.tools.system_control",
    "--hidden-import", "naina.tools.productivity",
    "--collect-all", "openWakeWord",
    "--collect-all", "sounddevice",
    str(ROOT / "naina/main.py"),
]

print("Building Naina.exe...")
result = subprocess.run(cmd, check=False)
if result.returncode == 0:
    print("\n✅ Build complete: dist/Naina.exe")
else:
    print("\n❌ Build failed — check output above")
    sys.exit(1)
