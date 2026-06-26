"""
logger.py — Pencatatan data CSV untuk eksperimen skripsi.

Setiap sesi recording menghasilkan file CSV terpisah dengan
timestamp di nama file. Kolom:
  timestamp, state, ball_x, ball_y, ball_area,
  cmd_vx, cmd_vy, cmd_omega, collect_result
"""

import csv
import os
import time
from datetime import datetime

import config


class DataLogger:
    """Logger CSV untuk telemetri robot."""

    def __init__(self):
        self._active = False
        self._writer = None
        self._file = None
        self._filename = None
        self._entry_count = 0
        self._start_time = None

        # Pastikan direktori log ada
        os.makedirs(config.LOG_DIR, exist_ok=True)

    # ─────────────────────────────────────────────────────────
    # Mulai / berhenti recording
    # ─────────────────────────────────────────────────────────
    def start_logging(self):
        """Buat file CSV baru dan mulai recording."""
        if self._active:
            return  # Sudah aktif, jangan buka file baru

        # Nama file otomatis berdasarkan waktu
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._filename = os.path.join(config.LOG_DIR, f"experiment_{ts}.csv")

        try:
            self._file = open(self._filename, "w", newline="", encoding="utf-8")
            self._writer = csv.writer(self._file)

            # Tulis header kolom
            self._writer.writerow([
                "timestamp",
                "elapsed_s",
                "state",
                "ball_x",
                "ball_y",
                "ball_area",
                "cmd_vx",
                "cmd_vy",
                "cmd_omega",
                "collect_result",
            ])

            self._entry_count = 0
            self._start_time = time.time()
            self._active = True

        except IOError as e:
            self._active = False
            self._filename = None
            print(f"[Logger] Gagal membuka file log: {e}")

    def stop_logging(self):
        """Tutup file CSV dan hentikan recording."""
        if not self._active:
            return

        try:
            if self._file:
                self._file.flush()
                self._file.close()
        except IOError:
            pass
        finally:
            self._active = False
            self._writer = None
            self._file = None

    # ─────────────────────────────────────────────────────────
    # Tulis satu baris data
    # ─────────────────────────────────────────────────────────
    def log_entry(self, state, ball_x, ball_y, ball_area,
                  cmd_vx, cmd_vy, cmd_omega, collect_result=""):
        """
        Catat satu entri telemetri ke CSV.

        Args:
            state          — State FSM saat ini (string)
            ball_x, ball_y — Koordinat centroid bola (int)
            ball_area      — Luas kontur bola (float)
            cmd_vx/vy/omega— Perintah motor yang dikirim
            collect_result — Hasil pengumpulan ("SUCCESS" / "" / dll.)
        """
        if not self._active or self._writer is None:
            return

        now = time.time()
        elapsed = round(now - self._start_time, 4) if self._start_time else 0

        try:
            self._writer.writerow([
                datetime.now().isoformat(timespec="milliseconds"),
                elapsed,
                state,
                ball_x,
                ball_y,
                round(ball_area, 1),
                cmd_vx,
                cmd_vy,
                cmd_omega,
                collect_result,
            ])
            self._entry_count += 1

            # Flush setiap 50 baris agar data tidak hilang saat crash
            if self._entry_count % 50 == 0:
                self._file.flush()

        except IOError as e:
            print(f"[Logger] Error tulis CSV: {e}")

    # ─────────────────────────────────────────────────────────
    # Info status untuk UI
    # ─────────────────────────────────────────────────────────
    def get_log_info(self):
        """Kembalikan informasi recording saat ini."""
        return {
            "active": self._active,
            "filename": os.path.basename(self._filename) if self._filename else None,
            "entry_count": self._entry_count,
            "elapsed": round(time.time() - self._start_time, 1) if self._start_time and self._active else 0,
        }

    # ─────────────────────────────────────────────────────────
    # Destruktor — pastikan file ditutup
    # ─────────────────────────────────────────────────────────
    def __del__(self):
        """Bersihkan resource saat objek dihancurkan."""
        self.stop_logging()
