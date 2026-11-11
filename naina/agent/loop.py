# naina/agent/loop.py
from loguru import logger
from naina.agent.brain import think
from naina.agent.dispatcher import parse_tool_call, dispatch
from naina.tools.base import get_tools_description

MAX_ITERATIONS = 10

async def run(user_text: str) -> str:
    """
    ReAct agent loop.
    1. Send user message to LLM with tool descriptions
    2. Parse tool call from response
    3. Execute tool, feed result back to LLM
    4. Repeat until no tool call or max iterations
    5. Return final natural language response
    """
    messages = [{"role": "user", "content": user_text}]
    tools_desc = get_tools_description()

    for iteration in range(MAX_ITERATIONS):
        logger.debug(f"ReAct iteration {iteration + 1}")
        response, source = await think(messages, tools_desc)

        tool_name, tool_input = parse_tool_call(response)

        if not tool_name:
            # No tool call — this is the final response
            logger.debug(f"Final response from {source}")
            return response.strip()

        logger.info(f"Calling tool: {tool_name} with {tool_input}")
        tool_result = await dispatch(tool_name, tool_input or {})

        # Add assistant + tool result to conversation
        messages.append({"role": "assistant", "content": response})
        messages.append({
            "role": "user",
            "content": f"Tool result for {tool_name}: {tool_result.to_dict()}"
        })

    return "Shivay, that task hit the iteration limit. Please try rephrasing."
