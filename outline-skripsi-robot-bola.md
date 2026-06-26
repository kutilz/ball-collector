# Outline Skripsi — Robot Pengumpul Bola Pingpong Otomatis

> Konsep gabungan (draft lama + planning baru). Judul usulan:
> **"Implementasi Computer Vision (YOLOv8) dan Kinematika Roda Mecanum pada
> Robot Pengumpul Bola Pingpong Otomatis Berbasis Sistem Terdistribusi"**
>
> Catatan judul: gunakan "Otomatis/Otomasi" konsisten dengan nama prodi
> (Otomasi Industri), hindari "Automasi".

---

## Halaman Awal (front matter)
- Halaman judul
- Lembar pengesahan
- Pernyataan keaslian naskah
- Ucapan terima kasih *(PERBAIKI: draft lama menyebut judul proyek lain
  "Manajemen Energi Gedung" — ganti ke judul skripsi ini)*
- Abstrak (ID) + kata kunci *(ganti lorem ipsum)*
- Abstract (EN) + keywords *(ganti lorem ipsum)*
- Daftar isi, daftar gambar, daftar tabel, daftar lampiran *(lengkapi)*

---

## BAB I — PENDAHULUAN

### 1.1 Latar Belakang Penelitian
- Masalah: pengumpulan bola pingpong manual saat latihan → buang waktu & tenaga.
- Gap dari SotA (pertahankan kerangka draft, tapi sesuaikan ke pingpong):
  - Persepsi: kamera rendah → blind spot.
  - Deteksi HSV tradisional rentan noise fotometrik / pencahayaan dinamis.
  - Mekanisme intake: **rombak argumen anti-suction** — alasan "inersia bola
    tenis" tidak berlaku untuk pingpong; ganti ke isu kebutuhan presisi
    penyelarasan & kecepatan koleksi banyak bola.
- Solusi yang diusulkan: CV terdistribusi (YOLOv8 di laptop), navigasi mecanum
  holonomik, active intake silinder TPU.

### 1.2 Rumusan Masalah
1. Bagaimana merancang CV terdistribusi (YOLOv8 di laptop + ESP32-CAM) yang
   akurat dan real-time untuk deteksi bola pingpong?
2. Bagaimana memformulasikan & mengimplementasikan kinematika mecanum (4WD)
   untuk navigasi holonomik mengejar bola, dengan koreksi heading (IMU)?
3. Bagaimana merancang & menguji mekanisme active intake silinder TPU (MG996R)
   untuk efektivitas penangkapan bola?

### 1.3 Tujuan Penelitian
*(cerminkan 1.2, kalimat afirmatif)*

### 1.4 Manfaat Penelitian
- Teoritis: arsitektur pemrosesan visual terdistribusi; tribologi material TPU
  pada mekanisme active intake.
- Praktis: otomasi koleksi bola di fasilitas latihan.

### 1.5 Ruang Lingkup & Batasan Masalah
- Target: bola pingpong oranye; lingkungan indoor, lantai datar.
- Deteksi: YOLOv8 di laptop (GPU), HSV sebagai baseline pembanding.
- Sasis: 4× mecanum DC + 2× DRV8833; kinematik dihitung di Arduino.
- Intake: silinder TPU (cetak Bambu Lab A1) digerakkan MG996R continuous.
- MCU: ESP32-CAM (kamera + relay) + Arduino Uno (low-level controller).
- Pan-tilt + PID kamera = opsional (enhancement), bukan core.

### 1.6 Sistematika Penulisan

---

## BAB II — TINJAUAN PUSTAKA & LANDASAN TEORI

### 2.1 Penelitian Terdahulu yang Relevan
- Telaah SotA + identifikasi gap *(VERIFIKASI tiap sitasi [n] real & relevan,
  renomori urut kemunculan — gaya IEEE)*.

### 2.2 Landasan Teori *(perbaiki hierarki: semua sub berikut = H3 di bawah 2.2)*
- 2.2.1 Computer Vision & YOLOv8 (detection, bukan segmentation)
- 2.2.2 Segmentasi Warna HSV (sebagai baseline pembanding)
- 2.2.3 Komunikasi Nirkabel & Latensi (WiFi, MJPEG vs UDP)
- 2.2.4 Kinematika Roda Mecanum & Inverse Kinematics
- 2.2.5 IMU (MPU6050) & Koreksi Heading (complementary filter)
- 2.2.6 Motor DC, Driver H-Bridge (DRV8833) & PWM
- 2.2.7 Mekanisme Active Intake & Tribologi Material TPU
- 2.2.8 Servo MG996R (modifikasi continuous rotation); PID pan-tilt (opsional)
- 2.2.9 Arsitektur Sistem Terdistribusi (laptop sebagai ground station)

### 2.3 Kerangka Berpikir
- Diagram alur: input (lapangan banyak bola) → proses (YOLO → kinematik →
  intake TPU) → output (bola terkumpul). *(Lengkapi Gambar; saat ini hanya ada
  placeholder "Gambar 4".)*

---

## BAB III — METODOLOGI PENELITIAN

### 3.1 Metode Penelitian
- R&D / Prototyping: analisis kebutuhan → desain → implementasi → pengujian →
  evaluasi → iterasi.

### 3.2 Alat dan Bahan
- Hardware: ESP32-CAM, Arduino Uno, 2× DRV8833, 4× mecanum + gearbox DC,
  MG996R, MPU6050, 2S LiPo, XL4015, logic level converter.
- Software: Python/OpenCV, YOLOv8 (Ultralytics), Flask, Arduino IDE, Onshape.

### 3.3 Perancangan Sistem
- 3.3.1 Blok diagram & arsitektur (laptop ↔ ESP32-CAM ↔ Arduino ↔ aktuator)
- 3.3.2 Perancangan mekanik: sasis mecanum, mount kamera (elevated), silinder
  intake TPU, hopper — desain Onshape, fabrikasi Bambu Lab A1.
- 3.3.3 Perancangan elektrik: skematik, arsitektur power (2S LiPo → XL4015 →
  rail 5V terpisah motor/logic), common ground, kapasitor.
- 3.3.4 Perancangan perangkat lunak:
  - Pipeline deteksi: YOLOv8 (primary) + HSV (baseline)
  - State machine: SEARCH → APPROACH → COLLECT
  - Inverse kinematics di Arduino + heading hold (MPU6050)
  - Protokol komunikasi: laptop → ESP32-CAM (`/cmd`) → UART → Arduino + watchdog
  - Web dashboard (Flask): video overlay, slider HSV, telemetri, manual, log CSV

### 3.4 Perancangan Pengujian
- Skenario arena terkontrol (mis. 2×2 m, grid), variabel (jumlah bola, posisi,
  cahaya/lux, jarak awal), min. 10–30 trial/kondisi.
- Metrik per subsistem (lihat BAB IV) + uji isolasi sebelum integrated.

### 3.5 Tempat dan Waktu Penelitian

---

## BAB IV — HASIL DAN PEMBAHASAN

### 4.1 Hasil Implementasi
- Realisasi mekanik, elektrik, software, dan dashboard.

### 4.2 Pengujian Subsistem Deteksi (Vision)
- **YOLOv8 vs HSV**: precision, recall, F1, FPS.
- Detection rate vs jarak (tiap 20 cm), vs tingkat cahaya (lux).
- Latency end-to-end (termasuk stream WiFi) — **ukur**, jangan asumsi <50ms.

### 4.3 Pengujian Subsistem Navigasi
- Akurasi posisioning (error cm), drift strafe (dengan vs tanpa IMU),
  waktu tempuh vs jarak, repeatability.

### 4.4 Pengujian Subsistem Intake
- Success rate penangkapan (%), waktu per bola.

### 4.5 Pengujian Sistem Terintegrasi
- Overall success rate clear lapangan, total waktu clear N bola, coverage,
  konsumsi daya / endurance.

### 4.6 Pembahasan
- Analisis hasil, keterbatasan, perbandingan dengan SotA.

---

## BAB V — PENUTUP
- 5.1 Kesimpulan (jawab rumusan masalah)
- 5.2 Saran (pengembangan lanjut, mis. pan-tilt PID, UDP, multi-warna)

---

## DAFTAR PUSTAKA
*(WAJIB dibuat — sitasi [1]–[15] sudah dipakai tapi reference list belum ada.
Pastikan format IEEE konsisten & semua sumber real.)*

## LAMPIRAN
- Kode program, skematik, datasheet, dataset YOLO, foto alat, data uji mentah.

---

## Checklist Perbaikan Cepat (dari draft lama)
- [ ] Ganti abstrak & abstract (saat ini lorem ipsum)
- [ ] Perbaiki judul di ucapan terima kasih (salah proyek)
- [ ] Samakan tanggal (cover 2024 / pernyataan 2026 / ucapan 2024)
- [ ] Verifikasi & renomori sitasi (IEEE, urut kemunculan)
- [ ] Perbaiki hierarki heading Landasan Teori (sub jadi H3)
- [ ] Konsisten "Otomasi" (bukan "Automasi")
- [ ] Commit target = pingpong; rombak argumen anti-suction
- [ ] Turunkan register bahasa (terlalu berbunga) ke akademik lugas
- [ ] Tambah BAB III & Daftar Pustaka
