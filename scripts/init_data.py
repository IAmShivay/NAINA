# naina/init_data.py
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "generated_scripts").mkdir(exist_ok=True)

defaults = {
    "memory.json": {"user_name": "Boss", "language": "hinglish", "preferences": {}},
    "todos.json": [],
    "expenses.json": [],
    "contacts.json": [],
    "tool_registry.json": {},
    "learned_patterns.json": {},
}
for filename, content in defaults.items():
    path = DATA_DIR / filename
    if not path.exists():
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False))

(DATA_DIR / "notes.txt").touch()
print("Data files created.")
