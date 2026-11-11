// naina/web/sw.js
const CACHE = 'naina-v3';
const SHELL = ['/', '/static/css/naina.css'];  // only cache shell, not JS

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL).catch(() => {})));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  // Delete ALL old caches on activate
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = e.request.url;

  // Never cache: API calls, WebSocket, JS files — always go to network
  if (url.includes('/api/') || url.includes('/ws') || url.includes('.js')) {
    e.respondWith(fetch(e.request));
    return;
  }

  // Cache-first for CSS and other static assets
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
