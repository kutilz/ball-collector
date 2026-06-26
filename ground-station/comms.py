"""
comms.py — Komunikasi dengan ESP32-CAM.

Fitur:
  • Capture frame dari MJPEG stream ESP32-CAM via HTTP
  • Kirim perintah motor via HTTP GET /cmd
  • Kirim perintah servo via HTTP GET /cmd (prefix SERVO)
  • Fallback ke webcam laptop saat DEMO_MODE aktif
"""

import threading
import time
import cv2
import numpy as np
import requests
import config


class RobotComms:
    """Kelas untuk mengelola komunikasi dengan robot ESP32-CAM."""

    def __init__(self):
        self._frame = None                 # Frame terbaru dari stream
        self._frame_lock = threading.Lock()
        self._stream_thread = None
        self._stream_running = False
        self._connected = False
        self._demo_mode = config.DEMO_MODE
        self._webcam = None                # VideoCapture webcam (demo)
        self._esp32_ip = config.ESP32_CAM_IP
        self._last_error = None
        self._fps = 0.0
        self._frame_count = 0
        self._fps_timer = time.time()

    # ─────────────────────────────────────────────────────────
    # Koneksi & stream
    # ─────────────────────────────────────────────────────────
    def connect(self, ip=None):
        """
        Coba koneksi ke ESP32-CAM. Jika gagal dan DEMO_MODE aktif,
        fallback ke webcam laptop.
        """
        if ip:
            self._esp32_ip = ip

        # Hentikan stream yang sedang berjalan
        self.disconnect()

        # Coba koneksi ke ESP32-CAM terlebih dahulu
        if not self._demo_mode:
            try:
                url = f"http://{self._esp32_ip}:{config.CMD_PORT}/"
                resp = requests.get(url, timeout=config.STREAM_TIMEOUT)
                if resp.status_code == 200:
                    self._start_mjpeg_stream()
                    self._connected = True
                    self._last_error = None
                    return True
            except requests.RequestException as e:
                self._last_error = f"ESP32 tidak tersedia: {e}"

        # Fallback ke webcam laptop (demo mode)
        return self._start_webcam()

    def disconnect(self):
        """Putuskan koneksi dan bersihkan resource."""
        self._stream_running = False
        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=3)
        if self._webcam is not None:
            self._webcam.release()
            self._webcam = None
        self._connected = False

    # ─────────────────────────────────────────────────────────
    # MJPEG stream dari ESP32-CAM
    # ─────────────────────────────────────────────────────────
    def _start_mjpeg_stream(self):
        """Mulai thread capture MJPEG stream dari ESP32-CAM."""
        self._stream_running = True
        self._stream_thread = threading.Thread(
            target=self._mjpeg_capture_loop, daemon=True
        )
        self._stream_thread.start()

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

                # Cari header dan footer JPEG
                start = buffer.find(b"\xff\xd8")
                end = buffer.find(b"\xff\xd9")

                if start != -1 and end != -1 and end > start:
                    jpg_data = buffer[start:end + 2]
                    buffer = buffer[end + 2:]

                    # Decode JPEG → frame BGR
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
    # Webcam fallback (demo mode)
    # ─────────────────────────────────────────────────────────
    def _start_webcam(self):
        """Buka webcam laptop sebagai sumber frame alternatif."""
        try:
            self._webcam = cv2.VideoCapture(0)
            if not self._webcam.isOpened():
                self._last_error = "Webcam tidak dapat dibuka"
                return False
            self._connected = True
            self._demo_mode = True
            self._last_error = None

            # Mulai thread capture webcam
            self._stream_running = True
            self._stream_thread = threading.Thread(
                target=self._webcam_capture_loop, daemon=True
            )
            self._stream_thread.start()
            return True

        except Exception as e:
            self._last_error = f"Gagal buka webcam: {e}"
            return False

    def _webcam_capture_loop(self):
        """Loop baca frame dari webcam laptop."""
        while self._stream_running and self._webcam is not None:
            ret, frame = self._webcam.read()
            if ret and frame is not None:
                with self._frame_lock:
                    self._frame = frame
                self._update_fps()
            else:
                time.sleep(0.01)
        # Pastikan webcam dilepas saat loop selesai
        if self._webcam is not None:
            self._webcam.release()
            self._webcam = None

    # ─────────────────────────────────────────────────────────
    # Ambil frame terbaru
    # ─────────────────────────────────────────────────────────
    def get_frame(self):
        """Kembalikan frame BGR terbaru, atau None jika belum ada."""
        with self._frame_lock:
            return self._frame.copy() if self._frame is not None else None

    # ─────────────────────────────────────────────────────────
    # Kirim perintah ke ESP32-CAM
    # ─────────────────────────────────────────────────────────
    def send_command(self, vx, vy, omega):
        """
        Kirim perintah motor ke ESP32 via HTTP GET.
        Format: /cmd?vx=<>&vy=<>&omega=<>
        """
        if self._demo_mode:
            return True  # Di demo mode, perintah diabaikan

        try:
            url = (
                f"http://{self._esp32_ip}:{config.CMD_PORT}/cmd"
                f"?vx={int(vx)}&vy={int(vy)}&omega={int(omega)}"
            )
            resp = requests.get(url, timeout=config.CMD_TIMEOUT)
            return resp.status_code == 200
        except requests.RequestException as e:
            self._last_error = f"Gagal kirim perintah: {e}"
            return False

    def send_servo(self, angle):
        """
        Kirim perintah servo ke ESP32 via HTTP GET.
        Format: /cmd?servo=<angle>
        """
        if self._demo_mode:
            return True

        try:
            url = (
                f"http://{self._esp32_ip}:{config.CMD_PORT}/cmd"
                f"?servo={int(angle)}"
            )
            resp = requests.get(url, timeout=config.CMD_TIMEOUT)
            return resp.status_code == 200
        except requests.RequestException as e:
            self._last_error = f"Gagal kirim servo: {e}"
            return False

    # ─────────────────────────────────────────────────────────
    # Hitung FPS
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
    # Status koneksi untuk telemetri
    # ─────────────────────────────────────────────────────────
    def get_status(self):
        """Kembalikan dictionary status koneksi."""
        return {
            "connected": self._connected,
            "demo_mode": self._demo_mode,
            "esp32_ip": self._esp32_ip,
            "fps": self._fps,
            "last_error": self._last_error,
        }
