# naina/voice/tts.py
import asyncio
import tempfile
import os
import time
import threading
import edge_tts
from loguru import logger
from naina.config import TTS_HINDI_VOICE, TTS_ENGLISH_VOICE

_HINGLISH_WORDS = {
    'haan','nahi','hai','karo','kar','raha','rahi','ho','kya','yeh','woh',
    'aur','toh','bhi','boss','mera','tera','aap','main','hum','theek',
    'accha','bahut','abhi','kal','dobara','bilkul','zaroor','suno','dekho',
    'laga','lagi','chahiye','batao','lagta','samjha','hua','hui','naina',
    'kuch','koi','jao','aao','bolo','suno','dono','sab','zyada','thoda',
    'matlab','lekin','kyunki','isliye','phir','pehle','baad','upar','neeche'
}

def detect_language(text: str) -> str:
    """
    Returns voice key:
      "hi_dev"  — Devanagari script → hi-IN-SwaraNeural (pure Hindi)
      "en"      — Latin script (English or Hinglish) → en-IN-NeerjaNeural

    NOTE: Hinglish in Latin script (e.g. "Haan Boss, kar raha hoon") must use
    the Indian-English voice (Neerja), NOT the Hindi voice (Swara).
    Swara expects Devanagari and will mispronounce Latin-script words badly.
    Neerja has an Indian accent and handles both English and Hinglish words correctly.
    """
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    if devanagari / max(len(text), 1) > 0.15:
        return "hi_dev"
    return "en"

def _play_audio(path: str) -> None:
    """Play an audio file in the background without opening an external player."""
    def _worker():
        try:
            import win32com.client
            player = win32com.client.Dispatch("WMPlayer.OCX")
            player.URL = path
            player.controls.play()
            # Wait for playback to finish
            while player.playState != 1:  # 1 = stopped
                time.sleep(0.2)
            player.close()
        except Exception:
            # Fallback: use winsound with a wav converted via ffmpeg if available
            try:
                import subprocess
                import winsound
                wav_path = path.replace(".mp3", ".wav")
                subprocess.run(
                    ["ffmpeg", "-y", "-i", path, wav_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=10
                )
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                os.remove(wav_path)
            except Exception as e2:
                logger.error(f"Audio playback failed: {e2}")
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    threading.Thread(target=_worker, daemon=True).start()


async def speak_async(text: str, lang: str | None = None) -> None:
    """Convert text to speech and play via edge-tts."""
    if not lang:
        lang = detect_language(text)

    voice = TTS_HINDI_VOICE if lang == "hi_dev" else TTS_ENGLISH_VOICE

    try:
        communicate = edge_tts.Communicate(text, voice)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name

        await communicate.save(tmp_path)
        _play_audio(tmp_path)
        logger.debug(f"TTS spoken: {text[:60]}...")
    except Exception as e:
        logger.error(f"TTS failed: {e}")

def speak(text: str, lang: str | None = None) -> None:
    """Sync wrapper for speak_async — creates a new event loop if needed."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule as task if we're already in an async context
            asyncio.ensure_future(speak_async(text, lang))
        else:
            loop.run_until_complete(speak_async(text, lang))
    except RuntimeError:
        asyncio.run(speak_async(text, lang))
