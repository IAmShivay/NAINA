# Naina — Hand Gesture Reference

Gestures are detected by **MediaPipe Hands** running in your browser via webcam.
No server processing — everything runs client-side at 20fps.

---

## How It Works (Technical)

MediaPipe tracks **21 landmarks** on your hand in real time:

```
Wrist = lm[0]
Thumb tip = lm[4]    Index tip = lm[8]
Middle tip = lm[12]  Ring tip  = lm[16]   Pinky tip = lm[20]
Knuckles   = lm[5], lm[9], lm[13], lm[17]
```

Each frame (~50ms), the system:
1. Reads landmark positions (0.0–1.0 normalized coordinates)
2. Applies **lerp smoothing** (factor 0.28) to remove jitter
3. Checks gesture conditions and fires browser `CustomEvent`s
4. App.js listens for those events and acts accordingly

---

## Gesture Map

| Gesture | How to Do It | What Triggers | Action |
|---|---|---|---|
| **Cursor** | Any hand in frame | Always | Moves the on-screen pointer (index fingertip, mirrored) |
| **Pinch** | Touch thumb tip to index fingertip | Distance < 0.06 | Click (900ms cooldown) |
| **Open Palm** | All 5 fingers extended, spread out | All tips above knuckles + thumb/index gap > 0.15 | "Back" — go to previous panel (1200ms cooldown) |
| **Fist** | Curl all 4 fingers down | All tips below their knuckles | "Select" — confirm selection (900ms cooldown) |
| **Swipe Left** | Move wrist quickly to the left | Wrist X velocity < -0.5 units/sec | "Next" — next panel (700ms cooldown) |
| **Swipe Right** | Move wrist quickly to the right | Wrist X velocity > +0.5 units/sec | "Prev" — previous panel (700ms cooldown) |
| **Dwell** | Hold index finger still for ~1.4s | Cursor stays within radius 0.07 | Click at dwell position |
| **Zoom In** | Tight pinch (barely touching) | Pinch distance < 0.05 | Zoom in on image viewer |
| **Zoom Out** | Spread thumb and index wide | Pinch distance 0.18–0.35 | Zoom out on image viewer |

---

## Gesture Events Fired (for developers)

All events are dispatched on `document`:

```javascript
document.addEventListener('gesture:cursor',     e => /* { x, y } — 0.0 to 1.0, -1 when hand absent */);
document.addEventListener('gesture:pinch',      e => /* { x, y } — position of pinch */);
document.addEventListener('gesture:pinch-dist', e => /* { dist } — live pinch distance */);
document.addEventListener('gesture:open-palm',  e => /* no detail */);
document.addEventListener('gesture:fist',       e => /* no detail */);
document.addEventListener('gesture:swipe-left', e => /* no detail */);
document.addEventListener('gesture:swipe-right',e => /* no detail */);
document.addEventListener('gesture:dwell',      e => /* { x, y } — dwell position */);
document.addEventListener('gesture:zoom-in',    e => /* no detail */);
document.addEventListener('gesture:zoom-out',   e => /* no detail */);
```

---

## Cursor Smoothing

Raw MediaPipe output has pixel-level jitter. The cursor uses lerp interpolation:

```javascript
_smoothX += (rawX - _smoothX) * 0.28;   // CURSOR_LERP = 0.28
_smoothY += (rawY - _smoothY) * 0.28;
```

- **Lower value** (e.g. 0.1) = very smooth, more lag
- **Higher value** (e.g. 0.5) = snappier, more jitter
- Resets to center (0.5, 0.5) when hand leaves frame

---

## Toggle Gesture Mode

- Click the **Gesture** button in the sidebar
- Or click the **Gesture ON/OFF** status label
- When off, webcam stops and no CPU is used

---

## Performance Notes

- Runs at **20fps** (throttled to avoid CPU overload)
- Uses MediaPipe model complexity **0** (fastest model)
- Detection confidence: 0.65 | Tracking confidence: 0.55
- Camera resolution: 320x240 (sufficient for hand tracking)
- Each gesture has a **cooldown** to prevent repeated firing from a single held gesture

---

## Tips for Best Results

1. Keep your hand **30–60 cm** from the webcam
2. Use in **good lighting** — shadows on the hand reduce accuracy
3. Keep the **background simple** (plain wall works best)
4. For swipes, move your **whole wrist**, not just fingers
5. For pinch, bring thumb and index **fully together** and hold briefly
6. For open palm, make sure all fingers are clearly spread apart
