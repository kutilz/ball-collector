"""
brain.py — State machine otak robot pengumpul bola.

States:
  IDLE     → Menunggu perintah start (diam)
  SEARCH   → Mencari bola
  APPROACH → Mendekati bola
  COLLECT  → Berhenti, aktifkan servo pengumpul, lalu kembali SEARCH

Dua strategi navigasi (config.NAV_STRATEGY, bisa diganti live dari UI):

  "continuous" — strategi awal: SEARCH berputar terus (omega konstan),
      APPROACH maju sambil omega = KP_STEERING × offset_x setiap frame.
      Peka latensi: kamera ±185 ms + RTT perintah ±170 ms (p95 410 ms) +
      jeda WiFi 7–20 s membuat koreksi selalu terlambat.

  "gyro" — akal-akalan dari data uji 2026-11-17, memakai TURN:deg firmware
      (putar relatif berbasis gyro, kelewatan sistematis +1,1°):
        SEARCH   : putar per langkah SEARCH_STEP_DEG, berhenti, nilai frame segar.
        APPROACH : sudut = atan(offset / f) → TURN (dikurangi TURN_COMP_DEG),
                   tunggu selesai + SETTLE_SEC, lalu maju lurus (omega = 0,
                   heading hold firmware menjaga arah). Bidik ulang bila
                   |sudut| > AIM_TOL_DEG.
      Hasil uji bidik: sisa 3 px (±0,5°) vs 10 px tanpa kompensasi.
      Penolak false positive: target harus muncul CONFIRM_FRAMES frame segar
      berturut-turut, dan deteksi yang melompat jauh dari posisi harapan
      dianggap hilang.

Keluaran update(): dict {vx, vy, omega, servo_cmd, turn, aim_deg, note}.
  turn ≠ None → loop utama mengirim TURN:turn (bukan CMD).
  Selama TURN berjalan, brain mengembalikan gerak (0,0,0) yang SAMA dengan
  intent comms, sehingga loop utama tidak mengirim CMD (CMD membatalkan TURN).
"""

import math
import time
import config


class StateMachine:
    """Finite State Machine untuk navigasi dan pengumpulan bola."""

    STATES = ("IDLE", "SEARCH", "APPROACH", "COLLECT")
    STRATEGIES = ("gyro", "continuous")

    def __init__(self):
        self._state = "IDLE"
        self._prev_state = "IDLE"
        self._state_enter_time = time.time()
        self._history = []
        self._collect_phase = 0
        self._collect_timer = 0.0
        self._balls_collected = 0
        self._running = False

        # ── Strategi gyro ────────────────────────────────────
        self._strategy_used = config.NAV_STRATEGY
        self._turn_pending = False      # TURN sudah diminta, belum selesai
        self._trust_after = 0.0         # Frame harus lebih baru dari waktu ini
        self._last_frame_used = 0.0
        self._confirm = 0               # Deteksi segar berturut-turut (SEARCH)
        self._lost = 0                  # Frame segar tanpa target (APPROACH)
        self._expected_cx = None        # Posisi x harapan target (px)
        self._last_motion = (0, 0, 0)
        self._aim_deg = None
        self._note = ""
        self._n_turns = 0               # Jumlah TURN sejak start (statistik)

    # ─────────────────────────────────────────────────────────
    # Kontrol start / stop auto-mode
    # ─────────────────────────────────────────────────────────
    def start(self):
        """Mulai mode otomatis — transisi ke SEARCH."""
        self._running = True
        self._reset_nav()
        # Frame dari sebelum tombol Otomatis ditekan tidak dipakai.
        self._trust_after = time.time()
        self._transition("SEARCH")

    def stop(self):
        """Berhentikan mode otomatis — kembali ke IDLE."""
        self._running = False
        self._reset_nav()
        self._transition("IDLE")

    def _reset_nav(self):
        self._turn_pending = False
        self._confirm = 0
        self._lost = 0
        self._expected_cx = None
        self._last_motion = (0, 0, 0)
        self._aim_deg = None
        self._note = ""

    @property
    def is_running(self):
        return self._running

    # ─────────────────────────────────────────────────────────
    # Update utama — dipanggil setiap iterasi loop utama
    # ─────────────────────────────────────────────────────────
    def update(self, detection, ctx=None):
        """
        Proses deteksi dan hasilkan perintah.

        Args:
            detection (dict): hasil VisionPipeline.process_frame()
            ctx (dict): {now, frame_time, turning, gyro_ready}
                frame_time — waktu frame yang menghasilkan `detection`
                turning    — TURN masih berjalan (comms.is_turning())
                gyro_ready — telemetri gyro ada & arah sudah dikalibrasi
        """
        if not self._running:
            return self._stop_cmd()
        ctx = ctx or {}

        strategy = config.NAV_STRATEGY
        if strategy == "gyro" and not ctx.get("gyro_ready", False):
            # TURN butuh robot tersambung & DIRCAL; tanpa itu pakai strategi lama.
            strategy = "continuous"
        if strategy != self._strategy_used:
            self._reset_nav()
            self._strategy_used = strategy

        if strategy == "gyro":
            return self._update_gyro(detection, ctx)
        return self._update_continuous(detection)

    # ═════════════════════════════════════════════════════════
    # Strategi "continuous" (P-controller lama, dipertahankan untuk pembanding)
    # ═════════════════════════════════════════════════════════
    def _update_continuous(self, detection):
        detected = detection.get("detected", False)
        area = detection.get("area", 0)
        offset_x = detection.get("offset_x", 0)
        self._note = ""

        if self._state == "SEARCH":
            if detected and area >= config.AREA_APPROACH:
                self._transition("APPROACH")
                return self._stop_cmd()
            return self._cmd(0, 0, config.SEARCH_SPEED, note="putar terus mencari")

        if self._state == "APPROACH":
            if not detected:
                self._transition("SEARCH")
                return self._stop_cmd()
            if area >= config.AREA_COLLECT:
                self._start_collect()
                return self._stop_cmd()
            omega = int(config.KP_STEERING * offset_x)
            return self._cmd(config.APPROACH_SPEED, 0, omega, note="maju + P-steering")

        if self._state == "COLLECT":
            return self._handle_collect()
        return self._stop_cmd()

    # ═════════════════════════════════════════════════════════
    # Strategi "gyro" (bidik pakai TURN, maju lurus pakai heading hold)
    # ═════════════════════════════════════════════════════════
    def _update_gyro(self, detection, ctx):
        now = ctx.get("now", time.time())

        if self._state == "COLLECT":
            return self._handle_collect()

        # 1. Tunggu TURN selesai. Gerak (0,0,0) = intent comms → tak ada CMD.
        if self._turn_pending:
            if ctx.get("turning", False):
                return self._cmd(0, 0, 0, note="menunggu TURN selesai")
            self._turn_pending = False
            self._trust_after = now + config.SETTLE_SEC
            self._note = "TURN selesai, menunggu frame segar"

        # 2. Hanya frame baru yang diambil SETELAH robot tenang.
        frame_time = ctx.get("frame_time", 0.0)
        if frame_time <= self._last_frame_used or frame_time < self._trust_after:
            return self._cmd(*self._last_motion, note=self._note or "menunggu frame segar")
        self._last_frame_used = frame_time

        if self._state == "SEARCH":
            return self._gyro_search(detection)
        if self._state == "APPROACH":
            return self._gyro_approach(detection)
        return self._stop_cmd()

    def _gyro_search(self, detection):
        pick = self._pick(detection, expected_cx=None)
        if pick is not None and pick["area"] >= config.AREA_APPROACH:
            self._confirm += 1
        else:
            self._confirm = 0

        if self._confirm >= config.CONFIRM_FRAMES:
            self._expected_cx = pick["cx"]
            self._transition("APPROACH")
            return self._cmd(0, 0, 0, note="target terkonfirmasi")
        if self._confirm > 0:
            return self._cmd(0, 0, 0, note=f"konfirmasi {self._confirm}/{config.CONFIRM_FRAMES}")
        return self._turn(config.SEARCH_STEP_DEG, note=f"SEARCH putar {config.SEARCH_STEP_DEG}°")

    def _gyro_approach(self, detection):
        pick = self._pick(detection, self._expected_cx)
        if pick is None:
            self._lost += 1
            if self._lost >= config.LOST_FRAMES:
                self._transition("SEARCH")
                return self._cmd(0, 0, 0, note="target hilang → SEARCH")
            # Berhenti selama ragu; jangan maju buta.
            return self._cmd(0, 0, 0, note=f"target hilang {self._lost}/{config.LOST_FRAMES}")
        self._lost = 0

        if pick["area"] >= config.AREA_COLLECT:
            self._start_collect()
            return self._stop_cmd()

        offset = pick["cx"] - config.FRAME_WIDTH / 2
        angle = math.degrees(math.atan(offset / config.focal_px()))
        self._aim_deg = round(angle, 2)
        if abs(angle) > config.AIM_TOL_DEG:
            cmd = math.copysign(max(abs(angle) - config.TURN_COMP_DEG, config.TURN_MIN_DEG), angle)
            # Setelah bidik, target seharusnya ada di tengah frame.
            self._expected_cx = config.FRAME_WIDTH / 2
            return self._turn(cmd, note=f"bidik {angle:+.1f}° → TURN {cmd:+.1f}°")

        self._expected_cx = pick["cx"]
        return self._cmd(config.APPROACH_SPEED, 0, 0,
                         note=f"maju lurus (sisa {angle:+.1f}°, heading hold)")

    def _pick(self, detection, expected_cx):
        """Pilih kandidat: terbesar, atau terdekat ke posisi harapan (bila ada).

        Kandidat yang melompat > JUMP_GATE_FRAC × lebar frame dari posisi
        harapan ditolak — pada uji bidik, kegagalan muncul saat target tertutup
        dan detektor conf-rendah beralih ke objek lain (orang, kursi).
        """
        cands = detection.get("candidates")
        if cands is None:  # Kompat: hasil deteksi lama tanpa daftar kandidat
            cands = ([{"cx": detection["cx"], "cy": detection["cy"], "area": detection["area"]}]
                     if detection.get("detected") else [])
        if not cands:
            return None
        if expected_cx is None:
            return cands[0]
        best = min(cands, key=lambda c: abs(c["cx"] - expected_cx))
        if abs(best["cx"] - expected_cx) > config.JUMP_GATE_FRAC * config.FRAME_WIDTH:
            return None
        return best

    # ─────────────────────────────────────────────────────────
    # COLLECT (sama untuk kedua strategi)
    # ─────────────────────────────────────────────────────────
    def _start_collect(self):
        self._transition("COLLECT")
        self._collect_phase = 0
        self._collect_timer = time.time()

    def _handle_collect(self):
        """
        COLLECT: Prosedur pengumpulan bola (3 fase):
          0 — Buka servo
          1 — Tunggu SWEEP_DELAY
          2 — Tutup servo, hitung bola, kembali ke SEARCH
        """
        elapsed = time.time() - self._collect_timer

        if self._collect_phase == 0:
            self._collect_phase = 1
            self._collect_timer = time.time()
            return {**self._stop_cmd(), "servo_cmd": "OPEN", "note": "servo buka"}

        if self._collect_phase == 1:
            if elapsed >= config.SWEEP_DELAY:
                self._collect_phase = 2
                self._collect_timer = time.time()
                return {**self._stop_cmd(), "servo_cmd": "CLOSE", "note": "servo tutup"}
            return self._stop_cmd()

        if self._collect_phase == 2:
            if elapsed >= config.SWEEP_DELAY:
                self._balls_collected += 1
                self._expected_cx = None
                # Frame berikutnya harus diambil setelah servo selesai bergerak.
                self._trust_after = time.time() + config.SETTLE_SEC
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
        self._history.append({
            "from": self._state,
            "to": new_state,
            "timestamp": now,
            "duration": round(now - self._state_enter_time, 3),
        })
        if len(self._history) > 200:
            self._history = self._history[-100:]

        self._prev_state = self._state
        self._state = new_state
        self._state_enter_time = now
        self._confirm = 0
        self._lost = 0

    # ─────────────────────────────────────────────────────────
    # Pembentuk perintah
    # ─────────────────────────────────────────────────────────
    def _cmd(self, vx, vy, omega, note=""):
        self._last_motion = (int(vx), int(vy), int(omega))
        self._note = note
        return {"vx": int(vx), "vy": int(vy), "omega": int(omega), "servo_cmd": None,
                "turn": None, "aim_deg": self._aim_deg, "note": note}

    def _turn(self, deg, note=""):
        self._turn_pending = True
        self._last_motion = (0, 0, 0)
        self._note = note
        self._n_turns += 1
        return {"vx": 0, "vy": 0, "omega": 0, "servo_cmd": None,
                "turn": round(float(deg), 1), "aim_deg": self._aim_deg, "note": note}

    def _stop_cmd(self):
        """Perintah diam (semua nol)."""
        self._last_motion = (0, 0, 0)
        return {"vx": 0, "vy": 0, "omega": 0, "servo_cmd": None,
                "turn": None, "aim_deg": self._aim_deg, "note": self._note}

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
            "strategy": self._strategy_used,
            "note": self._note,
            "aim_deg": self._aim_deg,
            "n_turns": self._n_turns,
        }
