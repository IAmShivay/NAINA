# naina/agent/memory.py
import json
from pathlib import Path
from loguru import logger
from naina.config import DATA_DIR

MEMORY_FILE = DATA_DIR / "memory.json"

def _load() -> dict:
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"user_name": "Boss", "preferences": {}}

def _save(data: dict) -> None:
    MEMORY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def get_user_name() -> str:
    return _load().get("user_name", "Boss")

def remember(key: str, value: str) -> str:
    data = _load()
    data["preferences"][key] = value
    _save(data)
    return f"Yaad kar liya Boss — {key}: {value}"

def recall(key: str) -> str:
    data = _load()
    val = data["preferences"].get(key)
    if val:
        return f"Haan Boss, {key} hai: {val}"
    return f"Mujhe {key} ke baare mein kuch yaad nahi Boss."

def set_user_name(name: str) -> None:
    data = _load()
    data["user_name"] = name
    _save(data)
