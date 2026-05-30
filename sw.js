const CACHE = '67bank-v1';
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(['./67bank.html'])));
});
self.addEventListener('activate', e => clients.claim());
self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).catch(() =>
      caches.match('./67bank.html')
    ))
  );
});
self.addEventListener('message', e => {
  if(e.data && e.data.type === 'INV_NOTIFY'){
    self.registration.showNotification('💰 67Bank — Инвестиции', {
      body: e.data.text,
      icon: './icon-192.png',
      badge: './icon-192.png',
      vibrate: [200, 100, 200],
      tag: 'investment',
      renotify: true,
      actions: [{ action: 'open', title: '📈 Открыть' }]
    });
  }
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(clients.openWindow('./67bank.html'));
});
