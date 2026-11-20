// Pusty service worker: przejmuje folder /tramwaje/, żeby nie obsługiwał go worker dziennika.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
