// naina/web/static/js/gesture.js
let gestureEnabled = false;
let mpCamera = null;
let hands = null;
let prevWristX = null;
let prevTime = 0;

// Throttle: process at most 20fps
let _lastFrame = 0;
const GESTURE_FRAME_MS = 1000 / 20;

// Lerp cursor smoothing — lower = smoother but more lag, higher = snappier
const CURSOR_LERP = 0.28;
let _smoothX = 0.5, _smoothY = 0.5;

// Dwell
let _dwellX = null, _dwellY = null, _dwellTimer = null;
const DWELL_R = 0.07, DWELL_MS = 1400;

// Pinch
let _pinching = false, _pinchCooldown = false;

// Open-palm / fist / swipe debounce
let _palmCooldown = false, _fistCooldown = false, _swipeCooldown = false;

function initGesture() {
  const video = document.getElementById('gesture-video');
  if (!video || typeof Hands === 'undefined') {
    console.warn('MediaPipe Hands not available');
    return;
  }

  hands = new Hands({
    locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4/${f}`
  });
  hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 0,          // 0 = fastest model
    minDetectionConfidence: 0.65,
    minTrackingConfidence: 0.55
  });
  hands.onResults(onResults);

  if (typeof Camera !== 'undefined') {
    mpCamera = new Camera(video, {
      onFrame: async () => {
        if (!gestureEnabled || !hands) return;
        const now = performance.now();
        if (now - _lastFrame < GESTURE_FRAME_MS) return; // throttle to 15fps
        _lastFrame = now;
        await hands.send({ image: video });
      },
      width: 320, height: 240
    });
    mpCamera.start();
    gestureEnabled = true;
    _syncUI(true);
  }

  document.getElementById('gesture-toggle')?.addEventListener('click', toggleGesture);
  document.getElementById('gesture-status')?.addEventListener('click', toggleGesture);
}

function _syncUI(on) {
  document.getElementById('gesture-toggle')?.classList.toggle('active', on);
  const lbl = document.getElementById('gesture-label');
  if (lbl) lbl.textContent = on ? 'Gesture ON' : 'Gesture Off';
}

export function toggleGesture() {
  gestureEnabled = !gestureEnabled;
  _syncUI(gestureEnabled);
  if (gestureEnabled) { mpCamera?.start(); showHint('Gesture ON'); }
  else { mpCamera?.stop(); fire('gesture:cursor', { x: -1, y: -1 }); }
}

function onResults(results) {
  if (!results.multiHandLandmarks?.length) {
    prevWristX = null; _dwellX = null; clearTimeout(_dwellTimer);
    _smoothX = 0.5; _smoothY = 0.5; // reset lerp so next entry starts fresh
    fire('gesture:cursor', { x: -1, y: -1 });
    return;
  }

  const lm  = results.multiHandLandmarks[0];
  const now = Date.now();
  const dt  = (now - prevTime) / 1000;
  prevTime  = now;

  const thumb = lm[4], idx = lm[8], wrist = lm[0];
  const rawX = 1 - idx.x, rawY = idx.y;  // mirror X

  // ── Lerp-smoothed cursor (removes jitter, keeps responsiveness) ───────────
  _smoothX += (rawX - _smoothX) * CURSOR_LERP;
  _smoothY += (rawY - _smoothY) * CURSOR_LERP;
  const cx = _smoothX, cy = _smoothY;

  fire('gesture:cursor', { x: cx, y: cy });

  // ── Pinch distance ────────────────────────────────────────────────────────
  const pinchDist = Math.hypot(thumb.x - idx.x, thumb.y - idx.y);
  fire('gesture:pinch-dist', { dist: pinchDist });

  // ── Pinch click (debounced) ───────────────────────────────────────────────
  if (pinchDist < 0.06 && !_pinching && !_pinchCooldown) {
    _pinching = true; _pinchCooldown = true;
    fire('gesture:pinch', { x: cx, y: cy });
    showHint('Pinch');
    setTimeout(() => { _pinchCooldown = false; }, 900);
  } else if (pinchDist > 0.1) {
    _pinching = false;
  }

  // ── Zoom ──────────────────────────────────────────────────────────────────
  if (pinchDist < 0.05)                           fire('gesture:zoom-in');
  else if (pinchDist > 0.18 && pinchDist < 0.35)  fire('gesture:zoom-out');

  // ── Swipe (with cooldown to avoid skipping multiple panels) ───────────────
  if (prevWristX !== null && dt > 0.01 && dt < 0.3 && !_swipeCooldown) {
    const vel = (wrist.x - prevWristX) / dt;
    if (vel > 0.5) {
      _swipeCooldown = true;
      fire('gesture:swipe-right'); showHint('Prev');
      setTimeout(() => { _swipeCooldown = false; }, 700);
    } else if (vel < -0.5) {
      _swipeCooldown = true;
      fire('gesture:swipe-left'); showHint('Next');
      setTimeout(() => { _swipeCooldown = false; }, 700);
    }
  }
  prevWristX = wrist.x;

  // ── Open palm ─────────────────────────────────────────────────────────────
  const tips = [4, 8, 12, 16, 20], bases = [2, 5, 9, 13, 17];
  const isOpen = tips.every((t, i) => lm[t].y < lm[bases[i]].y) && pinchDist > 0.15;
  if (isOpen && !_palmCooldown) {
    _palmCooldown = true;
    fire('gesture:open-palm');
    showHint('Back');
    setTimeout(() => { _palmCooldown = false; }, 1200);
  }

  // ── Fist ──────────────────────────────────────────────────────────────────
  const isFist = [8, 12, 16, 20].every((t, i) => lm[t].y > lm[bases[i + 1]].y);
  if (isFist && !_fistCooldown) {
    _fistCooldown = true;
    fire('gesture:fist');
    showHint('Select');
    setTimeout(() => { _fistCooldown = false; }, 900);
  }

  // ── Dwell click ───────────────────────────────────────────────────────────
  if (_dwellX === null) {
    _dwellX = cx; _dwellY = cy;
    _dwellTimer = setTimeout(() => {
      if (_dwellX !== null) fire('gesture:dwell', { x: _dwellX, y: _dwellY });
    }, DWELL_MS);
  } else if (Math.hypot(cx - _dwellX, cy - _dwellY) > DWELL_R) {
    _dwellX = cx; _dwellY = cy;
    clearTimeout(_dwellTimer);
    _dwellTimer = setTimeout(() => {
      if (_dwellX !== null) fire('gesture:dwell', { x: _dwellX, y: _dwellY });
    }, DWELL_MS);
  }
}

function fire(name, detail) {
  document.dispatchEvent(new CustomEvent(name, { detail }));
}

let _hintTimer;
function showHint(text) {
  const el = document.getElementById('gesture-indicator');
  if (!el) return;
  el.textContent = text;
  el.classList.add('show');
  clearTimeout(_hintTimer);
  _hintTimer = setTimeout(() => el.classList.remove('show'), 1400);
}

window.addEventListener('load', initGesture);
