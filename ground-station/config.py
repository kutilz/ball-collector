"""
config.py — Konfigurasi pusat ground station robot pengumpul bola.

Semua parameter sistem terkumpul di sini agar mudah di-tweak
tanpa harus menyentuh modul logika.
"""

import os

# ═══════════════════════════════════════════════════════════════
# Koneksi ESP32-CAM
# ═══════════════════════════════════════════════════════════════
ESP32_CAM_IP = "auto"              # "auto" = cari otomatis, atau isi IP tetap
ROBOT_HOSTNAME = "ballcollector.local"  # Nama mDNS firmware ESP32-CAM
STREAM_PORT = 81                    # Port MJPEG stream (:81/stream)
CMD_PORT = 80                       # Port HTTP command (:80/cmd)
STREAM_TIMEOUT = 5                  # Timeout koneksi stream (detik)
STREAM_READ_TIMEOUT = 3             # Stream diam selama ini = dianggap putus (detik)
STREAM_RECONNECT_DELAY = 1.0        # Jeda sebelum menyambung ulang stream (detik)
FRAME_STALE_SEC = 1.5               # Frame lebih tua dari ini = kamera tidak live (detik)
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
ROBOT_IP = "auto"                   # IP ESP32-CAM tujuan command ("auto" = cari)
TEL_POLL_INTERVAL = 0.2             # Interval polling /tel ESP32 (detik). /tel ringan (40–60 ms)
LINK_STALL_SEC = 1.5                # Tak ada balasan HTTP selama ini = kanal perintah macet

# ═══════════════════════════════════════════════════════════════
# Mode video ESP32 — akal-akalan firmware lama (uji 2026-11-17)
# ═══════════════════════════════════════════════════════════════
#   Saat MJPEG :81 dibuka terus, port 80 (/cmd, /tel) beberapa kali macet
#   7–20 s. Mode "snapshot" membuka stream, mengambil 1 frame, lalu menutupnya
#   lagi: video ±3 fps tapi perintah & telemetri tetap lancar.
#   "stream" = MJPEG terus-menerus, hanya untuk menonton/uji vision.
#   Firmware ESP32 rev 2026-11-17 punya /capture (1 JPEG per request) dan batas
#   FPS stream; ground station otomatis memakainya bila tersedia.
ESP32_VIDEO_MODE = "snapshot"
SNAPSHOT_INTERVAL = 0.20            # Jeda antar snapshot (detik)
SNAPSHOT_SKIP = 2                   # Buang frame awal (sisa buffer kamera, basi)
STREAM_FPS = 12                     # Batas FPS mode stream (firmware ESP32 rev 2026-11-17)

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
#   "yoloworld" → deteksi open-vocabulary YOLO-World: objek dicari lewat prompt
#                 teks (mis. "orange ping pong ball"), tanpa training ulang
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
# Uji 2026-11-17 (kamera robot, QVGA, rendah): conf 0.35 → recall YOLOv8n 0/16,
# 0.25 → 1/16, 0.10 → 12/16. Conf rendah memunculkan false positive; itu
# diredam di brain (CONFIRM_FRAMES + gerbang lompatan posisi).
YOLO_CONF = 0.15
YOLO_IMGSZ = 416
YOLO_CLASSES = [32]

# Konfigurasi YOLO-World — dipakai hanya saat backend "yoloworld" aktif.
#   YOLOWORLD_MODEL  : bobot YOLO-World (diunduh otomatis saat pertama dipakai).
#                      Varian "s" = paling ringan, cocok untuk inferensi CPU.
#   YOLOWORLD_PROMPT : daftar deskripsi teks objek yang dicari. Bisa diganti
#                      live dari UI. YOLO_CONF & YOLO_IMGSZ ikut dipakai.
YOLOWORLD_MODEL = "yolov8s-worldv2.pt"
YOLOWORLD_PROMPT = ["orange ping pong ball"]
WORLD_CONF = 0.30                   # Ambang YOLO-World (uji: 14/16 terdeteksi pada 0.35)

# ═══════════════════════════════════════════════════════════════
# HSV Default — Rentang warna bola ping-pong oranye
# ═══════════════════════════════════════════════════════════════
# Uji 2026-11-18: bola salmon pucat (H≈0–8, S≈60–160, V≈130–240) tidak lolos
# rentang lama (S≥100,V≥100 → 0 deteksi). V≥150 melewatkan bola saat kamera
# menggelapkan gambar (2 dari 8 frame, V≈131–145); V≥130 mendapat 8/8 tapi karung
# dan tiang merah ikut lolos di beberapa frame — ditolak oleh CONFIRM_FRAMES.
HSV_DEFAULTS = {
    "h_min": 0,
    "h_max": 22,
    "s_min": 60,
    "s_max": 255,
    "v_min": 130,
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
CENTER_TOLERANCE = 30   # Toleransi offset_x (px) dianggap "center"

# ── Jarak berhenti di depan bola (APPROACH → COLLECT) ─────────────
# Menggantikan AREA_COLLECT (8000 px²). Ambang area bergantung detektor (HSV = luas
# kontur, YOLO = luas bbox w*h, ±1,27x lebih besar), jadi jarak dihitung dari lebar
# bbox: Z_kamera = f · BALL_DIAMETER_CM / max(w, h)  (model lubang jarum).
# Uji 2026-11-18: K = Z·lebar ≈ 23–26 m·px di dekat vs teori 25,8 → cukup akurat dekat.
# Default 25 cm ≈ perilaku lama (COLLECT pada bbox ≈ 100 px ≈ 0,25 m).
BALL_DIAMETER_CM = 4.0       # Bola ping-pong 40 mm
STOP_DIST_CM = 25.0          # Jarak bola ke ujung depan robot saat berhenti (0 = menyentuh/nabrak)
CAM_FRONT_OFFSET_CM = 0.0    # Jarak lensa kamera → ujung depan robot/gripper (BELUM diukur; ukur!)
# Zona buta dekat: bola keluar frame (bawah) pada ±15–18 cm dari kamera (uji expC 18 Nov).
# Bila target lebih dekat dari batas ini, robot maju sampai bola di NEAR_VISIBLE_CM
# (masih terlihat), lalu maju "buta" selama sisa_jarak / kecepatan, lalu COLLECT.
NEAR_VISIBLE_CM = 20.0       # Jarak kamera terdekat yang masih andal terlihat
BLIND_PUSH_MAX_SEC = 4.0     # Batas keras lama maju buta (failsafe)


def ball_cam_dist_cm(bbox):
    """Perkiraan jarak bola dari KAMERA (cm) dari bbox (x, y, w, h); None bila tak valid."""
    if not bbox or len(bbox) < 4:
        return None
    size = max(bbox[2], bbox[3])   # max: bola terpotong tepi frame tetap terukur dari sisi utuh
    if size <= 0:
        return None
    return focal_px() * BALL_DIAMETER_CM / size


def ball_front_dist_cm(bbox):
    """Perkiraan jarak bola dari UJUNG DEPAN robot (cm); None bila tak valid."""
    z = ball_cam_dist_cm(bbox)
    return None if z is None else z - CAM_FRONT_OFFSET_CM

# ═══════════════════════════════════════════════════════════════
# Navigasi otomatis — strategi & parameter "bidik pakai gyro"
# ═══════════════════════════════════════════════════════════════
#   "gyro"       → SEARCH berputar per langkah (TURN), APPROACH = bidik sekali
#                  pakai TURN (sudut dari piksel), lalu maju lurus dengan heading
#                  hold. Tahan terhadap latensi kamera (~185 ms) & jeda WiFi.
#   "continuous" → P-controller lama: omega = KP_STEERING × offset_x tiap frame.
NAV_STRATEGY = "gyro"
CAMERA_HFOV_DEG = 52.8   # FOV horizontal OV2640 terukur (f ≈ 322 px pada lebar 320)
# TURN_COMP_DEG hanya dipakai pada bidik APPROACH (brain.py), bukan langkah SEARCH.
# CATATAN KONFLIK DATA: 17 Nov TURN kelewatan +1,1° → kompensasi 1,3°. 18 Nov TURN 30° rata-rata
# 29,1° (kurang 0,9°) dan bidik APPROACH sering menyisakan +2° setelah dikurangi 1,3°
# → kompensasi mungkin kini terlalu besar. Belum diubah (butuh uji bidik khusus); bisa
# di-tweak live dari kartu Kalibrasi → Navigasi.
TURN_COMP_DEG = 1.3      # TURN kelewatan sistematis +1,1° → perintah dikurangi segini
TURN_MIN_DEG = 2.5       # TURN < toleransi firmware (2°) tidak menggerakkan robot
TURN_MAX_DEG = 170       # TURN:±180 ambigu di wrap180 firmware → batasi
# Batas tunggu "TURN selesai" dihitung per sudut: min(TURN_GUARD_SEC, TURN_GUARD_BASE_SEC +
# |deg| / TURN_GUARD_DEG_PER_SEC). Uji 2026-11-18 (128 TURN 30° yang selesai): terlama 2,15 s,
# rata-rata 1,57 s. Pesan "selesai" hilang ±11–18% (bug LINK putus palsu di firmware, belum
# diflash) dan dulu tiap kejadian menghabiskan 8 s. Putar 30° → batas 6 s, bidik 2,5° → 3,3 s.
TURN_GUARD_SEC = 8.0     # Batas atas tunggu TURN selesai (detik)
TURN_GUARD_BASE_SEC = 3.0   # Dasar batas tunggu (detik) + sudut / TURN_GUARD_DEG_PER_SEC
TURN_GUARD_DEG_PER_SEC = 10.0  # Laju putar konservatif (°/s); terukur ±19°/s pada 30°
AIM_TOL_DEG = 2.0        # Target dianggap lurus di depan bila |sudut| ≤ ini
SEARCH_STEP_DEG = 30     # Langkah putar SEARCH (< HFOV supaya pandangan tumpang tindih)
SETTLE_SEC = 0.35        # Tunggu setelah TURN sebelum frame dipercaya (latensi kamera)
CONFIRM_FRAMES = 2       # Deteksi harus muncul di N frame segar berturut-turut
LOST_FRAMES = 3          # Target hilang N frame segar → kembali SEARCH
JUMP_GATE_FRAC = 0.25    # Deteksi melompat > fraksi lebar frame dari posisi harapan = curiga

# Gain heading hold hasil sweep strafe. Uji 2026-11-17 (Kd 0,3): Kp 4 → 11,2°, Kp 8 → 1,4°.
# Uji 2026-11-18 (Kp 16, Kd 3): geser menyimpang maks 2,3–5,2° (Kp 4: 11–17°), tidak berosilasi.
# Dikirim lewat tombol UI (GAIN:kp,kd,kpTurn, tersimpan di EEPROM).
HOLD_GAIN_RECOMMENDED = (16.0, 3.0, 3.0)

# ═══════════════════════════════════════════════════════════════
# Motor — Kecepatan default tiap state (0–255 PWM)
# ═══════════════════════════════════════════════════════════════
SEARCH_SPEED = 80       # Kecepatan rotasi saat SEARCH
APPROACH_SPEED = 60     # Kecepatan maju saat APPROACH
MANUAL_SPEED = 80       # Kecepatan translasi (maju/mundur/strafe) kontrol manual
# Satu titik ukur (uji 2026-11-18, maju 153 cm dalam 13,5 s pada PWM 100). Hanya untuk
# petunjuk "≈ cm/s" di UI; hubungan PWM → kecepatan di PWM lain BELUM diukur.
SPEED_CM_PER_S_AT_100 = 11.3
MANUAL_TURN = 70        # Kecepatan rotasi kontrol manual

# ═══════════════════════════════════════════════════════════════
# Servo — Sudut buka/tutup mekanisme pengumpul
# ═══════════════════════════════════════════════════════════════
# Dalam pulsa (mikrodetik), bukan sudut: pulsa langsung menentukan posisi tanduk
# servo, jadi nilai kalibrasi tetap sama walau pemetaan sudut di firmware berubah.
# BELUM dikalibrasi: cari nilainya di kartu "Kalibrasi Servo" (tab Kalibrasi).
# Nilai hasil kalibrasi disimpan ke SERVO_SETTINGS_FILE dan dimuat saat start.
SERVO_US_MIN = 500      # Batas aman pulsa (sama dengan firmware)
SERVO_US_MAX = 2500
SERVO_OPEN_US = 1000    # Pulsa posisi buka (µs)
SERVO_CLOSE_US = 2000   # Pulsa posisi tutup (µs)
SERVO_SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "servo_settings.json"
)
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
# Kalibrasi arah — disimpan di laptop (bukan di git) supaya bertahan restart
# ═══════════════════════════════════════════════════════════════
DRIVE_SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "drive_settings.json"
)

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
    "YOLO_CONF":        (0.05, 0.95, 0.05, "Confidence YOLO"),
    "WORLD_CONF":       (0.05, 0.95, 0.05, "Confidence YOLO-World"),
    # State machine
    "AREA_APPROACH":    (100, 5000, 50, "Area → APPROACH"),
    "STOP_DIST_CM":     (0.0, 60.0, 1.0, "Jarak Berhenti (cm)"),
    "CAM_FRONT_OFFSET_CM": (-5.0, 30.0, 0.5, "Kamera → Depan Robot (cm)"),
    "NEAR_VISIBLE_CM":  (10.0, 40.0, 1.0, "Batas Lihat Dekat (cm)"),
    "BLIND_PUSH_MAX_SEC": (0.5, 8.0, 0.5, "Maks Maju Buta (s)"),
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
    "SERVO_OPEN_US":    (500, 2500, 10, "Servo Buka (µs)"),
    "SERVO_CLOSE_US":   (500, 2500, 10, "Servo Tutup (µs)"),
    "SWEEP_DELAY":      (0.1, 2.0, 0.1, "Jeda Sweep (s)"),
    # Navigasi gyro & link
    "AIM_TOL_DEG":      (0.5, 10.0, 0.5, "Toleransi Bidik (°)"),
    "TURN_COMP_DEG":    (0.0, 3.0, 0.1, "Kompensasi TURN (°)"),
    "SEARCH_STEP_DEG":  (10, 50, 5, "Langkah SEARCH (°)"),
    "SETTLE_SEC":       (0.1, 1.5, 0.05, "Jeda Settle (s)"),
    "TURN_GUARD_SEC":   (2.0, 15.0, 0.5, "Batas Tunggu TURN (s)"),
    "TURN_GUARD_BASE_SEC": (1.0, 8.0, 0.5, "Dasar Tunggu TURN (s)"),
    "CONFIRM_FRAMES":   (1, 5, 1, "Frame Konfirmasi"),
    "LOST_FRAMES":      (1, 10, 1, "Frame Hilang → SEARCH"),
    "CAMERA_HFOV_DEG":  (30.0, 90.0, 0.1, "HFOV Kamera (°)"),
    "SNAPSHOT_INTERVAL": (0.0, 1.0, 0.05, "Jeda Snapshot (s)"),
}

# Param yang bertipe float (selain itu di-cast ke int saat update)
_FLOAT_PARAMS = {"KP_STEERING", "SWEEP_DELAY", "MOTION_HEARTBEAT", "YOLO_CONF", "WORLD_CONF",
                 "AIM_TOL_DEG", "TURN_COMP_DEG", "SETTLE_SEC", "CAMERA_HFOV_DEG",
                 "SNAPSHOT_INTERVAL", "TURN_GUARD_SEC", "TURN_GUARD_BASE_SEC",
                 "STOP_DIST_CM", "CAM_FRONT_OFFSET_CM", "NEAR_VISIBLE_CM", "BLIND_PUSH_MAX_SEC"}


def focal_px(width=None):
    """Panjang fokus (piksel) pada lebar frame kerja, dari HFOV terukur."""
    import math
    width = width or FRAME_WIDTH
    return (width / 2) / math.tan(math.radians(CAMERA_HFOV_DEG / 2))


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
