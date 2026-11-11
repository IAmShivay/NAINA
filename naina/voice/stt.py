# naina/voice/stt.py
# Python 3.13+ compatibility: aifc and audioop were removed from stdlib
import sys
import types as _types

for _mod in ('aifc', 'audioop'):
    if _mod not in sys.modules:
        _stub = _types.ModuleType(_mod)
        sys.modules[_mod] = _stub

import io
import numpy as np
import sounddevice as sd
from loguru import logger
from naina.config import STT_LANGUAGE

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
    _recognizer = sr.Recognizer()
    _recognizer.energy_threshold = 300
    _recognizer.dynamic_energy_threshold = True
    _recognizer.pause_threshold = 0.8
except Exception:
    SR_AVAILABLE = False
    _recognizer = None

RATE         = 16000
MAX_SECONDS  = 15

def listen_once(timeout: int = 10) -> str | None:
    """
    Record audio from mic using sounddevice, then transcribe via Google STT.
    Returns transcribed text or None.
    """
    logger.debug("Listening (sounddevice)...")
    try:
        # Record until silence or max duration
        audio_np = sd.rec(int(MAX_SECONDS * RATE), samplerate=RATE,
                          channels=1, dtype='int16')
        # Wait for recording (timeout seconds)
        sd.wait()
        audio_np = audio_np.flatten()
    except Exception as e:
        logger.warning(f"Microphone recording failed: {e}")
        return None

    if SR_AVAILABLE:
        return _transcribe_sr(audio_np)
    return None

def _transcribe_sr(audio_np: np.ndarray) -> str | None:
    """Convert numpy audio array to SR AudioData and call Google STT."""
    try:
        raw = audio_np.tobytes()
        audio_data = sr.AudioData(raw, sample_rate=RATE, sample_width=2)
        text = _recognizer.recognize_google(audio_data, language=STT_LANGUAGE)
        logger.info(f"STT (Google): {text}")
        return text
    except sr.UnknownValueError:
        logger.debug("Could not understand audio")
        return None
    except sr.RequestError as e:
        logger.warning(f"Google STT unavailable: {e} — trying Vosk")
        return _vosk_fallback(audio_np)
    except Exception as e:
        logger.error(f"STT error: {e}")
        return None

def _vosk_fallback(audio_np: np.ndarray) -> str | None:
    """Offline STT via Vosk (if installed and model downloaded)."""
    try:
        import json
        from vosk import Model, KaldiRecognizer
        model = Model(lang="en-us")
        rec   = KaldiRecognizer(model, RATE)
        if rec.AcceptWaveform(audio_np.tobytes()):
            result = json.loads(rec.Result())
            text   = result.get("text", "")
            if text:
                logger.info(f"STT (Vosk): {text}")
                return text
    except Exception as e:
        logger.error(f"Vosk failed: {e}")
    return None
