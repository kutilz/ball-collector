/**
 * app.js — Frontend ground station robot pengumpul bola.
 *
 * Fitur:
 *   • SocketIO telemetri real-time
 *   • Tab UI (Kontrol / Kalibrasi / Sensor)
 *   • Pemilih sumber video (ESP32 / Webcam / Video file) + upload
 *   • Toggle "kemudikan robot asli"
 *   • Kontrol mecanum (maju/mundur/strafe/diagonal/rotasi) + keyboard
 *   • Slider kalibrasi komponen (di-generate dari spec backend)
 *   • Visualizer sensor: kompas IMU, baterai, sinyal, roda mecanum, radar bola
 */

const socket = io();

// ═══════════════════════════════════════════════════════════════
// State lokal
// ═══════════════════════════════════════════════════════════════
let isAutoMode = false;
let isRecording = false;
let selectedSource = "webcam";
let driveRobot = false;
let manualSpeed = 80;   // disinkron dari kalibrasi MANUAL_SPEED
let manualTurn = 70;    // disinkron dari kalibrasi MANUAL_TURN
let frameW = 640, frameH = 480;
let keysPressed = new Set();

// Kelompok kalibrasi → urutan key di tiap kartu
const CALIB_GROUPS = {
    vision: ["MIN_CONTOUR_AREA", "ERODE_ITER", "DILATE_ITER", "YOLO_CONF"],
    fsm:    ["AREA_APPROACH", "AREA_COLLECT", "CENTER_TOLERANCE"],
    motor:  ["SEARCH_SPEED", "APPROACH_SPEED", "MANUAL_SPEED", "MANUAL_TURN", "KP_STEERING",
             "SAFETY_MAX_PWM", "MOTION_HEARTBEAT"],
    servo:  ["SERVO_OPEN", "SERVO_CLOSE", "SWEEP_DELAY"],
};
const FLOAT_KEYS = new Set(["KP_STEERING", "SWEEP_DELAY", "MOTION_HEARTBEAT", "YOLO_CONF"]);

// ═══════════════════════════════════════════════════════════════
// Referensi DOM
// ═══════════════════════════════════════════════════════════════
const $ = (id) => document.getElementById(id);
const el = {
    // Header pills
    connDot: $("conn-dot"), connLabel: $("conn-label"),
    robotDot: $("robot-dot"), robotLabel: $("robot-label"), robotPill: $("robot-pill"),
    sourceLabel: $("source-label"),
    // Sumber & koneksi
    espIp: $("esp32-ip"), btnConnect: $("btn-connect"), ipGroup: $("ip-group"),
    webcamGroup: $("webcam-group"), webcamIndex: $("webcam-index"),
    btnWebcamApply: $("btn-webcam-apply"), btnScanCam: $("btn-scan-cam"), webcamHint: $("webcam-hint"),
    connDetail: $("conn-detail"), robotDetail: $("robot-detail"),
    videoUpload: $("video-upload"), videoFileInput: $("video-file-input"),
    btnUploadVideo: $("btn-upload-video"), uploadLabel: $("upload-label"),
    driveToggle: $("drive-toggle"), driveRow: $("drive-toggle-row"),
    // Mode
    btnManual: $("btn-manual"), btnAuto: $("btn-auto"),
    brainState: $("brain-state"), stateDuration: $("state-duration"),
    ballsCollected: $("balls-collected"),
    // Video overlay + quickstats
    fpsVal: $("fps-val"), stateBadge: $("state-badge"), sourceBadge: $("source-badge"),
    detectionText: $("detection-text"), videoWrapper: document.querySelector(".video-wrapper"),
    qsState: $("qs-state"), qsBalls: $("qs-balls"), qsHeading: $("qs-heading"),
    qsFps: $("qs-fps"), qsVbat: $("qs-vbat"),
    // Deteksi / radar
    teleDetected: $("tele-detected"), teleBallX: $("tele-ball-x"), teleBallY: $("tele-ball-y"),
    teleBallArea: $("tele-ball-area"), teleOffsetX: $("tele-offset-x"), teleOffsetY: $("tele-offset-y"),
    radarBall: $("radar-ball"), radarVec: $("radar-vec"),
    // Telemetri sistem
    teleFps: $("tele-fps"), teleStreamFps: $("tele-stream-fps"),
    // Sensor: IMU
    compassNeedle: $("compass-needle"), compassTicks: $("compass-ticks"),
    imuHeading: $("imu-heading"), imuDir: $("imu-dir"),
    // Sensor: daya
    battFill: $("batt-fill"), battVolt: $("batt-volt"), battPct: $("batt-pct"),
    signalBars: $("signal-bars"), rssiVal: $("rssi-val"),
    // Sensor: mecanum
    driveVec: $("drive-vec"), rotArc: $("rot-arc"),
    cmdVx: $("cmd-vx"), cmdVy: $("cmd-vy"), cmdOmega: $("cmd-omega"),
    // Detektor bola (HSV vs AI/YOLO)
    detectorSeg: $("detector-seg"), detectorStatus: $("detector-status"),
    // HSV
    hMin: $("h_min"), hMax: $("h_max"), sMin: $("s_min"), sMax: $("s_max"), vMin: $("v_min"), vMax: $("v_max"),
    btnHsvReset: $("btn-hsv-reset"),
    // Logging
    btnLogToggle: $("btn-log-toggle"), btnLogText: $("btn-log-text"), recDot: $("rec-dot"),
    logFilename: $("log-filename"), logEntries: $("log-entries"), logElapsed: $("log-elapsed"),
    // Servo
    btnServoOpen: $("btn-servo-open"), btnServoClose: $("btn-servo-close"), btnServoCollect: $("btn-servo-collect"),
    // Kalibrasi
    btnCalibReset: $("btn-calib-reset"),
    // Toast
    toastContainer: $("toast-container"),
};

let hsvDefaults = { h_min: 5, h_max: 25, s_min: 100, s_max: 255, v_min: 100, v_max: 255 };

// ═══════════════════════════════════════════════════════════════
// Toast
// ═══════════════════════════════════════════════════════════════
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    el.toastContainer.appendChild(toast);
    setTimeout(() => { if (toast.parentElement) toast.remove(); }, 3500);
}

// ── Flash visual feedback pada elemen (ok/warn/err/info) ─────────
function flash(elem, kind = "info") {
    if (!elem) return;
    elem.classList.remove("flash-ok", "flash-warn", "flash-err", "flash-info");
    void elem.offsetWidth;                 // retrigger animasi
    elem.classList.add("flash-" + kind);
    setTimeout(() => elem.classList.remove("flash-" + kind), 600);
}

// Feedback universal: SETIAP tombol yang diklik berkedip — bukti "terklik".
document.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn, .tab-btn, .seg-btn, .switch");
    if (btn) flash(btn, "info");
}, true);

// Status perintah terakhir (baris feedback di kartu Kontrol Manual)
function setCmdStatus(status, action, detail) {
    const elc = document.getElementById("cmd-status");
    const txt = document.getElementById("cmd-status-text");
    if (!elc || !txt) return;
    const map = { ok: "ok", skipped: "warn", ignored: "warn", error: "err" };
    const kind = map[status] || "info";
    elc.className = "cmd-status cs-" + kind;
    txt.textContent = (action ? action + " — " : "") + (detail || status);
}

// ═══════════════════════════════════════════════════════════════
// TAB switching
// ═══════════════════════════════════════════════════════════════
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b === btn));
        document.querySelectorAll(".tab-content").forEach(c =>
            c.classList.toggle("active", c.id === "tab-" + tab));
    });
});

// ═══════════════════════════════════════════════════════════════
// SocketIO — terima data
// ═══════════════════════════════════════════════════════════════
socket.on("connect", () => showToast("Terhubung ke ground station", "success"));
socket.on("disconnect", () => {
    showToast("Koneksi ke server terputus!", "error");
    updateConnectionUI(false);
});

socket.on("init_state", (data) => {
    if (data.hsv) setSliderValues(data.hsv);
    if (data.hsv_defaults) hsvDefaults = data.hsv_defaults;
    if (data.detector) applyDetectorState(data.detector);
    isAutoMode = data.auto_mode || false;
    updateModeUI();
    if (data.comms) {
        applySourceState(data.comms);
        updateConnectionUI(data.comms.connected, data.comms);
    }
    if (data.calibration_spec) buildCalibration(data.calibration_spec, data.calibration || {});
    if (data.calibration) syncManualFromCalib(data.calibration);
});

socket.on("telemetry", (data) => {
    frameW = data.frame_w || frameW;
    frameH = data.frame_h || frameH;

    // Overlay + quickstats
    el.fpsVal.textContent = data.fps || 0;
    el.teleFps.textContent = data.fps || 0;
    el.teleStreamFps.textContent = data.stream_fps || 0;
    el.qsFps.textContent = data.fps || 0;
    el.qsBalls.textContent = data.balls_collected || 0;

    updateStateBadge(data.state);
    el.brainState.textContent = data.state;
    el.qsState.textContent = data.state;
    el.stateDuration.textContent = (data.state_duration || 0).toFixed(1) + "s";
    el.ballsCollected.textContent = data.balls_collected || 0;

    // Deteksi bola
    updateDetection(data);

    // Command + roda mecanum
    const vx = data.cmd_vx || 0, vy = data.cmd_vy || 0, omega = data.cmd_omega || 0;
    el.cmdVx.textContent = vx; el.cmdVy.textContent = vy; el.cmdOmega.textContent = omega;
    updateMecanum(vx, vy, omega);

    // Sensor IMU + daya
    updateCompass(data.heading || 0);
    updatePower(data.vbat || 0, data.rssi || 0);

    // Koneksi + mode
    updateConnectionUI(data.connected, data);
    updateRobotPill(data.drive_robot, data.robot_online);
    isAutoMode = data.auto_mode;
    updateModeUI();

    if (data.logging) updateLoggingUI(data.logging);
});

socket.on("connection_result", (data) => {
    if (data.success) showToast("Sumber video aktif", "success");
    else showToast("Gagal: " + (data.status?.last_error || "tidak diketahui"), "error");
    if (data.status) {
        applySourceState(data.status);
        updateConnectionUI(data.status.connected, data.status);
    }
});

socket.on("drive_status", (status) => {
    driveRobot = status.drive_robot;
    el.driveToggle.checked = driveRobot;
    el.driveRow.classList.toggle("armed", driveRobot);
    updateRobotPill(status.drive_robot, status.robot_online);
    showToast(driveRobot ? "Robot asli AKTIF dikemudikan" : "Kemudi robot dimatikan",
        driveRobot ? "warning" : "info");
});

socket.on("hsv_updated", (data) => setSliderValues(data));

// Hasil pengalihan backend detektor (broadcast ke semua client).
socket.on("detector_state", (data) => {
    applyDetectorState(data.info);
    if (data.ok) {
        showToast(data.info.backend === "yolo"
            ? "Detektor AI (YOLO) aktif" : "Detektor HSV aktif", "success");
    } else {
        showToast(data.error || "Gagal mengaktifkan detektor AI", "error");
    }
});

socket.on("mode_changed", (data) => {
    isAutoMode = data.auto_mode;
    updateModeUI();
    showToast(`Mode: ${isAutoMode ? "Otomatis" : "Manual"}`, "info");
});

socket.on("logging_status", (data) => {
    updateLoggingUI(data);
    showToast(data.active ? "Recording dimulai: " + data.filename : "Recording dihentikan",
        data.active ? "success" : "warning");
});

socket.on("servo_result", (data) => showToast(`Servo: ${data.cmd.toUpperCase()} (${data.angle}°)`, "info"));

// Feedback per-perintah: berhasil terkirim / diabaikan / gagal
socket.on("cmd_ack", (data) => {
    setCmdStatus(data.status, data.action, data.detail);
    const kind = data.status === "ok" ? "ok" : data.status === "error" ? "err" : "warn";
    // Flash tombol kontrol yg memicu (selain saat berhenti)
    if (lastCmdBtn && data.action !== "BERHENTI") flash(document.getElementById(lastCmdBtn), kind);
    // Toast hanya untuk kondisi yang perlu perhatian (gagal / diabaikan)
    if (data.status === "error") showToast(`${data.action}: ${data.detail}`, "error");
    else if (data.status === "skipped" && data.action !== "BERHENTI")
        showToast(`${data.action}: tidak terkirim — robot tidak dikemudikan`, "warning");
});

socket.on("calibration_updated", (data) => {
    const row = document.querySelector(`.calib-row[data-key="${data.key}"]`);
    if (row) {
        const inp = row.querySelector("input");
        const val = row.querySelector(".calib-val");
        if (inp && document.activeElement !== inp) inp.value = data.value;
        if (val) val.textContent = fmtCalib(data.key, data.value);
    }
    if (data.key === "MANUAL_SPEED") manualSpeed = data.value;
    if (data.key === "MANUAL_TURN") manualTurn = data.value;
});

socket.on("calibration_state", (state) => {
    Object.entries(state).forEach(([key, value]) => {
        const row = document.querySelector(`.calib-row[data-key="${key}"]`);
        if (row) {
            row.querySelector("input").value = value;
            row.querySelector(".calib-val").textContent = fmtCalib(key, value);
        }
    });
    syncManualFromCalib(state);
    showToast("Kalibrasi direset ke default", "info");
});

// ═══════════════════════════════════════════════════════════════
// UI updates
// ═══════════════════════════════════════════════════════════════
function updateStateBadge(state) {
    el.stateBadge.textContent = state;
    el.stateBadge.className = "video-overlay state-badge state-" + state.toLowerCase();
    el.videoWrapper.className = "video-wrapper state-" + state.toLowerCase();
}

function updateDetection(data) {
    if (data.detected) {
        el.teleDetected.textContent = "✓ Ya";
        el.teleDetected.style.color = "var(--accent-green)";
        el.teleBallX.textContent = data.ball_x;
        el.teleBallY.textContent = data.ball_y;
        el.teleBallArea.textContent = data.ball_area;
        el.teleOffsetX.textContent = data.offset_x;
        el.teleOffsetY.textContent = data.offset_y;
        el.detectionText.textContent = `Bola (${data.ball_x}, ${data.ball_y}) · Area ${data.ball_area}`;
    } else {
        el.teleDetected.textContent = "✗ Tidak";
        el.teleDetected.style.color = "var(--text-muted)";
        el.teleBallX.textContent = el.teleBallY.textContent = "—";
        el.teleBallArea.textContent = el.teleOffsetX.textContent = el.teleOffsetY.textContent = "—";
        el.detectionText.textContent = "Tidak ada deteksi";
    }
    updateRadar(data);
}

function updateConnectionUI(connected, status) {
    if (connected) {
        el.connDot.classList.add("connected");
        el.connLabel.textContent = "Terhubung";
        const srcName = sourceName(status?.source || selectedSource);
        el.connDetail.textContent = srcName;
        el.connDetail.style.color = "var(--accent-green)";
    } else {
        el.connDot.classList.remove("connected");
        el.connLabel.textContent = "Terputus";
        el.connDetail.textContent = "Tidak ada sumber";
        el.connDetail.style.color = "var(--accent-coral)";
    }
}

function updateRobotPill(drive, online) {
    el.robotPill.classList.toggle("active", !!drive);
    if (!drive) {
        el.robotDot.classList.remove("online");
        el.robotLabel.textContent = "Robot Off";
        el.robotDetail.textContent = "Tidak dikemudikan";
        el.robotDetail.style.color = "var(--text-secondary)";
        return;
    }
    el.robotDot.classList.toggle("online", !!online);
    el.robotLabel.textContent = online ? "Robot Online" : "Robot ...";
    el.robotDetail.textContent = online ? `Terhubung @ ${el.espIp.value}` : "Mencari ESP32…";
    el.robotDetail.style.color = online ? "var(--accent-green)" : "var(--accent-amber)";
}

function sourceName(src) {
    return src === "esp32" ? `ESP32-CAM @ ${el.espIp.value}`
        : src === "video" ? "File Video" : "Webcam Laptop";
}

function applySourceState(status) {
    if (status.source) {
        selectedSource = status.source;
        document.querySelectorAll(".seg-btn").forEach(b =>
            b.classList.toggle("active", b.dataset.source === status.source));
        el.sourceLabel.textContent = status.source === "esp32" ? "ESP32-CAM"
            : status.source === "video" ? "Video" : "Webcam";
        el.sourceBadge.textContent = (status.source || "webcam").toUpperCase();
        updateSourceGroups(status.source);
    }
    if (typeof status.webcam_index === "number" && el.webcamIndex
            && document.activeElement !== el.webcamIndex) {
        el.webcamIndex.value = status.webcam_index;
    }
    if (typeof status.drive_robot === "boolean") {
        driveRobot = status.drive_robot;
        el.driveToggle.checked = driveRobot;
        el.driveRow.classList.toggle("armed", driveRobot);
    }
    if (status.robot_ip && el.espIp.value === "192.168.4.1") el.espIp.value = status.robot_ip;
}

function updateModeUI() {
    el.btnAuto.classList.toggle("active", isAutoMode);
    el.btnManual.classList.toggle("active", !isAutoMode);
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
    [["h_min", hsv.h_min], ["h_max", hsv.h_max], ["s_min", hsv.s_min],
     ["s_max", hsv.s_max], ["v_min", hsv.v_min], ["v_max", hsv.v_max]].forEach(([id, v]) => {
        $(id).value = v; $(id + "_val").textContent = v;
    });
}

// ═══════════════════════════════════════════════════════════════
// DETEKTOR BOLA — pilih backend HSV vs AI (YOLO)
// ═══════════════════════════════════════════════════════════════
// Sorot tombol segmented sesuai backend aktif.
function highlightDetector(backend) {
    if (!el.detectorSeg) return;
    el.detectorSeg.querySelectorAll(".seg-btn").forEach(b =>
        b.classList.toggle("active", b.dataset.detector === backend));
}

// Terapkan info backend dari server ke UI (tombol + baris status).
// info: {backend, yolo_ready, yolo_model, yolo_error}
function applyDetectorState(info) {
    if (!info) return;
    highlightDetector(info.backend);
    const st = el.detectorStatus;
    if (!st) return;
    st.classList.remove("is-error", "is-ai");
    if (info.yolo_error) {
        st.textContent = "AI tidak tersedia: " + info.yolo_error;
        st.classList.add("is-error");
    } else if (info.backend === "yolo") {
        st.textContent = `Mode AI aktif — model ${info.yolo_model || "YOLO"}. `
            + `Atur ambang di slider "Confidence AI".`;
        st.classList.add("is-ai");
    } else {
        st.textContent = "Mode warna HSV aktif — atur rentang warna di bawah.";
    }
}

// ═══════════════════════════════════════════════════════════════
// SENSOR VISUALIZERS
// ═══════════════════════════════════════════════════════════════
// Kompas — generate ticks sekali
(function initCompassTicks() {
    if (!el.compassTicks) return;
    let ticks = "";
    for (let i = 0; i < 12; i++) {
        const ang = i * 30 * Math.PI / 180;
        const r1 = 50, r2 = (i % 3 === 0) ? 44 : 47;
        const x1 = 60 + r1 * Math.sin(ang), y1 = 60 - r1 * Math.cos(ang);
        const x2 = 60 + r2 * Math.sin(ang), y2 = 60 - r2 * Math.cos(ang);
        ticks += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}"/>`;
    }
    el.compassTicks.innerHTML = ticks;
})();

const DIR_NAMES = ["Utara", "Timur Laut", "Timur", "Tenggara", "Selatan", "Barat Daya", "Barat", "Barat Laut"];
function updateCompass(heading) {
    el.compassNeedle.style.transform = `rotate(${heading}deg)`;
    el.imuHeading.textContent = heading.toFixed(1) + "°";
    el.qsHeading.textContent = Math.round(heading) + "°";
    let h = ((heading % 360) + 360) % 360;
    el.imuDir.textContent = DIR_NAMES[Math.round(h / 45) % 8];
}

function updatePower(vbat, rssi) {
    // Baterai 2S LiPo: 6.0V (0%) → 8.4V (100%)
    if (vbat > 0) {
        const pct = Math.max(0, Math.min(100, ((vbat - 6.0) / (8.4 - 6.0)) * 100));
        el.battFill.style.width = pct + "%";
        el.battFill.className = "batt-fill" + (pct < 15 ? " critical" : pct < 30 ? " low" : "");
        el.battVolt.textContent = vbat.toFixed(2) + " V";
        el.battPct.textContent = Math.round(pct) + "% · 2S";
        el.qsVbat.textContent = vbat.toFixed(1) + "V";
    } else {
        el.battFill.style.width = "0%";
        el.battVolt.textContent = "-- V";
        el.battPct.textContent = "Sensor belum aktif";
        el.qsVbat.textContent = "--";
    }
    // RSSI → bar
    const bars = rssi === 0 ? 0 : rssi > -60 ? 4 : rssi > -70 ? 3 : rssi > -80 ? 2 : 1;
    el.signalBars.querySelectorAll("span").forEach((s, i) => s.classList.toggle("lit", i < bars));
    el.rssiVal.textContent = rssi === 0 ? "-- dBm" : rssi + " dBm";
}

function updateMecanum(vx, vy, omega) {
    // Kinematik mecanum (sama dgn firmware Arduino)
    let fl = vx + vy + omega, fr = vx - vy - omega, rl = vx - vy + omega, rr = vx + vy - omega;
    const mx = Math.max(Math.abs(fl), Math.abs(fr), Math.abs(rl), Math.abs(rr), 255);
    if (mx > 255) { fl = fl * 255 / mx; fr = fr * 255 / mx; rl = rl * 255 / mx; rr = rr * 255 / mx; }
    setWheel("wheel-fl", "wt-fl", fl);
    setWheel("wheel-fr", "wt-fr", fr);
    setWheel("wheel-rl", "wt-rl", rl);
    setWheel("wheel-rr", "wt-rr", rr);

    // Vektor translasi: vx=maju(atas), vy=kanan
    const k = 38 / 255;
    el.driveVec.setAttribute("x2", (100 + vy * k).toFixed(1));
    el.driveVec.setAttribute("y2", (80 - vx * k).toFixed(1));

    // Busur rotasi
    if (Math.abs(omega) < 3) {
        el.rotArc.setAttribute("d", "");
    } else {
        const sweep = Math.min(150, Math.abs(omega) / 255 * 150);
        const dir = omega > 0 ? 1 : -1;
        el.rotArc.setAttribute("d", arcPath(100, 80, 30, -90, -90 + sweep * dir));
    }
}

function setWheel(wheelId, textId, val) {
    const g = $(wheelId);
    const fill = g.querySelector(".wfill");
    g.classList.remove("fwd", "rev");
    g.classList.add(val >= 0 ? "fwd" : "rev");
    fill.style.opacity = Math.min(1, Math.abs(val) / 255).toFixed(2);
    $(textId).textContent = Math.round(val);
}

function arcPath(cx, cy, r, a0, a1) {
    const rad = (a) => a * Math.PI / 180;
    const x0 = cx + r * Math.cos(rad(a0)), y0 = cy + r * Math.sin(rad(a0));
    const x1 = cx + r * Math.cos(rad(a1)), y1 = cy + r * Math.sin(rad(a1));
    const large = Math.abs(a1 - a0) > 180 ? 1 : 0;
    const sweep = a1 > a0 ? 1 : 0;
    return `M ${x0.toFixed(1)} ${y0.toFixed(1)} A ${r} ${r} 0 ${large} ${sweep} ${x1.toFixed(1)} ${y1.toFixed(1)}`;
}

function updateRadar(data) {
    if (data.detected) {
        const x = 2 + (data.ball_x / frameW) * 196;
        const y = 2 + (data.ball_y / frameH) * 146;
        const r = Math.max(4, Math.min(16, Math.sqrt(data.ball_area || 0) / 6));
        el.radarBall.setAttribute("cx", x.toFixed(1));
        el.radarBall.setAttribute("cy", y.toFixed(1));
        el.radarBall.setAttribute("r", r.toFixed(1));
        el.radarVec.setAttribute("x2", x.toFixed(1));
        el.radarVec.setAttribute("y2", y.toFixed(1));
        el.radarVec.style.opacity = "0.8";
    } else {
        el.radarBall.setAttribute("r", "0");
        el.radarVec.style.opacity = "0";
    }
}

// ═══════════════════════════════════════════════════════════════
// KALIBRASI — generate slider dari spec
// ═══════════════════════════════════════════════════════════════
function fmtCalib(key, value) {
    return FLOAT_KEYS.has(key) ? Number(value).toFixed(2) : Math.round(value);
}

function buildCalibration(spec, values) {
    Object.entries(CALIB_GROUPS).forEach(([group, keys]) => {
        const container = document.querySelector(`.calib-group[data-group="${group}"]`);
        if (!container) return;
        container.innerHTML = "";
        keys.forEach(key => {
            if (!spec[key]) return;
            const [min, max, step, label] = spec[key];
            const val = (key in values) ? values[key] : min;
            const row = document.createElement("div");
            row.className = "calib-row";
            row.dataset.key = key;
            row.innerHTML = `
                <span class="calib-label">${label}</span>
                <span class="calib-val">${fmtCalib(key, val)}</span>
                <input type="range" min="${min}" max="${max}" step="${step}" value="${val}">`;
            const input = row.querySelector("input");
            const valEl = row.querySelector(".calib-val");
            input.addEventListener("input", () => {
                valEl.textContent = fmtCalib(key, input.value);
                socket.emit("update_calibration", { key, value: parseFloat(input.value) });
            });
            container.appendChild(row);
        });
    });
}

function syncManualFromCalib(values) {
    if ("MANUAL_SPEED" in values) manualSpeed = values.MANUAL_SPEED;
    if ("MANUAL_TURN" in values) manualTurn = values.MANUAL_TURN;
}

// ═══════════════════════════════════════════════════════════════
// SUMBER VIDEO + DRIVE
// ═══════════════════════════════════════════════════════════════
// Tampilkan grup input sesuai sumber (esp32=IP, webcam=index, video=upload)
function updateSourceGroups(src) {
    if (el.ipGroup) el.ipGroup.classList.toggle("hidden", src !== "esp32");
    if (el.webcamGroup) el.webcamGroup.classList.toggle("hidden", src !== "webcam");
    el.videoUpload.classList.toggle("hidden", src !== "video");
}

document.querySelectorAll(".seg-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const src = btn.dataset.source;
        selectedSource = src;
        document.querySelectorAll(".seg-btn").forEach(b => b.classList.toggle("active", b === btn));
        updateSourceGroups(src);
        el.sourceBadge.textContent = src.toUpperCase();
        el.sourceLabel.textContent = src === "esp32" ? "ESP32-CAM" : src === "video" ? "Video" : "Webcam";

        if (src === "video") {
            showToast("Pilih file video untuk diputar", "info");
        } else if (src === "webcam") {
            socket.emit("set_video_source", { source: "webcam", webcam_index: +el.webcamIndex.value });
            showToast("Mengaktifkan webcam #" + el.webcamIndex.value, "info");
        } else {
            socket.emit("set_video_source", { source: src, ip: el.espIp.value.trim() });
            showToast("Mengaktifkan sumber: " + sourceName(src), "info");
        }
    });
});

el.btnConnect.addEventListener("click", () => {
    socket.emit("set_video_source", { source: selectedSource, ip: el.espIp.value.trim() });
    if (driveRobot) socket.emit("set_drive", { enabled: true, ip: el.espIp.value.trim() });
    showToast("Menerapkan IP " + el.espIp.value, "info");
});

// Webcam: pakai index terpilih
el.btnWebcamApply.addEventListener("click", () => {
    selectedSource = "webcam";
    socket.emit("set_video_source", { source: "webcam", webcam_index: +el.webcamIndex.value });
    showToast("Membuka webcam #" + el.webcamIndex.value + "…", "info");
});

// Webcam: pindai kamera tersedia
el.btnScanCam.addEventListener("click", () => {
    el.webcamHint.textContent = "Memindai kamera… (beberapa detik)";
    socket.emit("scan_cameras");
});

socket.on("cameras_found", (data) => {
    const cams = data.cameras || [];
    if (!cams.length) {
        el.webcamHint.textContent = "Tidak ada kamera terdeteksi. Cek izin kamera Windows / kabel.";
        showToast("Tidak ada kamera terdeteksi", "warning");
    } else {
        el.webcamHint.textContent = "Kamera tersedia di index: " + cams.join(", ") + ". Pilih lalu 'Pakai Kamera'.";
        showToast("Kamera ditemukan: index " + cams.join(", "), "success");
    }
});

el.btnUploadVideo.addEventListener("click", () => el.videoFileInput.click());
el.videoFileInput.addEventListener("change", () => {
    const file = el.videoFileInput.files[0];
    if (!file) return;
    el.uploadLabel.textContent = "Mengunggah…";
    const fd = new FormData();
    fd.append("video", file);
    fetch("/upload_video", { method: "POST", body: fd })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                el.uploadLabel.textContent = res.filename;
                showToast("Video dimuat: " + res.filename, "success");
                if (res.status) applySourceState(res.status);
            } else {
                el.uploadLabel.textContent = "Pilih File Video…";
                showToast("Gagal memuat video: " + (res.error || ""), "error");
            }
        })
        .catch(() => { el.uploadLabel.textContent = "Pilih File Video…"; showToast("Upload gagal", "error"); });
});

el.driveToggle.addEventListener("change", () => {
    driveRobot = el.driveToggle.checked;
    socket.emit("set_drive", { enabled: driveRobot, ip: el.espIp.value.trim() });
});

// ═══════════════════════════════════════════════════════════════
// MODE + KONTROL MANUAL (mecanum)
// ═══════════════════════════════════════════════════════════════
el.btnManual.addEventListener("click", () => socket.emit("toggle_mode", { mode: "manual" }));
el.btnAuto.addEventListener("click", () => socket.emit("toggle_mode", { mode: "auto" }));

let lastCmdBtn = null;  // tombol kontrol terakhir ditekan (utk flash feedback)

const CMD_LABEL = {
    forward: "MAJU", backward: "MUNDUR", left: "STRAFE KIRI", right: "STRAFE KANAN",
    "strafe-fl": "SERONG KIRI-DEPAN", "strafe-fr": "SERONG KANAN-DEPAN",
    "strafe-rl": "SERONG KIRI-BLKG", "strafe-rr": "SERONG KANAN-BLKG",
    ccw: "PUTAR KIRI", cw: "PUTAR KANAN", stop: "BERHENTI",
};

function sendManualCmd(vx, vy, omega, action = "", btnId = null) {
    if (isAutoMode) {
        setCmdStatus("ignored", action, "Mode Otomatis aktif — kontrol manual nonaktif");
        return;
    }
    if (btnId) lastCmdBtn = btnId;
    socket.emit("manual_control", { vx, vy, omega, action });
}

// Peta perintah → vektor [vx, vy, omega]. vx=maju, vy=kanan, omega=cw.
function cmdVector(name) {
    const S = manualSpeed, T = manualTurn;
    switch (name) {
        case "forward":   return [S, 0, 0];
        case "backward":  return [-S, 0, 0];
        case "left":      return [0, -S, 0];
        case "right":     return [0, S, 0];
        case "strafe-fl": return [S, -S, 0];
        case "strafe-fr": return [S, S, 0];
        case "strafe-rl": return [-S, -S, 0];
        case "strafe-rr": return [-S, S, 0];
        case "ccw":       return [0, 0, -T];
        case "cw":        return [0, 0, T];
        default:          return [0, 0, 0];
    }
}

document.querySelectorAll(".btn-ctrl").forEach(btn => {
    const name = btn.dataset.cmd;
    if (name === "stop") {
        btn.addEventListener("click", () => sendManualCmd(0, 0, 0, CMD_LABEL.stop, btn.id));
        return;
    }
    const press = () => sendManualCmd(...cmdVector(name), CMD_LABEL[name], btn.id);
    const release = () => sendManualCmd(0, 0, 0, CMD_LABEL.stop, btn.id);
    btn.addEventListener("mousedown", press);
    btn.addEventListener("mouseup", release);
    btn.addEventListener("mouseleave", (e) => { if (e.buttons) release(); });
    btn.addEventListener("touchstart", (e) => { e.preventDefault(); press(); }, { passive: false });
    btn.addEventListener("touchend", (e) => { e.preventDefault(); release(); });
});

// Servo
el.btnServoOpen.addEventListener("click", () => socket.emit("servo_cmd", { cmd: "open" }));
el.btnServoClose.addEventListener("click", () => socket.emit("servo_cmd", { cmd: "close" }));
el.btnServoCollect.addEventListener("click", () => {
    socket.emit("servo_cmd", { cmd: "open" });
    setTimeout(() => socket.emit("servo_cmd", { cmd: "close" }), 500);
    showToast("Sekuens collect dijalankan", "info");
});

// Logging
el.btnLogToggle.addEventListener("click", () =>
    socket.emit("toggle_logging", { action: isRecording ? "stop" : "start" }));

// ═══════════════════════════════════════════════════════════════
// HSV sliders
// ═══════════════════════════════════════════════════════════════
["h_min", "h_max", "s_min", "s_max", "v_min", "v_max"].forEach(name => {
    const slider = $(name);
    slider.addEventListener("input", () => {
        $(name + "_val").textContent = slider.value;
        socket.emit("update_hsv", {
            h_min: +el.hMin.value, h_max: +el.hMax.value,
            s_min: +el.sMin.value, s_max: +el.sMax.value,
            v_min: +el.vMin.value, v_max: +el.vMax.value,
        });
    });
});

el.btnHsvReset.addEventListener("click", () => {
    socket.emit("update_hsv", hsvDefaults);
    setSliderValues(hsvDefaults);
    showToast("HSV direset ke default", "info");
});

// ── Pemilih detektor bola (HSV vs AI/YOLO) ──────────────────────
if (el.detectorSeg) {
    el.detectorSeg.querySelectorAll(".seg-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const backend = btn.dataset.detector;
            highlightDetector(backend);   // optimistik; server konfirmasi via detector_state
            if (backend === "yolo" && el.detectorStatus) {
                el.detectorStatus.classList.remove("is-error");
                el.detectorStatus.classList.add("is-ai");
                el.detectorStatus.textContent =
                    "Memuat model AI… (unduhan bobot bisa makan waktu saat pertama kali)";
            }
            socket.emit("set_detector", { backend });
        });
    });
}

el.btnCalibReset.addEventListener("click", () => socket.emit("reset_calibration", {}));

// ═══════════════════════════════════════════════════════════════
// Keyboard — WASD gerak, QE rotasi
// ═══════════════════════════════════════════════════════════════
const KEY_CMD = { w: "forward", s: "backward", a: "left", d: "right", q: "ccw", e: "cw" };
const KEY_BTN = { w: "btn-fwd", s: "btn-bwd", a: "btn-left", d: "btn-right", q: "btn-ccw", e: "btn-cw" };

document.addEventListener("keydown", (e) => {
    const key = e.key.toLowerCase();
    if (keysPressed.has(key)) return;
    keysPressed.add(key);
    if (e.target.tagName === "INPUT") return;

    if (key in KEY_CMD) {
        const name = KEY_CMD[key];
        sendManualCmd(...cmdVector(name), CMD_LABEL[name], KEY_BTN[key]);
        highlightButton(KEY_BTN[key]);
    } else if (key === " ") {
        e.preventDefault();
        sendManualCmd(0, 0, 0, CMD_LABEL.stop, "btn-stop");
        highlightButton("btn-stop");
    } else if (key === "t") {
        socket.emit("toggle_mode", { mode: isAutoMode ? "manual" : "auto" });
    }
});

document.addEventListener("keyup", (e) => {
    const key = e.key.toLowerCase();
    keysPressed.delete(key);
    if (e.target.tagName === "INPUT") return;
    if (key in KEY_CMD) { sendManualCmd(0, 0, 0, CMD_LABEL.stop, KEY_BTN[key]); unhighlightAllButtons(); }
    if (key === " ") unhighlightAllButtons();
});

function highlightButton(id) {
    unhighlightAllButtons();
    $(id)?.classList.add("pressed");
}
function unhighlightAllButtons() {
    document.querySelectorAll(".btn-ctrl.pressed").forEach(b => b.classList.remove("pressed"));
}

console.log("[Ground Station] Frontend siap — menunggu SocketIO…");
