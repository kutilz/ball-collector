"""
vision.py — Pipeline deteksi bola dengan backend yang bisa dipilih.

Tiga backend deteksi tersedia dan bisa dialihkan saat runtime dari UI:
  • "hsv"       — segmentasi warna HSV (OpenCV). Ringan, default, tanpa
                  dependensi berat. Cocok jalan di laptop/edge tanpa GPU.
  • "yolo"      — deteksi objek machine learning (YOLOv8 via Ultralytics).
                  Lebih tahan terhadap variasi warna/pencahayaan, tapi butuh
                  paket `ultralytics` terpasang (lihat requirements-ai.txt).
  • "yoloworld" — YOLO-World (open-vocabulary): objek dicari lewat prompt
                  teks, mis. "orange ping pong ball", tanpa training ulang.
                  Dependensi sama dengan "yolo".

Semua backend menghasilkan dict deteksi berformat SAMA sehingga otak robot
(brain.py) tidak perlu tahu backend mana yang aktif:

  detected, cx, cy, area, bbox, offset_x, offset_y, frame_annotated

Pipeline umum tiap frame:
  resize → (deteksi backend) → pilih objek terbesar → centroid + area →
  overlay anotasi (bbox, crosshair, panah offset, badge mode).
"""

import cv2
import numpy as np
import config


class VisionPipeline:
    """Orkestrator deteksi bola. Mendukung backend HSV, YOLO & YOLO-World."""

    VALID_BACKENDS = ("hsv", "yolo", "yoloworld")
    AI_BACKENDS = ("yolo", "yoloworld")

    def __init__(self):
        # ── Parameter HSV (default dari config) ──────────────
        self.h_min = config.HSV_DEFAULTS["h_min"]
        self.h_max = config.HSV_DEFAULTS["h_max"]
        self.s_min = config.HSV_DEFAULTS["s_min"]
        self.s_max = config.HSV_DEFAULTS["s_max"]
        self.v_min = config.HSV_DEFAULTS["v_min"]
        self.v_max = config.HSV_DEFAULTS["v_max"]

        # Kernel morfologi untuk noise removal (HSV)
        self._erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        self._dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

        # Cache mask terakhir untuk preview HSV
        self._last_mask = None

        # ── Backend aktif ────────────────────────────────────
        backend = getattr(config, "DETECTOR_BACKEND", "hsv")
        self.backend = backend if backend in self.VALID_BACKENDS else "hsv"

        # ── State model AI (lazy-load), per backend ──────────
        self._models = {k: None for k in self.AI_BACKENDS}  # None = belum dimuat
        self._errors = {k: None for k in self.AI_BACKENDS}  # error muat/inferensi terakhir
        self._model_names = {
            "yolo": getattr(config, "YOLO_MODEL", "yolov8n.pt"),
            "yoloworld": getattr(config, "YOLOWORLD_MODEL", "yolov8s-worldv2.pt"),
        }
        self._world_prompt = list(getattr(config, "YOLOWORLD_PROMPT", ["ping pong ball"]))
        # Backend yang terakhir diminta UI — errornya yang ditampilkan di status.
        self._requested = self.backend

    # ═════════════════════════════════════════════════════════
    # Pemilihan backend
    # ═════════════════════════════════════════════════════════
    def set_backend(self, name):
        """
        Alihkan backend deteksi ke "hsv", "yolo", atau "yoloworld".

        Untuk backend AI, model coba dimuat saat itu juga. Jika gagal (paket
        belum terpasang / bobot tak ditemukan), backend TETAP di nilai lama
        dan error dikembalikan agar UI bisa memberi tahu operator.

        Returns:
            dict: {"ok": bool, "backend": str, "error": str|None}
        """
        name = (name or "").lower()
        if name not in self.VALID_BACKENDS:
            return {"ok": False, "backend": self.backend,
                    "error": f"Backend '{name}' tidak dikenal."}

        self._requested = name
        if name in self.AI_BACKENDS and not self._ensure_model(name):
            # Gagal memuat → jangan pindah backend, laporkan alasan.
            return {"ok": False, "backend": self.backend, "error": self._errors[name]}

        self.backend = name
        return {"ok": True, "backend": self.backend, "error": None}

    def get_backend_info(self):
        """Info backend untuk sinkronisasi & diagnosa di UI."""
        shown = self._requested if self._requested in self.AI_BACKENDS else self.backend
        return {
            "backend": self.backend,
            "requested": self._requested,
            "error": self._errors.get(shown),
            "yolo_ready": self._models["yolo"] is not None,
            "yolo_model": self._model_names["yolo"],
            "world_ready": self._models["yoloworld"] is not None,
            "world_model": self._model_names["yoloworld"],
            "world_prompt": ", ".join(self._world_prompt),
        }

    def set_world_prompt(self, text):
        """
        Ganti prompt teks YOLO-World. Beberapa objek dipisah koma, mis.
        "orange ping pong ball, white ping pong ball". Bila model sudah
        dimuat, kelasnya langsung diperbarui.

        Returns:
            dict: {"ok": bool, "error": str|None}
        """
        prompt = [p.strip() for p in str(text or "").split(",") if p.strip()]
        if not prompt:
            return {"ok": False, "error": "Prompt YOLO-World tidak boleh kosong."}
        model = self._models["yoloworld"]
        if model is not None:
            try:
                model.set_classes(prompt)
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "error": f"Gagal menerapkan prompt: {exc}"}
        self._world_prompt = prompt
        return {"ok": True, "error": None}

    def _ensure_model(self, kind):
        """
        Muat model AI ("yolo"/"yoloworld") sekali (lazy). Return True bila
        model siap dipakai. Impor `ultralytics` sengaja ditunda ke sini supaya
        ground station tetap bisa jalan dengan HSV tanpa memasang torch.
        """
        if self._models[kind] is not None:
            return True
        try:
            from ultralytics import YOLO, YOLOWorld  # impor berat — hanya saat dibutuhkan
        except Exception:  # noqa: BLE001 — apa pun penyebabnya, degrade ke pesan UI
            self._errors[kind] = (
                "Paket 'ultralytics' belum terpasang. "
                "Jalankan: pip install -r requirements-ai.txt"
            )
            return False
        name = self._model_names[kind]
        try:
            if kind == "yoloworld":
                model = YOLOWorld(name)
                model.set_classes(self._world_prompt)  # encode prompt teks sekali
            else:
                model = YOLO(name)
            self._models[kind] = model
            self._errors[kind] = None
            return True
        except Exception as exc:  # noqa: BLE001
            self._errors[kind] = f"Gagal memuat model '{name}': {exc}"
            self._models[kind] = None
            return False

    # ═════════════════════════════════════════════════════════
    # Update parameter HSV dari slider UI
    # ═════════════════════════════════════════════════════════
    def update_hsv(self, h_min, h_max, s_min, s_max, v_min, v_max):
        """Perbarui batas-batas HSV untuk thresholding."""
        self.h_min = int(h_min)
        self.h_max = int(h_max)
        self.s_min = int(s_min)
        self.s_max = int(s_max)
        self.v_min = int(v_min)
        self.v_max = int(v_max)

    # ═════════════════════════════════════════════════════════
    # Pipeline utama: proses satu frame
    # ═════════════════════════════════════════════════════════
    def process_frame(self, frame):
        """
        Jalankan pipeline deteksi pada satu frame BGR memakai backend aktif.

        Returns dict: detected, cx, cy, area, bbox, offset_x, offset_y,
        frame_annotated. (Format identik untuk semua backend.)
        """
        if frame is None:
            return self._empty_result(frame)

        # 1. Resize ke resolusi kerja
        resized = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
        h_frame, w_frame = resized.shape[:2]
        cx_frame = w_frame // 2
        cy_frame = h_frame // 2

        # Buat kanvas anotasi + garis tengah vertikal (referensi heading)
        annotated = resized.copy()
        cv2.line(annotated, (cx_frame, 0), (cx_frame, h_frame),
                 (100, 100, 100), 1, cv2.LINE_AA)

        # 2. Deteksi via backend aktif → (cx, cy, area, bbox) atau None.
        #    Bila backend AI tapi model tak siap, fallback otomatis ke HSV
        #    agar robot tidak buta.
        if self.backend in self.AI_BACKENDS and self._ensure_model(self.backend):
            det = self._detect_ai(self.backend, resized)
            active = self.backend
        else:
            det = self._detect_hsv(resized)
            active = "hsv"

        self._draw_badge(annotated, active)

        if det is None:
            return self._empty_result(annotated)

        cx, cy, area, bbox = det
        offset_x = cx - cx_frame
        offset_y = cy - cy_frame
        self._annotate(annotated, cx, cy, area, bbox,
                       offset_x, offset_y, cx_frame, cy_frame)

        return {
            "detected": True,
            "cx": cx,
            "cy": cy,
            "area": area,
            "bbox": bbox,
            "offset_x": offset_x,
            "offset_y": offset_y,
            "frame_annotated": annotated,
        }

    # ═════════════════════════════════════════════════════════
    # Backend HSV — segmentasi warna
    # ═════════════════════════════════════════════════════════
    def _detect_hsv(self, resized):
        """
        Deteksi bola via thresholding HSV + morfologi + kontur terbesar.
        Returns (cx, cy, area, bbox) atau None. Menyimpan mask ke cache
        preview (self._last_mask).
        """
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)

        lower = np.array([self.h_min, self.s_min, self.v_min], dtype=np.uint8)
        upper = np.array([self.h_max, self.s_max, self.v_max], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)

        # Morfologi: erode buang noise, dilate isi gap. Iterasi live dari config.
        if config.ERODE_ITER > 0:
            mask = cv2.erode(mask, self._erode_kernel, iterations=config.ERODE_ITER)
        if config.DILATE_ITER > 0:
            mask = cv2.dilate(mask, self._dilate_kernel, iterations=config.DILATE_ITER)
        self._last_mask = mask

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < config.MIN_CONTOUR_AREA:
            return None

        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        bbox = cv2.boundingRect(largest)
        return cx, cy, float(area), bbox

    # ═════════════════════════════════════════════════════════
    # Backend AI (YOLO / YOLO-World) — deteksi objek machine learning
    # ═════════════════════════════════════════════════════════
    def _detect_ai(self, kind, resized):
        """
        Deteksi bola via YOLOv8 / YOLO-World. Pilih kotak terbesar di atas
        ambang confidence. YOLO dibatasi ke kelas config.YOLO_CLASSES;
        YOLO-World menerima semua kelas karena kelasnya = prompt teks.
        Returns (cx, cy, area, bbox) atau None.

        Catatan: "area" di sini = luas bounding box (w*h), bukan luas kontur.
        Skalanya berbeda dari HSV, jadi ambang AREA_APPROACH/AREA_COLLECT
        mungkin perlu dikalibrasi ulang saat memakai backend ini.
        """
        allowed = [] if kind == "yoloworld" else list(getattr(config, "YOLO_CLASSES", []) or [])
        try:
            results = self._models[kind].predict(
                resized,
                conf=float(config.YOLO_CONF),
                imgsz=int(getattr(config, "YOLO_IMGSZ", 416)),
                classes=allowed or None,
                verbose=False,
            )
        except Exception as exc:  # noqa: BLE001 — inferensi gagal → anggap tak ada deteksi
            self._errors[kind] = f"Inferensi {kind} gagal: {exc}"
            return None

        best = None          # (area, cx, cy, bbox)
        for res in results:
            boxes = getattr(res, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
                bw, bh = x2 - x1, y2 - y1
                area = bw * bh
                if best is None or area > best[0]:
                    cx = int(x1 + bw / 2)
                    cy = int(y1 + bh / 2)
                    bbox = (int(x1), int(y1), int(bw), int(bh))
                    best = (area, cx, cy, bbox)

        if best is None:
            return None
        area, cx, cy, bbox = best
        return cx, cy, area, bbox

    # ═════════════════════════════════════════════════════════
    # Anotasi overlay (dipakai semua backend)
    # ═════════════════════════════════════════════════════════
    def _annotate(self, annotated, cx, cy, area, bbox,
                  offset_x, offset_y, cx_frame, cy_frame):
        """Gambar bbox, crosshair, panah offset, dan teks info pada frame."""
        bx, by, bw, bh = bbox
        h_frame = annotated.shape[0]

        # Bounding rect hijau
        cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh),
                      (0, 255, 100), 2, cv2.LINE_AA)

        # Crosshair merah di centroid
        cross_size = 15
        cv2.line(annotated, (cx - cross_size, cy), (cx + cross_size, cy),
                 (0, 0, 255), 2, cv2.LINE_AA)
        cv2.line(annotated, (cx, cy - cross_size), (cx, cy + cross_size),
                 (0, 0, 255), 2, cv2.LINE_AA)

        # Panah offset dari tengah frame ke centroid
        cv2.arrowedLine(annotated, (cx_frame, cy_frame), (cx, cy),
                        (0, 200, 255), 2, cv2.LINE_AA, tipLength=0.15)

        # Teks info area dan offset
        info_text = f"Area: {int(area)}  Offset: ({offset_x}, {offset_y})"
        cv2.putText(annotated, info_text, (10, h_frame - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 200), 1, cv2.LINE_AA)

    def _draw_badge(self, annotated, active):
        """Badge kecil kiri-atas menandai backend deteksi yang aktif."""
        label = {"yolo": "AI: YOLO", "yoloworld": "AI: YOLO-World"}.get(active, "HSV")
        color = (255, 180, 0) if active in self.AI_BACKENDS else (0, 255, 200)
        cv2.putText(annotated, label, (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

    # ═════════════════════════════════════════════════════════
    # Preview mask HSV (untuk debugging threshold)
    # ═════════════════════════════════════════════════════════
    def get_mask_preview(self):
        """
        Kembalikan frame preview mask HSV terkini.
        Saat backend AI aktif, mask HSV tidak relevan → tampilkan info.
        """
        if self.backend in self.AI_BACKENDS:
            label = "YOLO-World" if self.backend == "yoloworld" else "YOLO"
            blank = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(blank, f"Mode AI ({label}) aktif", (70, 220),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 180, 0), 2, cv2.LINE_AA)
            cv2.putText(blank, "mask HSV nonaktif", (120, 255),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 120, 120), 1, cv2.LINE_AA)
            return blank

        if self._last_mask is None:
            blank = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH), dtype=np.uint8)
            return cv2.cvtColor(blank, cv2.COLOR_GRAY2BGR)

        # Konversi mask 1-channel ke 3-channel agar bisa di-encode JPEG
        return cv2.cvtColor(self._last_mask, cv2.COLOR_GRAY2BGR)

    # ═════════════════════════════════════════════════════════
    # Hasil kosong (tidak ada deteksi)
    # ═════════════════════════════════════════════════════════
    def _empty_result(self, frame):
        """Kembalikan dict deteksi kosong ketika bola tidak ditemukan."""
        if frame is None:
            frame = np.zeros(
                (config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8
            )
        return {
            "detected": False,
            "cx": 0,
            "cy": 0,
            "area": 0,
            "bbox": (0, 0, 0, 0),
            "offset_x": 0,
            "offset_y": 0,
            "frame_annotated": frame,
        }

    # ═════════════════════════════════════════════════════════
    # Getter HSV saat ini (untuk sinkronisasi UI)
    # ═════════════════════════════════════════════════════════
    def get_hsv_values(self):
        """Kembalikan dictionary nilai HSV saat ini."""
        return {
            "h_min": self.h_min,
            "h_max": self.h_max,
            "s_min": self.s_min,
            "s_max": self.s_max,
            "v_min": self.v_min,
            "v_max": self.v_max,
        }
