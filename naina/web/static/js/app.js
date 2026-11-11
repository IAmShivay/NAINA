// naina/web/static/js/app.js
import { speakBrowser } from './voice.js';

const API = window.location.origin;
const panels = ['chat','health','todos','system','music','files'];
let curPanel = 0;
let ws = null;

// ── WebSocket ─────────────────────────────────────────────────────────────────
function connectWS() {
  const url = API.replace(/^http/,'ws') + '/ws';
  ws = new WebSocket(url);
  ws.onmessage = (e) => {
    const d = JSON.parse(e.data);
    if (d.type === 'thinking') addMsg('NAINA','...','naina thinking');
    else if (d.type === 'response') { removeThinking(); addMsg('NAINA', d.text, 'naina'); speakBrowser(d.text); }
  };
  ws.onclose = () => setTimeout(connectWS, 3000);
}

// ── Chat ──────────────────────────────────────────────────────────────────────
async function sendChat(text) {
  if (!text?.trim()) return;
  addMsg('YOU', text, 'user');
  document.getElementById('chat-input').value = '';
  try {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ text }));
    } else {
      const r = await fetch(`${API}/api/chat`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text, speak_response:false}) });
      const d = await r.json();
      addMsg('NAINA', d.response, 'naina');
      speakBrowser(d.response);
    }
  } catch(_) { addMsg('NAINA','Boss, connection issue. Dobara try karo.','naina'); }
}
window.sendChat = sendChat;

function addMsg(sender, text, cls) {
  const c = document.getElementById('chat-messages');
  const d = document.createElement('div');
  d.className = `message ${cls}`;
  const time = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  d.innerHTML = `
    <div class="msg-meta">
      <span class="msg-from">${sender}</span>
      <span class="msg-time">${time}</span>
    </div>
    <div class="msg-body">${text}</div>`;
  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
}
function removeThinking() { document.querySelectorAll('.message.thinking').forEach(e=>e.remove()); }

// ── Panels ────────────────────────────────────────────────────────────────────
function switchPanel(name) {
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(t=>t.classList.remove('active'));
  document.getElementById(`panel-${name}`)?.classList.add('active');
  document.querySelector(`[data-panel="${name}"]`)?.classList.add('active');
  curPanel = panels.indexOf(name);
  if (name === 'system') refreshSysStats();
  if (name === 'files' && !_filePath) loadFiles(null);
}
function nextPanel() { curPanel=(curPanel+1)%panels.length; switchPanel(panels[curPanel]); }
function prevPanel() { curPanel=(curPanel-1+panels.length)%panels.length; switchPanel(panels[curPanel]); }

// ── System Stats ──────────────────────────────────────────────────────────────
async function refreshSysStats() {
  try {
    const r = await fetch(`${API}/api/chat`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text:'get system stats'}) });
    const d = await r.json();
    const m = d.response.match(/\{[\s\S]*\}/);
    if (m) {
      const s = JSON.parse(m[0]).result;
      document.getElementById('cpu-val').textContent  = `${s.cpu_percent}%`;
      document.getElementById('ram-val').textContent  = `${s.ram_used_gb}/${s.ram_total_gb} GB`;
      document.getElementById('disk-val').textContent = `${s.disk_used_gb}/${s.disk_total_gb} GB`;
      document.getElementById('cpu-bar').style.width  = `${s.cpu_percent}%`;
      document.getElementById('ram-bar').style.width  = `${s.ram_percent}%`;
      document.getElementById('disk-bar').style.width = `${s.disk_percent}%`;
    }
  } catch(_) {}
}
async function refreshBattery() {
  try {
    const r = await fetch(`${API}/api/chat`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text:'get battery status'}) });
    const d = await r.json();
    const m = d.response.match(/\{[\s\S]*\}/);
    if (m) {
      const b = JSON.parse(m[0]).result;
      document.getElementById('batt-val').textContent = `${b.percent}%${b.plugged?' +':' '}`;
      document.getElementById('batt-bar').style.width = `${b.percent}%`;
    }
  } catch(_) {}
}

// ── Clock ─────────────────────────────────────────────────────────────────────
function tick() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

// ── Health ────────────────────────────────────────────────────────────────────
window.requestHealth = () => sendChat('aaj ki health batao');

// ── File Browser ──────────────────────────────────────────────────────────────
let _filePath = null;
let _fileItems = [];
let _fileParent = null;
let _hoveredFileIdx = -1;

async function loadFiles(path) {
  const url = path ? `${API}/api/files?path=${encodeURIComponent(path)}` : `${API}/api/files`;
  try {
    const r = await fetch(url);
    const d = await r.json();
    _filePath = d.path;
    _fileParent = d.parent;
    _fileItems = d.items;
    renderFileGrid();
  } catch(_) {
    document.getElementById('file-grid').innerHTML = '<div class="file-error">Could not load directory</div>';
  }
}
window.loadFiles = loadFiles;

function _fileIcon(item) {
  if (item.is_dir)  return '[DIR]';
  if (item.is_image) return '[IMG]';
  const e = item.ext;
  if (['.mp4','.mkv','.avi','.mov','.webm'].includes(e)) return '[VID]';
  if (['.mp3','.wav','.flac','.ogg','.m4a'].includes(e)) return '[AUD]';
  if (['.pdf','.doc','.docx','.txt','.md'].includes(e))  return '[DOC]';
  if (['.zip','.rar','.7z','.tar'].includes(e))          return '[ZIP]';
  return '[FILE]';
}

function renderFileGrid() {
  const grid  = document.getElementById('file-grid');
  const crumb = document.getElementById('file-crumb');
  if (!grid) return;
  if (crumb) crumb.textContent = _filePath || '';

  grid.innerHTML = _fileItems.map((item, i) => `
    <div class="file-card" data-idx="${i}" data-path="${item.path}" data-isdir="${item.is_dir}" data-isimg="${item.is_image}"
         onclick="fileCardClick(${i})">
      <div class="file-icon">${_fileIcon(item)}</div>
      <div class="file-name">${item.name}</div>
    </div>`).join('');
}
window.fileCardClick = (i) => openFileItem(_fileItems[i]);

async function openFileItem(item) {
  if (!item) return;
  if (item.is_dir) {
    loadFiles(item.path);
  } else if (item.is_image) {
    try {
      const r = await fetch(`${API}/api/file/image?path=${encodeURIComponent(item.path)}`);
      const d = await r.json();
      openViewer(d.data_url, d.name, item.path);
    } catch(_) {}
  }
}

function highlightFileCard(idx) {
  document.querySelectorAll('.file-card').forEach((c,i) => c.classList.toggle('hovered', i === idx));
  _hoveredFileIdx = idx;
}

// ── Image Viewer ──────────────────────────────────────────────────────────────
let _viewerOpen = false;
let _viewerZoom = 1;
let _viewerPath = null;
let _prevPinchDist = null;

function openViewer(dataUrl, name, filePath) {
  _viewerOpen = true;
  _viewerZoom = 1;
  _viewerPath = filePath;
  const ov = document.getElementById('viewer-overlay');
  const img = document.getElementById('viewer-img');
  const lbl = document.getElementById('viewer-label');
  if (!ov || !img) return;
  img.src = dataUrl;
  img.style.transform = 'scale(1)';
  img.style.filter = '';  // let CSS handle the hologram filter
  if (lbl) lbl.textContent = name;
  ov.classList.add('open');
}

function closeViewer() {
  _viewerOpen = false;
  _viewerZoom = 1;
  _prevPinchDist = null;
  document.getElementById('viewer-overlay')?.classList.remove('open');
}
window.closeViewer = closeViewer;

// ── Hand cursor ───────────────────────────────────────────────────────────────
const _cursor = document.getElementById('hand-cursor');

document.addEventListener('gesture:cursor', (e) => {
  const {x, y} = e.detail;
  if (!_cursor) return;
  if (x < 0) { _cursor.style.opacity = '0'; return; }
  _cursor.style.opacity = '1';
  _cursor.style.left = `${x * 100}vw`;
  _cursor.style.top  = `${y * 100}vh`;

  // Hit-test file cards when in files panel
  if (panels[curPanel] === 'files' && !_viewerOpen) {
    const el = document.elementFromPoint(x * window.innerWidth, y * window.innerHeight);
    const card = el?.closest('.file-card');
    if (card) {
      const idx = parseInt(card.dataset.idx);
      if (idx !== _hoveredFileIdx) highlightFileCard(idx);
    }
  }
});

// ── Gesture events ────────────────────────────────────────────────────────────
document.addEventListener('gesture:zoom-in', () => {
  if (panels[curPanel] !== 'files' && !_viewerOpen)
    window.__nainaScene?.zoomIn();
});
document.addEventListener('gesture:zoom-out', () => {
  if (panels[curPanel] !== 'files' && !_viewerOpen)
    window.__nainaScene?.zoomOut();
});

document.addEventListener('gesture:pinch-dist', (e) => {
  if (!_viewerOpen) { _prevPinchDist = null; return; }
  const dist = e.detail.dist;
  if (_prevPinchDist !== null) {
    const delta = (_prevPinchDist - dist) * 8;
    if (Math.abs(delta) > 0.02) {
      _viewerZoom = Math.max(0.4, Math.min(5, _viewerZoom + delta));
      const img = document.getElementById('viewer-img');
      if (img) img.style.transform = `scale(${_viewerZoom})`;
    }
  }
  _prevPinchDist = dist;
});

document.addEventListener('gesture:pinch', (e) => {
  if (_viewerOpen) return; // viewer uses continuous dist
  if (panels[curPanel] === 'files') {
    if (_hoveredFileIdx >= 0) openFileItem(_fileItems[_hoveredFileIdx]);
  }
});

document.addEventListener('gesture:dwell', (e) => {
  if (_viewerOpen || panels[curPanel] !== 'files') return;
  const {x, y} = e.detail;
  const el = document.elementFromPoint(x * window.innerWidth, y * window.innerHeight);
  const card = el?.closest('.file-card');
  if (card) {
    const idx = parseInt(card.dataset.idx);
    openFileItem(_fileItems[idx]);
  }
});

document.addEventListener('gesture:swipe-left',  () => {
  if (_viewerOpen) { closeViewer(); return; }
  nextPanel();
});
document.addEventListener('gesture:swipe-right', () => {
  if (_viewerOpen) { closeViewer(); return; }
  prevPanel();
});

document.addEventListener('gesture:open-palm', () => {
  if (_viewerOpen) { closeViewer(); return; }
  if (panels[curPanel] === 'files' && _fileParent) {
    loadFiles(_fileParent);
  } else {
    switchPanel('chat');
  }
});

document.addEventListener('gesture:fist', () => {
  if (_viewerOpen) { closeViewer(); return; }
  if (panels[curPanel] === 'files') {
    if (_hoveredFileIdx >= 0) openFileItem(_fileItems[_hoveredFileIdx]);
  } else {
    const v = document.getElementById('chat-input').value;
    if (v) sendChat(v);
  }
});

document.addEventListener('voice:result', (e) => sendChat(e.detail.text));

// ── UI events ─────────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-btn[data-panel]').forEach(t => t.addEventListener('click', () => switchPanel(t.dataset.panel)));
document.getElementById('send-btn')?.addEventListener('click', () => sendChat(document.getElementById('chat-input').value));
document.getElementById('chat-input')?.addEventListener('keydown', e => { if(e.key==='Enter') sendChat(e.target.value); });
document.getElementById('todo-add-btn')?.addEventListener('click', () => {
  const inp = document.getElementById('todo-input');
  if (inp?.value.trim()) { sendChat(`add todo: ${inp.value}`); inp.value=''; }
});

// ── Music Player ──────────────────────────────────────────────────────────────
let _songs = [];
let _filteredSongs = [];
let _musicIdx = -1;
let _musicAudio = null;
let _musicPlaying = false;

async function loadMusicList(q = '') {
  try {
    const url = q ? `${API}/api/music/list?q=${encodeURIComponent(q)}` : `${API}/api/music/list`;
    const r = await fetch(url);
    const d = await r.json();
    _filteredSongs = d.songs || [];
    if (!q) _songs = _filteredSongs;
    renderMusicList();
  } catch(_) {
    document.getElementById('music-list').innerHTML = '<div class="music-list-empty">Could not load music folder.</div>';
  }
}

function renderMusicList() {
  const el = document.getElementById('music-list');
  if (!el) return;
  if (!_filteredSongs.length) {
    el.innerHTML = '<div class="music-list-empty">No songs found.</div>';
    return;
  }
  el.innerHTML = _filteredSongs.map((s, i) => `
    <div class="music-item ${_musicIdx === i ? 'active' : ''}" data-idx="${i}" onclick="musicPlay(${i})">
      <span class="music-item-num">${String(i+1).padStart(2,'0')}</span>
      <span class="music-item-name">${s.name}</span>
      <span class="music-item-ext">${s.ext.replace('.','').toUpperCase()}</span>
    </div>`).join('');
}

function _setMusicPlaying(playing) {
  _musicPlaying = playing;
  document.getElementById('music-play-ico').textContent = playing ? '||' : '>';
  document.getElementById('music-play-lbl').textContent = playing ? 'PAUSE' : 'PLAY';
  document.getElementById('music-wave')?.classList.toggle('playing', playing);
}

window.musicPlay = function(idx) {
  if (idx < 0 || idx >= _filteredSongs.length) return;
  _musicIdx = idx;
  const song = _filteredSongs[idx];

  // Stop previous
  if (_musicAudio) { _musicAudio.pause(); _musicAudio.src = ''; _musicAudio = null; }

  const audio = new Audio(`${API}/api/music/play?path=${encodeURIComponent(song.path)}`);
  _musicAudio = audio;
  audio.onended = () => { _setMusicPlaying(false); musicPlayNext(); };
  audio.onerror = () => { _setMusicPlaying(false); console.error('[Music] Failed to play:', song.name); };
  audio.play().then(() => _setMusicPlaying(true)).catch(e => console.error('[Music]', e));

  document.getElementById('music-now-title').textContent = song.name;
  renderMusicList();
};

function musicPlayNext() {
  if (_filteredSongs.length === 0) return;
  musicPlay((_musicIdx + 1) % _filteredSongs.length);
}
function musicPlayPrev() {
  if (_filteredSongs.length === 0) return;
  musicPlay((_musicIdx - 1 + _filteredSongs.length) % _filteredSongs.length);
}
function musicToggle() {
  if (!_musicAudio) { if (_filteredSongs.length) musicPlay(0); return; }
  if (_musicPlaying) { _musicAudio.pause(); _setMusicPlaying(false); }
  else               { _musicAudio.play().then(() => _setMusicPlaying(true)); }
}

document.getElementById('music-play-btn')?.addEventListener('click', musicToggle);
document.getElementById('music-next-btn')?.addEventListener('click', musicPlayNext);
document.getElementById('music-prev-btn')?.addEventListener('click', musicPlayPrev);
document.getElementById('music-search')?.addEventListener('input', (e) => loadMusicList(e.target.value));

// ── Boot ──────────────────────────────────────────────────────────────────────
connectWS();
tick(); setInterval(tick, 1000);
setInterval(refreshSysStats, 30000);
setInterval(refreshBattery, 60000);
refreshBattery();
loadMusicList();
