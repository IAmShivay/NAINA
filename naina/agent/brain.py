# naina/agent/brain.py
import httpx
from loguru import logger
from naina.config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT,
    GROQ_API_KEY, GROQ_MODEL
)

try:
    from groq import AsyncGroq as _AsyncGroq
    _groq_available = True
except ImportError:
    _groq_available = False
    logger.warning("groq package not installed — run: pip install groq")

_ollama_checked = False
_ollama_ok = False

def reset_ollama_check() -> None:
    """Call this to force re-check of Ollama on next request (e.g. after user starts Ollama)."""
    global _ollama_checked
    _ollama_checked = False

async def _ensure_ollama_checked() -> bool:
    """Check Ollama once and cache the result."""
    global _ollama_checked, _ollama_ok
    if _ollama_checked:
        return _ollama_ok
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            _ollama_ok = r.status_code == 200
            if _ollama_ok:
                # Check if our model is available
                tags = r.json().get("models", [])
                names = [m.get("name","") for m in tags]
                if not any(OLLAMA_MODEL in n for n in names):
                    logger.warning(f"Ollama running but model '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}")
                    _ollama_ok = False
    except Exception as e:
        logger.warning(f"Ollama not reachable at {OLLAMA_BASE_URL}: {e}")
        logger.warning("To fix: install Ollama from https://ollama.com and run: ollama pull llama3.2:3b")
        _ollama_ok = False
    _ollama_checked = True
    return _ollama_ok

SYSTEM_PROMPT = """You are Naina, a sharp and professional AI assistant. Always address the user as "Shivay".

LANGUAGE: English only. Always respond in clear, fluent, professional English regardless of what language the user writes in.

TONE: Confident, direct, slightly warm. Like a highly competent personal assistant who gets things done without unnecessary chatter.

TOOL USE: When you need a tool, respond EXACTLY like:
TOOL: tool_name | INPUT: {"key": "value"}
When you have the final answer, respond naturally — no tool syntax.

RULES:
- Be concise. 1-3 sentences unless the user asks for detail.
- Never say "I cannot" or "I am unable to" — always attempt the task.
- No emoji, no asterisks, no markdown formatting — plain spoken English only.
- Do not repeat the user's question back to them.
- Do not add filler phrases like "Certainly!", "Of course!", "Great question!" — get straight to the point."""

async def call_ollama(messages: list[dict], tools_description: str = "") -> str:
    """Call Ollama local LLM."""
    system = SYSTEM_PROMPT
    if tools_description:
        system += f"\n\nAvailable tools:\n{tools_description}"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 512}
    }
    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

async def call_groq(messages: list[dict], tools_description: str = "") -> str:
    """Call Groq cloud LLM as fallback."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")
    if not _groq_available:
        raise RuntimeError("groq package not installed — run: pip install groq")

    system = SYSTEM_PROMPT
    if tools_description:
        system += f"\n\nAvailable tools:\n{tools_description}"

    client = _AsyncGroq(api_key=GROQ_API_KEY)
    chat = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": system}] + messages,
        temperature=0.7,
        max_tokens=512
    )
    return chat.choices[0].message.content

async def think(messages: list[dict], tools_description: str = "") -> tuple[str, str]:
    """
    Try Ollama first. Fall back to Groq on timeout/error.
    Returns (response_text, source) where source is "ollama" or "groq".
    """
    ollama_ready = await _ensure_ollama_checked()

    if ollama_ready:
        try:
            logger.debug("Calling Ollama...")
            text = await call_ollama(messages, tools_description)
            logger.debug(f"Ollama responded: {text[:80]}...")
            return text, "ollama"
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"Ollama unavailable ({e}), falling back to Groq")
        except Exception as e:
            logger.warning(f"Ollama error: {e}, falling back to Groq")
    else:
        logger.debug("Ollama not ready, skipping to Groq")

    try:
        text = await call_groq(messages, tools_description)
        logger.debug(f"Groq responded: {text[:80]}...")
        return text, "groq"
    except ValueError:
        # No Groq key set
        if not ollama_ready:
            return (
                "SETUP REQUIRED: No AI engine is running. "
                "Option 1 — Install Ollama: download from ollama.com, then run 'ollama pull llama3.2:3b' in terminal. "
                "Option 2 — Use Groq (free, fast): get a free API key from console.groq.com and set GROQ_API_KEY in naina/config.py.",
                "offline"
            )
        return "Shivay, Groq API key is not set in config.py. Add it to use cloud AI as backup.", "offline"
    except Exception as e:
        logger.error(f"Groq also failed: {e}")
        return "Shivay, both AI engines are unavailable. Check Ollama is running and internet is connected.", "offline"
