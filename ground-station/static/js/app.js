/**
 * app.js — Frontend logic untuk ground station robot pengumpul bola.
 *
 * Fitur:
 *   • Koneksi SocketIO untuk telemetri real-time
 *   • Keyboard handler (WASD, QE, Space, T)
 *   • HSV slider → emit ke server
 *   • Kontrol manual (tombol arah)
 *   • Update UI state badge, telemetri, logging
 *   • Toast notification system
 */

// ═══════════════════════════════════════════════════════════════
// Inisialisasi SocketIO
// ═══════════════════════════════════════════════════════════════
const socket = io();

// Kecepatan motor untuk kontrol manual
const MANUAL_SPEED = 80;
const MANUAL_TURN = 70;

// ═══════════════════════════════════════════════════════════════
// Referensi elemen DOM
// ═══════════════════════════════════════════════════════════════
const el = {
    // Status koneksi
    connDot:       document.getElementById("conn-dot"),
    connLabel:     document.getElementById("conn-label"),
    connDetail:    document.getElementById("conn-detail"),
    connMode:      document.getElementById("conn-mode"),
    espIp:         document.getElementById("esp32-ip"),
    btnConnect:    document.getElementById("btn-connect"),

    // Mode
    btnManual:     document.getElementById("btn-manual"),
    btnAuto:       document.getElementById("btn-auto"),
    brainState:    document.getElementById("brain-state"),
    stateDuration: document.getElementById("state-duration"),
    ballsCollected:document.getElementById("balls-collected"),

    // Video overlay
    fpsVal:        document.getElementById("fps-val"),
    stateBadge:    document.getElementById("state-badge"),
    detectionText: document.getElementById("detection-text"),
    videoWrapper:  document.querySelector(".video-wrapper"),

    // Deteksi
    teleDetected:  document.getElementById("tele-detected"),
    teleBallX:     document.getElementById("tele-ball-x"),
    teleBallY:     document.getElementById("tele-ball-y"),
    teleBallArea:  document.getElementById("tele-ball-area"),
    teleOffsetX:   document.getElementById("tele-offset-x"),
    teleOffsetY:   document.getElementById("tele-offset-y"),
    cardDetection: document.getElementById("card-detection"),

    // Telemetri
    teleFps:       document.getElementById("tele-fps"),
    teleStreamFps: document.getElementById("tele-stream-fps"),
    teleCmdVx:     document.getElementById("tele-cmd-vx"),
    teleCmdVy:     document.getElementById("tele-cmd-vy"),
    teleCmdOmega:  document.getElementById("tele-cmd-omega"),

    // HSV sliders
    hMin: document.getElementById("h_min"),  hMinVal: document.getElementById("h_min_val"),
    hMax: document.getElementById("h_max"),  hMaxVal: document.getElementById("h_max_val"),
    sMin: document.getElementById("s_min"),  sMinVal: document.getElementById("s_min_val"),
    sMax: document.getElementById("s_max"),  sMaxVal: document.getElementById("s_max_val"),
    vMin: document.getElementById("v_min"),  vMinVal: document.getElementById("v_min_val"),
    vMax: document.getElementById("v_max"),  vMaxVal: document.getElementById("v_max_val"),
    btnHsvReset: document.getElementById("btn-hsv-reset"),

    // Logging
    btnLogToggle: document.getElementById("btn-log-toggle"),
    btnLogText:   document.getElementById("btn-log-text"),
    recDot:       document.getElementById("rec-dot"),
    logFilename:  document.getElementById("log-filename"),
    logEntries:   document.getElementById("log-entries"),
    logElapsed:   document.getElementById("log-elapsed"),

    // Servo
    btnServoOpen:  document.getElementById("btn-servo-open"),
    btnServoClose: document.getElementById("btn-servo-close"),

    // Toast
    toastContainer: document.getElementById("toast-container"),
};

// ═══════════════════════════════════════════════════════════════
// State lokal
// ═══════════════════════════════════════════════════════════════
let isAutoMode = false;
let isRecording = false;
let keysPressed = new Set();  // Track tombol yang sedang ditekan

// ═══════════════════════════════════════════════════════════════
// Toast Notification
// ═══════════════════════════════════════════════════════════════
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    el.toastContainer.appendChild(toast);

    // Hapus setelah animasi selesai (3.3 detik)
    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 3500);
}

// ═══════════════════════════════════════════════════════════════
// SocketIO Events — Terima data dari server
// ═══════════════════════════════════════════════════════════════

socket.on("connect", () => {
    showToast("Terhubung ke ground station", "success");
});

socket.on("disconnect", () => {
    showToast("Koneksi ke server terputus!", "error");
    updateConnectionUI(false);
});

// State awal saat pertama kali connect
socket.on("init_state", (data) => {
    // Sinkronisasi HSV sliders
    if (data.hsv) {
        setSliderValues(data.hsv);
    }
    // Sinkronisasi mode
    isAutoMode = data.auto_mode || false;
    updateModeUI();
    // Sinkronisasi koneksi
    if (data.comms) {
        updateConnectionUI(data.comms.connected, data.comms.demo_mode);
    }
});

// Telemetri berkala dari background thread
socket.on("telemetry", (data) => {
    // FPS
    el.fpsVal.textContent = data.fps || 0;
    el.teleFps.textContent = data.fps || 0;
    el.teleStreamFps.textContent = data.stream_fps || 0;

    // State
    updateStateBadge(data.state);
    el.brainState.textContent = data.state;
    el.stateDuration.textContent = (data.state_duration || 0).toFixed(1) + "s";
    el.ballsCollected.textContent = data.balls_collected || 0;

    // Deteksi bola
    if (data.detected) {
        el.teleDetected.textContent = "✓ Ya";
        el.teleDetected.style.color = "var(--accent-green)";
        el.teleBallX.textContent = data.ball_x;
        el.teleBallY.textContent = data.ball_y;
        el.teleBallArea.textContent = data.ball_area;
        el.teleOffsetX.textContent = data.offset_x;
        el.teleOffsetY.textContent = data.offset_y;
        el.detectionText.textContent = `Bola: (${data.ball_x}, ${data.ball_y}) Area: ${data.ball_area}`;
        el.cardDetection.classList.add("detected");
    } else {
        el.teleDetected.textContent = "✗ Tidak";
        el.teleDetected.style.color = "var(--text-muted)";
        el.teleBallX.textContent = "—";
        el.teleBallY.textContent = "—";
        el.teleBallArea.textContent = "—";
        el.teleOffsetX.textContent = "—";
        el.teleOffsetY.textContent = "—";
        el.detectionText.textContent = "Tidak ada deteksi";
        el.cardDetection.classList.remove("detected");
    }

    // Perintah motor
    el.teleCmdVx.textContent = data.cmd_vx || 0;
    el.teleCmdVy.textContent = data.cmd_vy || 0;
    el.teleCmdOmega.textContent = data.cmd_omega || 0;

    // Koneksi
    updateConnectionUI(data.connected, data.demo_mode);

    // Mode
    isAutoMode = data.auto_mode;
    updateModeUI();

    // Logging
    if (data.logging) {
        updateLoggingUI(data.logging);
    }
});

// Hasil koneksi
socket.on("connection_result", (data) => {
    if (data.success) {
        showToast("Berhasil terhubung ke robot!", "success");
    } else {
        showToast("Gagal terhubung: " + (data.status?.last_error || "unknown"), "error");
    }
    updateConnectionUI(data.status?.connected, data.status?.demo_mode);
});

// HSV updated confirmation
socket.on("hsv_updated", (data) => {
    setSliderValues(data);
});

// Mode changed
socket.on("mode_changed", (data) => {
    isAutoMode = data.auto_mode;
    updateModeUI();
    showToast(`Mode: ${isAutoMode ? "Otomatis" : "Manual"}`, "info");
});

// Logging status
socket.on("logging_status", (data) => {
    updateLoggingUI(data);
    if (data.active) {
        showToast("Recording dimulai: " + data.filename, "success");
    } else {
        showToast("Recording dihentikan", "warning");
    }
});

// Servo result
socket.on("servo_result", (data) => {
    showToast(`Servo: ${data.cmd.toUpperCase()} (${data.angle}°)`, "info");
});

// ═══════════════════════════════════════════════════════════════
// UI Update Functions
// ═══════════════════════════════════════════════════════════════

function updateStateBadge(state) {
    const badge = el.stateBadge;
    badge.textContent = state;

    // Hapus semua class state sebelumnya
    badge.className = "video-overlay state-badge";
    el.videoWrapper.className = "video-wrapper";

    // Tambah class baru berdasarkan state
    const stateClass = `state-${state.toLowerCase()}`;
    badge.classList.add(stateClass);
    el.videoWrapper.classList.add(stateClass);
}

function updateConnectionUI(connected, demoMode) {
    if (connected) {
        el.connDot.classList.add("connected");
        el.connLabel.textContent = "Terhubung";
        el.connDetail.textContent = demoMode ? "Webcam (Demo)" : `ESP32 @ ${el.espIp.value}`;
        el.connDetail.style.color = "var(--accent-green)";
        el.connMode.textContent = demoMode ? "Demo" : "ESP32-CAM";
    } else {
        el.connDot.classList.remove("connected");
        el.connLabel.textContent = "Terputus";
        el.connDetail.textContent = "Belum terhubung";
        el.connDetail.style.color = "var(--accent-coral)";
        el.connMode.textContent = "—";
    }
}

function updateModeUI() {
    if (isAutoMode) {
        el.btnAuto.classList.add("active");
        el.btnManual.classList.remove("active");
    } else {
        el.btnManual.classList.add("active");
        el.btnAuto.classList.remove("active");
    }
}

function updateLoggingUI(logInfo) {
    isRecording = logInfo.active;
    if (isRecording) {
        el.btnLogText.textContent = "Stop Recording";
        el.recDot.classList.add("active");
        el.btnLogToggle.classList.add("recording");
        el.logFilename.textContent = logInfo.filename || "—";
        el.logEntries.textContent = logInfo.entry_count || 0;
        el.logElapsed.textContent = (logInfo.elapsed || 0).toFixed(0) + "s";
    } else {
        el.btnLogText.textContent = "Mulai Recording";
        el.recDot.classList.remove("active");
        el.btnLogToggle.classList.remove("recording");
    }
}

function setSliderValues(hsv) {
    el.hMin.value = hsv.h_min; el.hMinVal.textContent = hsv.h_min;
    el.hMax.value = hsv.h_max; el.hMaxVal.textContent = hsv.h_max;
    el.sMin.value = hsv.s_min; el.sMinVal.textContent = hsv.s_min;
    el.sMax.value = hsv.s_max; el.sMaxVal.textContent = hsv.s_max;
    el.vMin.value = hsv.v_min; el.vMinVal.textContent = hsv.v_min;
    el.vMax.value = hsv.v_max; el.vMaxVal.textContent = hsv.v_max;
}

// ═══════════════════════════════════════════════════════════════
// Event Handlers — Tombol UI
// ═══════════════════════════════════════════════════════════════

// Koneksi
el.btnConnect.addEventListener("click", () => {
    const ip = el.espIp.value.trim();
    socket.emit("connect_robot", { ip: ip });
    showToast("Menghubungkan ke " + ip + "...", "info");
});

// Mode toggle
el.btnManual.addEventListener("click", () => {
    socket.emit("toggle_mode", { mode: "manual" });
});

el.btnAuto.addEventListener("click", () => {
    socket.emit("toggle_mode", { mode: "auto" });
});

// Kontrol manual — tombol arah
function sendManualCmd(vx, vy, omega) {
    if (isAutoMode) return;  // Abaikan di auto-mode
    socket.emit("manual_control", { vx, vy, omega });
}

document.getElementById("btn-fwd").addEventListener("mousedown", () => sendManualCmd(MANUAL_SPEED, 0, 0));
document.getElementById("btn-bwd").addEventListener("mousedown", () => sendManualCmd(-MANUAL_SPEED, 0, 0));
document.getElementById("btn-ccw").addEventListener("mousedown", () => sendManualCmd(0, 0, -MANUAL_TURN));
document.getElementById("btn-cw").addEventListener("mousedown",  () => sendManualCmd(0, 0, MANUAL_TURN));
document.getElementById("btn-stop").addEventListener("click",    () => sendManualCmd(0, 0, 0));

// Mouse up → stop motor (untuk tombol arah)
["btn-fwd", "btn-bwd", "btn-ccw", "btn-cw"].forEach(id => {
    const btn = document.getElementById(id);
    btn.addEventListener("mouseup",    () => sendManualCmd(0, 0, 0));
    btn.addEventListener("mouseleave", () => sendManualCmd(0, 0, 0));
});

// Servo
el.btnServoOpen.addEventListener("click", () => {
    socket.emit("servo_cmd", { cmd: "open" });
});

el.btnServoClose.addEventListener("click", () => {
    socket.emit("servo_cmd", { cmd: "close" });
});

// Logging
el.btnLogToggle.addEventListener("click", () => {
    socket.emit("toggle_logging", {
        action: isRecording ? "stop" : "start"
    });
});

// ═══════════════════════════════════════════════════════════════
// HSV Sliders — emit perubahan ke server
// ═══════════════════════════════════════════════════════════════
const hsvSliders = ["h_min", "h_max", "s_min", "s_max", "v_min", "v_max"];

hsvSliders.forEach(name => {
    const slider = document.getElementById(name);
    const valDisplay = document.getElementById(name + "_val");

    slider.addEventListener("input", () => {
        valDisplay.textContent = slider.value;

        // Kirim semua nilai HSV saat ini
        socket.emit("update_hsv", {
            h_min: parseInt(el.hMin.value),
            h_max: parseInt(el.hMax.value),
            s_min: parseInt(el.sMin.value),
            s_max: parseInt(el.sMax.value),
            v_min: parseInt(el.vMin.value),
            v_max: parseInt(el.vMax.value),
        });
    });
});

// Reset HSV ke default
el.btnHsvReset.addEventListener("click", () => {
    const defaults = { h_min: 5, h_max: 25, s_min: 100, s_max: 255, v_min: 100, v_max: 255 };
    socket.emit("update_hsv", defaults);
    setSliderValues(defaults);
    showToast("HSV direset ke default", "info");
});

// ═══════════════════════════════════════════════════════════════
// Keyboard Controls
// ═══════════════════════════════════════════════════════════════
document.addEventListener("keydown", (e) => {
    // Cegah double-trigger
    if (keysPressed.has(e.key.toLowerCase())) return;
    keysPressed.add(e.key.toLowerCase());

    // Jangan proses jika sedang mengetik di input
    if (e.target.tagName === "INPUT") return;

    const key = e.key.toLowerCase();

    switch (key) {
        case "w":
            sendManualCmd(MANUAL_SPEED, 0, 0);
            highlightButton("btn-fwd");
            break;
        case "s":
            sendManualCmd(-MANUAL_SPEED, 0, 0);
            highlightButton("btn-bwd");
            break;
        case "a":
            sendManualCmd(0, 0, -MANUAL_TURN);
            highlightButton("btn-ccw");
            break;
        case "d":
            sendManualCmd(0, 0, MANUAL_TURN);
            highlightButton("btn-cw");
            break;
        case "q":
            sendManualCmd(0, 0, -MANUAL_TURN);
            highlightButton("btn-ccw");
            break;
        case "e":
            sendManualCmd(0, 0, MANUAL_TURN);
            highlightButton("btn-cw");
            break;
        case " ":
            e.preventDefault();
            sendManualCmd(0, 0, 0);
            highlightButton("btn-stop");
            break;
        case "t":
            // Toggle mode auto/manual
            socket.emit("toggle_mode", { mode: isAutoMode ? "manual" : "auto" });
            break;
    }
});

document.addEventListener("keyup", (e) => {
    keysPressed.delete(e.key.toLowerCase());

    if (e.target.tagName === "INPUT") return;

    const key = e.key.toLowerCase();
    const moveKeys = ["w", "a", "s", "d", "q", "e"];

    if (moveKeys.includes(key)) {
        sendManualCmd(0, 0, 0);
        unhighlightAllButtons();
    }
    if (key === " ") {
        unhighlightAllButtons();
    }
});

// Highlight efek visual pada tombol saat keyboard ditekan
function highlightButton(id) {
    unhighlightAllButtons();
    const btn = document.getElementById(id);
    if (btn) btn.classList.add("pressed");
}

function unhighlightAllButtons() {
    ["btn-fwd", "btn-bwd", "btn-ccw", "btn-cw", "btn-stop"].forEach(id => {
        document.getElementById(id)?.classList.remove("pressed");
    });
}

// ═══════════════════════════════════════════════════════════════
// Inisialisasi
// ═══════════════════════════════════════════════════════════════
console.log("[Ground Station] Frontend initialized — menunggu koneksi SocketIO...");
