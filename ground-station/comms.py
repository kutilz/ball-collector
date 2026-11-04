"""
comms.py — Komunikasi & sumber video robot pengumpul bola.

Dua kanal yang DIPISAH:

  1. SUMBER VIDEO (frame untuk vision):
       • "esp32"  → MJPEG stream dari ESP32-CAM
       • "webcam" → webcam laptop
       • "video"  → file video (.mp4/.avi), bisa di-loop

  2. KANAL COMMAND (kemudikan robot asli):
       • Command motor/servo dikirim ke ESP32 (ROBOT_IP) lewat HTTP GET
         /cmd?q=CMD:vx,vy,omega  dan  /cmd?q=SERVO:sudut
       • Aktif bila sumber = esp32, ATAU drive_robot = True (robot jalan
         beneran walau vision pakai webcam/video).

Pemisahan ini memungkinkan: deteksi di laptop (webcam/video) sambil
robot fisik tetap bergerak via ESP32.

IP "auto" (atau kosong) = cari robot otomatis: mDNS ballcollector.local dulu,
lalu scan subnet /24 laptop untuk perangkat yang menjawab /tel.
"""

import collections
import concurrent.futures
import json
import socket
import threading
import time
import cv2
import numpy as np
import requests
import config

AUTO_IP = "auto"

JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"
MAX_MJPEG_BUFFER = 2 * 1024 * 1024  # Frame QVGA cuma puluhan KB


def _is_auto(ip):
    return not ip or ip.strip().lower() == AUTO_IP


def _extract_jpegs(buffer):
    """Pisahkan JPEG utuh dari buffer MJPEG. Return (daftar_jpeg, sisa_buffer).

    EOI dicari SETELAH SOI: byte FF D9 nyasar sebelum frame berikutnya dibuang.
    Kalau tidak, EOI nyasar itu terus ditemukan lebih dulu daripada SOI dan
    stream beku selamanya walau datanya masih mengalir.
    """
    jpegs = []
    while True:
        start = buffer.find(JPEG_SOI)
        if start == -1:
            return jpegs, buffer[-1:]  # Byte terakhir bisa jadi FF dari SOI terpotong
        end = buffer.find(JPEG_EOI, start + 2)
        if end == -1:
            rest = buffer[start:]
            return jpegs, b"" if len(rest) > MAX_MJPEG_BUFFER else rest
        jpegs.append(buffer[start:end + 2])
        buffer = buffer[end + 2:]


def _is_robot(host, timeout):
    """True kalau host menjawab /tel seperti firmware ESP32-CAM robot."""
    try:
        resp = requests.get(f"http://{host}:{config.CMD_PORT}/tel", timeout=timeout)
        return resp.status_code == 200 and "tel" in resp.json()
    except (requests.RequestException, ValueError):
        return False


def _local_subnets():
    """Prefix /24 interface laptop; interface default route diurutkan pertama."""
    ips = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Tidak kirim paket, cuma pilih interface
            ips.append(s.getsockname()[0])
    except OSError:
        pass
    try:
        ips += socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        pass
    subnets = []
    for ip in ips:
        if ip.startswith(("127.", "169.254.")):
            continue
        base = ip.rsplit(".", 1)[0]
        if base not in subnets:
            subnets.append(base)
    return subnets


def discover_robot(hint=None):
    """Cari IP ESP32-CAM robot. hint = IP terakhir yang diketahui (dicek dulu)."""
    if hint and not _is_auto(hint) and _is_robot(hint, 1.0):
        return hint
    try:
        ip = socket.gethostbyname(config.ROBOT_HOSTNAME)
        if _is_robot(ip, 2.0):
            return ip
    except OSError:
        pass
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as ex:
        for base in _local_subnets():
            hosts = [f"{base}.{i}" for i in range(1, 255)]
            for host, ok in zip(hosts, ex.map(lambda h: _is_robot(h, 0.5), hosts)):
                if ok:
                    return host
    return None


class RobotComms:
    """Mengelola sumber video + kanal command ke robot ESP32-CAM."""

    VALID_SOURCES = ("esp32", "webcam", "video")

    def __init__(self):
        # ── Sumber video ─────────────────────────────────────
        self._source = config.VIDEO_SOURCE
        self._video_file = config.VIDEO_FILE
        self._esp32_ip = config.ESP32_CAM_IP

        self._webcam_index = config.WEBCAM_INDEX
        self._frame = None
        self._frame_lock = threading.Lock()
        self._frame_time = 0.0             # Waktu frame terakhir diterima
        self._capture = None               # cv2.VideoCapture (webcam/video)
        self._open_ok = False              # hasil open kamera terakhir
        self._camera_scan = None           # hasil pindai kamera (list / None)
        self._stream_thread = None
        self._stream_stop = threading.Event()  # Sinyal berhenti thread sumber aktif
        self._stream_is_mjpeg = False
        self._connected = False            # Sumber video aktif?

        # ── Kalibrasi arah ───────────────────────────────────
        self._invert_vy = False            # Balik sumbu geser kiri/kanan
        self._invert_omega = False         # Balik sumbu putar
        self._wheel_flip = None            # Mask flip roda dari Arduino (FL=1,FR=2,RL=4,RR=8)
        self._wheel_flip_supported = None  # None = belum ada telemetri
        self._wheel_flip_hold_until = 0.0  # Abaikan telemetri lama setelah mengirim flip
        self._load_drive_settings()

        # ── Kanal command (robot asli) ───────────────────────
        self._robot_ip = config.ROBOT_IP
        self._last_found_ip = None         # Hasil discovery terakhir (dicek dulu)
        self._drive_robot = config.DRIVE_ROBOT
        self._robot_online = False         # ESP32 command terakhir sukses?

        # ── Command worker (OS thread asli, NON-BLOCKING ke hub) ─────────
        # SEMUA HTTP ke robot terjadi di thread ini, supaya handler SocketIO
        # & loop utama (green-thread eventlet) tidak pernah ter-block oleh
        # requests yang lambat/timeout. Operator selalu bisa pencet STOP.
        self._session = requests.Session()         # keep-alive ke ESP32
        self._cmd_lock = threading.Lock()
        self._pending_motion = None                # (vx,vy,omega) terbaru / None
        self._pending_motion_action = None         # label aksi utk ack / None
        self._pending_oneshots = collections.deque()  # (q, action) FIFO
        self._cmd_event = threading.Event()        # bangunkan worker
        self._cmd_worker = None
        self._cmd_worker_running = False
        self._ack_queue = collections.deque(maxlen=50)  # feedback utk UI
        self._last_motion = (0, 0, 0)              # motion aktif (utk heartbeat)
        self._last_motion_time = 0.0

        # ── Telemetri dari ESP32 / Arduino ───────────────────
        self._status_thread = None
        self._status_running = False
        self._heading = 0.0                # ° dari MPU6050
        self._vbat = 0.0                   # Tegangan baterai (placeholder)
        self._rssi = 0                     # Kekuatan sinyal WiFi ESP32

        # ── FPS & error ──────────────────────────────────────
        self._last_error = None
        self._fps = 0.0
        self._frame_count = 0
        self._fps_timer = time.time()

    # ═════════════════════════════════════════════════════════
    # Pengaturan sumber & driving
    # ═════════════════════════════════════════════════════════
    def set_source(self, source, path=None, esp32_ip=None, webcam_index=None):
        """Ganti sumber video lalu mulai ulang capture."""
        if source not in self.VALID_SOURCES:
            self._last_error = f"Sumber tidak dikenal: {source}"
            return False
        self._source = source
        if path is not None:
            self._video_file = path
        if esp32_ip:
            self._esp32_ip = esp32_ip
        if webcam_index is not None:
            try:
                self._webcam_index = int(webcam_index)
            except (TypeError, ValueError):
                pass
        return self.start_source()

    def _resolve_auto(self):
        """Isi IP yang masih 'auto' dengan hasil discovery. False kalau tidak ketemu.

        Blocking beberapa detik (seperti cek awal stream); hanya dipanggil saat
        connect/aktifkan drive, bukan di jalur command.
        """
        if not (_is_auto(self._esp32_ip) or _is_auto(self._robot_ip)):
            return True
        found = discover_robot(hint=self._last_found_ip)
        if not found:
            self._last_error = (f"Robot tidak ditemukan (coba {config.ROBOT_HOSTNAME} "
                                "dan scan subnet). Laptop & robot satu WiFi?")
            return False
        self._last_found_ip = found
        if _is_auto(self._esp32_ip):
            self._esp32_ip = found
        if _is_auto(self._robot_ip):
            self._robot_ip = found
        return True

    def set_drive(self, enabled, robot_ip=None):
        """Aktif/nonaktifkan pengiriman command ke robot asli."""
        self._drive_robot = bool(enabled)
        if robot_ip:
            self._robot_ip = robot_ip
        if self._drive_robot and _is_auto(self._robot_ip):
            # Pencarian makan beberapa detik; jangan memblokir tombol STOP.
            threading.Thread(target=self._resolve_auto, daemon=True).start()
        if self._drive_robot:
            self._ensure_command_worker()
            self._start_status_poll()
        else:
            # Nonaktifkan drive (failsafe berlapis):
            #  1) STOP eksplisit selagi kanal masih ada (mis. source=esp32),
            #  2) hentikan heartbeat seketika (_last_motion=0) sehingga tak ada
            #     CMD lagi → watchdog Arduino menstop motor dalam 500ms.
            self.send_command(0, 0, 0)
            with self._cmd_lock:
                self._last_motion = (0, 0, 0)
            self._robot_online = False
        return self._drive_robot

    def _command_target(self):
        """IP tujuan command, atau None jika command tidak boleh dikirim."""
        if self._source == "esp32":
            target = self._esp32_ip
        elif self._drive_robot:
            target = self._robot_ip
        else:
            return None
        return None if _is_auto(target) else target  # 'auto' belum ketemu

    # ═════════════════════════════════════════════════════════
    # Mulai / hentikan sumber video
    # ═════════════════════════════════════════════════════════
    def connect(self, ip=None):
        """Kompat lama: set IP (kalau ada) lalu mulai sumber aktif."""
        if ip:
            self._esp32_ip = ip
            self._robot_ip = ip
        return self.start_source()

    def start_source(self):
        """Mulai capture sesuai sumber yang dipilih."""
        self.disconnect()
        # Command worker selalu hidup (idle bila tak ada perintah) agar
        # heartbeat & STOP failsafe siap kapan pun.
        self._ensure_command_worker()

        if self._source == "esp32":
            ok = self._start_mjpeg_stream()
        elif self._source == "video":
            ok = self._start_capture(self._video_file)
        else:  # webcam
            ok = self._start_capture(self._webcam_index)

        # Robot driving (status poll) aktif bila perlu kanal command. Sumber
        # esp32 selalu perlu; IP 'auto' baru terisi setelah thread stream mencari.
        if self._source == "esp32" or self._command_target() is not None:
            self._start_status_poll()
        return ok

    def disconnect(self):
        """Hentikan capture sumber video dan bersihkan resource."""
        self._stream_stop.set()
        # Kamera lokal wajib dilepas dulu sebelum dibuka lagi. Thread MJPEG tidak
        # perlu ditunggu di sini (thread baru yang menunggunya) agar hub tak terblokir.
        if (not self._stream_is_mjpeg and self._stream_thread
                and self._stream_thread.is_alive()):
            self._stream_thread.join(timeout=3)
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._connected = False
        self._frame_time = 0.0

    # ─────────────────────────────────────────────────────────
    # MJPEG stream dari ESP32-CAM
    # ─────────────────────────────────────────────────────────
    def _start_mjpeg_stream(self):
        """Mulai thread stream. Non-blocking: hasil koneksi tampil lewat status."""
        self._last_error = None
        self._stream_is_mjpeg = True
        self._stream_stop = threading.Event()
        self._stream_thread = threading.Thread(
            target=self._mjpeg_capture_loop,
            args=(self._stream_stop, self._stream_thread),
            daemon=True,
        )
        self._stream_thread.start()
        return True

    def _mjpeg_capture_loop(self, stop, prev_thread=None):
        """Jaga stream tetap hidup: sambung ulang setiap kali putus atau macet."""
        # Server stream ESP32 hanya melayani satu klien; tutup koneksi lama dulu.
        if prev_thread is not None and prev_thread.is_alive():
            prev_thread.join(timeout=config.STREAM_READ_TIMEOUT + 1)

        while not stop.is_set():
            if not _is_auto(self._esp32_ip) or self._resolve_auto():
                try:
                    self._read_mjpeg_stream(stop)
                except Exception as e:  # noqa: BLE001 — thread ini tak boleh mati diam-diam
                    self._last_error = f"Stream terputus: {e}"
            if not stop.is_set():
                self._connected = False
                stop.wait(config.STREAM_RECONNECT_DELAY)

    def _read_mjpeg_stream(self, stop):
        """Baca satu koneksi MJPEG sampai putus, macet, atau diminta berhenti."""
        url = f"http://{self._esp32_ip}:{config.STREAM_PORT}/stream"
        timeout = (config.STREAM_TIMEOUT, config.STREAM_READ_TIMEOUT)
        with requests.get(url, stream=True, timeout=timeout) as resp:
            if resp.status_code != 200:
                self._last_error = f"Stream ESP32 balas {resp.status_code}"
                return
            buffer = b""
            last_frame = time.time()
            for chunk in resp.iter_content(chunk_size=4096):
                if stop.is_set():
                    return
                jpegs, buffer = _extract_jpegs(buffer + chunk)
                # Hanya frame terbaru yang berguna; yang lain cuma menambah latensi.
                for jpg in reversed(jpegs):
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8),
                                         cv2.IMREAD_COLOR)
                    if frame is not None:
                        self._store_frame(frame)
                        self._connected = True
                        self._last_error = None
                        last_frame = time.time()
                        break
                if time.time() - last_frame > config.STREAM_READ_TIMEOUT:
                    self._last_error = "Data stream masuk tapi tidak ada gambar valid"
                    return
            self._last_error = "Stream ditutup oleh robot"

    # ─────────────────────────────────────────────────────────
    # Capture webcam / file video (cv2.VideoCapture)
    # ─────────────────────────────────────────────────────────
    def _open_videocapture(self, target):
        """
        Buka cv2.VideoCapture dengan beberapa backend (Windows-friendly).

        Webcam di Windows bisa gagal di salah satu backend: MSMF (default)
        kadang lambat/gagal, DSHOW kadang tak bisa capture-by-index. Jadi kita
        coba beberapa backend berurutan dan pakai yang pertama berhasil membuka
        DAN benar-benar bisa membaca 1 frame (isOpened() saja kadang bohong).
        """
        if isinstance(target, int):
            # Default (CAP_ANY) dulu — bersih di mesin yang MSMF-nya normal;
            # DSHOW sebagai fallback untuk mesin yang MSMF-nya bermasalah.
            for backend in (cv2.CAP_ANY, cv2.CAP_DSHOW):
                cap = cv2.VideoCapture(target, backend)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
                    ok, _ = cap.read()  # validasi: benar-benar bisa baca frame
                    if ok:
                        return cap
                cap.release()
            return None
        # File video — backend default sudah memadai
        cap = cv2.VideoCapture(target)
        return cap if cap.isOpened() else None

    # ── Pindai kamera tersedia (NON-BLOCKING via thread asli) ────────────
    def scan_cameras_async(self, max_index=5):
        """
        Mulai pindai index webcam 0..max_index di thread asli (cv2 blocking
        TIDAK boleh di hub eventlet). Hasil diambil via drain_camera_scan().
        """
        def _scan():
            found = []
            for idx in range(max_index + 1):
                # Lewati kamera yang sedang dipakai sebagai sumber aktif
                if (self._source == "webcam" and idx == self._webcam_index
                        and self._capture is not None):
                    found.append(idx)
                    continue
                cap = self._open_videocapture(idx)
                if cap is not None:
                    found.append(idx)
                    cap.release()
            self._camera_scan = found

        self._camera_scan = None
        threading.Thread(target=_scan, daemon=True).start()

    def drain_camera_scan(self):
        """Ambil hasil pindai sekali (list index), atau None bila belum siap."""
        result = self._camera_scan
        if result is not None:
            self._camera_scan = None
        return result

    def _start_capture(self, target):
        """
        Mulai thread capture. Kamera dibuka DI DALAM thread itu (open + read
        di thread yang sama).

        Penting di Windows: backend MSMF sensitif thread/COM — membuka kamera di
        satu thread lalu membacanya di thread lain bikin grabFrame gagal
        (error -1072873821). Maka open dilakukan di thread capture. _start_capture
        menunggu hasil open singkat (bounded) agar bisa lapor sukses/gagal ke UI.
        """
        self._stream_is_mjpeg = False
        self._stream_stop = threading.Event()
        self._open_ok = False
        open_event = threading.Event()
        self._stream_thread = threading.Thread(
            target=self._capture_loop,
            args=(target, self._stream_stop, open_event),
            daemon=True,
        )
        self._stream_thread.start()
        # Tunggu hasil open (maks ~4s) — one-time, hanya saat ganti sumber.
        open_event.wait(timeout=4.0)
        return self._open_ok

    def _capture_loop(self, target, stop, open_event=None):
        """Buka kamera (di thread INI) lalu loop baca frame."""
        cap = self._open_videocapture(target)
        if cap is None:
            if isinstance(target, int):
                label = f"webcam #{target} (cek izin kamera / dipakai app lain)"
            else:
                label = f"file '{target}'"
            self._last_error = f"Tidak bisa membuka {label}"
            self._connected = False
            self._open_ok = False
            if open_event:
                open_event.set()
            return

        self._capture = cap
        self._connected = True
        self._last_error = None
        self._open_ok = True
        if open_event:
            open_event.set()

        is_file = self._source == "video"
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = (1.0 / fps) if (is_file and fps and fps > 1) else 0.0

        fail_count = 0
        while not stop.is_set():
            ret, frame = cap.read()
            if ret and frame is not None:
                fail_count = 0
                self._store_frame(frame)
                if frame_delay:
                    time.sleep(frame_delay)
            elif is_file and config.VIDEO_LOOP:
                # File video habis → ulang dari awal
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                # Webcam gagal grab — beri tahu bila berkepanjangan (device
                # dicabut / berhenti streaming), supaya user bisa ganti index.
                fail_count += 1
                if not is_file and fail_count == 50:
                    self._last_error = ("Webcam berhenti mengirim frame — "
                                        "coba index kamera lain")
                    self._connected = False
                time.sleep(0.01)

        cap.release()
        if self._capture is cap:
            self._capture = None

    # ─────────────────────────────────────────────────────────
    # Ambil frame terbaru
    # ─────────────────────────────────────────────────────────
    def get_frame(self):
        """Kembalikan frame BGR terbaru, atau None jika belum ada."""
        with self._frame_lock:
            return self._frame.copy() if self._frame is not None else None

    def _store_frame(self, frame):
        with self._frame_lock:
            self._frame = frame
            self._frame_time = time.time()
        self._update_fps()

    def is_camera_live(self):
        """True kalau frame terbaru masih segar (bukan gambar beku)."""
        return time.time() - self._frame_time <= config.FRAME_STALE_SEC

    # ═════════════════════════════════════════════════════════
    # Kalibrasi arah
    # ═════════════════════════════════════════════════════════
    def _load_drive_settings(self):
        try:
            with open(config.DRIVE_SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self._invert_vy = bool(data.get("invert_vy", False))
            self._invert_omega = bool(data.get("invert_omega", False))
        except (OSError, ValueError, AttributeError):
            pass  # Belum pernah disimpan / file rusak: pakai default

    def set_axis_invert(self, axis, inverted):
        """Balik sumbu 'vy' atau 'omega' dan simpan. False kalau axis tak dikenal."""
        if axis == "vy":
            self._invert_vy = bool(inverted)
        elif axis == "omega":
            self._invert_omega = bool(inverted)
        else:
            return False
        try:
            with open(config.DRIVE_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"invert_vy": self._invert_vy,
                           "invert_omega": self._invert_omega}, f)
        except OSError as e:
            self._last_error = f"Gagal menyimpan kalibrasi arah: {e}"
        return True

    def send_wheel_flip(self, mask, action=None):
        """Kirim mask flip roda ke Arduino (disimpan di EEPROM-nya). Non-blocking."""
        if self._command_target() is None:
            return "skipped"
        self._ensure_command_worker()
        with self._cmd_lock:
            self._pending_oneshots.append((f"FLIP:{mask}", action))
        # Telemetri berikutnya masih bisa membawa nilai lama; tahan sebentar.
        # Kalau pengiriman gagal, nilai asli muncul lagi setelah waktu ini.
        self._wheel_flip = mask
        self._wheel_flip_hold_until = time.time() + 2.5
        self._cmd_event.set()
        return "queued"

    def get_drive_calibration(self):
        return {
            "invert_vy": self._invert_vy,
            "invert_omega": self._invert_omega,
            "wheel_flip": self._wheel_flip,
            "wheel_flip_supported": self._wheel_flip_supported,
        }

    # ═════════════════════════════════════════════════════════
    # Kanal command ke ESP32 — NON-BLOCKING (worker thread asli)
    # ═════════════════════════════════════════════════════════
    # API publik (send_command/servo/collect) hanya MENGANTRI lalu langsung
    # kembali — TIDAK pernah melakukan HTTP di thread pemanggil. Status string:
    #   "skipped" → tak ada robot tujuan (mis. webcam tanpa drive)
    #   "queued"  → masuk antrian; hasil ok/error menyusul via drain_acks()
    # HTTP nyata + ok/error ditentukan di _command_worker_loop.

    @staticmethod
    def _clamp(v, lo, hi):
        return lo if v < lo else (hi if v > hi else v)

    def _clamp_motion(self, vx, vy, omega):
        """Guardrail: batasi magnitudo ke ±SAFETY_MAX_PWM sebelum dikirim."""
        cap = int(config.SAFETY_MAX_PWM)
        return (self._clamp(int(vx), -cap, cap),
                self._clamp(int(vy), -cap, cap),
                self._clamp(int(omega), -cap, cap))

    def _apply_axis_invert(self, vx, vy, omega):
        """Terapkan kalibrasi sumbu ke semua perintah gerak (manual & otomatis)."""
        return (vx,
                -vy if self._invert_vy else vy,
                -omega if self._invert_omega else omega)

    def send_command(self, vx, vy, omega, action=None):
        """Antri perintah motor (coalesced: terbaru menang). Non-blocking."""
        if self._command_target() is None:
            return "skipped"
        self._ensure_command_worker()
        with self._cmd_lock:
            self._pending_motion = (int(vx), int(vy), int(omega))
            if action:
                self._pending_motion_action = action
        self._cmd_event.set()
        return "queued"

    def send_servo(self, angle, action=None):
        """Antri perintah servo (one-shot FIFO). Non-blocking."""
        if self._command_target() is None:
            return "skipped"
        self._ensure_command_worker()
        angle = self._clamp(int(angle), 0, 180)
        with self._cmd_lock:
            self._pending_oneshots.append((f"SERVO:{angle}", action))
        self._cmd_event.set()
        return "queued"

    def send_collect(self, action=None):
        """Antri sekuens collect (one-shot FIFO). Non-blocking."""
        if self._command_target() is None:
            return "skipped"
        self._ensure_command_worker()
        with self._cmd_lock:
            self._pending_oneshots.append(("COLLECT", action))
        self._cmd_event.set()
        return "queued"

    # ── Worker thread: satu-satunya tempat HTTP perintah dijalankan ──────
    def _ensure_command_worker(self):
        """Mulai command worker bila belum jalan (idempotent)."""
        if self._cmd_worker_running:
            return
        self._cmd_worker_running = True
        self._cmd_worker = threading.Thread(
            target=self._command_worker_loop, daemon=True
        )
        self._cmd_worker.start()

    def _http_send(self, q):
        """HTTP GET /cmd?q=<q> — BLOCKING, hanya dipanggil dari worker thread."""
        target = self._command_target()
        if target is None:
            return "skipped"
        try:
            url = f"http://{target}:{config.CMD_PORT}/cmd"
            resp = self._session.get(url, params={"q": q},
                                     timeout=config.CMD_TIMEOUT)
            self._robot_online = resp.status_code == 200
            if not self._robot_online:
                self._last_error = f"Robot balas {resp.status_code}"
                return "error"
            return "ok"
        except requests.RequestException as e:
            self._robot_online = False
            self._last_error = f"Gagal kirim perintah: {e}"
            return "error"

    def _push_ack(self, action, status):
        """Catat feedback utk UI (hanya untuk aksi eksplisit ber-label)."""
        if not action:
            return
        with self._cmd_lock:
            self._ack_queue.append({"action": action, "status": status})

    def drain_acks(self):
        """Ambil & kosongkan antrian feedback (dipanggil dari loop utama)."""
        with self._cmd_lock:
            if not self._ack_queue:
                return []
            acks = list(self._ack_queue)
            self._ack_queue.clear()
        return acks

    def _command_worker_loop(self):
        """
        Loop worker: proses one-shot (servo/collect) lalu motion (coalesced).
        Bila idle & motion terakhir non-nol → HEARTBEAT: kirim ulang agar
        watchdog Arduino (500ms) tidak menstop motor saat tombol ditahan.
        """
        while self._cmd_worker_running:
            # Bangun saat ada perintah, atau tiap MOTION_HEARTBEAT utk heartbeat.
            self._cmd_event.wait(timeout=config.MOTION_HEARTBEAT)
            self._cmd_event.clear()

            # 1. One-shots (servo/collect) — berurutan, tak boleh hilang.
            while True:
                with self._cmd_lock:
                    item = (self._pending_oneshots.popleft()
                            if self._pending_oneshots else None)
                if item is None:
                    break
                q, action = item
                self._push_ack(action, self._http_send(q))

            # 2. Motion — kirim yang terbaru (coalesced) atau heartbeat.
            with self._cmd_lock:
                motion = self._pending_motion
                action = self._pending_motion_action
                self._pending_motion = None
                self._pending_motion_action = None

            now = time.time()
            if motion is not None:
                mv = self._apply_axis_invert(*self._clamp_motion(*motion))
                # Catat intent SEBELUM kirim: heartbeat tahu motion terkini walau
                # HTTP ini lambat/gagal, dan akan retry motion yang sama.
                self._last_motion = mv
                self._last_motion_time = now
                status = self._http_send(f"CMD:{mv[0]},{mv[1]},{mv[2]}")
                self._push_ack(action, status)
            elif (self._command_target() is not None
                  and self._last_motion != (0, 0, 0)
                  and now - self._last_motion_time >= config.MOTION_HEARTBEAT):
                # Heartbeat senyap (tanpa ack) — suapi watchdog Arduino.
                mv = self._last_motion
                self._http_send(f"CMD:{mv[0]},{mv[1]},{mv[2]}")
                self._last_motion_time = now

        # Worker berhenti → best-effort STOP (failsafe).
        self._http_send("CMD:0,0,0")

    # ═════════════════════════════════════════════════════════
    # Polling /status ESP32 → telemetri Arduino (heading, vbat, rssi)
    # ═════════════════════════════════════════════════════════
    def _start_status_poll(self):
        """Mulai thread polling /status (idempotent)."""
        if self._status_running:
            return
        self._status_running = True
        self._status_thread = threading.Thread(
            target=self._status_poll_loop, daemon=True
        )
        self._status_thread.start()

    def _status_poll_loop(self):
        """Ambil /status ESP32 secara berkala, parse telemetri Arduino."""
        while self._status_running:
            target = self._command_target()
            if target is not None:
                try:
                    url = f"http://{target}:{config.CMD_PORT}/status"
                    resp = requests.get(url, timeout=config.CMD_TIMEOUT)
                    if resp.status_code == 200:
                        data = resp.json()
                        self._rssi = int(data.get("rssi", 0))
                        self._robot_online = True
                        self._parse_arduino_tel(data.get("arduino_telemetry", ""))
                except (requests.RequestException, ValueError):
                    self._robot_online = False
            time.sleep(config.STATUS_POLL_INTERVAL)

    def _parse_arduino_tel(self, tel):
        """Parse 'TEL:heading,vbat,rate,target,hold,turn,sign[,flip]' dari Arduino."""
        if not tel or not tel.startswith("TEL:"):
            return
        try:
            parts = tel[4:].split(",")
            self._heading = float(parts[0])
            if len(parts) > 1:
                self._vbat = float(parts[1])
            # Firmware lama tidak mengirim field flip.
            self._wheel_flip_supported = len(parts) > 7
            if len(parts) > 7 and time.time() >= self._wheel_flip_hold_until:
                self._wheel_flip = int(parts[7]) & 0x0F
        except (ValueError, IndexError):
            pass

    # ─────────────────────────────────────────────────────────
    # FPS
    # ─────────────────────────────────────────────────────────
    def _update_fps(self):
        """Perbarui kalkulasi FPS setiap detik."""
        self._frame_count += 1
        elapsed = time.time() - self._fps_timer
        if elapsed >= 1.0:
            self._fps = round(self._frame_count / elapsed, 1)
            self._frame_count = 0
            self._fps_timer = time.time()

    # ─────────────────────────────────────────────────────────
    # Status untuk telemetri UI
    # ─────────────────────────────────────────────────────────
    def get_status(self):
        """Kembalikan dictionary status koneksi & telemetri."""
        return {
            "connected": self._connected,
            "source": self._source,
            "demo_mode": self._source != "esp32",
            "video_file": self._video_file,
            "webcam_index": self._webcam_index,
            "esp32_ip": self._esp32_ip,
            "robot_ip": self._robot_ip,
            "drive_robot": self._drive_robot,
            "robot_online": self._robot_online,
            "camera_live": self.is_camera_live(),
            "drive_cal": self.get_drive_calibration(),
            "fps": self._fps if self.is_camera_live() else 0,
            "heading": round(self._heading, 1),
            "vbat": round(self._vbat, 2),
            "rssi": self._rssi,
            "last_error": self._last_error,
        }
