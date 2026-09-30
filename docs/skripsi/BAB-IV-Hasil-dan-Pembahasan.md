# BAB IV — HASIL DAN PEMBAHASAN

> **Catatan penulisan (hapus saat dipindah ke Word):**
> - **4.1 Hasil Implementasi** sudah final (deskripsi sistem terwujud) —
>   lengkapi `[Gambar]` dengan FOTO ALAT NYATA milikmu.
> - **4.2–4.6 sudah berupa PROSA LENGKAP + tabel.** Yang tersisa hanya
>   **mengisi angka**: setiap `⟨…⟩` (dalam kalimat) dan sel `…` (dalam tabel)
>   adalah slot data hasil pengujian. **Prosedur pengambilan tiap angka ada di
>   Subbab 3.4.1–3.4.6.** Jangan mengarang — isi setelah pengujian nyata.
> - Kalimat dalam kurung siku `[Analisis: …]` adalah **arahan** apa yang harus
>   kamu simpulkan setelah angka masuk (bukan kalimat final — ganti/hapus).
> - Butir bertanda **(opsional)** boleh langsung dibuang saat bimbingan bila
>   dosen menilai tak perlu.
> - Sitasi IEEE `[n]` → `Daftar-Pustaka.md`. Caption: tabel di ATAS, gambar di BAWAH.

---

## 4.1 Hasil Implementasi

Bagian ini memaparkan realisasi sistem yang telah dibangun, meliputi aspek
mekanik, elektrik, serta perangkat lunak dan dasbor, sesuai rancangan pada
BAB III.

### 4.1.1 Realisasi Mekanik

Robot terealisasi dengan sasis empat roda Mecanum (4WD) beserta dudukan kamera
ESP32-CAM yang dipasang tetap pada posisi ditinggikan, mekanisme *intake* berupa
gripper hasil cetak 3D yang digerakkan servo MG996R, serta penampung (*hopper*)
bola pada badan robot. Seluruh komponen struktural dirancang di Onshape dan
dicetak 3D; bagian gripper yang bersentuhan dengan bola dicetak dari TPU agar
lentur. [Gambar 4.1: Foto robot hasil rakitan — tampak depan, samping, dan atas.]
[Gambar 4.2: Detail mekanisme gripper TPU dan hopper.]

### 4.1.2 Realisasi Elektrik

Sistem elektrik terealisasi dengan baterai LiPo 2S sebagai sumber daya, dua
*driver* DRV8833 untuk empat motor Mecanum, modul *buck* XL4015 untuk rel 5 V
logika dan servo, sensor MPU6050 pada jalur I²C, serta sambungan UART antara
ESP32-CAM dan Arduino Uno melalui *logic level converter*. Rel motor dan rel
logika dipisah dengan *ground* bersama. [Gambar 4.3: Foto rangkaian elektrik
robot.] [Tabel 4.1: Hasil pengukuran tegangan rel saat motor & servo aktif —
(diisi: tegangan rel motor, rel 5 V, dan besar *sag* saat beban penuh).]

### 4.1.3 Realisasi Perangkat Lunak dan Dasbor

Perangkat lunak *ground station* terealisasi dengan modul deteksi (HSV),
*state machine*, komunikasi, pencatatan, dan server web Flask + Flask-SocketIO.
Dasbor menampilkan tayangan video dengan *overlay* deteksi, pratinjau *mask*
HSV, *slider* kalibrasi HSV dan parameter sistem, telemetri (keadaan FSM,
*heading*, FPS, status koneksi), kendali manual, pemilihan mode otomatis/manual,
serta perekaman data CSV. *Firmware* Arduino menjalankan kinematika invers
Mecanum, pembacaan MPU6050, kendali servo, dan *watchdog*; *firmware* ESP32-CAM
menjalankan *streaming* MJPEG dan penerusan perintah ke Arduino. [Gambar 4.4:
Tangkapan layar dasbor — tayangan video dengan overlay deteksi dan panel
kalibrasi.] [Gambar 4.5: Tampilan pratinjau *mask* HSV hasil segmentasi.]

## 4.2 Pengujian Subsistem Deteksi (Vision)

Pengujian subsistem deteksi bertujuan mengukur ketelitian dan kecepatan deteksi
bola serta membandingkan metode segmentasi warna HSV dengan detektor YOLOv8.
Seluruh pengujian pada subbab ini mengikuti prosedur pada Subbab 3.4.2, dengan
kedua metode diuji pada berkas masukan yang identik demi keadilan perbandingan.

### 4.2.1 Akurasi Deteksi (HSV) dan Perbandingan dengan YOLOv8

Akurasi deteksi diukur dari klasifikasi TP/FP/FN atas *n* = ⟨…⟩ frame set uji,
lalu diringkas menjadi *precision*, *recall*, dan *F1-score* (Subbab 2.2.3).
Hasil perbandingan kedua metode disajikan pada Tabel 4.2.

[Tabel 4.2: Perbandingan performa deteksi HSV vs YOLOv8]

| Metrik | HSV | YOLOv8 |
|--------|:---:|:------:|
| *Precision* | … | … |
| *Recall* | … | … |
| *F1-score* | … | … |
| FPS (rata-rata) | … | … |
| Jumlah sampel uji (*n*) | … | … |

Berdasarkan Tabel 4.2, metode HSV memperoleh *precision* ⟨…⟩, *recall* ⟨…⟩, dan
*F1-score* ⟨…⟩ pada laju rata-rata ⟨…⟩ FPS, sedangkan YOLOv8 (varian ⟨yolov8n /
model kustom⟩) memperoleh *precision* ⟨…⟩, *recall* ⟨…⟩, *F1-score* ⟨…⟩ pada
⟨…⟩ FPS. [Analisis: nyatakan metode mana lebih teliti dan mana lebih cepat, lalu
kuantifikasi selisihnya (mis. "YOLOv8 lebih tinggi F1 sebesar ⟨…⟩ poin, tetapi
HSV ⟨…⟩× lebih cepat"). Kaitkan dengan kompromi klasik vs *machine learning*
yang konsisten dilaporkan pada domain lain [9], [10], [11], dan tegaskan
implikasinya bagi pemilihan detektor daring pada konteks perangkat ini.]

### 4.2.2 Laju Deteksi terhadap Jarak

Laju deteksi terhadap jarak diukur dengan menempatkan bola pada penanda grid
20–100 cm dari kamera (Subbab 3.4.2 butir 6); hasilnya pada Tabel 4.3 dan
divisualisasikan pada Gambar 4.6.

[Tabel 4.3: Laju deteksi (%) terhadap jarak]

| Jarak (cm) | 20 | 40 | 60 | 80 | 100 | … |
|------------|:--:|:--:|:--:|:--:|:---:|:-:|
| Laju deteksi (%) | … | … | … | … | … | … |

[Gambar 4.6: Grafik laju deteksi terhadap jarak.]

[Analisis: jelaskan tren laju deteksi terhadap jarak (mis. tinggi dan stabil
pada jarak dekat–menengah, lalu menurun mulai jarak ⟨…⟩ cm karena luas kontur
bola turun di bawah ambang `MIN_CONTOUR_AREA`), dan kaitkan dengan jarak kerja
efektif robot serta ambang transisi FSM (`AREA_APPROACH`/`AREA_COLLECT`).]

### 4.2.3 Laju Deteksi terhadap Tingkat Cahaya

Ketahanan deteksi terhadap iluminasi diuji pada tiga kondisi cahaya dengan nilai
lux tercatat (Subbab 3.4.2 butir 7), sebagaimana Tabel 4.4.

[Tabel 4.4: Laju deteksi (%) terhadap tingkat cahaya]

| Kondisi cahaya | Lux | Laju deteksi (%) |
|----------------|:---:|:----------------:|
| Redup | … | … |
| Normal | … | … |
| Terang | … | … |

[Analisis: tunjukkan sensitivitas segmentasi HSV terhadap perubahan cahaya
(kelemahan klasik metode warna [9], [10]); bila laju turun pada kondisi
⟨redup/terang⟩, hubungkan dengan perlunya **kalibrasi ambang HSV saat operasi**
yang disediakan dasbor sebagai mitigasi. (opsional) bandingkan pula ketahanan
YOLOv8 pada kondisi yang sama bila datanya diambil.]

### 4.2.4 Latensi dan FPS End-to-End

Latensi *end-to-end* diukur dengan metode *stopwatch* visual (Subbab 3.4.2 butir
5), bukan diasumsikan. Hasilnya pada Tabel 4.5.

[Tabel 4.5: Latensi *end-to-end* dan FPS pemrosesan]

| Besaran | Nilai |
|---------|:-----:|
| FPS *streaming* (ESP32-CAM→laptop) | … |
| FPS pemrosesan deteksi | … |
| Latensi *end-to-end* (ms) | … |

Latensi *end-to-end* terukur sebesar ⟨…⟩ ms dengan FPS pemrosesan ⟨…⟩.
[Analisis: uraikan bahwa latensi ini menjadi keterlambatan fasa pada lingkar
kendali visual, sehingga membatasi kecepatan pendekatan agresif dan membenarkan
nilai `KP_STEERING` yang konservatif (0,5) untuk menghindari osilasi; kaitkan
dengan karakteristik MJPEG-over-HTTP yang sederhana namun boros *bandwidth* dan
berlatensi lebih tinggi dibanding UDP [36], [37] — menjadi dasar Saran transport
berlatensi rendah (BAB V).]

## 4.3 Pengujian Subsistem Navigasi

Pengujian navigasi memvalidasi penerapan kinematika invers Mecanum dan efek
koreksi *heading* dari IMU, mengikuti prosedur Subbab 3.4.3. Hasil pengukuran
posisi dan waktu dirangkum pada Tabel 4.6, sedangkan efek koreksi IMU pada
*drift strafe* pada Tabel 4.7.

[Tabel 4.6: Hasil pengujian navigasi]

| Pengujian | Hasil (rata-rata ± SB) | n |
|-----------|:----------------------:|:-:|
| Galat posisi berhenti ke bola (cm) | … | … |
| Waktu tempuh vs jarak awal (s) | … | … |
| *Repeatability* posisi akhir (SB, cm) | … | … |

[Tabel 4.7: *Drift* saat *strafe* — dengan vs tanpa koreksi IMU]

| Kondisi | Jarak *strafe* (cm) | Deviasi melintang (cm) |
|---------|:-------------------:|:----------------------:|
| Tanpa IMU | … | … |
| Dengan IMU | … | … |

Robot berhenti dengan galat posisi rata-rata ⟨…⟩ cm terhadap bola, dan pada uji
*strafe* sejauh ⟨…⟩ cm deviasi melintang berkurang dari ⟨…⟩ cm (tanpa IMU)
menjadi ⟨…⟩ cm (dengan koreksi IMU). [Analisis: simpulkan bahwa kinematika
Mecanum berhasil menghasilkan gerak holonomik terarah, namun tanpa *encoder*
gerak bersifat *open-loop* sehingga selip roda dan *drift* giroskop menyisakan
galat; kuantifikasi seberapa besar koreksi IMU menekan *drift* (persentase
perbaikan) dan tegaskan bahwa pelacakan target tetap bertumpu pada umpan balik
visual [25], [28].]

## 4.4 Pengujian Subsistem Intake (Gripper)

Keandalan mekanisme gripper cetak 3D diuji mengikuti Subbab 3.4.4, dengan
keberhasilan didefinisikan sebagai bola tercengkeram dan terarah ke penampung
tanpa terpantul keluar. Hasilnya pada Tabel 4.8.

[Tabel 4.8: Hasil pengujian mekanisme gripper]

| Metrik | Nilai | n |
|--------|:-----:|:-:|
| Tingkat keberhasilan cengkeram (%) | … | … |
| Waktu per bola (s) | … | … |

Mekanisme gripper mencapai tingkat keberhasilan cengkeram ⟨…⟩ % dengan waktu
rata-rata ⟨…⟩ s per bola. [Analisis: kaitkan tingkat keberhasilan dengan
kepatuhan (*compliance*) material TPU yang mendeformasi mengikuti permukaan bola
dan meredam pantulan—keunggulan dibanding mekanisme kaku untuk bola ringan
[33], [34]; bila ada kegagalan, identifikasi penyebabnya (mis. posisi bola di
tepi jangkauan, sudut buka/tutup servo) sebagai bahan perbaikan.]

## 4.5 Pengujian Sistem Terintegrasi

Pengujian sistem terintegrasi menilai kinerja robot secara utuh dalam siklus
mencari–mendekati–mengumpulkan pada arena berisi *N* bola (Subbab 3.4.5). Hasil
dirangkum pada Tabel 4.9 dan didokumentasikan pada Gambar 4.7.

[Tabel 4.9: Hasil pengujian sistem terintegrasi]

| Metrik | Nilai | n |
|--------|:-----:|:-:|
| Tingkat keberhasilan *clear* lapangan (%) | … | … |
| Total waktu *clear* N bola (s) | … | … |
| Cakupan bola terkumpul (%) | … | … |
| Konsumsi daya / *endurance* (opsional) | … | … |

[Gambar 4.7: Dokumentasi pengujian sistem terintegrasi di arena.]

Pada skenario *N* = ⟨…⟩ bola, robot mengumpulkan ⟨…⟩ % bola (cakupan) dengan
total waktu *clear* ⟨…⟩ s dan tingkat keberhasilan ⟨…⟩ %. [Analisis: tafsirkan
kinerja siklus penuh FSM (IDLE→SEARCH→APPROACH→COLLECT), identifikasi tahap yang
paling sering menjadi titik gagal (mis. kehilangan target saat mendekat, bola
terlewat saat *search*), dan hubungkan dengan hasil subsistem di 4.2–4.4.
Nyatakan pula kontribusi fitur keselamatan (*watchdog*/*heartbeat*): robot tidak
pernah bergerak liar meskipun komunikasi WiFi sesekali terganggu — indikator
keandalan operasi. (opsional) Metrik *endurance* daya hanya diisi bila pengujian
baterai dilakukan; bila tidak, nyatakan sebagai keterbatasan.]

## 4.6 Pembahasan

Bagian ini mengaitkan hasil pengujian tiap subsistem dan sistem terintegrasi
dengan rumusan masalah (Subbab 1.2) serta teori dan penelitian terdahulu (BAB
II). Pembahasan disusun mengikuti ketiga rumusan masalah agar keterkaitannya
jelas.

**4.6.1 Pemilihan metode deteksi sesuai konteks penerapan (rumusan masalah 1).**
Hasil Subbab 4.2 memperlihatkan kompromi antara ketelitian dan kecepatan:
⟨ringkas selisih F1 dan FPS dari Tabel 4.2⟩. Walaupun YOLOv8 ⟨lebih/kurang⟩
teliti, beban komputasinya lebih besar dan menuntut dataset serta pelatihan,
sejalan dengan temuan bahwa model YOLO standar terlalu berat untuk dijalankan
langsung pada perangkat robot mobil tanpa akselerasi memadai [4]. Dengan latensi
*end-to-end* terukur ⟨…⟩ ms (Tabel 4.5) yang sudah menambah keterlambatan pada
lingkar kendali, metode HSV yang ringan dan dapat dikalibrasi saat operasi
menjadi pilihan yang **lebih sesuai sebagai detektor daring** pada konteks sistem
ini, sementara YOLOv8 tetap bernilai sebagai pembanding kuantitatif dan kandidat
untuk kondisi yang lebih kompleks. [Analisis: nyatakan apakah selisih akurasi
sepadan dengan tambahan beban komputasinya bagi kasus penggunaan ini [11].]

**4.6.2 Navigasi holonomik tanpa encoder (rumusan masalah 2).** Subbab 4.3
menunjukkan kinematika invers Mecanum berhasil menggerakkan robot secara
holonomik dengan galat posisi ⟨…⟩ cm. Karena sistem tidak memakai *encoder*,
gerak bersifat *open-loop* sehingga selip roda Mecanum dan *drift* integrasi
giroskop menyisakan galat; koreksi *heading* IMU menekan *drift strafe* sebesar
⟨…⟩ % (Tabel 4.7), namun keandalan estimasi *heading* terbatas pada horizon
waktu pendek karena tidak digunakan fusi sensor lanjut [25], [28]. Hal ini
membenarkan strategi bahwa **pelacakan target bertumpu pada umpan balik visual**,
bukan *odometry* murni.

**4.6.3 Intake, arsitektur kendali, dan keselamatan (rumusan masalah 3).**
Subbab 4.4 menunjukkan gripper TPU lentur mencapai keberhasilan cengkeram ⟨…⟩ %;
kepatuhan material membantu meredam pantulan bola ping-pong yang ringan,
konsisten dengan keunggulan *soft/compliant gripper* dibanding mekanisme kaku
[33], [34]. Pada tingkat sistem (Subbab 4.5), koordinasi FSM dan fitur
keselamatan (*watchdog* 500 ms + *heartbeat* 0,15 s) menjaga robot tetap
terkendali; kontribusi keselamatan ini merupakan nilai keandalan yang nyata pada
robot bergerak, meskipun tidak berupa metrik akurasi.

**4.6.4 Keterbatasan penelitian.** Beberapa keterbatasan yang teridentifikasi:
(a) transport video MJPEG-over-HTTP menambah latensi dibanding protokol seperti
UDP [36], [37]; (b) ketiadaan *encoder* membuat navigasi *open-loop* dan rentan
selip; (c) estimasi *heading* dari giroskop tunggal rawan *drift*; (d) kamera
terpasang tetap sehingga jangkauan deteksi terbatas saat robot sangat dekat
dengan bola; serta (e) ⟨keterbatasan lain sesuai temuan, mis. endurance daya
belum diuji⟩. Keterbatasan-keterbatasan ini menjadi dasar langsung bagi Saran
pengembangan pada BAB V.

> **(opsional — boleh dihapus saat bimbingan)** Bila dosen menghendaki, Subbab
> 4.6 dapat diringkas menjadi satu narasi mengalir tanpa penomoran 4.6.1–4.6.4,
> atau sebaliknya diperkaya dengan pembahasan per-metrik. Struktur bernomor di
> atas sengaja disediakan agar mudah dipangkas.
