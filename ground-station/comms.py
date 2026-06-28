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
"""

import collections
import threading
import time
import cv2
import numpy as np
import requests
import config


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
        self._capture = None               # cv2.VideoCapture (webcam/video)
        self._open_ok = False              # hasil open kamera terakhir
        self._camera_scan = None           # hasil pindai kamera (list / None)
        self._stream_thread = None
        self._stream_running = False
        self._connected = False            # Sumber video aktif?

        # ── Kanal command (robot asli) ───────────────────────
        self._robot_ip = config.ROBOT_IP
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

    def set_drive(self, enabled, robot_ip=None):
        """Aktif/nonaktifkan pengiriman command ke robot asli."""
        self._drive_robot = bool(enabled)
        if robot_ip:
            self._robot_ip = robot_ip
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
            return self._esp32_ip
        if self._drive_robot:
            return self._robot_ip
        return None

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

        # Robot driving (status poll) aktif bila perlu kanal command
        if self._command_target() is not None:
            self._start_status_poll()
        return ok

    def disconnect(self):
        """Hentikan capture sumber video dan bersihkan resource."""
        self._stream_running = False
        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=3)
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._connected = False

    # ─────────────────────────────────────────────────────────
    # MJPEG stream dari ESP32-CAM
    # ─────────────────────────────────────────────────────────
    def _start_mjpeg_stream(self):
        """Mulai thread capture MJPEG stream dari ESP32-CAM."""
        # Cek ketersediaan ESP32 dulu
        try:
            url = f"http://{self._esp32_ip}:{config.CMD_PORT}/"
            resp = requests.get(url, timeout=config.STREAM_TIMEOUT)
            if resp.status_code != 200:
                self._last_error = f"ESP32 balas {resp.status_code}"
                return False
        except requests.RequestException as e:
            self._last_error = f"ESP32 tidak tersedia: {e}"
            return False

        self._connected = True
        self._last_error = None
        self._stream_running = True
        self._stream_thread = threading.Thread(
            target=self._mjpeg_capture_loop, daemon=True
        )
        self._stream_thread.start()
        return True

    def _mjpeg_capture_loop(self):
        """Loop baca MJPEG stream — parse boundary JPEG secara manual."""
        stream_url = f"http://{self._esp32_ip}:{config.STREAM_PORT}/stream"
        try:
            resp = requests.get(stream_url, stream=True,
                                timeout=config.STREAM_TIMEOUT)
            buffer = b""
            for chunk in resp.iter_content(chunk_size=4096):
                if not self._stream_running:
                    break
                buffer += chunk

                start = buffer.find(b"\xff\xd8")
                end = buffer.find(b"\xff\xd9")

                if start != -1 and end != -1 and end > start:
                    jpg_data = buffer[start:end + 2]
                    buffer = buffer[end + 2:]

                    frame = cv2.imdecode(
                        np.frombuffer(jpg_data, dtype=np.uint8),
                        cv2.IMREAD_COLOR,
                    )
                    if frame is not None:
                        with self._frame_lock:
                            self._frame = frame
                        self._update_fps()

        except requests.RequestException as e:
            self._last_error = f"Stream terputus: {e}"
            self._connected = False

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
        self._stream_running = True
        self._open_ok = False
        open_event = threading.Event()
        self._stream_thread = threading.Thread(
            target=self._capture_loop, args=(target, open_event), daemon=True
        )
        self._stream_thread.start()
        # Tunggu hasil open (maks ~4s) — one-time, hanya saat ganti sumber.
        open_event.wait(timeout=4.0)
        return self._open_ok

    def _capture_loop(self, target, open_event=None):
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
        while self._stream_running:
            ret, frame = cap.read()
            if ret and frame is not None:
                fail_count = 0
                with self._frame_lock:
                    self._frame = frame
                self._update_fps()
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
                mv = self._clamp_motion(*motion)
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
        """Parse string 'TEL:heading,vbat' dari Arduino."""
        if not tel or not tel.startswith("TEL:"):
            return
        try:
            parts = tel[4:].split(",")
            self._heading = float(parts[0])
            if len(parts) > 1:
                self._vbat = float(parts[1])
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
            "fps": self._fps,
            "heading": round(self._heading, 1),
            "vbat": round(self._vbat, 2),
            "rssi": self._rssi,
            "last_error": self._last_error,
        }
