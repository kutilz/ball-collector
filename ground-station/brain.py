"""
brain.py — State machine otak robot pengumpul bola.

States:
  IDLE     → Menunggu perintah start (diam)
  SEARCH   → Mencari bola
  APPROACH → Mendekati bola
  COLLECT  → Berhenti, aktifkan servo pengumpul, lalu kembali SEARCH

APPROACH → COLLECT saat jarak bola (dari lebar bbox) ≤ STOP_DIST_CM. Bila jarak itu
lebih dekat dari jangkauan lihat kamera (NEAR_VISIBLE_CM), robot maju "buta" selama
sisa_jarak / kecepatan (sub-fase APPROACH, bukan state baru), lalu COLLECT.

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

        # ── Jarak berhenti (STOP_DIST_CM) ────────────────────
        self._now = time.time()
        self._push_until = None         # Maju buta ke zona dekat sampai waktu ini
        self._last_dist = None          # Jarak depan terakhir target (cm), utk "hilang di dekat"
        self._last_cam_dist = None

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
        self._push_until = None
        self._last_dist = None
        self._last_cam_dist = None

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
        self._now = ctx.get("now", time.time())

        # Maju buta ke zona dekat (bola sudah di bawah jangkauan kamera). Dijalankan
        # sebelum syarat "frame segar": selama fase ini kamera memang tidak dipakai.
        if self._push_until is not None:
            if self._state == "APPROACH" and self._now < self._push_until:
                return self._cmd(config.APPROACH_SPEED, 0, 0, note=self._note)
            self._push_until = None
            if self._state == "APPROACH":
                self._start_collect()
                return self._stop_cmd()

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
                near = self._push_if_lost_near()
                if near is not None:
                    return near
                self._transition("SEARCH")
                return self._stop_cmd()
            stop = self._stop_check({"bbox": detection.get("bbox")}, allow_push=True)
            if stop is not None:
                return stop
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
            # Hilang karena masuk zona buta dekat (bukan karena salah lihat)?
            near = self._push_if_lost_near()
            if near is not None:
                return near
            self._lost += 1
            if self._lost >= config.LOST_FRAMES:
                self._transition("SEARCH")
                return self._cmd(0, 0, 0, note="target hilang → SEARCH")
            # Berhenti selama ragu; jangan maju buta.
            return self._cmd(0, 0, 0, note=f"target hilang {self._lost}/{config.LOST_FRAMES}")
        self._lost = 0

        stop = self._stop_check(pick, allow_push=False)
        if stop is not None:
            return stop

        offset = pick["cx"] - config.FRAME_WIDTH / 2
        angle = math.degrees(math.atan(offset / config.focal_px()))
        self._aim_deg = round(angle, 2)
        if abs(angle) > config.AIM_TOL_DEG:
            cmd = math.copysign(max(abs(angle) - config.TURN_COMP_DEG, config.TURN_MIN_DEG), angle)
            # Setelah bidik, target seharusnya ada di tengah frame.
            self._expected_cx = config.FRAME_WIDTH / 2
            return self._turn(cmd, note=f"bidik {angle:+.1f}° → TURN {cmd:+.1f}°")

        # Maju buta hanya setelah bidikan lurus: kamera tidak bisa mengoreksi lagi.
        stop = self._stop_check(pick, allow_push=True)
        if stop is not None:
            return stop

        self._expected_cx = pick["cx"]
        dist = "" if self._last_dist is None else f", bola ≈{self._last_dist:.0f} cm"
        return self._cmd(config.APPROACH_SPEED, 0, 0,
                         note=f"maju lurus (sisa {angle:+.1f}°{dist})")

    def _pick(self, detection, expected_cx):
        """Pilih kandidat: terbesar, atau terdekat ke posisi harapan (bila ada).

        Kandidat yang melompat > JUMP_GATE_FRAC × lebar frame dari posisi
        harapan ditolak — pada uji bidik, kegagalan muncul saat target tertutup
        dan detektor conf-rendah beralih ke objek lain (orang, kursi).
        """
        cands = detection.get("candidates")
        if cands is None:  # Kompat: hasil deteksi lama tanpa daftar kandidat
            cands = ([{"cx": detection["cx"], "cy": detection["cy"], "area": detection["area"],
                       "bbox": detection.get("bbox")}]
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
    # Jarak berhenti (sama untuk kedua strategi)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _target_in_blind_zone():
        """True bila jarak berhenti yang diminta lebih dekat dari jangkauan lihat kamera."""
        return config.STOP_DIST_CM + config.CAM_FRONT_OFFSET_CM < config.NEAR_VISIBLE_CM

    def _stop_check(self, cand, allow_push):
        """Bandingkan jarak bola dengan STOP_DIST_CM.

        Kembalikan perintah (COLLECT atau mulai maju buta) bila waktunya berhenti,
        atau None bila robot masih harus mendekat.
        """
        dist = config.ball_front_dist_cm(cand.get("bbox"))
        if dist is None:
            return None
        self._last_dist = dist
        self._last_cam_dist = dist + config.CAM_FRONT_OFFSET_CM

        if dist <= config.STOP_DIST_CM:
            self._note = f"berhenti: bola ≈{dist:.0f} cm (target {config.STOP_DIST_CM:.0f} cm)"
            self._start_collect()
            return self._stop_cmd()
        if allow_push and self._target_in_blind_zone() \
                and self._last_cam_dist <= config.NEAR_VISIBLE_CM:
            return self._start_push(dist)
        return None

    def _push_if_lost_near(self):
        """Target hilang tepat setelah terlihat sangat dekat → anggap masuk zona buta."""
        if (self._target_in_blind_zone() and self._last_cam_dist is not None
                and self._last_cam_dist <= config.NEAR_VISIBLE_CM + 5.0):
            return self._start_push(self._last_dist)
        return None

    def _start_push(self, dist):
        """Maju lurus tanpa kamera sejauh (dist − STOP_DIST_CM), lalu COLLECT.

        Waktu = jarak / kecepatan. Kecepatan hanya terukur di PWM 100 (11,3 cm/s);
        di PWM lain dianggap sebanding (perkiraan). Dibatasi BLIND_PUSH_MAX_SEC.
        """
        remaining = max(0.0, dist - config.STOP_DIST_CM)
        pwm = min(config.APPROACH_SPEED, config.SAFETY_MAX_PWM)
        speed = config.SPEED_CM_PER_S_AT_100 * pwm / 100.0
        if remaining <= 0 or speed <= 0:
            self._start_collect()
            return self._stop_cmd()
        secs = min(remaining / speed, config.BLIND_PUSH_MAX_SEC)
        self._push_until = self._now + secs
        self._last_cam_dist = None   # cegah memicu ulang
        return self._cmd(config.APPROACH_SPEED, 0, 0,
                         note=f"maju buta {remaining:.0f} cm ≈ {secs:.1f} s (bola di zona buta)")

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
        self._last_dist = None
        self._last_cam_dist = None

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
