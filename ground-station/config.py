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
# Sumber Video — pilih input frame untuk pipeline vision
# ═══════════════════════════════════════════════════════════════
#   "esp32"  → MJPEG stream dari ESP32-CAM (robot asli)
#   "webcam" → webcam laptop (deteksi lokal, robot tetap bisa dikemudikan)
#   "video"  → file video (.mp4/.avi) untuk uji ulang / demo
VIDEO_SOURCE = "webcam"
VIDEO_FILE = ""                     # Path file video saat VIDEO_SOURCE = "video"
VIDEO_LOOP = True                   # Ulangi file video saat habis
WEBCAM_INDEX = 0                    # Indeks device webcam laptop

# ═══════════════════════════════════════════════════════════════
# Kemudikan Robot Asli — kirim command ke ESP32 walau video lokal
# ═══════════════════════════════════════════════════════════════
#   Saat True, command motor/servo TETAP dikirim ke ROBOT_IP meskipun
#   sumber video webcam/file. Ini bikin "robot jalan beneran" sambil
#   deteksi tetap di laptop.
DRIVE_ROBOT = False
ROBOT_IP = "192.168.4.1"            # IP ESP32-CAM tujuan command (mode drive)
STATUS_POLL_INTERVAL = 1.0          # Interval polling /status ESP32 (detik)

# ═══════════════════════════════════════════════════════════════
# Resolusi frame yang diproses (resize untuk efisiensi)
# ═══════════════════════════════════════════════════════════════
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ═══════════════════════════════════════════════════════════════
# Detektor Bola — pilih backend deteksi (bisa diganti live dari UI)
# ═══════════════════════════════════════════════════════════════
#   "hsv"  → segmentasi warna HSV (ringan, default, tanpa dependensi berat)
#   "yolo" → deteksi objek berbasis machine learning (YOLOv8, butuh ultralytics)
# Backend bisa dialihkan runtime lewat event 'set_detector'; nilai ini hanya
# menentukan mode awal saat ground station start.
DETECTOR_BACKEND = "hsv"

# Konfigurasi YOLO — dipakai hanya saat backend "yolo" aktif.
#   YOLO_MODEL   : path file bobot .pt. Nama model resmi (mis. "yolov8n.pt")
#                  otomatis diunduh Ultralytics saat pertama dipakai. Ganti ke
#                  path model kustom hasil latih (Colab) bila sudah ada.
#   YOLO_CONF    : ambang confidence minimum (0–1). Bisa di-tune live dari UI.
#   YOLO_IMGSZ   : ukuran sisi inferensi (kecil = lebih cepat, sedikit kurang teliti).
#   YOLO_CLASSES : filter indeks kelas yang dianggap "bola". [32] = "sports ball"
#                  pada model COCO pretrained. Kosongkan ([]) untuk model kustom
#                  1-kelas (terima semua deteksi).
YOLO_MODEL = "yolov8n.pt"
YOLO_CONF = 0.35
YOLO_IMGSZ = 416
YOLO_CLASSES = [32]

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
# Vision — Filter kontur & morfologi (tunable via UI kalibrasi)
# ═══════════════════════════════════════════════════════════════
MIN_CONTOUR_AREA = 50   # Area kontur minimal (px²) agar tidak dianggap noise
ERODE_ITER = 2          # Iterasi erosi (hapus bintik noise)
DILATE_ITER = 2         # Iterasi dilasi (isi lubang blob)

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
MANUAL_SPEED = 80       # Kecepatan translasi (maju/mundur/strafe) kontrol manual
MANUAL_TURN = 70        # Kecepatan rotasi kontrol manual

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
# Keselamatan — guardrail & heartbeat kanal perintah
# ═══════════════════════════════════════════════════════════════
# SAFETY_MAX_PWM: batas magnitudo vx/vy/omega yang dikirim ke robot. Turunkan
#   (mis. 120) saat uji agar robot bergerak pelan & aman. 255 = tanpa batas.
SAFETY_MAX_PWM = 255
# MOTION_HEARTBEAT: interval (detik) command worker mengirim ulang perintah motor
#   aktif agar watchdog Arduino (500ms) tidak menstop motor saat tombol ditahan.
#   HARUS < 0.5s. 0.15s memberi margin ~3x.
MOTION_HEARTBEAT = 0.15

# ═══════════════════════════════════════════════════════════════
# Logging — Penyimpanan CSV eksperimen
# ═══════════════════════════════════════════════════════════════
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# ═══════════════════════════════════════════════════════════════
# Loop Timing
# ═══════════════════════════════════════════════════════════════
MAIN_LOOP_DELAY = 0.03  # ~33 FPS target loop utama (detik)


# ═══════════════════════════════════════════════════════════════
# Kalibrasi runtime — parameter yang bisa di-tweak live dari UI
# ═══════════════════════════════════════════════════════════════
# Tiap entri: nama → (min, max, step, label). Modul brain/vision membaca
# nilai config.<NAMA> secara live, jadi mutasi runtime langsung berdampak
# tanpa perlu restart.
CALIBRATION_SPEC = {
    # Deteksi / vision
    "MIN_CONTOUR_AREA": (10, 2000, 10, "Area Min Kontur"),
    "ERODE_ITER":       (0, 5, 1, "Iterasi Erode"),
    "DILATE_ITER":      (0, 5, 1, "Iterasi Dilate"),
    "YOLO_CONF":        (0.05, 0.95, 0.05, "Confidence AI"),
    # State machine
    "AREA_APPROACH":    (100, 5000, 50, "Area → APPROACH"),
    "AREA_COLLECT":     (1000, 40000, 500, "Area → COLLECT"),
    "CENTER_TOLERANCE": (5, 150, 5, "Toleransi Center (px)"),
    # Motor
    "SEARCH_SPEED":     (0, 255, 5, "Speed SEARCH"),
    "APPROACH_SPEED":   (0, 255, 5, "Speed APPROACH"),
    "MANUAL_SPEED":     (0, 255, 5, "Speed Manual"),
    "MANUAL_TURN":      (0, 255, 5, "Turn Manual"),
    "KP_STEERING":      (0.0, 3.0, 0.05, "Kp Steering"),
    # Keselamatan
    "SAFETY_MAX_PWM":   (0, 255, 5, "Batas Kecepatan (PWM)"),
    "MOTION_HEARTBEAT": (0.05, 0.4, 0.01, "Heartbeat Motor (s)"),
    # Servo
    "SERVO_OPEN":       (0, 180, 1, "Servo Buka (°)"),
    "SERVO_CLOSE":      (0, 180, 1, "Servo Tutup (°)"),
    "SWEEP_DELAY":      (0.1, 2.0, 0.1, "Jeda Sweep (s)"),
}

# Param yang bertipe float (selain itu di-cast ke int saat update)
_FLOAT_PARAMS = {"KP_STEERING", "SWEEP_DELAY", "MOTION_HEARTBEAT", "YOLO_CONF"}


def get_calibration():
    """Kembalikan dict {nama: nilai_sekarang} untuk semua param kalibrasi."""
    return {key: globals()[key] for key in CALIBRATION_SPEC}


def update_calibration(key, value):
    """
    Perbarui satu parameter kalibrasi secara runtime (di-clamp ke rentangnya).
    Mengembalikan nilai final yang tersimpan, atau None jika key tak dikenal.
    """
    if key not in CALIBRATION_SPEC:
        return None
    lo, hi, _step, _label = CALIBRATION_SPEC[key]
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    value = max(lo, min(hi, value))
    if key not in _FLOAT_PARAMS:
        value = int(round(value))
    globals()[key] = value
    return value
