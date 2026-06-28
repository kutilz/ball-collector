# BAB I — PENDAHULUAN

> **Catatan penulisan (hapus saat dipindah ke Word):**
> - Sitasi memakai gaya IEEE `[n]`. Nomor dirujuk ke `Daftar-Pustaka.md`
>   (berjalan, urut kemunculan). Setiap sitasi **wajib diverifikasi ulang**
>   sebelum sidang; yang masih ragu ditandai `[PERLU VERIFIKASI]` di daftar pustaka.
> - Register sengaja dibuat lugas-akademik (bukan berbunga-bunga).
> - Placeholder gambar/tabel ditandai `[Gambar 1.x]` untuk dilengkapi.

---

## 1.1 Latar Belakang Penelitian

Dalam sesi latihan olahraga raket seperti tenis meja, sejumlah besar bola
kerap berserakan di area latihan setelah dipukul berulang kali. Pengumpulan
bola secara manual oleh atlet maupun pelatih menyita waktu dan tenaga yang
seharusnya dapat dialokasikan untuk latihan produktif. Persoalan repetitif
semacam ini merupakan kandidat yang baik untuk diotomasi menggunakan robot
bergerak (*mobile robot*) yang mampu mendeteksi, mendekati, dan mengumpulkan
bola secara mandiri.

Sejumlah penelitian terdahulu telah mengembangkan robot pengumpul bola
olahraga, tetapi dengan pendekatan dan keterbatasan yang beragam. Pada ranah
tenis meja, Yeon dkk. merancang robot pengumpul bola tenis meja otonom [2],
sedangkan Sato dkk. mengembangkan robot serupa berbasis sasis penggerak
diferensial (*differential drive*) dengan kamera RGB dan mekanisme penyapu
elastis [1]. Untuk bola ping-pong, Cheng melaporkan robot pengumpul berbasis
*embedded vision* yang menghitung posisi relatif bola pada citra lalu
mengirimkannya ke pengendali gerak [3]. Pada konteks lokal, beberapa karya di
Indonesia mengangkat tema serupa dengan pendekatan mekanis berbeda, misalnya
robot pengumpul bola ping-pong berbasis **sistem vakum** yang dipadukan dengan
deteksi kamera [7] maupun sensor warna Pixy2 [8]. Adapun pada robot pengumpul
bola golf, solusi terdahulu cenderung mengandalkan konfigurasi penginderaan
yang "lebih nyaman", seperti kamera *bird-view* yang dipasang di atas area
latihan [5] atau navigasi berbasis stereo [6], yang tidak langsung sesuai untuk
robot berbiaya rendah dengan kamera tunggal terpasang di bodi.

Telaah terhadap karya-karya tersebut memperlihatkan beberapa keterbatasan yang
berulang. Pertama, pada aspek **persepsi visual**, banyak platform berbiaya
rendah memasang kamera statis pada ketinggian rendah sehingga rentan kehilangan
target ketika robot mendekat pada jarak kritis, dan metode deteksi berbasis
warna konvensional diketahui peka terhadap perubahan pencahayaan [9], [10].
Kedua, pada aspek **mekanisme penangkapan**, pendekatan berbeda memiliki
kompromi masing-masing: sistem vakum menambah kebutuhan daya dan kompleksitas
[7], [8], sementara mekanisme penyapu kaku yang berputar dapat memantulkan bola
ringan seperti ping-pong alih-alih menangkapnya. Ketiga, pada aspek
**arsitektur komputasi**, pemrosesan deteksi berbasis *machine learning*
menuntut sumber daya komputasi yang besar; Gu dkk. menunjukkan bahwa
model YOLOv3 standar terlalu berat untuk dijalankan secara langsung pada
perangkat robot mobil, sehingga perlu dimodifikasi agar lebih ringan [4].
Temuan ini menegaskan bahwa pemilihan metode deteksi tidak dapat dilepaskan
dari **konteks penerapannya** pada perangkat keras yang tersedia.

Sebagai metode deteksi, terdapat dua paradigma yang lazim dipertentangkan.
Segmentasi warna pada ruang **HSV** (*Hue, Saturation, Value*) bersifat ringan
secara komputasi dan dapat dikalibrasi langsung di lapangan tanpa memerlukan
proses pelatihan dataset, sehingga cocok untuk pemrosesan waktu nyata pada
perangkat terbatas. Sebaliknya, detektor berbasis CNN seperti keluarga YOLO
lebih tahan terhadap variasi kondisi visual, namun menuntut dataset berlabel,
proses pelatihan, dan beban inferensi yang lebih tinggi [13], [14], [15].
Beberapa studi pembanding pada domain lain—misalnya deteksi tomat [9], deteksi
tanaman jagung [10], maupun pengukuran kepadatan lalu lintas [11]—secara
konsisten menyimpulkan kompromi yang sama: metode klasik unggul pada kecepatan
dan kemudahan penerapan, sedangkan metode *machine learning* unggul pada
ketahanan di kondisi kompleks. Dengan demikian, pertanyaan yang relevan
bukanlah "metode mana yang paling modern", melainkan **metode mana yang paling
sesuai dengan konteks penerapan sistem yang dibangun**, dan seberapa besar
selisih performanya bila diukur secara adil.

Berdasarkan uraian tersebut, penelitian ini merancang dan mengimplementasikan
robot pengumpul bola ping-pong otonom dengan **arsitektur terdistribusi** yang
pragmatis dan berbiaya rendah. Pemrosesan deteksi visual dipindahkan dari
mikrokontroler ke sebuah laptop yang berperan sebagai *ground station*; deteksi
operasional utama menggunakan **segmentasi warna HSV** pada OpenCV, sementara
**YOLOv8 digunakan sebagai pembanding yang dilatih dan dievaluasi secara
luring** (*offline*) untuk mengukur selisih performa deteksi secara kuantitatif
(*precision*, *recall*, *F1-score*, dan *frame rate*) [15], [16]. Citra
diperoleh dari kamera **ESP32-CAM** yang terpasang tetap dan dialirkan melalui
*streaming* MJPEG di atas WiFi, sedangkan perintah gerak dikirim dari laptop ke
ESP32-CAM lalu diteruskan melalui jalur serial UART ke **Arduino Uno** sebagai
pengendali tingkat rendah. Untuk lokomosi, robot menggunakan **sasis empat roda
Mecanum (4WD)** yang kinematika inversnya dihitung di Arduino [12], sehingga
robot mampu bergerak holonomik; pada mode otonom, strategi navigasi difokuskan
pada gerak maju dengan koreksi arah (*steering*) proporsional berbasis posisi
bola pada citra. Mekanisme pengumpulan menggunakan **gripper hasil cetak 3D
yang digerakkan servo**, membuka-menutup untuk mencengkeram bola dan
mengarahkannya ke penampung. Keseluruhan sistem
dikoordinasikan oleh sebuah *finite state machine* dan dilengkapi mekanisme
keselamatan berupa *watchdog* dan *heartbeat* perintah untuk mencegah robot
bergerak liar saat komunikasi terputus.

Dengan konfigurasi tersebut, kontribusi penelitian ini tidak terletak pada satu
algoritma tunggal yang paling canggih, melainkan pada **integrasi sistem
ujung-ke-ujung** yang dapat berjalan, diuji, dan dianalisis secara terukur pada
perangkat berbiaya rendah: pemilihan metode deteksi yang sesuai konteks
penerapan, penerapan kinematika Mecanum pada mikrokontroler kelas Arduino Uno,
serta arsitektur kendali terdistribusi yang aman dan dapat dikalibrasi saat
operasi berlangsung.

## 1.2 Rumusan Masalah

Berdasarkan latar belakang yang telah diuraikan, rumusan masalah dalam
penelitian ini adalah sebagai berikut:

1. Bagaimana merancang dan mengimplementasikan sistem deteksi bola ping-pong
   berbasis segmentasi warna HSV pada arsitektur terdistribusi (laptop dan
   ESP32-CAM), serta bagaimana performanya bila dibandingkan secara luring
   dengan detektor YOLOv8 ditinjau dari *precision*, *recall*, *F1-score*, dan
   kecepatan pemrosesan (FPS)?
2. Bagaimana memformulasikan dan mengimplementasikan kinematika invers roda
   Mecanum (4WD) pada Arduino Uno untuk menggerakkan robot mendekati bola,
   dengan koreksi arah berbasis *P-controller* dari posisi bola pada citra?
3. Bagaimana merancang dan menguji mekanisme *intake* berbasis gripper cetak 3D
   yang digerakkan servo, beserta
   arsitektur kendali (*finite state machine*) dan fitur keselamatan
   (*watchdog* dan *heartbeat*) agar robot dapat mengumpulkan bola secara
   andal?

## 1.3 Tujuan Penelitian

Sejalan dengan rumusan masalah di atas, tujuan penelitian ini adalah:

1. Merancang dan mengimplementasikan sistem deteksi bola ping-pong berbasis
   segmentasi warna HSV yang berjalan waktu nyata pada arsitektur terdistribusi,
   serta mengukur selisih performanya terhadap detektor YOLOv8 secara luring.
2. Menerapkan kinematika invers roda Mecanum (4WD) pada Arduino Uno dan
   mengubahnya menjadi sinyal PWM, sehingga robot dapat bernavigasi mendekati
   bola dengan koreksi arah proporsional berbasis citra.
3. Membangun dan menguji secara empiris mekanisme *intake* berbasis gripper
   cetak 3D yang digerakkan servo, serta arsitektur kendali dan keselamatan
   sistem, dan mengevaluasi keberhasilan
   pengumpulan bola pada lingkungan pengujian terkontrol.

## 1.4 Manfaat Penelitian

Penelitian ini diharapkan memberikan manfaat secara teoritis maupun praktis.

**Manfaat teoritis.** Penelitian ini berkontribusi pada keilmuan robotika dan
otomasi, khususnya pada (a) kajian pemilihan metode deteksi visual yang sesuai
konteks penerapan melalui perbandingan terukur antara segmentasi warna HSV dan
detektor YOLOv8, serta (b) penerapan kinematika roda Mecanum pada arsitektur
mikrokontroler berbiaya rendah dengan kanal kendali terdistribusi yang
dilengkapi mekanisme keselamatan.

**Manfaat praktis.** Secara praktis, sistem yang dihasilkan dapat diterapkan di
fasilitas latihan olahraga untuk membantu mengotomasi pengumpulan bola,
sehingga membebaskan atlet dan pelatih dari tugas repetitif memungut bola dan
meningkatkan waktu produktif selama sesi latihan.

## 1.5 Ruang Lingkup dan Batasan Masalah

Agar penelitian terfokus, ditetapkan ruang lingkup dan batasan berikut:

1. **Objek dan lingkungan.** Target deteksi adalah bola ping-pong (berwarna
   kontras terhadap latar). Pengujian dilakukan pada lingkungan dalam ruangan
   (*indoor*) dengan lantai datar.
2. **Sistem deteksi.** Deteksi operasional utama menggunakan segmentasi warna
   HSV pada OpenCV yang dijalankan di laptop. YOLOv8 diposisikan sebagai
   **pembanding luring**, yaitu dilatih dan dievaluasi pada dataset bola di luar
   jalur kendali waktu nyata, bukan sebagai detektor yang berjalan di robot.
3. **Arsitektur komunikasi.** Citra dialirkan dari ESP32-CAM melalui MJPEG di
   atas HTTP/WiFi; perintah gerak dikirim dari laptop melalui HTTP ke ESP32-CAM
   lalu diteruskan via UART ke Arduino Uno. Protokol berlatensi rendah seperti
   UDP tidak termasuk dalam lingkup implementasi dan dibahas sebagai arah
   pengembangan.
4. **Sasis dan aktuator.** Robot menggunakan empat roda Mecanum dengan motor DC
   dan dua *driver* H-bridge DRV8833; kinematika invers dihitung di Arduino Uno.
   Kamera dipasang tetap (*fixed*), tanpa mekanisme *pan-tilt*.
5. **Mekanisme intake.** Pengumpulan bola menggunakan gripper hasil cetak 3D
   yang digerakkan satu servo (membuka-menutup untuk mencengkeram bola), bukan
   silinder rotasi kontinu.
6. **Estimasi orientasi.** Orientasi (*heading*) diperkirakan dari integrasi
   data giroskop sumbu-Z sensor MPU6050; fusi sensor lanjutan seperti
   *complementary filter* tidak termasuk dalam lingkup dan dibahas sebagai arah
   pengembangan.
7. **Kendali otonom.** Navigasi otonom dikoordinasikan oleh *finite state
   machine* (IDLE–SEARCH–APPROACH–COLLECT) dengan koreksi arah berbasis
   *P-controller*. Penyetelan kendali lanjutan (PID penuh) berada di luar
   lingkup.

## 1.6 Sistematika Penulisan

Penulisan skripsi ini disusun dalam lima bab dengan sistematika sebagai berikut:

- **BAB I Pendahuluan**, memuat latar belakang, rumusan masalah, tujuan,
  manfaat, ruang lingkup dan batasan, serta sistematika penulisan.
- **BAB II Tinjauan Pustaka dan Landasan Teori**, memuat telaah penelitian
  terdahulu yang relevan beserta dasar teori yang melandasi perancangan sistem.
- **BAB III Metodologi Penelitian**, memuat metode penelitian, alat dan bahan,
  perancangan sistem (mekanik, elektrik, dan perangkat lunak), serta rancangan
  pengujian.
- **BAB IV Hasil dan Pembahasan**, memuat hasil implementasi, hasil pengujian
  tiap subsistem dan sistem terintegrasi, serta pembahasannya.
- **BAB V Penutup**, memuat kesimpulan yang menjawab rumusan masalah dan saran
  untuk pengembangan selanjutnya.
