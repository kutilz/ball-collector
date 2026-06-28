/*
 * robot-viewer.js — Preview 3D robot (GLB) yang ringan untuk dashboard.
 *
 * Dipanggil LAZY: three.js (~670KB) baru di-download saat user pertama kali
 * membuka tab Sensor (lihat bootstrap di index.html). Render loop juga otomatis
 * berhenti saat viewer tak terlihat / tab browser disembunyikan → hemat GPU/CPU.
 *
 * Semua dependency di-host LOKAL (vendor/three) — nol ketergantungan internet,
 * konsisten dgn aturan offline ground station saat ESP32 mode AP.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Level kualitas (LOD) — file GLB beda kerapatan triangle. Dipilih via selector
// di card; tersimpan di localStorage. Server serve no-store, jadi tak ada jebakan
// cache saat model di-regenerate.
const QUALITY_URLS = {
    low:  '/model/robot-low.glb',
    med:  '/model/robot-med.glb',
    high: '/model/robot-high.glb',
};

export function initRobotViewer(container) {
    if (!container || container.dataset.inited === '1') return;
    container.dataset.inited = '1';

    const statusEl = container.querySelector('.robot3d-status');
    const setStatus = (txt, isError) => {
        if (!statusEl) return;
        statusEl.textContent = txt;
        statusEl.style.display = txt ? 'block' : 'none';
        statusEl.classList.toggle('is-error', !!isError);
    };

    // ── Renderer (transparan biar background card kelihatan) ──
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.domElement.classList.add('robot3d-canvas');
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(40, 1, 0.01, 100);
    camera.position.set(0.35, 0.28, 0.45);

    // ── Lighting: lembut & murah (tanpa shadow map) ──
    scene.add(new THREE.HemisphereLight(0xbfd4ff, 0x2a3040, 1.15));
    const key = new THREE.DirectionalLight(0xffffff, 2.0);
    key.position.set(0.6, 1.0, 0.8);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x88aaff, 0.7);
    fill.position.set(-0.7, 0.2, -0.5);
    scene.add(fill);

    // ── Controls ──
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 1.2;
    controls.rotateSpeed = 0.9;

    // ── Loader model dgn level kualitas (LOD) ──
    const loader = new GLTFLoader();
    let currentModel = null;
    let framed = false;            // frame kamera cuma sekali (jaga view saat ganti kualitas)
    let loadToken = 0;             // anti-race bila ganti level cepat

    function disposeModel(obj) {
        if (!obj) return;
        scene.remove(obj);
        obj.traverse((o) => {
            if (!o.isMesh) return;
            if (o.geometry) o.geometry.dispose();
            const m = o.material;
            if (Array.isArray(m)) m.forEach((x) => x && x.dispose());
            else if (m) m.dispose();
        });
    }

    function frameCamera(model) {
        const box = new THREE.Box3().setFromObject(model);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z) || 1;
        const radius = maxDim * 0.5;
        const dist = radius / Math.sin((camera.fov * Math.PI) / 180 / 2);
        camera.position.set(center.x + dist * 0.8, center.y + dist * 0.55, center.z + dist * 0.95);
        camera.near = dist / 100;
        camera.far = dist * 100;
        camera.updateProjectionMatrix();
        controls.target.copy(center);
        controls.minDistance = radius * 1.1;
        controls.maxDistance = dist * 3;
        controls.update();
    }

    function loadModel(level) {
        const url = QUALITY_URLS[level] || QUALITY_URLS.med;
        const token = ++loadToken;
        setStatus('Memuat model…');
        loader.load(
            url,
            (gltf) => {
                if (token !== loadToken) { disposeModel(gltf.scene); return; }  // sudah di-supersede
                disposeModel(currentModel);
                currentModel = gltf.scene;
                scene.add(currentModel);
                if (!framed) { frameCamera(currentModel); framed = true; }
                setStatus('', false);
            },
            (ev) => {
                if (token === loadToken && ev && ev.total) {
                    setStatus(`Memuat model… ${Math.round((ev.loaded / ev.total) * 100)}%`);
                }
            },
            (err) => {
                if (token !== loadToken) return;
                console.error('[robot-viewer] gagal memuat model:', err);
                setStatus('Gagal memuat model 3D', true);
            }
        );
    }

    // Selector kualitas (Low/Med/High) — pilihan disimpan di localStorage.
    const STORE_KEY = 'robot3d-quality';
    const select = document.getElementById('robot3d-quality');
    let level = 'med';
    try { level = localStorage.getItem(STORE_KEY) || 'med'; } catch (e) { /* private mode */ }
    if (!QUALITY_URLS[level]) level = 'med';
    if (select) {
        select.value = level;
        select.addEventListener('change', () => {
            const lv = select.value;
            try { localStorage.setItem(STORE_KEY, lv); } catch (e) { /* ignore */ }
            loadModel(lv);
        });
    }
    loadModel(level);

    // ── Resize: ikuti ukuran container ──
    function resize() {
        const w = container.clientWidth;
        const h = container.clientHeight;
        if (!w || !h) return;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
    }
    const ro = new ResizeObserver(resize);
    ro.observe(container);
    resize();

    // ── Render loop: jalan hanya saat viewer terlihat & tab aktif ──
    let running = false;
    let rafId = 0;
    function tick() {
        if (!running) return;
        rafId = requestAnimationFrame(tick);
        controls.update();
        renderer.render(scene, camera);
    }
    function start() {
        if (running || document.hidden) return;
        running = true;
        tick();
    }
    function stop() {
        running = false;
        if (rafId) cancelAnimationFrame(rafId);
    }

    // Berhenti merender saat tab/card tak terlihat (hemat baterai laptop).
    const vis = new IntersectionObserver(
        (entries) => {
            for (const e of entries) e.isIntersecting ? start() : stop();
        },
        { threshold: 0.05 }
    );
    vis.observe(container);
    document.addEventListener('visibilitychange', () => {
        document.hidden ? stop() : start();
    });
    start();

    // Handle diagnostik — berguna utk debugging / verifikasi di renderer headless
    // (mis. preview dgn document.hidden=true di mana rAF di-throttle).
    container._robot3d = {
        renderer, scene, camera, controls,
        renderOnce: () => renderer.render(scene, camera),
    };
}
