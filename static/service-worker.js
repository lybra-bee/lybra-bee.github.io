const CACHE_NAME = 'lybra-bee-cache-v1';
const urlsToCache = [
  '/',
  '/css/style.css',
  '/posts/',
  '/gallery/',
  '/about/'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
