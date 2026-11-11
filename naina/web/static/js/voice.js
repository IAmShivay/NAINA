// naina/web/static/js/voice.js
let recognition = null;
let isListening  = false;


// ── TTS — edge-tts streaming backend ─────────────────────────────────────────
// Uses MediaSource API so playback starts on first audio chunk (~300ms).
// AbortController cancels any in-flight fetch when a new speak() is called.
let _currentAudio    = null;
let _fetchController = null;
let _mediaSource     = null;

// Unlock AudioContext on first user interaction (browser autoplay policy)
let _audioUnlocked = false;
document.addEventListener('click', function _unlock() {
  if (_audioUnlocked) return;
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  ctx.resume(); ctx.close();
  _audioUnlocked = true;
}, { once: true });

function _stopCurrent() {
  if (_fetchController) { _fetchController.abort(); _fetchController = null; }
  if (_currentAudio)    { _currentAudio.pause(); _currentAudio.src = ''; _currentAudio = null; }
  if (_mediaSource && _mediaSource.readyState === 'open') {
    try { _mediaSource.endOfStream(); } catch (_) {}
  }
  _mediaSource = null;
}

export async function speakBrowser(text) {
  _stopCurrent();

  const controller = new AbortController();
  _fetchController = controller;

  // MediaSource lets the browser decode+play while we're still downloading
  const ms  = new MediaSource();
  _mediaSource = ms;
  const url = URL.createObjectURL(ms);
  const audio = new Audio(url);
  _currentAudio = audio;

  audio.onended = () => { URL.revokeObjectURL(url); };

  await new Promise((resolve, reject) => {
    ms.addEventListener('sourceopen', async () => {
      URL.revokeObjectURL(url); // object URL no longer needed once source is open
      let sb;
      try {
        sb = ms.addSourceBuffer('audio/mpeg');
      } catch (e) {
        // Fallback: browser doesn't support audio/mpeg MediaSource (Safari) — use blob
        reject(e);
        return;
      }

      const queue   = [];
      let   done    = false;
      let   appending = false;

      const pump = () => {
        if (appending || sb.updating) return;
        if (queue.length === 0) {
          if (done && ms.readyState === 'open') {
            try { ms.endOfStream(); } catch (_) {}
          }
          return;
        }
        appending = true;
        const chunk = queue.shift();
        sb.appendBuffer(chunk);
      };

      sb.addEventListener('updateend', () => { appending = false; pump(); });

      try {
        const resp = await fetch(`/api/tts?text=${encodeURIComponent(text)}`, { signal: controller.signal });
        if (!resp.ok) throw new Error(`TTS ${resp.status}`);

        const reader = resp.body.getReader();
        let started = false;
        while (true) {
          const { value, done: streamDone } = await reader.read();
          if (streamDone) break;
          if (_fetchController !== controller) return; // superseded
          queue.push(value);
          pump();
          if (!started) { started = true; audio.play().catch(() => {}); }
        }
        done = true;
        pump();
        resolve();
      } catch (e) {
        if (e.name !== 'AbortError') console.error('[TTS] stream failed:', e.message);
        reject(e);
      }
    }, { once: true });

    audio.src = url; // triggers sourceopen
  }).catch(async (e) => {
    // Fallback for browsers without audio/mpeg MediaSource (e.g. Safari)
    if (e.name === 'AbortError') return;
    _stopCurrent();
    const controller2 = new AbortController();
    _fetchController = controller2;
    try {
      const resp = await fetch(`/api/tts?text=${encodeURIComponent(text)}`, { signal: controller2.signal });
      if (!resp.ok) return;
      const blob    = await resp.blob();
      if (_fetchController !== controller2) return;
      _fetchController = null;
      const blobUrl = URL.createObjectURL(blob);
      const a2      = new Audio(blobUrl);
      _currentAudio = a2;
      a2.onended = () => { URL.revokeObjectURL(blobUrl); };
      a2.play().catch(() => {});
    } catch (_) {}
  });
}

// ── STT — click-to-toggle ─────────────────────────────────────────────────────
function _makeRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return null;
  const r = new SR();
  r.lang = 'hi-IN';
  r.continuous = false;
  r.interimResults = false;

  r.onresult = (e) => {
    const text = e.results[0][0].transcript;
    document.dispatchEvent(new CustomEvent('voice:result', { detail: { text } }));
    setListening(false);
  };
  r.onerror = (e) => {
    console.warn('STT error:', e.error);
    setListening(false);
    const el = document.getElementById('voice-text');
    if (e.error === 'not-allowed' && el) el.textContent = 'Mic blocked — allow in browser settings';
    else if (e.error === 'no-speech' && el) el.textContent = 'No speech — try again';
  };
  r.onend = () => setListening(false);
  return r;
}

function _handleMicClick() {
  if (isListening) { stopListen(); return; }
  recognition = _makeRecognition();
  startListen();
}

export function initVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    const el = document.getElementById('voice-text');
    if (el) el.textContent = 'Voice not supported — use Chrome or Edge';
    return;
  }
  recognition = _makeRecognition();
  document.getElementById('voice-btn')?.addEventListener('click', _handleMicClick);
  document.getElementById('voice-btn-bar')?.addEventListener('click', _handleMicClick);
}

export function startListen() {
  if (!recognition || isListening) return;
  try { recognition.start(); setListening(true); }
  catch (e) { console.warn('Could not start recognition:', e); setListening(false); }
}

export function stopListen() {
  if (recognition && isListening) try { recognition.stop(); } catch (_) {}
  setListening(false);
}

function setListening(v) {
  isListening = v;
  document.getElementById('voice-btn')?.classList.toggle('listening', v);
  document.getElementById('voice-btn-bar')?.classList.toggle('listening', v);
  const el = document.getElementById('voice-text');
  if (el) el.textContent = v ? 'Listening... speak now' : 'Say "Hey Naina" or tap MIC';
  document.getElementById('voice-ring')?.classList.toggle('active', v);
  document.getElementById('vb-waveform')?.classList.toggle('active', v);
  window.__nainaScene?.setVoiceActive(v);
}

initVoice();
export { isListening };
