# naina/tools/base.py
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class ToolResult:
    success: bool
    result: Any = None
    error: str = ""

    def to_dict(self) -> dict:
        return {"success": self.success, "result": self.result, "error": self.error}

# Global tool registry: name → {"fn": callable, "description": str, "triggers": list[str]}
TOOL_REGISTRY: dict[str, dict] = {}

def register_tool(name: str, description: str, triggers: list[str]):
    """Decorator to register a tool function."""
    def decorator(fn: Callable) -> Callable:
        TOOL_REGISTRY[name] = {
            "fn": fn,
            "description": description,
            "triggers": triggers,
        }
        return fn
    return decorator

def get_tools_description() -> str:
    """Returns a formatted string of all available tools for the LLM system prompt."""
    lines = []
    for name, info in TOOL_REGISTRY.items():
        lines.append(f"- {name}: {info['description']}")
    return "\n".join(lines)
