# naina/tools/productivity.py
import json
import datetime
from loguru import logger
from naina.tools.base import ToolResult, register_tool
from naina.config import DATA_DIR

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    _scheduler = BackgroundScheduler()
    _scheduler.start()
    SCHEDULER_OK = True
except Exception as e:
    logger.warning(f"APScheduler failed to start: {e}")
    SCHEDULER_OK = False
    _scheduler = None

TODOS_FILE = DATA_DIR / "todos.json"
NOTES_FILE = DATA_DIR / "notes.txt"

def _load_todos() -> list:
    try:
        return json.loads(TODOS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_todos(todos: list) -> None:
    TODOS_FILE.write_text(json.dumps(todos, indent=2, ensure_ascii=False), encoding="utf-8")

@register_tool("add_todo", "Add a task to the to-do list", ["todo add", "kaam add", "task add", "remind me to"])
def add_todo(task: str) -> ToolResult:
    try:
        todos = _load_todos()
        item = {"id": len(todos) + 1, "task": task, "done": False,
                "created": datetime.datetime.now().isoformat()}
        todos.append(item)
        _save_todos(todos)
        return ToolResult(success=True, result=f"Todo added: {task}")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool("read_todos", "Read all pending todos", ["todo list", "todos", "kaam kya hai", "tasks"])
def read_todos() -> ToolResult:
    try:
        todos = [t for t in _load_todos() if not t["done"]]
        if not todos:
            return ToolResult(success=True, result="Koi pending todo nahi hai Boss!")
        items = [f"{t['id']}. {t['task']}" for t in todos]
        return ToolResult(success=True, result=items)
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool("complete_todo", "Mark a todo as done by its ID number", ["todo done", "task done", "complete", "khatam"])
def complete_todo(id: int) -> ToolResult:
    try:
        todos = _load_todos()
        for t in todos:
            if t["id"] == id:
                t["done"] = True
                _save_todos(todos)
                return ToolResult(success=True, result=f"Todo {id} complete!")
        return ToolResult(success=False, error=f"Todo {id} nahi mila")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool("save_note", "Save a note", ["note", "note karo", "save note", "likh do"])
def save_note(text: str) -> ToolResult:
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] {text}")
        return ToolResult(success=True, result="Note save ho gayi Boss!")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool("read_notes", "Read the most recent saved notes", ["notes padho", "notes", "read notes"])
def read_notes(last_n: int = 5) -> ToolResult:
    try:
        lines = NOTES_FILE.read_text(encoding="utf-8").strip().split("\n")
        recent = [l for l in lines if l.strip()][-last_n:]
        return ToolResult(success=True, result=recent)
    except Exception as e:
        return ToolResult(success=False, error=str(e))

def _speak_alarm(label: str) -> None:
    """Trigger TTS for alarm — import inside to avoid circular import."""
    try:
        from naina.voice.tts import speak
        speak(f"Boss! {label} — alarm baj gaya!")
    except Exception as e:
        logger.error(f"Alarm TTS failed: {e}")

@register_tool("set_alarm", "Set an alarm at a specific time HH:MM (24h format)", ["alarm", "alarm set", "uthao", "wake me"])
def set_alarm(time_str: str, label: str = "Alarm!") -> ToolResult:
    try:
        if not SCHEDULER_OK:
            return ToolResult(success=False, error="Scheduler not available")
        h, m = map(int, time_str.strip().split(":"))
        now = datetime.datetime.now()
        alarm_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if alarm_dt <= now:
            alarm_dt += datetime.timedelta(days=1)
        _scheduler.add_job(
            lambda: _speak_alarm(label),
            "date", run_date=alarm_dt,
            id=f"alarm_{time_str.replace(':','')}"
        )
        return ToolResult(success=True, result=f"Alarm set for {time_str} — {label}")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool("set_timer", "Set a countdown timer for N minutes", ["timer", "countdown", "minutes mein"])
def set_timer(minutes: int, label: str = "Timer done!") -> ToolResult:
    try:
        if not SCHEDULER_OK:
            return ToolResult(success=False, error="Scheduler not available")
        run_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        _scheduler.add_job(
            lambda: _speak_alarm(f"{minutes} minute ho gaye — {label}"),
            "date", run_date=run_at
        )
        return ToolResult(success=True, result=f"Timer set for {minutes} minutes")
    except Exception as e:
        return ToolResult(success=False, error=str(e))

@register_tool("set_reminder", "Set a reminder at a specific time with a message", ["reminder", "remind", "yaad dilao"])
def set_reminder(time_str: str, message: str) -> ToolResult:
    return set_alarm(time_str, message)

@register_tool("calculate", "Calculate a mathematical expression", ["calculate", "math", "hisab", "kitna"])
def calculate(expression: str) -> ToolResult:
    try:
        # Safe eval — only math operations
        allowed = set("0123456789+-*/().,% ")
        if not all(c in allowed for c in expression):
            return ToolResult(success=False, error="Unsafe expression")
        result = eval(expression, {"__builtins__": {}})
        return ToolResult(success=True, result=str(result))
    except Exception as e:
        return ToolResult(success=False, error=str(e))
