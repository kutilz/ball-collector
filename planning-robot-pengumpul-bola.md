# Planning Skripsi — Robot Pengumpul Bola Pingpong Otonom

> Robot mobile berbasis ESP32-CAM + Arduino Uno yang mendeteksi, mendekati, dan
> mengumpulkan bola pingpong secara otomatis menggunakan penggerak mecanum.

---

## 1. Daftar Komponen (Final)

### Sudah dimiliki / dikonfirmasi

| Komponen                   | Jumlah          | Fungsi                                                          |
| -------------------------- | --------------- | --------------------------------------------------------------- |
| ESP32-CAM                  | 1               | Kamera nirkabel (MJPEG stream) + relay command WiFi→UART        |
| Laptop (RTX 5060)          | 1               | Ground station: deteksi, brain (state machine), web UI, logging |
| Router kecil / hotspot HP  | 1               | Jaringan WiFi bersama laptop ↔ ESP32-CAM (station mode)         |
| Arduino Uno                | 1               | Low-level controller (kinematik mecanum + servo + failsafe)     |
| DRV8833                    | 2               | Driver 4 motor DC mecanum (2 channel/chip)                      |
| Mecanum wheel + gearbox DC | 4               | Penggerak omnidirectional                                       |
| MG996R servo               | 1               | Aktuator collector (flipper/sweeper)                            |
| MPU6050 (IMU)              | 1               | Heading & koreksi drift saat strafe                             |
| Baterai 2S LiPo            | 1 (+1 cadangan) | Sumber daya motor + logic                                       |
| XL4015 (buck)              | 1               | Step-down ke rail 5V (motor logic + servo)                      |
| Logic Level Converter      | 1               | Shift level UART (Uno 5V → ESP32 3.3V) — opsional               |

### Catatan keputusan komponen

- **DRV8833 dipilih (bukan DRV8825).** DRV8825 = driver STEPPER, tidak bisa
  menggerakkan motor DC. DRV8833 = dual H-bridge DC, efisien, dropout rendah,
  cocok untuk beban ringan (bola pingpong). Batas praktis ~1.2A continuous /
  ~2A peak per channel — **verifikasi running current motor < ~1A** biar tidak
  thermal cutoff.
- **XL4015** sanggup arus MG996R (stall ~2.5A). Beri rail 5V terpisah dari motor.
- **MPU6050** menambah closed-loop heading → strafe mecanum lebih lurus,
  sekaligus jadi bab "sensor fusion" kecil di laporan.
- **Logic Level Converter** kemungkinan hanya perlu untuk jalur Uno→ESP32.

### Rekomendasi tambahan (opsional, naikin kualitas thesis)

- **Hopper/penampung bola** di badan robot (bagian mekanik wajib).
- **Sensor cahaya / lux meter** (boleh pakai HP) untuk variabel pengujian.
- Kapasitor bulk (≥470µF) di rail motor + kapasitor keramik 0.1µF di terminal
  motor untuk meredam noise.

---

## 2. Arsitektur Sistem

**Pembagian peran (HYBRID): Laptop = otak + mata + web UI, ESP32-CAM = kamera +
relay nirkabel, Arduino Uno = low-level controller.**

> Prinsip: laptop pegang HIGH-LEVEL (persepsi + planning), Arduino pegang
> LOW-LEVEL (kinematik + IMU + safety). Latency WiFi hanya memengaruhi keputusan
> high-level, bukan inner loop kontrol motor → aman untuk robot yang bergerak
> pelan seperti ball collector.

```
   +-------------------------+      WiFi (LAN/hotspot)     +----------------+
   |   LAPTOP (ground stn)   |  <== MJPEG stream ========  |   ESP32-CAM    |
   | - terima video stream   |                            | - kamera       |
   | - deteksi (HSV / YOLO)  |  == command (HTTP/socket)=> | - WiFi relay   |
   | - state machine (brain) |                            +-------+--------+
   | - web dashboard (Flask) |                                    | UART
   | - logging CSV           |                            +-------v--------+
   +-------------------------+                            |  Arduino Uno   |
                                                          | - mecanum kine |
                                                          | - heading hold |
                                                          | - servo + WATCHDOG
                                                          +---+----+----+--+
                                                              |    |    |
                                                       2xDRV8833  Servo  MPU6050
                                                       4 motor   MG996R   (I2C)
```

### Alur data

1. ESP32-CAM streaming MJPEG ke laptop lewat WiFi (mis. QVGA ~10–15 fps).
2. Laptop konversi HSV → threshold oranye → kontur terbesar → centroid (x,y) +
   luas blob. (`offset_x` → arah belok; `luas blob` → estimasi jarak.)
3. State machine di laptop putuskan aksi → kirim command ringkas ke ESP32-CAM
   (mis. `"VX,VY,W"` vektor kecepatan, atau `"SEARCH/APPROACH/COLLECT"`).
4. ESP32-CAM teruskan command ke Arduino via UART.
5. Arduino terjemahkan ke 4 kecepatan roda (inverse kinematics) + koreksi heading
   (MPU6050) + trigger servo saat COLLECT. **Jika tak ada command dalam X ms →
   watchdog stop semua motor.**

### Kenapa pembagian ini

- Web interface di laptop = simpel (semua di satu mesin, tinggal buka browser).
- Deteksi di laptop = jauh lebih kuat & mudah di-debug/visualisasi (RTX 5060),
  YOLO jadi opsi gratis. ESP32-CAM tak lagi terbebani deteksi.
- GPIO ESP32-CAM tersedot kamera → cukup untuk stream + 1 UART relay.
- Pin Uno ketat: 2× DRV8833 butuh banyak pin, dan library Servo memakai Timer1
  (bentrok PWM pin 9/10). **Wajib bikin pin mapping di awal.**

### Catatan koneksi WiFi & failsafe (WAJIB)

- **Station mode**: ESP32-CAM + laptop nyambung ke router kecil / hotspot HP yang
  sama; akses ESP32-CAM via static IP. (Jangan AP mode → laptop kehilangan
  internet saat development.)
- **Watchdog Arduino**: bila tidak menerima command valid dalam window tertentu
  (mis. 300–500 ms), motor otomatis berhenti. Wajib agar robot tidak lepas
  kendali saat WiFi drop.
- **Trade-off jujur**: deteksi di laptop = ini BUKAN edge-AI lagi (persepsi di
  ground station). Tidak masalah untuk skripsi "robot otonom pengumpul bola";
  jadi pertimbangan hanya jika framing wajib menonjolkan edge-AI.

---

## 3. Arsitektur Power

```
  2S LiPo (7.4–8.4V)
      |
      +------------------------------> 2x DRV8833  (VM motor)  -> 4 motor mecanum
      |
      +---> XL4015 (buck -> 5V) ---+--> rail 5V servo (MG996R)
                                   +--> rail 5V logic (Uno, level converter)
      |
      +---> (ESP32-CAM 5V in via buck terpisah / rail bersih)

  COMMON GROUND wajib semua modul. Cap bulk di rail motor + cap keramik di motor.
```

- **Pisahkan rail motor dan rail logic.** Spike motor/servo bisa nge-reset MCU.
- MG996R idealnya rail 5V sendiri (atau XL4015 yang sama tapi cap besar), jangan
  numpang 3.3V/5V regulator board Arduino.
- Ukur tegangan rail saat motor + servo aktif bersamaan (cek sag).

---

## 4. Strategi Vision (deteksi di LAPTOP)

**Deteksi dijalankan di laptop** (OpenCV/Python), bukan di ESP32-CAM. ESP32-CAM
hanya streaming frame.

- **Metode utama: HSV color segmentation + contour centroid.** Untuk satu bola
  oranye, ini lebih simpel, lebih robust, real-time, dan NOL kerja dataset/training.
- **Pakai bola pingpong ORANYE**, bukan putih. Oranye gampang di-threshold di
  ruang warna HSV dan robust terhadap background; putih ketukar lantai/dinding.
- Pipeline: terima stream → resize kecil → BGR→HSV → inRange(oranye) →
  morphology (erode/dilate) → findContours → ambil terbesar → centroid + area.
- Kalibrasi range HSV di kondisi cahaya arena (paling enak via slider di web UI).

### YOLO — opsional, bukan default

- Dengan RTX 5060, YOLO jalan ngebut di laptop (bukan bottleneck).
- TAPI untuk satu bola oranye, YOLO **overkill** — butuh anotasi + training,
  sementara HSV sudah cukup dan lebih reliable.
- YOLO baru worth kalau: bola multi-warna, banyak oklusi, atau butuh "bab deep
  learning" untuk bobot skripsi. **Rekomendasi: HSV sebagai primary, YOLO sebagai
  pembanding opsional** (bisa jadi sub-bab "perbandingan metode deteksi" → nambah
  data eksperimen Bagian 7.1).

---

## 5. Strategi Collection (Mekanik)

**Rekomendasi: scoop/ramp depan + flipper servo + hopper** (bukan gripper presisi).

Alasan: bola pingpong ringan, licin, gampang kabur saat di-grip, dan one-by-one
lambat. Robot menyetir masuk ke bola → bola naik ramp rendah → MG996R menyapu/
flip bola ke hopper di belakang. Servo tetap kepakai, fungsinya sweeping.

> Pakai gripper presisi **hanya jika** framing skripsi mengharuskan ada
> "manipulator". Kalau framing-nya "robot otonom pengumpul" → scoop+flipper menang.

---

## 6. State Machine (Logika Kontrol)

```
[SEARCH] --bola terdeteksi--> [APPROACH] --bola dekat & terpusat--> [COLLECT]
   ^                                |                                    |
   |          bola hilang  <--------+                                    |
   +------------------------------ selesai collect <---------------------+
```

| State    | Aksi                                               | Transisi keluar                          |
| -------- | -------------------------------------------------- | ---------------------------------------- |
| SEARCH   | Putar/patroli cari bola                            | Blob oranye terdeteksi                   |
| APPROACH | Maju + koreksi offset_x ke 0, jaga heading (IMU)   | Luas blob > threshold (dekat) & terpusat |
| COLLECT  | Berhenti, jalankan sweep servo, masukkan ke hopper | Servo selesai 1 siklus                   |
| (loop)   | Kembali ke SEARCH                                  | —                                        |

> Catatan: state machine ini jalan di LAPTOP (high-level). Arduino hanya
> mengeksekusi command low-level + watchdog.

---

## 6b. Web Interface (Dashboard di Laptop)

Semua jalan di laptop (Flask/FastAPI + browser), diakses via `localhost:port`
atau IP laptop di LAN. Karena terpusat di laptop, akses & development gampang.

### Komponen dashboard

- **Live video + overlay deteksi** (bounding box / centroid bola, real-time).
- **Slider tuning HSV** (H/S/V min-max) — ubah threshold langsung tanpa re-flash.
  Penyelamat waktu saat kalibrasi → langsung mendukung data variasi pencahayaan.
- **Status state machine** + telemetri: heading (IMU), tegangan baterai, command
  terkini, FPS deteksi.
- **Kontrol manual** (maju/mundur/strafe/putar) + tombol start/stop AUTO mode.
- **Logging CSV**: tombol mulai/stop perekaman data → langsung jadi data BAB IV
  (timestamp, state, posisi bola, command, hasil collect, dll).

### Stack yang disarankan

- Backend: Python + Flask/FastAPI (kamu sudah biasa Flask) + OpenCV untuk deteksi.
- Frontend: HTML/JS sederhana (MJPEG `<img>` untuk video, fetch/WebSocket untuk
  telemetri & command). Tidak perlu framework berat.
- Komunikasi ke robot: HTTP request / WebSocket / UDP ke ESP32-CAM (static IP).

### Implikasi arsitektur untuk kemudahan akses

- ESP32-CAM cukup expose 2 endpoint: `/stream` (MJPEG) dan `/cmd` (terima command
  → forward ke Arduino via UART). Sederhana & ringan.
- Semua "kepintaran" (deteksi, keputusan, UI, log) terpusat di satu proses Python
  di laptop → mudah debug, mudah ambil data, mudah demo ke dosen.

---

## 7. Data yang Diambil (per Subsistem)

### 7.1 Subsistem Deteksi (Vision)

- Precision, Recall, F1-score (dari TP / FP / FN).
- Detection rate vs jarak (tiap 20 cm s/d jarak maksimum).
- Detection rate vs tingkat cahaya (redup / normal / terang, ukur lux).
- Latency / FPS pemrosesan di laptop (end-to-end termasuk stream WiFi).
- (Opsional) Perbandingan HSV vs YOLO: akurasi & FPS.

### 7.2 Subsistem Navigasi / Locomotion

- Akurasi posisioning: error jarak berhenti robot ke bola (cm) sebelum collect.
- Waktu tempuh ke bola vs jarak awal.
- Drift mecanum saat strafe: gerak menyamping X cm, ukur deviasi melintang →
  validasi kinematik + efek koreksi IMU (uji dengan/tanpa MPU6050).
- Repeatability gerakan (std deviasi posisi akhir untuk command sama).

### 7.3 Subsistem Collection

- Success rate collect per bola (%).
- Waktu per bola (detik).

### 7.4 Level Sistem (Integrated — paling penting)

- Overall success rate clear lapangan (%).
- Total waktu clear N bola tersebar (detik).
- Coverage: % bola terkumpul dalam waktu tetap.
- Konsumsi daya / endurance baterai (mAh per sesi, durasi operasi).

---

## 8. Desain Eksperimen

- **Arena terkontrol** ukuran tetap (mis. 2×2 m) dengan grid penanda posisi.
- Variabel yang divariasikan:
  - Jumlah bola (mis. 1, 3, 5, 10).
  - Pola posisi bola (fixed vs random).
  - Tingkat cahaya (redup / normal / terang, dicatat lux-nya).
  - Jarak awal robot–bola.
- **Minimal 10–30 trial per kondisi.** Laporkan `mean ± std` dan success rate (%)
  dengan jumlah trial (n). Hindari hanya 1–2 kali percobaan.
- **Uji subsistem (isolasi) dulu, baru integrated.** Kalau ada subsistem jelek,
  ketahuan sumbernya di pembahasan.
- Variabel kontrol (dijaga konstan): ukuran arena, jenis lantai, voltase baterai
  awal, warna/ukuran bola.

---

## 9. Metodologi Pengembangan

Pakai **R&D (Research & Development)** atau **Prototyping** — cocok untuk
pembangunan robot iteratif:

```
Analisis kebutuhan -> Desain (mekanik/elektrik/software)
   -> Implementasi -> Pengujian -> Evaluasi -> (iterasi balik ke desain)
```

---

## 10. Sistematika Penulisan (Struktur Bab)

- **BAB I — Pendahuluan**
  Latar belakang, rumusan masalah, tujuan, batasan masalah, manfaat.
- **BAB II — Landasan Teori**
  Kinematika mecanum (inverse kinematics, roller 45°, persamaan kecepatan tiap
  roda), color segmentation HSV, motor driver H-bridge, IMU/MPU6050, ESP32-CAM,
  komunikasi UART.
- **BAB III — Metodologi / Perancangan**
  Blok diagram sistem, flowchart, perancangan mekanik, perancangan elektrik
  (skematik + power), perancangan software (state machine), perancangan pengujian.
- **BAB IV — Hasil & Pembahasan**
  Seluruh data Bagian 7 + analisis (per subsistem lalu integrated).
- **BAB V — Kesimpulan & Saran**

> **Tip nilai:** Bab kinematika mecanum (turunan inverse kinematics lengkap)
> adalah "emas" untuk menunjukkan kedalaman matematis — sekaligus justifikasi
> kuat kenapa pakai mecanum meski butuh 2 driver.

---

## 11. To-Do / Urutan Pengerjaan yang Disarankan

1. [ ] Verifikasi spesifikasi motor mecanum (running current vs limit DRV8833).
2. [ ] Rakit power architecture + ukur sag tegangan saat beban penuh.
3. [ ] Pin mapping Uno (2× DRV8833 + servo + I2C MPU6050) — hindari konflik timer.
4. [ ] Tes kinematik mecanum open-loop (maju, mundur, strafe, putar).
5. [ ] Integrasi MPU6050 untuk koreksi heading + watchdog stop di Arduino.
6. [ ] Setup WiFi station mode + MJPEG stream ESP32-CAM (uji FPS ke laptop).
7. [ ] Protokol command laptop → ESP32-CAM (`/cmd`) → UART → Arduino.
8. [ ] Kalibrasi HSV deteksi bola oranye di laptop (via slider web UI).
9. [ ] Bangun web dashboard (video overlay, slider HSV, telemetri, manual, log CSV).
10. [ ] Rakit mekanik collector (ramp + flipper + hopper).
11. [ ] Integrasi state machine penuh (di laptop).
12. [ ] Pengujian subsistem → pengujian integrated → ambil data.

---

## Item yang Masih Perlu Diputuskan

- Spesifikasi pasti motor mecanum (RPM, voltase, stall current) → konfirmasi
  kecocokan DRV8833.
- Apakah ada encoder roda (closed-loop) atau open-loop + IMU saja.
- Framing collector: scoop+flipper (rekomendasi) vs gripper presisi.
- Ukuran arena & jumlah bola final untuk skenario pengujian.
