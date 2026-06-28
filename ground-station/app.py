"""
app.py — Aplikasi utama ground station.

Flask + Flask-SocketIO untuk:
  • Streaming video MJPEG (/video_feed, /hsv_preview)
  • WebSocket event: kontrol manual, HSV tuning, logging, dll.
  • Background thread: capture → vision → brain → comms → telemetri
"""

import os
import gzip
import time
import threading
import cv2
from werkzeug.utils import secure_filename
from flask import Flask, Response, render_template, request, jsonify
from flask_socketio import SocketIO, emit

import config
from vision import VisionPipeline
from brain import StateMachine
from comms import RobotComms
from logger import DataLogger

# ═══════════════════════════════════════════════════════════════
# Inisialisasi Flask & SocketIO
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__)
app.config["SECRET_KEY"] = "ball-collector-ground-station"
# Jangan cache aset statis (CSS/JS) — biar perubahan langsung kebaca tanpa
# perlu hard-reload manual. Penting saat kalibrasi/iterasi UI.
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


@app.after_request
def _no_cache(resp):
    """Cegah browser meng-cache HTML & aset statis ground station."""
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp

# Direktori upload video uji
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# Inisialisasi modul-modul
# ═══════════════════════════════════════════════════════════════
vision = VisionPipeline()
brain = StateMachine()
comms = RobotComms()
logger = DataLogger()

# Snapshot nilai kalibrasi default (sebelum dimutasi runtime) untuk tombol reset
_CALIBRATION_DEFAULTS = config.get_calibration()

# ═══════════════════════════════════════════════════════════════
# State global
# ═══════════════════════════════════════════════════════════════
auto_mode = False           # True = brain FSM aktif, False = manual
last_manual_cmd = {"vx": 0, "vy": 0, "omega": 0}  # perintah manual terakhir (utk visualizer)
latest_annotated = None     # Frame terakhir yang sudah dianotasi
latest_lock = threading.Lock()
bg_thread = None            # Background processing thread
bg_running = False
bg_started = False          # Guard: loop utama hanya dimulai sekali


# ═══════════════════════════════════════════════════════════════
# Route: Dashboard utama
# ═══════════════════════════════════════════════════════════════
@app.route("/")
def index():
    """Halaman dashboard kontrol."""
    return render_template("index.html")


# ═══════════════════════════════════════════════════════════════
# Route: Model 3D robot (GLB) — preview ringan di dashboard
# ═══════════════════════════════════════════════════════════════
_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static", "models"
)
_ALLOWED_MODELS = {"robot-low", "robot-med", "robot-high"}  # level LOD preview 3D
_model_gzip_cache = {}  # name -> (mtime, bytes) GLB ter-gzip


@app.route("/model/<name>.glb")
def robot_model(name):
    """Serve GLB robot ter-gzip untuk preview 3D (level LOD low/med/high).

    Hasil kompresi di-cache di memori per-file & di-recompress otomatis bila
    file berubah (cache di-key dgn mtime) → regenerasi model langsung kebaca.
    Header cache ikut kebijakan no-store global (_no_cache) — sengaja TIDAK
    immutable supaya update model tak terjebak cache browser lama.
    """
    if name not in _ALLOWED_MODELS:
        return ("Model tidak dikenal", 404)
    path = os.path.join(_MODELS_DIR, name + ".glb")
    if not os.path.exists(path):
        return (f"Model '{name}' belum tersedia", 404)
    mtime = os.path.getmtime(path)
    cached = _model_gzip_cache.get(name)
    if cached is None or cached[0] != mtime:
        with open(path, "rb") as f:
            cached = (mtime, gzip.compress(f.read(), 6))
        _model_gzip_cache[name] = cached
    data = cached[1]
    resp = Response(data, mimetype="model/gltf-binary")
    resp.headers["Content-Encoding"] = "gzip"
    resp.headers["Content-Length"] = str(len(data))
    return resp


# ═══════════════════════════════════════════════════════════════
# Route: MJPEG video stream (anotated)
# ═══════════════════════════════════════════════════════════════
def _generate_video():
    """Generator MJPEG multipart untuk video feed."""
    while True:
        with latest_lock:
            frame = latest_annotated
        if frame is not None:
            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg.tobytes()
                + b"\r\n"
            )
        else:
            # Kirim frame hitam sementara menunggu
            import numpy as np
            blank = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(blank, "Menunggu koneksi...", (120, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
            _, jpeg = cv2.imencode(".jpg", blank)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg.tobytes()
                + b"\r\n"
            )
        # PENTING: socketio.sleep (bukan time.sleep) agar YIELD ke hub eventlet.
        # time.sleep di sini memblokir seluruh server → tombol jadi tak responsif.
        socketio.sleep(0.03)


@app.route("/video_feed")
def video_feed():
    """Endpoint MJPEG stream — disematkan sebagai <img src>."""
    return Response(
        _generate_video(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ═══════════════════════════════════════════════════════════════
# Route: HSV mask preview
# ═══════════════════════════════════════════════════════════════
def _generate_hsv_preview():
    """Generator MJPEG untuk preview mask HSV."""
    while True:
        mask_frame = vision.get_mask_preview()
        _, jpeg = cv2.imencode(".jpg", mask_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + jpeg.tobytes()
            + b"\r\n"
        )
        socketio.sleep(0.1)  # Preview tidak perlu 30fps (yield ke hub eventlet)


@app.route("/hsv_preview")
def hsv_preview():
    """Endpoint MJPEG stream mask HSV."""
    return Response(
        _generate_hsv_preview(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ═══════════════════════════════════════════════════════════════
# Route: Upload file video uji → langsung jadikan sumber
# ═══════════════════════════════════════════════════════════════
@app.route("/upload_video", methods=["POST"])
def upload_video():
    """Terima file video, simpan ke uploads/, dan set sebagai sumber."""
    if "video" not in request.files:
        return jsonify({"success": False, "error": "Tidak ada file"}), 400

    file = request.files["video"]
    if not file.filename:
        return jsonify({"success": False, "error": "Nama file kosong"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    success = comms.set_source("video", path=save_path)
    return jsonify({
        "success": success,
        "filename": filename,
        "status": comms.get_status(),
    })


# ═══════════════════════════════════════════════════════════════
# SocketIO Events
# ═══════════════════════════════════════════════════════════════

@socketio.on("connect")
def handle_connect(auth=None):
    """Client baru terhubung — pastikan loop utama jalan, lalu kirim state awal."""
    start_background_thread()
    emit("init_state", {
        "hsv": vision.get_hsv_values(),
        "hsv_defaults": config.HSV_DEFAULTS,
        "brain": brain.get_status(),
        "comms": comms.get_status(),
        "log": logger.get_log_info(),
        "auto_mode": auto_mode,
        "calibration": config.get_calibration(),
        "calibration_spec": config.CALIBRATION_SPEC,
    })


@socketio.on("disconnect")
def handle_disconnect():
    """
    FAILSAFE: operator/socket terputus (tab ditutup, browser crash, WiFi drop)
    → hentikan auto-mode dan enqueue STOP. Berlapis dengan watchdog Arduino
    (500ms). Default aman untuk setup operator-tunggal.
    """
    global auto_mode
    if auto_mode:
        auto_mode = False
        brain.stop()
    comms.send_command(0, 0, 0)  # non-blocking enqueue STOP


@socketio.on("connect_robot")
def handle_connect_robot(data):
    """Set IP robot/ESP32 lalu mulai sumber video aktif."""
    ip = data.get("ip", config.ESP32_CAM_IP)
    success = comms.connect(ip)
    emit("connection_result", {
        "success": success,
        "status": comms.get_status(),
    })


@socketio.on("set_video_source")
def handle_set_video_source(data):
    """Ganti sumber video: esp32 / webcam / video (file)."""
    source = data.get("source", "webcam")
    path = data.get("path")
    esp32_ip = data.get("ip")
    webcam_index = data.get("webcam_index")
    success = comms.set_source(source, path=path, esp32_ip=esp32_ip,
                               webcam_index=webcam_index)
    emit("connection_result", {
        "success": success,
        "status": comms.get_status(),
    })


@socketio.on("scan_cameras")
def handle_scan_cameras():
    """Pindai index webcam yang tersedia (async, hasil via 'cameras_found')."""
    comms.scan_cameras_async()
    emit("scan_started", {})


@socketio.on("set_drive")
def handle_set_drive(data):
    """Aktif/nonaktif kemudikan robot asli (kirim command ke ESP32)."""
    enabled = data.get("enabled", False)
    ip = data.get("ip")
    comms.set_drive(enabled, robot_ip=ip)
    emit("drive_status", comms.get_status())


@socketio.on("update_calibration")
def handle_update_calibration(data):
    """Perbarui satu parameter kalibrasi runtime."""
    key = data.get("key")
    value = data.get("value")
    final = config.update_calibration(key, value)
    if final is not None:
        emit("calibration_updated", {"key": key, "value": final}, broadcast=True)


@socketio.on("reset_calibration")
def handle_reset_calibration(data):
    """Kembalikan semua parameter kalibrasi ke nilai default modul."""
    for key, val in _CALIBRATION_DEFAULTS.items():
        config.update_calibration(key, val)
    emit("calibration_state", config.get_calibration(), broadcast=True)


@socketio.on("update_hsv")
def handle_update_hsv(data):
    """Perbarui parameter HSV dari slider UI."""
    vision.update_hsv(
        data.get("h_min", vision.h_min),
        data.get("h_max", vision.h_max),
        data.get("s_min", vision.s_min),
        data.get("s_max", vision.s_max),
        data.get("v_min", vision.v_min),
        data.get("v_max", vision.v_max),
    )
    emit("hsv_updated", vision.get_hsv_values())


def _ack_detail(status):
    """Terjemahkan status pengiriman command ke teks feedback UI."""
    if status == "ok":
        return "Terkirim ke robot ✓"
    if status == "skipped":
        return "Tidak terkirim — robot tidak dikemudikan (aktifkan 'Kemudikan Robot Asli')"
    if status == "ignored":
        return "Diabaikan — mode Otomatis aktif"
    return comms.get_status().get("last_error") or "Gagal kirim ke robot"


@socketio.on("manual_control")
def handle_manual_control(data):
    """Terima perintah manual dari joystick/keyboard + balas feedback."""
    global auto_mode, last_manual_cmd
    action = data.get("action", "")

    if auto_mode:
        emit("cmd_ack", {"action": action, "status": "ignored",
                         "detail": _ack_detail("ignored")})
        return

    vx = data.get("vx", 0)
    vy = data.get("vy", 0)
    omega = data.get("omega", 0)
    # Catat intent agar visualizer roda/command mencerminkan kontrol manual,
    # walau robot asli tidak dikemudikan.
    last_manual_cmd = {"vx": vx, "vy": vy, "omega": omega}
    # Non-blocking: hanya mengantri. "skipped" diketahui langsung (tanpa I/O) →
    # balas seketika. "queued" → hasil ok/error menyusul async via drain_acks().
    status = comms.send_command(vx, vy, omega, action=action)
    if status == "skipped":
        emit("cmd_ack", {"action": action, "status": "skipped",
                         "detail": _ack_detail("skipped")})


@socketio.on("toggle_mode")
def handle_toggle_mode(data):
    """Alihkan antara mode otomatis dan manual."""
    global auto_mode
    mode = data.get("mode", "manual")

    if mode == "auto":
        auto_mode = True
        brain.start()
    else:
        auto_mode = False
        brain.stop()
        # Hentikan robot saat beralih ke manual
        comms.send_command(0, 0, 0)

    emit("mode_changed", {"auto_mode": auto_mode, "brain": brain.get_status()})


@socketio.on("toggle_logging")
def handle_toggle_logging(data):
    """Mulai atau hentikan recording CSV."""
    action = data.get("action", "toggle")
    if action == "start" or (action == "toggle" and not logger.get_log_info()["active"]):
        logger.start_logging()
    else:
        logger.stop_logging()

    emit("logging_status", logger.get_log_info())


@socketio.on("servo_cmd")
def handle_servo_cmd(data):
    """Perintah servo manual + balas feedback."""
    cmd = data.get("cmd", "open")
    angle = config.SERVO_OPEN if cmd == "open" else config.SERVO_CLOSE
    label = "SERVO BUKA" if cmd == "open" else "SERVO TUTUP"
    # Non-blocking: enqueue. ok/error menyusul async; skipped balas seketika.
    status = comms.send_servo(angle, action=label)
    emit("servo_result", {"cmd": cmd, "angle": angle, "status": status})
    if status == "skipped":
        emit("cmd_ack", {"action": label, "status": "skipped",
                         "detail": _ack_detail("skipped")})


# ═══════════════════════════════════════════════════════════════
# Background Thread: Loop utama pemrosesan
# ═══════════════════════════════════════════════════════════════
def _main_loop():
    """
    Loop utama ground station:
      1. Ambil frame dari comms
      2. Proses vision → deteksi bola
      3. Jika auto-mode: jalankan brain → kirim perintah
      4. Log data jika recording aktif
      5. Broadcast telemetri ke semua client via SocketIO
    """
    global latest_annotated, bg_running

    bg_running = True
    fps_counter = 0
    fps_timer = time.time()
    current_fps = 0.0

    while bg_running:
        loop_start = time.time()

        # 1. Ambil frame
        frame = comms.get_frame()

        # 2. Proses vision
        detection = vision.process_frame(frame)

        # Simpan frame beranotasi untuk stream
        with latest_lock:
            latest_annotated = detection.get("frame_annotated")

        # 3. Jalankan brain jika auto-mode
        cmd = {"vx": 0, "vy": 0, "omega": 0, "servo_cmd": None}
        if auto_mode and brain.is_running:
            cmd = brain.update(detection)

            # Kirim perintah motor ke robot
            comms.send_command(cmd["vx"], cmd["vy"], cmd["omega"])

            # Kirim perintah servo jika ada
            if cmd["servo_cmd"] == "OPEN":
                comms.send_servo(config.SERVO_OPEN)
            elif cmd["servo_cmd"] == "CLOSE":
                comms.send_servo(config.SERVO_CLOSE)

        # 4. Log data jika recording aktif
        if logger.get_log_info()["active"]:
            collect_result = ""
            if cmd.get("servo_cmd") == "CLOSE":
                collect_result = "ATTEMPT"
            logger.log_entry(
                state=brain.get_status()["state"],
                ball_x=detection.get("cx", 0),
                ball_y=detection.get("cy", 0),
                ball_area=detection.get("area", 0),
                cmd_vx=cmd.get("vx", 0),
                cmd_vy=cmd.get("vy", 0),
                cmd_omega=cmd.get("omega", 0),
                collect_result=collect_result,
            )

        # 5. Hitung FPS loop
        fps_counter += 1
        if time.time() - fps_timer >= 1.0:
            current_fps = fps_counter
            fps_counter = 0
            fps_timer = time.time()

        # 6. Broadcast telemetri
        # Command yang ditampilkan: auto → output brain; manual → intent terakhir
        # operator (supaya visualizer roda/command tidak selalu nol di manual).
        disp_cmd = cmd if auto_mode else last_manual_cmd
        brain_status = brain.get_status()
        comms_status = comms.get_status()
        telemetry = {
            "fps": current_fps,
            "stream_fps": comms_status.get("fps", 0),
            "state": brain_status["state"],
            "running": brain_status["running"],
            "balls_collected": brain_status["balls_collected"],
            "state_duration": brain_status["state_duration"],
            "detected": detection.get("detected", False),
            "ball_x": detection.get("cx", 0),
            "ball_y": detection.get("cy", 0),
            "ball_area": round(detection.get("area", 0), 1),
            "offset_x": detection.get("offset_x", 0),
            "offset_y": detection.get("offset_y", 0),
            "cmd_vx": disp_cmd.get("vx", 0),
            "cmd_vy": disp_cmd.get("vy", 0),
            "cmd_omega": disp_cmd.get("omega", 0),
            "connected": comms_status.get("connected", False),
            "demo_mode": comms_status.get("demo_mode", False),
            "source": comms_status.get("source", "webcam"),
            "drive_robot": comms_status.get("drive_robot", False),
            "robot_online": comms_status.get("robot_online", False),
            "auto_mode": auto_mode,
            "logging": logger.get_log_info(),
            # Telemetri sensor (untuk visualizer)
            "heading": comms_status.get("heading", 0.0),
            "vbat": comms_status.get("vbat", 0.0),
            "rssi": comms_status.get("rssi", 0),
            "frame_w": config.FRAME_WIDTH,
            "frame_h": config.FRAME_HEIGHT,
        }
        socketio.emit("telemetry", telemetry)

        # 7. Feedback async dari command worker (ok/error perintah motor/servo).
        #    Emit dari sini (green-task) — JANGAN emit dari worker thread asli.
        for ack in comms.drain_acks():
            socketio.emit("cmd_ack", {**ack, "detail": _ack_detail(ack["status"])})

        # 8. Hasil pindai kamera (async) → kirim ke UI.
        cams = comms.drain_camera_scan()
        if cams is not None:
            socketio.emit("cameras_found", {"cameras": cams})

        # Jaga loop rate — socketio.sleep agar yield ke hub eventlet
        # (time.sleep di background task green-thread juga memblokir hub).
        elapsed = time.time() - loop_start
        sleep_time = max(0, config.MAIN_LOOP_DELAY - elapsed)
        socketio.sleep(sleep_time)


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════
def start_background_thread():
    """
    Mulai background processing thread (idempotent).

    Catatan: socketio.start_background_task mengembalikan EventletThread yang
    TIDAK punya .is_alive(), jadi kita pakai flag bg_started — bukan introspeksi
    thread — untuk memastikan loop hanya dimulai sekali.
    """
    global bg_thread, bg_started
    if not bg_started:
        bg_started = True
        bg_thread = socketio.start_background_task(_main_loop)


if __name__ == "__main__":
    print("=" * 60)
    print("  Robot Pengumpul Bola — Ground Station")
    print("  Buka http://localhost:5000 di browser")
    print("=" * 60)

    # Redam traceback broken-pipe (WinError 10053 / ConnectionAbortedError) yang
    # muncul saat stream MJPEG diputus browser (reload/tutup tab). Ini noise tak
    # berbahaya — bukan crash — tapi membanjiri console. debug_exceptions=False
    # menyembunyikan traceback hub eventlet untuk exception yang sudah ditangani.
    import eventlet
    try:
        eventlet.hubs.get_hub().debug_exceptions = False
    except Exception:
        pass

    # Mulai sumber video aktif saat startup (default: webcam)
    if not comms.start_source():
        print(f"[!] Sumber video gagal dimulai: {comms.get_status().get('last_error')}")
        print("    (Webcam mungkin dipakai app lain / izin kamera ditolak.)")

    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
