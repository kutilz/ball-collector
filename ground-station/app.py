"""
app.py — Aplikasi utama ground station.

Flask + Flask-SocketIO untuk:
  • Streaming video MJPEG (/video_feed, /hsv_preview)
  • WebSocket event: kontrol manual, HSV tuning, logging, dll.
  • Background thread: capture → vision → brain → comms → telemetri
"""

import time
import threading
import cv2
from flask import Flask, Response, render_template
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
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ═══════════════════════════════════════════════════════════════
# Inisialisasi modul-modul
# ═══════════════════════════════════════════════════════════════
vision = VisionPipeline()
brain = StateMachine()
comms = RobotComms()
logger = DataLogger()

# ═══════════════════════════════════════════════════════════════
# State global
# ═══════════════════════════════════════════════════════════════
auto_mode = False           # True = brain FSM aktif, False = manual
latest_annotated = None     # Frame terakhir yang sudah dianotasi
latest_lock = threading.Lock()
bg_thread = None            # Background processing thread
bg_running = False


# ═══════════════════════════════════════════════════════════════
# Route: Dashboard utama
# ═══════════════════════════════════════════════════════════════
@app.route("/")
def index():
    """Halaman dashboard kontrol."""
    return render_template("index.html")


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
        time.sleep(0.03)


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
        time.sleep(0.1)  # Preview tidak perlu 30fps


@app.route("/hsv_preview")
def hsv_preview():
    """Endpoint MJPEG stream mask HSV."""
    return Response(
        _generate_hsv_preview(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ═══════════════════════════════════════════════════════════════
# SocketIO Events
# ═══════════════════════════════════════════════════════════════

@socketio.on("connect")
def handle_connect():
    """Client baru terhubung — kirim state awal."""
    emit("init_state", {
        "hsv": vision.get_hsv_values(),
        "brain": brain.get_status(),
        "comms": comms.get_status(),
        "log": logger.get_log_info(),
        "auto_mode": auto_mode,
    })


@socketio.on("connect_robot")
def handle_connect_robot(data):
    """Coba koneksi ke ESP32-CAM (atau fallback webcam)."""
    ip = data.get("ip", config.ESP32_CAM_IP)
    success = comms.connect(ip)
    emit("connection_result", {
        "success": success,
        "status": comms.get_status(),
    })


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


@socketio.on("manual_control")
def handle_manual_control(data):
    """Terima perintah manual dari joystick/keyboard."""
    global auto_mode
    if auto_mode:
        return  # Abaikan kontrol manual saat auto-mode

    vx = data.get("vx", 0)
    vy = data.get("vy", 0)
    omega = data.get("omega", 0)
    comms.send_command(vx, vy, omega)


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
    """Perintah servo manual."""
    cmd = data.get("cmd", "open")
    angle = config.SERVO_OPEN if cmd == "open" else config.SERVO_CLOSE
    comms.send_servo(angle)
    emit("servo_result", {"cmd": cmd, "angle": angle})


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
            "cmd_vx": cmd.get("vx", 0),
            "cmd_vy": cmd.get("vy", 0),
            "cmd_omega": cmd.get("omega", 0),
            "connected": comms_status.get("connected", False),
            "demo_mode": comms_status.get("demo_mode", False),
            "auto_mode": auto_mode,
            "logging": logger.get_log_info(),
        }
        socketio.emit("telemetry", telemetry)

        # Jaga loop rate
        elapsed = time.time() - loop_start
        sleep_time = max(0, config.MAIN_LOOP_DELAY - elapsed)
        time.sleep(sleep_time)


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════
def start_background_thread():
    """Mulai background processing thread."""
    global bg_thread
    if bg_thread is None or not bg_thread.is_alive():
        bg_thread = socketio.start_background_task(_main_loop)


@socketio.on("connect")
def on_first_connect():
    """Pastikan background thread berjalan saat client pertama terhubung."""
    start_background_thread()


if __name__ == "__main__":
    print("=" * 60)
    print("  Robot Pengumpul Bola — Ground Station")
    print("  Buka http://localhost:5000 di browser")
    print("=" * 60)

    # Auto-connect saat startup (demo mode)
    if config.DEMO_MODE:
        comms.connect()

    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
