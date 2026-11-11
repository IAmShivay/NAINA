# naina/tunnel/tailscale.py
"""
Tailscale private-network tunnel support.

No extra process needed — Tailscale runs as a Windows service and assigns
a stable 100.x.x.x IP to this machine.  We just detect that IP and log it
so you know the private URL to access Naina from any device on your
Tailscale network (phone, laptop, etc.).
"""
import subprocess
from loguru import logger
from naina.config import FASTAPI_PORT

_tailscale_ip: str | None = None


def get_ip() -> str | None:
    return _tailscale_ip


def get_url() -> str | None:
    ip = get_ip()
    return f"http://{ip}:{FASTAPI_PORT}" if ip else None


def detect_and_log() -> str | None:
    """
    Detect Tailscale IPv4 address via `tailscale ip -4`.
    Returns the IP string, or None if Tailscale is not running / not installed.
    """
    global _tailscale_ip
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True, text=True, timeout=4
        )
        ip = result.stdout.strip()
        if result.returncode == 0 and ip:
            _tailscale_ip = ip
            logger.info(
                f"Tailscale active — private URL: http://{ip}:{FASTAPI_PORT}  "
                f"(accessible from any device on your Tailscale network)"
            )
            return ip
        else:
            logger.warning(
                "Tailscale not connected. "
                "Start Tailscale and run 'tailscale up' to enable private tunnel."
            )
    except FileNotFoundError:
        logger.warning(
            "tailscale CLI not found — private tunnel disabled. "
            "Install from: https://tailscale.com/download"
        )
    except Exception as e:
        logger.warning(f"Tailscale detection failed: {e}")
    return None
