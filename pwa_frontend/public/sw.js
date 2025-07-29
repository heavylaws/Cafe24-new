const CACHE_NAME = 'cafe24-pos-v1.0.0';
const API_CACHE_NAME = 'cafe24-api-v1.0.0';

// Assets to cache for offline functionality
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png'
];

// API endpoints to cache for offline access
const API_ENDPOINTS_TO_CACHE = [
  '/api/v1/orders/active',
  '/api/v1/realtime/orders/active-live',
  '/api/v1/realtime/dashboard/live-stats'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Install');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activate');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
            console.log('[ServiceWorker] Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Fetch event - handle network requests
self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url);
  
  // Handle API requests
  if (requestUrl.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(event.request));
    return;
  }
  
  // Handle static assets
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached response if available
        if (response) {
          return response;
        }
        
        // Otherwise fetch from network
        return fetch(event.request)
          .then((response) => {
            // Don't cache if not successful
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone response for caching
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });
            
            return response;
          })
          .catch(() => {
            // Return offline page or fallback
            if (event.request.destination === 'document') {
              return caches.match('/');
            }
          });
      })
  );
});

// Handle API requests with caching strategy
async function handleApiRequest(request) {
  const url = new URL(request.url);
  const pathname = url.pathname;
  
  // For GET requests that should be cached
  if (request.method === 'GET' && shouldCacheApiEndpoint(pathname)) {
    try {
      // Try network first
      const networkResponse = await fetch(request.clone());
      
      if (networkResponse.ok) {
        // Cache successful response
        const cache = await caches.open(API_CACHE_NAME);
        const responseToCache = networkResponse.clone();
        
        // Add timestamp to cached response
        const responseWithTimestamp = new Response(
          JSON.stringify({
            ...await responseToCache.json(),
            _cached_at: Date.now(),
            _offline: false
          }),
          {
            status: responseToCache.status,
            statusText: responseToCache.statusText,
            headers: responseToCache.headers
          }
        );
        
        cache.put(request, responseWithTimestamp);
        return networkResponse;
      }
    } catch (error) {
      console.log('[ServiceWorker] Network failed for:', pathname);
    }
    
    // Fallback to cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[ServiceWorker] Serving from cache:', pathname);
      const cachedData = await cachedResponse.json();
      
      // Mark as offline and add age info
      const offlineResponse = new Response(
        JSON.stringify({
          ...cachedData,
          _offline: true,
          _cached_age: Date.now() - (cachedData._cached_at || 0)
        }),
        {
          status: 200,
          statusText: 'OK (Offline)',
          headers: { 'Content-Type': 'application/json' }
        }
      );
      
      return offlineResponse;
    }
  }
  
  // For non-cacheable requests, just try network
  try {
    return await fetch(request);
  } catch (error) {
    // Return offline error response
    return new Response(
      JSON.stringify({
        error: 'Network unavailable',
        message: 'This request requires an internet connection',
        _offline: true
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Check if API endpoint should be cached for offline access
function shouldCacheApiEndpoint(pathname) {
  return API_ENDPOINTS_TO_CACHE.some(endpoint => pathname.includes(endpoint)) ||
         pathname.includes('/orders/active') ||
         pathname.includes('/dashboard/live-stats');
}

// Handle background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync:', event.tag);
  
  if (event.tag === 'order-status-update') {
    event.waitUntil(syncOrderStatusUpdates());
  }
  
  if (event.tag === 'offline-actions') {
    event.waitUntil(syncOfflineActions());
  }
});

// Sync order status updates when back online
async function syncOrderStatusUpdates() {
  try {
    // Get pending updates from IndexedDB (implementation would go here)
    console.log('[ServiceWorker] Syncing order status updates...');
    
    // For now, just notify that sync is available
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_AVAILABLE',
        payload: { action: 'order-status-update' }
      });
    });
  } catch (error) {
    console.error('[ServiceWorker] Failed to sync order updates:', error);
  }
}

// Sync offline actions when back online
async function syncOfflineActions() {
  try {
    console.log('[ServiceWorker] Syncing offline actions...');
    
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_AVAILABLE',
        payload: { action: 'offline-actions' }
      });
    });
  } catch (error) {
    console.error('[ServiceWorker] Failed to sync offline actions:', error);
  }
}

// Handle push notifications (for future enhancement)
self.addEventListener('push', (event) => {
  if (!event.data) {
    return;
  }
  
  const data = event.data.json();
  console.log('[ServiceWorker] Push notification received:', data);
  
  const options = {
    body: data.message,
    icon: '/logo192.png',
    badge: '/favicon.ico',
    vibrate: [200, 100, 200],
    tag: data.tag || 'default',
    data: data.data || {}
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'Cafe24 POS', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[ServiceWorker] Notification clicked:', event.notification);
  
  event.notification.close();
  
  // Focus existing window or open new one
  event.waitUntil(
    self.clients.matchAll().then((clients) => {
      if (clients.length > 0) {
        return clients[0].focus();
      }
      return self.clients.openWindow('/');
    })
  );
});

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
  console.log('[ServiceWorker] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_API_RESPONSE') {
    const { url, data } = event.data.payload;
    cacheApiResponse(url, data);
  }
});

// Cache API response manually
async function cacheApiResponse(url, data) {
  try {
    const cache = await caches.open(API_CACHE_NAME);
    const response = new Response(
      JSON.stringify({
        ...data,
        _cached_at: Date.now(),
        _offline: false
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
    
    await cache.put(url, response);
    console.log('[ServiceWorker] Manually cached API response:', url);
  } catch (error) {
    console.error('[ServiceWorker] Failed to cache API response:', error);
  }
}