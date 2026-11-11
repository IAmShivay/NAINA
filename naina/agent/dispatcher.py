# naina/agent/dispatcher.py
import json
import re
from loguru import logger
from naina.tools.base import TOOL_REGISTRY, ToolResult

TOOL_PATTERN = re.compile(r"TOOL:\s*(\w+)\s*\|\s*INPUT:\s*(\{.*?\})", re.DOTALL)

def parse_tool_call(llm_output: str) -> tuple[str | None, dict | None]:
    """Parse LLM output for TOOL: name | INPUT: {...} pattern."""
    match = TOOL_PATTERN.search(llm_output)
    if not match:
        return None, None
    tool_name = match.group(1).strip()
    try:
        tool_input = json.loads(match.group(2))
    except json.JSONDecodeError:
        tool_input = {}
    return tool_name, tool_input

async def dispatch(tool_name: str, tool_input: dict) -> ToolResult:
    """Execute a registered tool by name."""
    if tool_name not in TOOL_REGISTRY:
        logger.warning(f"Unknown tool: {tool_name}")
        return ToolResult(success=False, error=f"Tool '{tool_name}' not found")

    tool_info = TOOL_REGISTRY[tool_name]
    try:
        fn = tool_info["fn"]
        import asyncio
        if asyncio.iscoroutinefunction(fn):
            result = await fn(**tool_input)
        else:
            result = fn(**tool_input)

        if isinstance(result, ToolResult):
            return result
        return ToolResult(success=True, result=result)
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return ToolResult(success=False, error=str(e))
