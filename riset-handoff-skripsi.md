# Handoff Prompt — Riset Bahan Skripsi (untuk Claude Research / deep-research)

> Paste blok di bawah ke Claude Research. Tujuannya mengumpulkan **bahan & sitasi nyata**
> untuk BAB I (latar belakang/SotA) dan BAB II (landasan teori) skripsi, sesuai
> ruang lingkup yang sudah dikunci. Bukan untuk menulis bab — hanya menyiapkan amunisi.

---

## PROMPT

Saya sedang menyusun skripsi S-1 Pendidikan Teknik Otomasi Industri dan Robotika (Universitas
Pendidikan Indonesia) berjudul **"Implementasi Computer Vision dan Kinematika Roda Mecanum pada
Otomasi Robot Pengumpul Bola Ping-Pong"**. Saya butuh kamu melakukan riset literatur mendalam dan
mengumpulkan **sumber akademik yang real dan dapat diverifikasi** sebagai bahan BAB I dan BAB II.

### Konteks sistem yang BENAR-BENAR dibangun (jangan menyimpang dari ini)
Robot pengumpul bola ping-pong otonom, arsitektur **terdistribusi**:
- **Deteksi (utama): segmentasi warna HSV** di OpenCV (laptop) — BGR→HSV→inRange→erode/dilate→
  findContours→kontur terbesar→centroid via moments→offset dari titik tengah frame.
- **YOLOv8 dipakai sebagai PEMBANDING offline**, bukan detektor utama: dilatih pada dataset bola,
  dievaluasi precision/recall/F1/mAP/FPS, lalu dibandingkan dengan HSV. (Bukan deep learning yang
  jalan real-time di robot.)
- **Sasis: 4 roda Mecanum (4WD)**, motor DC + 2× driver H-bridge DRV8833. Kinematika invers
  dihitung di **Arduino Uno** (FL=vx+vy+ω, FR=vx−vy−ω, RL=vx−vy+ω, RR=vx+vy−ω), output PWM.
- **IMU MPU6050**: heading dari **integrasi gyro sumbu-Z saja** (bukan complementary filter).
- **Kamera ESP32-CAM fixed** (tidak ada pan-tilt). Video via **MJPEG over HTTP/WiFi**
  (bukan UDP). Command motor/servo via HTTP GET ke ESP32 → diteruskan UART ke Arduino.
- **Intake: servo standar** menyapu buka-tutup (sweep antar sudut), bukan silinder rotasi-kontinu.
- **Kontrol otonom: Finite State Machine** IDLE→SEARCH(putar cari bola)→APPROACH(maju +
  **P-controller** steering dari offset bola)→COLLECT(servo sweep). Navigasi auto pakai
  maju+rotasi (holonomik/strafe tersedia di kinematika & kontrol manual).
- **Ground station: Flask + WebSocket**, dashboard video overlay, slider kalibrasi HSV, telemetri,
  kontrol manual, log CSV. Ada **rekayasa keselamatan**: watchdog motor (timeout 500 ms),
  motion-heartbeat (0.15 s), clamp batas PWM, kalibrasi parameter runtime.

### Yang TIDAK boleh diklaim sudah jadi (ini hanya untuk BAB V "Saran" / konteks pembanding teori)
UDP low-latency, pan-tilt + PID tracking, silinder TPU rotasi-kontinu, complementary filter.
Tetap riset teorinya secukupnya supaya bisa dibahas sebagai justifikasi pilihan & arah pengembangan,
tapi jangan diframekan sebagai bagian sistem yang berjalan.

### Yang saya butuh kamu kumpulkan

**A. Penelitian terdahulu / State of the Art (untuk BAB I gap analysis & BAB II.1):**
1. Robot pengumpul bola olahraga (tenis, tenis meja/ping-pong) — sistem yang ada, navigasi,
   metode deteksi, dan **keterbatasannya** (blind spot kamera rendah, deteksi rapuh, mekanisme
   intake gagal). Cari yang real & bisa disitir.
2. Deteksi bola memakai YOLO / deep learning pada robot atau aplikasi olahraga.
3. Robot mobil berbasis roda Mecanum (kontrol, kinematika, aplikasi).
4. Studi yang membandingkan **segmentasi warna klasik (HSV) vs deteksi berbasis CNN/deep learning**.

**B. Landasan teori (untuk BAB II.2) — untuk tiap topik beri sintesis 2–3 paragraf siap-adaptasi
+ rumus/persamaan kunci + 3–6 sumber nyata:**
1. Computer Vision & ruang warna HSV: model HSV, thresholding `inRange`, operasi morfologi
   (erosi/dilasi), deteksi kontur, moments & centroid. (Detektor utama — bahas paling dalam.)
2. Object detection deep learning: CNN, detektor satu-tahap (single-stage), keluarga YOLO,
   **arsitektur YOLOv8** (anchor-free, backbone/neck/head, C2f), proses training, augmentasi.
3. Metrik evaluasi deteksi: precision, recall, F1-score, IoU, mAP, confusion matrix, FPS —
   penting karena dipakai membandingkan HSV vs YOLOv8.
4. Kinematika roda Mecanum: geometri roller 45°, superposisi vektor, **matriks kinematika invers
   4WD**, hubungan ke PWM/RPM.
5. IMU MPU6050 & estimasi heading: giroskop, integrasi sudut, **drift/bias** integrasi gyro,
   dead-reckoning. (Complementary filter = konteks pembanding + saran.)
6. Aktuator gerak: motor DC, driver H-bridge **DRV8833**, prinsip PWM kontrol kecepatan & arah.
7. Komunikasi nirkabel & streaming: WiFi, **MJPEG streaming** vs alternatif (UDP), latensi
   end-to-end pada sistem kendali real-time, ESP32-CAM.
8. Servo & mekanisme pengumpul; material **TPU** (sifat elastomerik, gesekan/compliance untuk
   memegang bola) — diframekan sebagai mekanisme sweep, bukan silinder kontinu.
9. Sistem terdistribusi/ground station: arsitektur client-server, Flask, WebSocket/Socket.IO.
10. Finite State Machine & **P-controller** (proporsional) untuk navigasi visual servoing.

### Format keluaran yang saya minta
- Tulis dalam **Bahasa Indonesia akademik lugas** (boleh kutip sumber berbahasa Inggris).
- Susun **per subbab** persis seperti daftar A & B di atas.
- Untuk tiap subbab: sintesis ringkas + daftar sumber dengan **judul, penulis, tahun, venue/jurnal,
  dan DOI/URL**. Tandai persamaan/gambar penting yang layak disitir.
- **Hanya sumber yang benar-benar ada.** Jika tidak yakin sebuah referensi nyata, tandai
  "[PERLU VERIFIKASI]" — jangan mengarang judul, penulis, atau DOI.
- Prioritaskan sumber yang dapat diakses (jurnal/konferensi IEEE, scienceDirect, MDPI, arXiv,
  dokumentasi Ultralytics/OpenCV resmi). Boleh sertakan jurnal/skripsi Indonesia (SINTA/Garuda)
  yang relevan untuk konteks lokal.
- Di akhir, buat **satu daftar pustaka gabungan bergaya IEEE**, dinomori, siap saya pakai.

Tujuan akhir: saya bisa menulis BAB I dan BAB II dengan sitasi yang valid dan argumen gap yang
sesuai dengan sistem nyata di atas — bukan versi aspirasional.
