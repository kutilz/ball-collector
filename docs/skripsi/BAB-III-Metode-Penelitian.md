# BAB III — METODE PENELITIAN

> **Catatan penulisan (hapus saat dipindah ke Word):**
> - Sitasi IEEE `[n]` → `Daftar-Pustaka.md`. Istilah baku: *machine learning*;
>   mekanisme intake = **gripper cetak 3D digerakkan servo**.
> - **Caption UPI:** judul **tabel di ATAS**, judul **gambar di BAWAH**.
>   Placeholder: `[Gambar 3.x]`, `[Tabel 3.x]`.
> - Bagian **3.5 Tempat dan Waktu** wajib kamu isi sendiri (lokasi lab/rumah,
>   rentang bulan pengerjaan).
> - Nilai parameter (HSV, ambang area, kecepatan, dll.) diambil dari `config.py`
>   dan firmware — sesuaikan bila kamu mengubahnya sebelum sidang.

---

## 3.1 Metode Penelitian

Penelitian ini menggunakan metode **Penelitian dan Pengembangan** (*Research and
Development*, R&D) dengan pendekatan *prototyping*, yang sesuai untuk pembangunan
sistem robotik yang bersifat iteratif. Metode ini menempuh tahapan: analisis
kebutuhan, perancangan (mekanik, elektrik, dan perangkat lunak), implementasi,
pengujian, dan evaluasi, dengan kemungkinan iterasi kembali ke tahap
perancangan apabila hasil pengujian belum memenuhi kebutuhan. Tahapan tersebut
diringkas sebagai berikut.

1. **Analisis kebutuhan** — mengidentifikasi kebutuhan fungsional (deteksi bola,
   navigasi mendekati bola, pengumpulan bola) dan non-fungsional (keselamatan,
   kemudahan kalibrasi, pencatatan data).
2. **Perancangan** — merancang arsitektur sistem terdistribusi, mekanik sasis
   dan *intake*, sistem elektrik dan daya, serta perangkat lunak (deteksi,
   *state machine*, kinematika, komunikasi, dan dasbor).
3. **Implementasi** — fabrikasi mekanik (cetak 3D), perakitan elektronik,
   pemrograman *firmware* Arduino dan ESP32-CAM, serta pemrograman *ground
   station*.
4. **Pengujian** — pengujian per subsistem (deteksi, navigasi, *intake*)
   dilanjutkan pengujian sistem terintegrasi.
5. **Evaluasi** — menganalisis hasil pengujian, lalu melakukan iterasi perbaikan
   bila diperlukan.

[Gambar 3.1: Diagram alur metode penelitian R&D/prototyping —
Analisis kebutuhan → Perancangan → Implementasi → Pengujian → Evaluasi
(dengan panah iterasi balik ke Perancangan).]

## 3.2 Alat dan Bahan

### 3.2.1 Perangkat Keras

Perangkat keras yang digunakan dirangkum pada Tabel 3.1.

[Tabel 3.1: Daftar perangkat keras dan fungsinya]

| No | Komponen | Jumlah | Fungsi |
|----|----------|:------:|--------|
| 1 | ESP32-CAM (OV2640) | 1 | Kamera nirkabel (*streaming* MJPEG) + penerus perintah WiFi→UART |
| 2 | Arduino Uno | 1 | Pengendali tingkat rendah: kinematika Mecanum, servo, IMU, *watchdog* |
| 3 | Laptop (ber-GPU) | 1 | *Ground station*: deteksi, *state machine*, dasbor web, pencatatan |
| 4 | Router/*hotspot* | 1 | Jaringan WiFi bersama laptop ↔ ESP32-CAM (mode *station*) |
| 5 | Driver motor DRV8833 | 2 | Dua *driver* dual H-bridge untuk 4 motor DC |
| 6 | Roda Mecanum + gearbox motor DC | 4 | Penggerak omnidireksional (4WD) |
| 7 | Servo MG996R | 1 | Aktuator gripper pengumpul bola |
| 8 | Sensor IMU MPU6050 | 1 | Estimasi *heading* (giroskop sumbu-Z) |
| 9 | Baterai LiPo 2S (7,4 V) | 1 | Sumber daya motor dan logika |
| 10 | Modul *buck* XL4015 | 1 | Penurun tegangan ke rel 5 V (logika & servo) |
| 11 | *Logic level converter* | 1 | Penyesuai level UART (Uno 5 V ↔ ESP32 3,3 V) |
| 12 | Penampung bola (*hopper*) | 1 | Wadah bola hasil pengumpulan |
| 13 | Kapasitor *bulk* & keramik | secukupnya | Peredam *noise* pada rel motor |

### 3.2.2 Perangkat Lunak

[Tabel 3.2: Daftar perangkat lunak dan kegunaannya]

| No | Perangkat Lunak | Kegunaan |
|----|-----------------|----------|
| 1 | Python 3.11 + OpenCV | Pemrosesan citra (segmentasi HSV) di *ground station* |
| 2 | Flask + Flask-SocketIO + eventlet | Server web dasbor & komunikasi *real-time* |
| 3 | NumPy | Komputasi numerik citra |
| 4 | Arduino IDE | Pemrograman *firmware* Arduino Uno & ESP32-CAM |
| 5 | Ultralytics YOLOv8 + Google Colab | Pelatihan & evaluasi model pembanding (luring) |
| 6 | Roboflow / LabelImg | Anotasi dataset bola untuk pelatihan YOLOv8 |
| 7 | Onshape (CAD) | Perancangan mekanik (sasis, dudukan kamera, gripper, *hopper*) |
| 8 | Bambu Studio | Penyiapan cetak 3D |

## 3.3 Perancangan Sistem

### 3.3.1 Arsitektur dan Blok Diagram Sistem

Sistem dirancang sebagai **sistem terdistribusi** dengan pembagian peran:
**laptop** sebagai *ground station* yang menangani persepsi tingkat tinggi
(deteksi dan pengambilan keputusan) dan antarmuka pengguna; **ESP32-CAM**
sebagai sumber citra dan penerus perintah nirkabel; serta **Arduino Uno** sebagai
pengendali tingkat rendah (kinematika, aktuasi, dan keselamatan). Pembagian ini
didasari prinsip bahwa latensi WiFi hanya memengaruhi keputusan tingkat tinggi,
bukan lingkar kendali motor, sehingga aman untuk robot yang bergerak lambat
seperti pengumpul bola.

Alur data sistem adalah sebagai berikut:

1. ESP32-CAM mengalirkan citra MJPEG ke laptop melalui WiFi.
2. Laptop memproses citra (segmentasi HSV) untuk memperoleh *centroid* bola dan
   galat posisinya terhadap pusat *frame*.
3. *State machine* di laptop menentukan aksi dan menghasilkan vektor kecepatan
   $(v_x, v_y, \omega)$.
4. Perintah dikirim dari laptop ke ESP32-CAM melalui HTTP, lalu diteruskan ke
   Arduino Uno melalui UART.
5. Arduino menghitung kinematika invers Mecanum, membangkitkan PWM untuk keempat
   motor melalui DRV8833, serta menggerakkan servo gripper saat pengumpulan.
   Jika tidak menerima perintah dalam selang tertentu, *watchdog* menghentikan
   motor.

[Gambar 3.2: Blok diagram arsitektur sistem — Laptop (ground station) ↔ WiFi ↔
ESP32-CAM ↔ UART ↔ Arduino Uno → {2×DRV8833 → 4 motor Mecanum, servo MG996R,
MPU6050}.]

### 3.3.2 Perancangan Mekanik

Rancangan mekanik terdiri atas tiga bagian utama: sasis, dudukan kamera, dan
mekanisme *intake*. Seluruh komponen dirancang menggunakan perangkat lunak CAD
**Onshape** dan difabrikasi dengan pencetakan 3D mesin **Bambu Lab A1**.

- **Sasis Mecanum 4WD.** Sasis menempatkan empat roda Mecanum pada keempat sudut
  dengan orientasi rol yang sesuai (pola rol membentuk huruf O/X) agar
  superposisi gaya menghasilkan gerak holonomik. Empat motor DC ber-*gearbox*
  dipasang langsung pada tiap roda.
- **Dudukan kamera.** ESP32-CAM dipasang **tetap** (*fixed*) pada posisi yang
  ditinggikan agar memperluas bidang pandang ke area lantai di depan robot dan
  mengurangi area buta saat mendekati bola. Tidak digunakan mekanisme *pan-tilt*.
- **Mekanisme *intake* (gripper).** Pengumpulan bola menggunakan **gripper hasil
  cetak 3D** yang digerakkan satu servo MG996R. Bagian gripper yang bersentuhan
  dengan bola dicetak dari filamen **TPU** agar lentur (*compliant*) sehingga
  mengikuti bentuk bola dan meredam pantulan saat akuisisi. Gripper membuka
  (sudut kecil) untuk menerima bola lalu menutup (sudut besar) untuk
  mencengkeram dan mengarahkannya ke **penampung (*hopper*)** di badan robot.

[Gambar 3.3: Desain 3D robot (Onshape) — tampak sasis Mecanum, dudukan kamera
ESP32-CAM, gripper, dan hopper.]

### 3.3.3 Perancangan Elektrik

**Arsitektur daya.** Sumber daya berupa baterai LiPo 2S (7,4–8,4 V). Rel daya
**dipisah** antara motor dan logika untuk mencegah lonjakan arus motor/servo
mengganggu mikrokontroler:

- Baterai 2S → langsung ke dua DRV8833 (tegangan motor VM) → empat motor Mecanum.
- Baterai 2S → modul *buck* XL4015 → rel 5 V untuk logika (Arduino, *level
  converter*) dan servo MG996R.
- Seluruh modul menggunakan **ground bersama** (*common ground*).
- Kapasitor *bulk* (≥470 µF) dipasang pada rel motor dan kapasitor keramik
  0,1 µF pada terminal motor untuk meredam *noise*.

[Gambar 3.4: Diagram arsitektur daya — LiPo 2S → {DRV8833 (motor), XL4015 →
rel 5 V (logika & servo)}, common ground.]

**Pemetaan pin Arduino Uno.** Karena pustaka *Servo* memakai *Timer1* yang
menonaktifkan PWM pada pin 9 dan 10, pin PWM motor dialokasikan pada pin 3, 5, 6,
dan 11. Pemetaan pin ditunjukkan pada Tabel 3.3.

[Tabel 3.3: Pemetaan pin Arduino Uno]

| Fungsi | Pin PWM | Pin Arah |
|--------|:-------:|:--------:|
| Motor depan-kiri (FL) | 3 | 4 |
| Motor depan-kanan (FR) | 5 | 7 |
| Motor belakang-kiri (RL) | 6 | 8 |
| Motor belakang-kanan (RR) | 11 | 12 |
| Servo gripper | 2 | — |
| MPU6050 (I²C) | A4 (SDA), A5 (SCL) | — |
| UART ke ESP32-CAM | 0 (RX), 1 (TX) | — |
| LED indikator | 13 | — |

[Gambar 3.5: Skematik rangkaian elektrik keseluruhan.]

### 3.3.4 Perancangan Perangkat Lunak

Perangkat lunak terbagi atas *firmware* (Arduino dan ESP32-CAM) dan *ground
station* (Python). Pada *ground station*, modul disusun terpisah: **vision**
(deteksi), **brain** (*state machine*), **comms** (komunikasi & sumber video),
**logger** (pencatatan CSV), dan **app** (server web + lingkar utama).

#### a. Pipeline Deteksi (HSV) dan Pembanding YOLOv8

Pipeline deteksi utama berjalan di laptop dengan tahapan: *resize* frame ke
640×480 → konversi BGR→HSV → `inRange` dengan ambang warna oranye → operasi
morfologi (erosi dan dilasi) → `findContours` → pemilihan kontur terbesar →
penghitungan *centroid* dan luas → penghitungan galat *offset* terhadap pusat
*frame*. Nilai ambang HSV awal serta parameter morfologi dapat dikalibrasi
langsung melalui *slider* pada dasbor (lihat Tabel 3.4).

[Tabel 3.4: Parameter awal pipeline deteksi (dari `config.py`)]

| Parameter | Nilai awal | Keterangan |
|-----------|:----------:|------------|
| Rentang Hue (H) | 5–25 | Warna oranye bola |
| Rentang Saturation (S) | 100–255 | Kejenuhan |
| Rentang Value (V) | 100–255 | Kecerahan |
| Iterasi erosi / dilasi | 2 / 2 | Pembersihan *mask* |
| Luas kontur minimum | 50 px² | Ambang anti-*noise* |
| Resolusi proses | 640×480 | Ukuran frame kerja |

Sebagai pembanding, model **YOLOv8** dilatih secara **luring**: citra bola
dikumpulkan dan dianotasi (Roboflow/LabelImg), lalu dilatih di Google Colab
ber-GPU [21], [22]. Model hasil pelatihan dievaluasi pada set uji yang sama
dengan HSV, menggunakan metrik *precision*, *recall*, *F1-score*, dan FPS,
sehingga diperoleh perbandingan performa kedua metode (lihat Subbab 3.4).

#### b. State Machine (Logika Kendali Otonom)

Kendali otonom diatur oleh *finite state machine* dengan empat keadaan, sesuai
Tabel 3.5. Transisi antar keadaan ditentukan oleh status deteksi dan luas
kontur bola (sebagai estimasi jarak).

[Tabel 3.5: Definisi keadaan *state machine*]

| Keadaan | Aksi | Transisi keluar |
|---------|------|-----------------|
| IDLE | Diam, menunggu perintah mulai | Operator menekan mulai → SEARCH |
| SEARCH | Berputar perlahan mencari bola | Bola terdeteksi & luas ≥ ambang → APPROACH |
| APPROACH | Maju + koreksi arah *P-controller* | Bola hilang → SEARCH; luas ≥ ambang dekat → COLLECT |
| COLLECT | Berhenti, buka–tutup gripper, hitung bola | Sekuens selesai → SEARCH |

Pada keadaan APPROACH, kecepatan rotasi dihitung dengan kendali proporsional
$\omega = K_p \cdot e_x$, dengan $e_x$ galat *offset* horizontal bola dan $K_p$
faktor proporsional (nilai awal 0,5). Ambang transisi memakai luas kontur:
SEARCH→APPROACH pada luas ≥ 500 px², dan APPROACH→COLLECT pada luas ≥ 8000 px².

[Gambar 3.6: Diagram *state machine* IDLE–SEARCH–APPROACH–COLLECT.]

#### c. Kinematika Invers di Arduino

Arduino menerima vektor kecepatan $(v_x, v_y, \omega)$ dan menghitung kecepatan
keempat roda dengan bentuk kinematika invers tereduksi:

$$
\begin{aligned}
FL &= v_x + v_y + \omega, & FR &= v_x - v_y - \omega,\\
RL &= v_x - v_y + \omega, & RR &= v_x + v_y - \omega.
\end{aligned}
$$

Nilai keempat roda dinormalisasi bila ada yang melampaui 255, lalu dipetakan ke
besaran PWM (kecepatan) dan pin arah (maju/mundur) tiap motor. *Heading*
diperbarui dari integrasi giroskop sumbu-Z MPU6050 (rentang ±250 °/s,
sensitivitas 131 LSB/°/s, *DLPF* 44 Hz) dengan *dead zone* untuk laju sudut
kecil guna menahan *drift*.

#### d. Protokol Komunikasi dan Keselamatan

Komunikasi laptop→robot memisahkan dua kanal: **kanal video** (MJPEG dari
ESP32-CAM, port 81 `/stream`) dan **kanal perintah** (HTTP GET ke ESP32-CAM,
port 80 `/cmd`). Format perintah dan telemetri dirangkum pada Tabel 3.6.
Perintah diteruskan ESP32-CAM ke Arduino melalui UART 115200 baud.

[Tabel 3.6: Format protokol perintah dan telemetri]

| Pesan | Format | Arah | Fungsi |
|-------|--------|------|--------|
| Gerak | `CMD:vx,vy,omega` | Laptop→ESP32→Arduino | Vektor kecepatan (−255..255) |
| Servo | `SERVO:sudut` | Laptop→ESP32→Arduino | Posisi gripper (0..180) |
| Kumpul | `COLLECT` | Laptop→ESP32→Arduino | Sekuens pengumpulan |
| Telemetri | `TEL:heading,vbat` | Arduino→ESP32→Laptop | *Heading* & tegangan |

Sistem dilengkapi tiga lapis **keselamatan**: (1) **watchdog** di Arduino yang
menghentikan motor bila tidak menerima perintah valid dalam 500 ms; (2)
**heartbeat** dari *ground station* yang mengirim ulang perintah gerak aktif
tiap 0,15 s agar *watchdog* tidak keliru menghentikan motor saat tombol ditahan;
serta (3) **pembatasan PWM** (*clamp*) dan **failsafe** STOP otomatis bila
koneksi operator terputus atau mode dimatikan. Seluruh komunikasi HTTP ke robot
dijalankan pada *thread* pekerja non-pemblokir agar antarmuka tetap responsif
dan tombol STOP selalu dapat ditekan.

[Gambar 3.7: Diagram alur protokol komunikasi & mekanisme watchdog/heartbeat.]

#### e. Dasbor Web (Ground Station)

Dasbor dibangun dengan Flask dan Flask-SocketIO (mode asinkron *eventlet*).
Komunikasi *real-time* memakai WebSocket, sementara video disajikan sebagai
aliran MJPEG yang disematkan pada elemen gambar. Lingkar utama (*background
task*) berjalan berulang: mengambil frame → memproses deteksi → menjalankan
*state machine* (saat mode otomatis) → mengirim perintah → mencatat data →
menyiarkan telemetri ke klien. Fitur dasbor meliputi: tayangan video dengan
*overlay* deteksi, pratinjau *mask* HSV, *slider* kalibrasi HSV dan parameter
sistem, telemetri (keadaan FSM, *heading*, FPS, status koneksi), kendali manual,
tombol mode otomatis/manual, serta perekaman data **CSV** untuk keperluan
pengujian. Tersedia pula **mode demo** yang memakai webcam laptop atau berkas
video sebagai sumber citra ketika ESP32-CAM tidak tersedia.

[Gambar 3.8: Tangkapan layar dasbor *ground station*.]

## 3.4 Perancangan dan Prosedur Pengujian

Pengujian dilakukan secara bertahap: **uji per subsistem (isolasi)** terlebih
dahulu, lalu **uji sistem terintegrasi**, agar sumber masalah mudah ditelusuri.
Pengujian dilaksanakan pada **arena terkontrol** (mis. 2×2 m) berlantai datar di
dalam ruangan, dengan penanda grid posisi berjarak 20 cm dari lakban. Variabel
yang divariasikan meliputi jumlah bola (mis. 1, 3, 5, 10), pola posisi bola
(tetap/acak), tingkat cahaya (redup/normal/terang, dicatat nilai luksnya), dan
jarak awal robot–bola. Variabel kontrol yang dijaga konstan: ukuran arena, jenis
lantai, tegangan awal baterai, serta ukuran dan warna bola. Setiap kondisi diuji
**minimal 10–30 percobaan**, dan hasil dilaporkan sebagai rata-rata ± simpangan
baku beserta tingkat keberhasilan (%) dan jumlah percobaan (*n*). Selama
pengujian, telemetri direkam otomatis oleh fitur **pencatatan CSV** pada dasbor
(kolom: `timestamp`, `elapsed_s`, `state`, `ball_x`, `ball_y`, `ball_area`,
`cmd_vx`, `cmd_vy`, `cmd_omega`, `collect_result`) sehingga tiap percobaan
memiliki jejak data yang dapat ditinjau ulang.

Ringkasan metrik per subsistem disajikan pada Tabel 3.7, sedangkan prosedur
rincinya diuraikan pada Subbab 3.4.1–3.4.6.

[Tabel 3.7: Rancangan pengujian dan metrik per subsistem]

| Subsistem | Metrik | Cara ukur |
|-----------|--------|-----------|
| Deteksi (vision) | *Precision*, *recall*, *F1*; laju deteksi vs jarak (tiap 20 cm) & vs lux; FPS/latensi *end-to-end*; perbandingan HSV vs YOLOv8 | Anotasi TP/FP/FN; variasi jarak & cahaya; pencatatan log |
| Navigasi | Galat posisi berhenti (cm); waktu tempuh vs jarak; *drift* saat *strafe* (dengan vs tanpa IMU); *repeatability* | Pengukuran fisik di arena grid; ulang per kondisi |
| Intake (gripper) | Tingkat keberhasilan cengkeram (%); waktu per bola (s) | Hitung berhasil/gagal; *stopwatch* |
| Sistem terintegrasi | Tingkat keberhasilan *clear* lapangan (%); total waktu *clear* N bola; cakupan; konsumsi daya/endurance | Skenario arena penuh; pencatatan log CSV |

### 3.4.1 Instrumen dan Alat Ukur

Agar pengukuran konsisten dan dapat diulang, digunakan instrumen berikut.

1. **Meteran/penggaris dan pita ukur** — mengukur galat posisi berhenti, jarak
   awal robot–bola, jarak *strafe*, dan deviasi melintang (dalam cm).
2. **Penanda grid lantai** — lakban ditempel membentuk kisi 20 cm pada arena
   2×2 m; titik *start* robot dan pola sebaran bola ditandai tetap agar tiap
   percobaan berangkat dari kondisi awal yang sama.
3. **Stopwatch** (atau kolom `elapsed_s` pada log CSV) — mengukur waktu tempuh,
   waktu per bola, dan total waktu *clear* lapangan.
4. **Lux meter** (aplikasi *lux meter* ponsel atau alat digital) — mengukur
   tingkat cahaya (lux) untuk uji ketahanan deteksi terhadap iluminasi.
5. **Multimeter digital** — mengukur tegangan rel motor dan rel 5 V serta besar
   *sag* saat beban penuh (Tabel 4.1) dan tegangan baterai untuk uji *endurance*.
6. **Perekaman set uji (berkas video)** — merekam citra bola dan menyimpannya
   sebagai berkas video; berkas yang sama diumpankan ke pipeline HSV dan YOLOv8
   melalui sumber video (`VIDEO_SOURCE = "video"`) agar kedua metode diuji pada
   **masukan identik** demi keadilan perbandingan.
7. **Panel telemetri dan log CSV dasbor** — mencatat FPS pemrosesan, keadaan
   FSM, luas kontur (`ball_area`, sebagai proksi jarak), dan perintah gerak
   secara otomatis untuk setiap percobaan.

### 3.4.2 Prosedur Pengujian Subsistem Deteksi (Vision)

Tujuan: mengukur ketelitian dan kecepatan deteksi HSV serta membandingkannya
dengan YOLOv8 pada masukan yang sama.

1. **Penyiapan set uji.** Kumpulkan citra bola pada beragam posisi, jarak, dan
   tingkat cahaya, lalu simpan sebagai satu berkas video uji berisi *n* frame
   (mis. *n* = 200–300). Berkas ini menjadi masukan tetap untuk kedua metode.
2. **Penetapan acuan (*ground truth*).** Tandai secara manual, untuk tiap frame,
   ada/tidaknya bola dan posisi sebenarnya sebagai acuan penilaian.
3. **Uji HSV.** Jalankan pipeline HSV (ambang awal Tabel 3.4) pada set uji.
   Untuk tiap frame, klasifikasikan hasil sebagai *true positive* (TP), *false
   positive* (FP), atau *false negative* (FN), lalu hitung *precision*,
   *recall*, dan *F1-score* dengan rumus pada Subbab 2.2.3 [16].
4. **Uji YOLOv8.** Alihkan detektor ke YOLOv8 (model `yolov8n` atau model hasil
   latih di Colab) melalui *toggle* pada dasbor, jalankan pada **set uji yang
   sama**, dan hitung metrik yang sama; jika tersedia, catat pula mAP@0,5 [23].
5. **FPS dan latensi *end-to-end*.** FPS pemrosesan dibaca dari panel telemetri
   (lingkar utama menyasar ~33 FPS). Latensi *end-to-end* diukur dengan metode
   *stopwatch* visual: tampilkan pewaktu milidetik di depan kamera, lalu
   bandingkan nilai pada sumber dan pada tayangan dasbor; ulangi ≥ 30 kali dan
   ambil rata-ratanya [37].
6. **Laju deteksi terhadap jarak.** Letakkan bola tepat pada penanda 20, 40, 60,
   80, dan 100 cm dari kamera. Pada tiap jarak, rekam sejumlah frame dan hitung
   laju deteksi = (frame terdeteksi benar ÷ total frame) × 100 %.
7. **Laju deteksi terhadap cahaya.** Ulangi pengukuran laju deteksi pada tiga
   kondisi cahaya (redup/normal/terang), catat nilai lux tiap kondisi.

Kesetaraan perbandingan dijaga dengan menyamakan berkas masukan, resolusi proses
(640×480), dan perangkat keras yang menjalankan kedua metode.

### 3.4.3 Prosedur Pengujian Subsistem Navigasi

Tujuan: memvalidasi kinematika Mecanum dan efek koreksi *heading* IMU. Pengujian
dilakukan pada arena grid.

1. **Galat posisi berhenti.** Letakkan satu bola pada titik tetap; jalankan robot
   dari titik *start* pada mode otomatis hingga mencapai keadaan COLLECT dan
   berhenti. Ukur jarak sisa antara pusat gripper dan pusat bola (cm). Ulangi
   *n* = 10–30 kali, laporkan rata-rata ± simpangan baku.
2. **Waktu tempuh terhadap jarak awal.** Variasikan jarak awal robot–bola (mis.
   50, 100, 150 cm) dan catat waktu dari mulai bergerak hingga berhenti
   (stopwatch atau selisih `elapsed_s`).
3. **Drift saat *strafe* (dengan vs tanpa IMU).** Pada mode manual, perintahkan
   gerak menyamping murni ($v_y$) sejauh jarak tetap (mis. 100 cm) sepanjang
   garis acuan lurus. Ukur deviasi melintang (cm) dari garis tersebut, pada dua
   kondisi: koreksi *heading* IMU **aktif** dan **nonaktif**. Selisih keduanya
   menunjukkan kontribusi koreksi IMU.
4. **Repeatability.** Ulangi skenario butir 1 berkali-kali dari kondisi awal
   identik; simpangan baku posisi akhir menyatakan keterulangannya.

### 3.4.4 Prosedur Pengujian Subsistem Intake (Gripper)

Tujuan: mengukur keandalan mekanisme cengkeram gripper cetak 3D.

1. **Definisi keberhasilan.** Satu percobaan dinyatakan **berhasil** bila bola
   tercengkeram dan terarah ke penampung tanpa terpantul keluar dari gripper.
2. **Prosedur.** Tempatkan bola pada zona jangkauan gripper, lalu picu sekuens
   COLLECT (servo membuka pada 30° → menutup pada 150°, dengan jeda 0,5 s).
   Catat berhasil/gagal tiap percobaan; ulangi *n* = 20–30 kali sehingga
   diperoleh tingkat keberhasilan (%).
3. **Waktu per bola.** Ukur durasi dari awal sekuens COLLECT hingga bola masuk
   penampung (stopwatch atau selisih `elapsed_s`), laporkan rata-rata ±
   simpangan baku. Variasi opsional: posisi bola (tengah/pinggir gripper).

### 3.4.5 Prosedur Pengujian Sistem Terintegrasi

Tujuan: menilai kinerja robot secara utuh saat mencari–mendekati–mengumpulkan.

1. **Skenario.** Sebarkan *N* bola (mis. 1, 3, 5, 10) dengan pola tetap dan acak
   pada arena; jalankan robot pada mode otomatis dari keadaan IDLE.
2. **Tingkat keberhasilan *clear* lapangan (%).** Hitung proporsi bola yang
   berhasil dikumpulkan terhadap *N*, atau proporsi percobaan yang berhasil
   mengumpulkan seluruh *N* bola dalam batas waktu yang ditetapkan.
3. **Total waktu *clear*.** Ukur waktu dari mulai hingga bola terakhir masuk
   penampung (stopwatch dan/atau log CSV).
4. **Cakupan.** Rasio bola terkumpul terhadap total bola yang ditebar.
5. **Konsumsi daya/*endurance*.** Catat tegangan baterai awal dan akhir
   (multimeter) serta durasi operasi hingga ambang *cutoff* LiPo (mis. 6,6 V).
   Bila pengujian daya tidak dilakukan, keterbatasan ini dinyatakan secara jujur
   pada pembahasan dan diarahkan sebagai saran (BAB V).

### 3.4.6 Teknik Analisis Data

Data kuantitatif diringkas dengan **rata-rata** dan **simpangan baku**:

$$
\bar{x}=\frac{1}{n}\sum_{i=1}^{n} x_i,\qquad
s=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}\left(x_i-\bar{x}\right)^2}.
$$

Metrik keberhasilan dinyatakan sebagai persentase, keberhasilan (%) =
(jumlah berhasil ÷ jumlah percobaan) × 100 %, sedangkan metrik deteksi
(*precision*, *recall*, *F1*) dihitung sesuai Subbab 2.2.3. Hasil disajikan
dalam bentuk tabel dan grafik (laju deteksi terhadap jarak, serta deviasi
*drift* dengan/tanpa IMU), lalu ditafsirkan dan dikaitkan dengan teori maupun
penelitian terdahulu pada Subbab 4.6.

## 3.5 Tempat dan Waktu Penelitian

> **[Diisi penulis]** — sebutkan tempat pelaksanaan (mis. laboratorium/rumah)
> dan rentang waktu pengerjaan (mis. bulan–bulan tahun pelaksanaan), dapat
> disertai tabel jadwal kegiatan (*timeline*) penelitian.

[Tabel 3.8: Jadwal kegiatan penelitian — (diisi penulis).]
