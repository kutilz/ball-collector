"""
vision.py — Pipeline deteksi bola ping-pong oranye menggunakan
segmentasi warna HSV pada OpenCV.

Pipeline:
  resize → BGR2HSV → inRange → erode/dilate → findContours →
  kontur terbesar → centroid + area → overlay anotasi.
"""

import cv2
import numpy as np
import config


class VisionPipeline:
    """Kelas utama untuk deteksi bola berdasarkan warna HSV."""

    def __init__(self):
        # Inisialisasi batas HSV dari konfigurasi default
        self.h_min = config.HSV_DEFAULTS["h_min"]
        self.h_max = config.HSV_DEFAULTS["h_max"]
        self.s_min = config.HSV_DEFAULTS["s_min"]
        self.s_max = config.HSV_DEFAULTS["s_max"]
        self.v_min = config.HSV_DEFAULTS["v_min"]
        self.v_max = config.HSV_DEFAULTS["v_max"]

        # Kernel morfologi untuk noise removal
        self._erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        self._dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

        # Cache mask terakhir untuk preview HSV
        self._last_mask = None
        self._last_hsv_frame = None

    # ─────────────────────────────────────────────────────────
    # Update parameter HSV dari slider UI
    # ─────────────────────────────────────────────────────────
    def update_hsv(self, h_min, h_max, s_min, s_max, v_min, v_max):
        """Perbarui batas-batas HSV untuk thresholding."""
        self.h_min = int(h_min)
        self.h_max = int(h_max)
        self.s_min = int(s_min)
        self.s_max = int(s_max)
        self.v_min = int(v_min)
        self.v_max = int(v_max)

    # ─────────────────────────────────────────────────────────
    # Pipeline utama: proses satu frame
    # ─────────────────────────────────────────────────────────
    def process_frame(self, frame):
        """
        Jalankan pipeline deteksi pada satu frame BGR.

        Returns:
            dict berisi:
                detected (bool)   — apakah bola ditemukan
                cx, cy (int)      — koordinat centroid bola
                area (float)      — luas kontur (px²)
                bbox (tuple)      — (x, y, w, h) bounding rect
                offset_x (int)    — jarak centroid ke tengah frame (sumbu X)
                offset_y (int)    — jarak centroid ke tengah frame (sumbu Y)
                frame_annotated   — frame BGR dengan overlay anotasi
        """
        if frame is None:
            return self._empty_result(frame)

        # 1. Resize ke resolusi kerja
        resized = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
        h_frame, w_frame = resized.shape[:2]
        cx_frame = w_frame // 2   # Titik tengah frame
        cy_frame = h_frame // 2

        # 2. Konversi BGR → HSV
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        self._last_hsv_frame = hsv

        # 3. Thresholding berdasarkan rentang HSV
        lower = np.array([self.h_min, self.s_min, self.v_min], dtype=np.uint8)
        upper = np.array([self.h_max, self.s_max, self.v_max], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)

        # 4. Morfologi: erode untuk hilangkan noise, dilate untuk isi gap
        mask = cv2.erode(mask, self._erode_kernel, iterations=2)
        mask = cv2.dilate(mask, self._dilate_kernel, iterations=2)
        self._last_mask = mask

        # 5. Cari kontur
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Buat salinan frame untuk anotasi
        annotated = resized.copy()

        # Gambar garis tengah vertikal (referensi heading)
        cv2.line(annotated, (cx_frame, 0), (cx_frame, h_frame),
                 (100, 100, 100), 1, cv2.LINE_AA)

        if not contours:
            return self._empty_result(annotated)

        # 6. Pilih kontur terbesar
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        # Filter area terlalu kecil (noise)
        if area < 50:
            return self._empty_result(annotated)

        # 7. Hitung centroid via moments
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return self._empty_result(annotated)

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # 8. Hitung offset dari tengah frame
        offset_x = cx - cx_frame
        offset_y = cy - cy_frame

        # 9. Bounding rectangle
        bx, by, bw, bh = cv2.boundingRect(largest)

        # ── Anotasi overlay ──────────────────────────────────
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

        return {
            "detected": True,
            "cx": cx,
            "cy": cy,
            "area": area,
            "bbox": (bx, by, bw, bh),
            "offset_x": offset_x,
            "offset_y": offset_y,
            "frame_annotated": annotated,
        }

    # ─────────────────────────────────────────────────────────
    # Preview mask HSV (untuk debugging threshold)
    # ─────────────────────────────────────────────────────────
    def get_mask_preview(self):
        """
        Kembalikan frame preview mask HSV terkini.
        Digunakan oleh endpoint /hsv_preview untuk debugging.
        """
        if self._last_mask is None:
            # Kembalikan gambar hitam jika belum ada mask
            blank = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH), dtype=np.uint8)
            return cv2.cvtColor(blank, cv2.COLOR_GRAY2BGR)

        # Konversi mask 1-channel ke 3-channel agar bisa di-encode sebagai JPEG
        mask_bgr = cv2.cvtColor(self._last_mask, cv2.COLOR_GRAY2BGR)
        return mask_bgr

    # ─────────────────────────────────────────────────────────
    # Hasil kosong (tidak ada deteksi)
    # ─────────────────────────────────────────────────────────
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

    # ─────────────────────────────────────────────────────────
    # Getter HSV saat ini (untuk sinkronisasi UI)
    # ─────────────────────────────────────────────────────────
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
