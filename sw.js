const V = "maquiavel-8";
const FILES = [
    "./", "./index.html", "./poops.html", "./lapse.html",
    "./chain_poops.mjs", "./chain_lapse.mjs",
    "./core.mjs", "./mem.mjs", "./int64.mjs",
    "./rpc_worker.mjs", "./ps4_offsets.mjs",
    "./payload.bin",
    "./patches/1100.bin", "./patches/1150.bin",
    "./patches/1200.bin", "./patches/1250.bin",
    "./patches/1300.bin", "./patches/1302.bin",
    "./patches/1304.bin", "./patches/1350.bin",
    "./patches/1352.bin",
];

self.addEventListener("install", e => {
    e.waitUntil(
        caches.open(V)
            .then(c => c.addAll(FILES))
            .catch(() => {})
            .then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", e => {
    e.waitUntil(
        caches.keys()
            .then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", e => {
    if (e.request.method !== "GET") return;
    e.respondWith(
        caches.match(e.request).then(cached => {
            if (cached) return cached;
            return fetch(e.request).then(r => {
                if (r && r.ok) {
                    try {
                        const copy = r.clone();
                        caches.open(V).then(c => c.put(e.request, copy)).catch(() => {});
                    } catch (_) {}
                }
                return r;
            }).catch(() => (e.request.mode === "navigate"
                ? caches.match("./index.html") : null));
        })
    );
});
