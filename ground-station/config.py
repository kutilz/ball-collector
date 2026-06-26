"""
config.py — Konfigurasi pusat ground station robot pengumpul bola.

Semua parameter sistem terkumpul di sini agar mudah di-tweak
tanpa harus menyentuh modul logika.
"""

import os

# ═══════════════════════════════════════════════════════════════
# Koneksi ESP32-CAM
# ═══════════════════════════════════════════════════════════════
ESP32_CAM_IP = "192.168.4.1"       # IP default AP ESP32-CAM
STREAM_PORT = 81                    # Port MJPEG stream (:81/stream)
CMD_PORT = 80                       # Port HTTP command (:80/cmd)
STREAM_TIMEOUT = 5                  # Timeout koneksi stream (detik)
CMD_TIMEOUT = 2                     # Timeout kirim perintah (detik)

# ═══════════════════════════════════════════════════════════════
# Demo Mode — pakai webcam laptop kalau ESP32 tidak tersedia
# ═══════════════════════════════════════════════════════════════
DEMO_MODE = True                    # True = fallback ke webcam laptop

# ═══════════════════════════════════════════════════════════════
# Resolusi frame yang diproses (resize untuk efisiensi)
# ═══════════════════════════════════════════════════════════════
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ═══════════════════════════════════════════════════════════════
# HSV Default — Rentang warna bola ping-pong oranye
# ═══════════════════════════════════════════════════════════════
HSV_DEFAULTS = {
    "h_min": 5,
    "h_max": 25,
    "s_min": 100,
    "s_max": 255,
    "v_min": 100,
    "v_max": 255,
}

# ═══════════════════════════════════════════════════════════════
# State Machine — Threshold transisi antar state
# ═══════════════════════════════════════════════════════════════
AREA_APPROACH = 500     # Area minimal (px²) untuk transisi SEARCH → APPROACH
AREA_COLLECT = 8000     # Area minimal (px²) untuk transisi APPROACH → COLLECT
CENTER_TOLERANCE = 30   # Toleransi offset_x (px) dianggap "center"

# ═══════════════════════════════════════════════════════════════
# Motor — Kecepatan default tiap state (0–255 PWM)
# ═══════════════════════════════════════════════════════════════
SEARCH_SPEED = 80       # Kecepatan rotasi saat SEARCH
APPROACH_SPEED = 60     # Kecepatan maju saat APPROACH

# ═══════════════════════════════════════════════════════════════
# Servo — Sudut buka/tutup mekanisme pengumpul
# ═══════════════════════════════════════════════════════════════
SERVO_OPEN = 30         # Sudut servo posisi buka (°)
SERVO_CLOSE = 150       # Sudut servo posisi tutup (°)
SWEEP_DELAY = 0.5       # Jeda antara buka → tutup (detik)

# ═══════════════════════════════════════════════════════════════
# P-Controller Gain — Steering proporsional saat APPROACH
# ═══════════════════════════════════════════════════════════════
KP_STEERING = 0.5       # Gain proporsional offset_x → omega

# ═══════════════════════════════════════════════════════════════
# Logging — Penyimpanan CSV eksperimen
# ═══════════════════════════════════════════════════════════════
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# ═══════════════════════════════════════════════════════════════
# Loop Timing
# ═══════════════════════════════════════════════════════════════
MAIN_LOOP_DELAY = 0.03  # ~33 FPS target loop utama (detik)
