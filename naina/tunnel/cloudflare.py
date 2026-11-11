# naina/tunnel/cloudflare.py
import subprocess
import threading
import re
from loguru import logger
from naina.config import FASTAPI_PORT

_tunnel_url: str | None = None

def get_url() -> str | None:
    return _tunnel_url

def start_tunnel() -> None:
    """Start cloudflared tunnel in background thread."""
    thread = threading.Thread(target=_run_tunnel, daemon=True)
    thread.start()

def _run_tunnel() -> None:
    global _tunnel_url
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{FASTAPI_PORT}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in proc.stdout:
            logger.debug(f"cloudflared: {line.strip()}")
            match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
            if match:
                _tunnel_url = match.group()
                logger.info(f"Cloudflare tunnel active: {_tunnel_url}")
                break
        proc.wait()
    except FileNotFoundError:
        logger.warning(
            "cloudflared not found — tunnel disabled. "
            "Install from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        )
    except Exception as e:
        logger.error(f"Tunnel error: {e}")
