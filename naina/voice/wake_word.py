# naina/voice/wake_word.py
# Uses Vosk keyword-grammar spotting — detects "hey naina" / "naina" offline
import json
import queue
import threading
from loguru import logger

try:
    import sounddevice as sd
    SD_AVAILABLE = True
except ImportError:
    SD_AVAILABLE = False
    logger.warning("sounddevice not available — wake word listener disabled")

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logger.warning("vosk not installed — wake word detection disabled")

CHUNK    = 4000    # ~250ms at 16kHz
RATE     = 16000
CHANNELS = 1

# All variations to accept as wake word
_KEYWORDS = ["hey naina", "naina", "hei naina", "hey nina", "nina"]

class WakeWordListener:
    def __init__(self, on_detected: callable):
        self.on_detected = on_detected
        self._stop  = threading.Event()
        self._queue: queue.Queue = queue.Queue()
        self._rec   = None

        if VOSK_AVAILABLE:
            try:
                model = Model(lang="en-us")   # auto-downloads small model on first run
                # Grammar mode: Vosk only considers these words — very fast & accurate
                grammar = json.dumps(_KEYWORDS + ["[unk]"])
                self._rec = KaldiRecognizer(model, RATE, grammar)
                logger.info(f"Wake word ready — listening for: {_KEYWORDS}")
            except Exception as e:
                logger.warning(f"Vosk wake word init failed: {e}")

    def start(self) -> None:
        if not SD_AVAILABLE:
            logger.warning("Wake word not started — sounddevice unavailable")
            return
        t = threading.Thread(target=self._listen_loop, daemon=True)
        t.start()
        logger.info("Wake word listener started (Vosk keyword spotting)")

    def stop(self) -> None:
        self._stop.set()

    def _audio_callback(self, indata, frames, time, status):
        self._queue.put(bytes(indata))

    def _listen_loop(self) -> None:
        if not self._rec:
            logger.warning("Wake word disabled — no Vosk recognizer")
            return
        try:
            with sd.RawInputStream(samplerate=RATE, channels=CHANNELS,
                                   dtype='int16', blocksize=CHUNK,
                                   callback=self._audio_callback):
                logger.debug("Wake word loop running")
                while not self._stop.is_set():
                    try:
                        data = self._queue.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    detected = False
                    if self._rec.AcceptWaveform(data):
                        text = json.loads(self._rec.Result()).get("text", "").lower()
                        detected = any(kw in text for kw in ["naina"])
                    else:
                        text = json.loads(self._rec.PartialResult()).get("partial", "").lower()
                        detected = any(kw in text for kw in ["naina"])

                    if detected and text.strip():
                        logger.info(f"Wake word detected: '{text}'")
                        self._stop.set()
                        self._rec.Reset()
                        self.on_detected()
                        self._stop.clear()
        except Exception as e:
            logger.error(f"Wake word stream error: {e}")
