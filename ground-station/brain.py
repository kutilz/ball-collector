"""
brain.py — State machine otak robot pengumpul bola.

States:
  IDLE     → Menunggu perintah start (diam)
  SEARCH   → Berputar mencari bola
  APPROACH → Mendekati bola dengan P-controller steering
  COLLECT  → Berhenti, aktifkan servo pengumpul, lalu kembali SEARCH
"""

import time
import config


class StateMachine:
    """Finite State Machine untuk navigasi dan pengumpulan bola."""

    # Daftar state yang valid
    STATES = ("IDLE", "SEARCH", "APPROACH", "COLLECT")

    def __init__(self):
        self._state = "IDLE"
        self._prev_state = "IDLE"
        self._state_enter_time = time.time()  # Waktu masuk state saat ini
        self._history = []                    # Riwayat transisi state
        self._collect_phase = 0               # Sub-fase di dalam COLLECT
        self._collect_timer = 0.0             # Timer internal COLLECT
        self._balls_collected = 0             # Jumlah bola terkumpul
        self._running = False                 # Flag auto-mode aktif

    # ─────────────────────────────────────────────────────────
    # Kontrol start / stop auto-mode
    # ─────────────────────────────────────────────────────────
    def start(self):
        """Mulai mode otomatis — transisi ke SEARCH."""
        self._running = True
        self._transition("SEARCH")

    def stop(self):
        """Berhentikan mode otomatis — kembali ke IDLE."""
        self._running = False
        self._transition("IDLE")

    @property
    def is_running(self):
        return self._running

    # ─────────────────────────────────────────────────────────
    # Update utama — dipanggil setiap frame
    # ─────────────────────────────────────────────────────────
    def update(self, detection):
        """
        Proses deteksi dan hasilkan perintah motor + servo.

        Args:
            detection (dict): Hasil dari VisionPipeline.process_frame()

        Returns:
            dict: {vx, vy, omega, servo_cmd}
                vx     — kecepatan maju/mundur
                vy     — kecepatan lateral (tidak dipakai, 0)
                omega  — kecepatan rotasi
                servo_cmd — None | "OPEN" | "CLOSE"
        """
        # Kalau tidak sedang auto-mode, kembalikan perintah diam
        if not self._running:
            return self._stop_cmd()

        detected = detection.get("detected", False)
        area = detection.get("area", 0)
        offset_x = detection.get("offset_x", 0)

        # ── Logika per state ─────────────────────────────────
        if self._state == "SEARCH":
            return self._handle_search(detected, area)

        elif self._state == "APPROACH":
            return self._handle_approach(detected, area, offset_x)

        elif self._state == "COLLECT":
            return self._handle_collect()

        # Default (termasuk IDLE)
        return self._stop_cmd()

    # ─────────────────────────────────────────────────────────
    # Handler per state
    # ─────────────────────────────────────────────────────────
    def _handle_search(self, detected, area):
        """
        SEARCH: Putar robot perlahan untuk mencari bola.
        Jika bola terdeteksi dengan area cukup → APPROACH.
        """
        if detected and area >= config.AREA_APPROACH:
            self._transition("APPROACH")
            # Langsung masuk handler APPROACH di frame berikutnya
            return self._stop_cmd()

        # Putar searah jarum jam
        return {
            "vx": 0,
            "vy": 0,
            "omega": config.SEARCH_SPEED,
            "servo_cmd": None,
        }

    def _handle_approach(self, detected, area, offset_x):
        """
        APPROACH: Maju mendekati bola, steering proporsional
        berdasarkan offset_x (P-controller).
        Jika bola hilang → kembali SEARCH.
        Jika area cukup besar → COLLECT.
        """
        # Bola hilang — cari lagi
        if not detected:
            self._transition("SEARCH")
            return self._stop_cmd()

        # Bola sudah sangat dekat — mulai prosedur pengumpulan
        if area >= config.AREA_COLLECT:
            self._transition("COLLECT")
            self._collect_phase = 0
            self._collect_timer = time.time()
            return self._stop_cmd()

        # P-controller: koreksi heading proporsional terhadap offset_x
        omega = int(config.KP_STEERING * offset_x)

        # Maju selama bola masih terlihat
        vx = config.APPROACH_SPEED

        return {
            "vx": vx,
            "vy": 0,
            "omega": omega,
            "servo_cmd": None,
        }

    def _handle_collect(self):
        """
        COLLECT: Prosedur pengumpulan bola (3 fase):
          0 — Buka servo
          1 — Tunggu SWEEP_DELAY
          2 — Tutup servo, hitung bola, kembali ke SEARCH
        """
        elapsed = time.time() - self._collect_timer

        if self._collect_phase == 0:
            # Fase 0: Perintahkan servo membuka
            self._collect_phase = 1
            self._collect_timer = time.time()
            return {
                "vx": 0, "vy": 0, "omega": 0,
                "servo_cmd": "OPEN",
            }

        elif self._collect_phase == 1:
            # Fase 1: Tunggu servo terbuka penuh
            if elapsed >= config.SWEEP_DELAY:
                self._collect_phase = 2
                self._collect_timer = time.time()
                return {
                    "vx": 0, "vy": 0, "omega": 0,
                    "servo_cmd": "CLOSE",
                }
            return self._stop_cmd()

        elif self._collect_phase == 2:
            # Fase 2: Tunggu servo tertutup, lalu kembali SEARCH
            if elapsed >= config.SWEEP_DELAY:
                self._balls_collected += 1
                self._transition("SEARCH")
            return self._stop_cmd()

        return self._stop_cmd()

    # ─────────────────────────────────────────────────────────
    # Transisi state
    # ─────────────────────────────────────────────────────────
    def _transition(self, new_state):
        """Catat transisi state dan perbarui timestamp."""
        if new_state == self._state:
            return

        now = time.time()
        duration_in_prev = now - self._state_enter_time

        self._history.append({
            "from": self._state,
            "to": new_state,
            "timestamp": now,
            "duration": round(duration_in_prev, 3),
        })

        # Batasi riwayat agar tidak membengkak
        if len(self._history) > 200:
            self._history = self._history[-100:]

        self._prev_state = self._state
        self._state = new_state
        self._state_enter_time = now

    # ─────────────────────────────────────────────────────────
    # Perintah berhenti
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _stop_cmd():
        """Kembalikan perintah diam (semua nol)."""
        return {"vx": 0, "vy": 0, "omega": 0, "servo_cmd": None}

    # ─────────────────────────────────────────────────────────
    # Status untuk telemetri UI
    # ─────────────────────────────────────────────────────────
    def get_status(self):
        """Kembalikan informasi state saat ini untuk ditampilkan di UI."""
        now = time.time()
        return {
            "state": self._state,
            "prev_state": self._prev_state,
            "running": self._running,
            "state_duration": round(now - self._state_enter_time, 2),
            "balls_collected": self._balls_collected,
            "history_len": len(self._history),
            "last_transitions": self._history[-5:] if self._history else [],
        }
