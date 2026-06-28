# BAB II — TINJAUAN PUSTAKA DAN LANDASAN TEORI

> **Catatan penulisan (hapus saat dipindah ke Word):**
> - Sitasi IEEE `[n]` → `Daftar-Pustaka.md`. Persamaan ditulis dalam notasi
>   LaTeX agar mudah diketik ulang di *Equation Editor* Word; nomori ulang
>   `(2.x)` saat final.
> - Istilah baku: *machine learning* (bukan "pembelajaran mendalam"); mekanisme
>   intake = **gripper cetak 3D digerakkan servo** (bukan "penyapu").
> - Placeholder gambar/tabel: `[Gambar 2.x]`, `[Tabel 2.x]`.

---

## 2.1 Penelitian Terdahulu yang Relevan

Pengembangan robot pengumpul bola olahraga telah menjadi objek sejumlah
penelitian, namun telaah terhadap tingkat kemutakhiran teknologi (*state of the
art*) memperlihatkan beberapa keterbatasan yang menjadi celah penelitian
(*research gap*). Telaah berikut dikelompokkan menurut tiga aspek: persepsi
visual, mekanisme penangkapan, dan arsitektur komputasi.

Pada aspek **persepsi visual**, sebagian besar robot pengumpul bola
mengandalkan kamera dengan konfigurasi yang menyederhanakan persepsi. Wu dkk.
menggunakan kamera *bird-view* yang dipasang di atas area untuk robot pengumpul
bola golf [5], sedangkan Yun dkk. memakai penginderaan stereo [6]. Konfigurasi
demikian kuat untuk pemetaan area, tetapi tidak langsung sesuai untuk robot
berbiaya rendah dengan satu kamera tetap di bodi. Pada robot tenis, Gu dkk.
menegaskan bahwa deteksi bola menggunakan *machine learning* pada perangkat
mobil terbatas oleh ukuran model dan kecepatan inferensi, sehingga YOLOv3
standar dinilai terlalu lambat untuk operasi robotik praktis tanpa akselerasi
GPU [4]. Studi pembanding metode deteksi pada domain lain memperkuat hal ini:
segmentasi warna terbukti ringan tetapi peka terhadap perubahan pencahayaan,
sementara detektor berbasis CNN lebih tahan namun lebih berat secara komputasi
[9], [10], [11].

Pada aspek **mekanisme penangkapan** (*intake*), literatur memperlihatkan
kompromi pada tiap pendekatan. Karya lokal di Indonesia mengangkat robot
pengumpul bola ping-pong berbasis **sistem vakum** yang dipadukan dengan deteksi
kamera [7] maupun sensor warna Pixy2 [8]; pendekatan ini efektif namun menambah
kebutuhan daya dan kompleksitas pneumatik. Di sisi lain, Sato dkk. menggunakan
mekanisme penyapu/bilah elastis berputar pada robot pengumpul bola tenis meja
[1]; mekanisme kaku yang berputar berisiko memantulkan bola ringan seperti
ping-pong bila penyelarasan dan kepatuhan (*compliance*) material tidak memadai.
Hal ini memotivasi penggunaan **gripper lentur hasil cetak 3D** berbahan
elastomer yang mendeformasi mengikuti permukaan bola sehingga meredam energi
tumbukan saat akuisisi.

Pada aspek **arsitektur komputasi**, banyak penelitian menempatkan *machine
learning* sebagai pusat sistem persepsi, namun dengan konsekuensi beban
komputasi, kebutuhan dataset, dan rekayasa yang tidak kecil [4], [13], [14].
Cheng menunjukkan bahwa pendekatan *embedded vision* untuk bola ping-pong dapat
bekerja dengan menghitung posisi relatif bola pada citra lalu mengirimkannya ke
pengendali gerak [3], tetapi belum menempatkan segmentasi HSV sebagai detektor
daring utama dan YOLOv8 sebagai pembanding luring terukur dalam satu arsitektur
terdistribusi.

Dari telaah tersebut, celah penelitian yang diisi oleh penelitian ini bukanlah
"membuat robot pengumpul bola pertama", melainkan **kombinasi desain sistem
yang pragmatis dan terukur**: robot pengumpul bola ping-pong otonom yang
memadukan deteksi daring berbasis HSV di *ground station*, pembanding YOLOv8
luring yang dievaluasi secara kuantitatif, sasis Mecanum 4WD dengan kinematika
invers pada mikrokontroler kelas Arduino Uno, mekanisme intake gripper lentur
cetak 3D, serta arsitektur kendali terdistribusi yang dilengkapi fitur
keselamatan. Kombinasi ini belum banyak dipotret secara utuh pada literatur
terdahulu. [Tabel 2.1: ringkasan penelitian terdahulu dan celah penelitian]

## 2.2 Landasan Teori

### 2.2.1 Computer Vision dan Segmentasi Warna HSV

*Computer vision* adalah bidang yang mengekstraksi informasi numerik dari citra
digital. Pada penelitian ini, blok persepsi utama berupa **segmentasi warna**
pada ruang warna HSV (*Hue, Saturation, Value*), bukan deteksi objek berbasis
CNN. Ruang warna HSV memisahkan informasi warna (*hue*), kejenuhan
(*saturation*), dan kecerahan (*value*), sehingga pemilihan warna target lebih
tahan terhadap variasi pencahayaan dibandingkan bekerja langsung pada ruang
RGB/BGR [17], [19], [20]. Alur baku yang didokumentasikan OpenCV adalah mengubah
citra dari BGR ke HSV dengan `cvtColor`, lalu menyeleksi piksel target dengan
`inRange` berdasarkan batas bawah dan atas pada ketiga kanal [17].

Secara matematis, keluaran `inRange` adalah *mask* biner $M(x,y)$:

$$
M(x,y)=
\begin{cases}
1, & H_{\min}\le H \le H_{\max}\ \wedge\ S_{\min}\le S \le S_{\max}\ \wedge\ V_{\min}\le V \le V_{\max}\\
0, & \text{lainnya}
\end{cases}
$$

Karena *streaming* nirkabel dapat menambah derau, *mask* dibersihkan dengan
operasi **morfologi**. Erosi ($A \ominus B$) mengikis tepi dan menghilangkan
bintik noise terisolasi, sedangkan dilasi ($A \oplus B$) mengembalikan ukuran
area target dan menutup lubang kecil, dengan $B$ sebagai *structuring element*
[18]. Objek target lalu ditentukan dari kontur hasil `findContours`; kontur
dengan luas terbesar dipilih sebagai kandidat bola.

Posisi bola diukur dari **momen citra** kontur tersebut. Momen spasial orde
$p,q$ dari fungsi intensitas $I(x,y)$ adalah

$$
M_{pq}=\sum_{x}\sum_{y} x^{p}\,y^{q}\,I(x,y),
$$

sehingga $M_{00}$ menyatakan luas dan koordinat pusat massa (*centroid*)
dihitung dengan [18]:

$$
c_{x}=\frac{M_{10}}{M_{00}},\qquad c_{y}=\frac{M_{01}}{M_{00}}.
$$

Selisih antara $c_{x}$ dan titik tengah horizontal citra menghasilkan
**galat pergeseran** (*offset*) yang menjadi masukan kendali arah robot.
Pendekatan ini sejalan dengan prinsip *visual servoing* sederhana: untuk tugas
mencari–mendekati–mengumpulkan, cukup diketahui apakah target berada di kiri,
kanan, atau dekat pusat citra, tanpa perlu estimasi pose tiga dimensi yang
mahal. Kelemahan klasik segmentasi warna—kepekaan terhadap perubahan iluminasi
[9]—dimitigasi dengan menyediakan antarmuka kalibrasi ambang HSV secara langsung
(*runtime*) sebelum operasi otonom.

### 2.2.2 Object Detection Berbasis Machine Learning (YOLOv8)

Berbeda dengan segmentasi warna yang berbasis aturan, deteksi objek berbasis
*machine learning* bertumpu pada *Convolutional Neural Network* (CNN) yang
belajar dari data berlabel. Keluarga *You Only Look Once* (YOLO) termasuk
detektor **satu tahap** (*single-stage*) yang langsung memprediksi lokasi dan
kelas objek dalam satu lintasan inferensi, sehingga lazim dipilih untuk
kebutuhan waktu nyata [15]. YOLOv8 memperkenalkan beberapa ciri arsitektur:
*head* yang **anchor-free** dan terpisah (*decoupled*), serta blok **C2f** pada
*backbone* dan *neck* yang memperbaiki aliran gradien tanpa menambah beban
komputasi berlebih [21].

Pada pelatihan, model YOLO meminimalkan fungsi rugi total yang secara konseptual
menggabungkan komponen klasifikasi dan lokalisasi,

$$
L_{\text{total}} = L_{\text{cls}} + L_{\text{box}} + L_{\text{dfl}},
$$

dengan $L_{\text{dfl}}$ (*distribution focal loss*) sebagai komponen regresi
distribusi koordinat pada YOLO modern. Proses pelatihan juga memanfaatkan
augmentasi data seperti *mosaic*, *mixup*, pembalikan citra, dan *jitter* HSV
untuk meningkatkan ketahanan model [21], [22].

Dalam penelitian ini, YOLOv8 **tidak** dijalankan sebagai detektor daring di
robot, melainkan dilatih dan dievaluasi secara **luring** (*offline*) pada
dataset bola untuk memperoleh tolok ukur performa deteksi. Hal ini berdasar
pada temuan bahwa inferensi YOLO menuntut dataset, pelatihan, dan beban
komputasi yang signifikan [4], [13], [14], sehingga lebih tepat diposisikan
sebagai **pembanding** terhadap metode HSV daripada sebagai detektor yang
berjalan di atas arsitektur *streaming* WiFi dan mikrokontroler.

### 2.2.3 Metrik Evaluasi Deteksi

Perbandingan antara HSV dan YOLOv8 menuntut metrik kuantitatif yang membedakan
ketepatan klasifikasi, ketepatan lokalisasi, dan kecepatan pemrosesan. Dasar
metrik adalah *confusion matrix* yang mengategorikan hasil deteksi menjadi
*true positive* (TP), *false positive* (FP), dan *false negative* (FN) [16].
Dari sini didefinisikan **precision** dan **recall**:

$$
\text{Precision}=\frac{TP}{TP+FP},\qquad
\text{Recall}=\frac{TP}{TP+FN}.
$$

Keduanya diringkas menjadi satu skor dengan **F1-score**, yaitu rata-rata
harmonik:

$$
F_{1}=\frac{2\cdot \text{Precision}\cdot \text{Recall}}{\text{Precision}+\text{Recall}}.
$$

Kualitas lokalisasi *bounding box* diukur dengan **Intersection over Union**
(IoU) antara kotak prediksi $B_{p}$ dan kotak acuan $B_{gt}$ [23]:

$$
\text{IoU}=\frac{\text{area}(B_{p}\cap B_{gt})}{\text{area}(B_{p}\cup B_{gt})}.
$$

Dari kurva *precision–recall* pada berbagai ambang keyakinan dihitung *Average
Precision* (AP), lalu dirata-ratakan antarkelas menjadi **mean Average
Precision** (mAP); notasi mAP@0,5 merujuk pada ambang IoU 0,5 [16], [23], [24].
Selain metrik ketelitian, **frame rate** (FPS) dipakai sebagai indikator
kelayakan waktu nyata. Pemisahan metrik ini penting bagi penelitian ini agar
simpulan yang ditarik bersifat jujur: metode tertentu dapat lebih akurat,
sementara metode lain lebih layak untuk dijalankan di sistem nyata.

### 2.2.4 Kinematika Invers Roda Mecanum (4WD)

Roda Mecanum adalah roda holonomik dengan rangkaian rol pasif yang terpasang
miring, lazimnya bersudut 45° terhadap poros roda. Kombinasi arah dan kecepatan
putar keempat roda memungkinkan sasis bergerak maju–mundur, menyamping
(*strafe*), dan berputar secara simultan tanpa mengubah sudut kemudi [12], [25].
Kecepatan tiap roda merupakan fungsi linear dari kecepatan sasis: longitudinal
$v_{x}$, transversal $v_{y}$, dan kecepatan sudut $\omega_{z}$. Bentuk
**kinematika invers** untuk konfigurasi 4WD simetris dapat ditulis [12], [26]:

$$
\begin{bmatrix}\omega_{FL}\\ \omega_{FR}\\ \omega_{RL}\\ \omega_{RR}\end{bmatrix}
=\frac{1}{r}
\begin{bmatrix}
1 & -1 & -(l_{x}+l_{y})\\
1 & \phantom{-}1 & \phantom{-}(l_{x}+l_{y})\\
1 & \phantom{-}1 & -(l_{x}+l_{y})\\
1 & -1 & \phantom{-}(l_{x}+l_{y})
\end{bmatrix}
\begin{bmatrix}v_{x}\\ v_{y}\\ \omega_{z}\end{bmatrix},
$$

dengan $r$ jari-jari roda, serta $l_{x}$ dan $l_{y}$ setengah jarak antar-poros
arah longitudinal dan transversal. Pada penelitian ini, bentuk tersebut
diimplementasikan dalam wujud tereduksi yang umum dipakai pada Arduino, yaitu
$FL=v_{x}+v_{y}+\omega$, $FR=v_{x}-v_{y}-\omega$, $RL=v_{x}-v_{y}+\omega$, dan
$RR=v_{x}+v_{y}-\omega$, setelah penetapan konvensi tanda dan normalisasi skala
agar tidak melampaui batas PWM. Karena sistem tidak menggunakan *encoder* roda
(tanpa *closed-loop* kecepatan), keluaran kinematika lebih tepat disebut
**perintah kecepatan relatif** yang dipetakan ke PWM, bukan jaminan kecepatan
absolut; pada permukaan licin, roda Mecanum rentan selip sehingga navigasi
berbasis *odometry* murni kurang andal dan perlu dikoreksi umpan balik visual
[25].

### 2.2.5 IMU MPU6050 dan Estimasi Heading

MPU6050 adalah *Inertial Measurement Unit* yang mengintegrasikan giroskop dan
akselerometer tiga sumbu dengan ADC 16-bit, berkomunikasi melalui antarmuka
I²C. Giroskopnya dapat dikonfigurasi pada rentang skala penuh ±250, ±500,
±1000, atau ±2000 °/s dengan faktor sensitivitas yang bersesuaian [27]. Pada
penelitian ini, yang dibutuhkan bukan orientasi tiga dimensi penuh, melainkan
**heading relatif** terhadap sumbu-Z (*yaw*) untuk mendukung gerak mencari dan
referensi rotasi. Heading diperkirakan dengan integrasi diskrit:

$$
\theta_{k}=\theta_{k-1}+(\omega_{z}-b_{z})\,\Delta t,
$$

dengan $\omega_{z}$ laju sudut terukur, $b_{z}$ bias giroskop, dan $\Delta t$
selang cuplik. Permasalahan utama integrasi giroskop adalah **drift**: bias yang
tidak terkompensasi menimbulkan galat sudut yang tumbuh terhadap waktu [28].
Oleh karena itu, sistem melakukan estimasi bias pada fase diam saat inisialisasi
dan menerapkan *dead zone* terhadap laju sudut kecil. Metode fusi sensor lanjut
seperti *complementary filter* (yang memadukan kestabilan jangka panjang
akselerometer dengan respons cepat giroskop) **tidak** digunakan pada penelitian
ini dan dibahas sebagai arah pengembangan; konsekuensinya, estimasi heading
hanya andal untuk horizon waktu pendek, sedangkan pelacakan target tetap
mengandalkan umpan balik visual.

### 2.2.6 Motor DC, Driver H-Bridge (DRV8833), dan PWM

Lokomosi sasis menggunakan empat motor DC bersikat dengan *gearbox*, yang dipilih
karena sederhana dan murah. Kecepatan rata-rata motor DC dikendalikan melalui
**Pulse Width Modulation** (PWM), yaitu pengaturan *duty cycle* sinyal pada
tegangan suplai tetap:

$$
V_{\text{avg}} \approx D \cdot V_{s},
$$

dengan $D$ *duty cycle* dan $V_{s}$ tegangan sumber [31]. Karena mikrokontroler
tidak mampu menyuplai arus motor secara langsung, digunakan *driver* **H-bridge
DRV8833** dari Texas Instruments. Tiap IC DRV8833 berisi dua H-bridge, mendukung
tegangan suplai 2,7–10,8 V, arus kontinu hingga 1,5 A RMS per kanal, antarmuka
PWM sederhana, serta proteksi arus lebih, hubung singkat, *undervoltage
lockout*, dan suhu lebih [30]. Dengan dua IC DRV8833, keempat motor sasis 4WD
dapat dikendalikan terpisah. Rantai pemrosesannya: kinematika invers
menghasilkan target kecepatan tiap roda, lalu target dipetakan ke arah putar
(melalui pin arah) dan *duty cycle* PWM pada tiap kanal H-bridge. Keberadaan
proteksi dan kemudahan pembatasan PWM ini juga menjadi dasar teknis bagi fitur
keselamatan sistem, seperti pembatasan PWM maksimum dan penghentian motor oleh
*watchdog* saat komunikasi terputus.

### 2.2.7 Mekanisme Intake: Gripper Cetak 3D dan Material TPU

Mekanisme pengumpulan bola pada penelitian ini berupa **gripper** yang
difabrikasi dengan pencetakan 3D dan digerakkan oleh satu motor servo. Servo
hobi bekerja dengan prinsip **kendali posisi**: lebar pulsa kendali menentukan
sudut poros, sehingga aktuator sesuai untuk gerakan membuka–menutup yang
terdefinisi [32]. Gripper digerakkan dari posisi membuka ke posisi menutup untuk
mencengkeram bola dan mengarahkannya ke kompartemen penampung.

Bagian gripper yang bersentuhan dengan bola dicetak menggunakan filamen
elastomer **Thermoplastic Polyurethane** (TPU). Sifat elastomerik TPU berasal
dari kombinasi segmen lunak dan keras pada struktur polimernya, sehingga
menawarkan fleksibilitas (*compliance*), ketangguhan, dan ketahanan aus yang
baik; sifat mekanik TPU cetak 3D sangat dipengaruhi parameter proses pencetakan
[33]. Dalam konteks pengambilan objek, gripper lentur (*soft/compliant
gripper*) berbahan lunak mampu mendeformasi mengikuti bentuk objek sehingga
meningkatkan keberhasilan cengkeraman dan meredam energi tumbukan [34], [35].
Untuk bola ping-pong yang ringan dan keras, kepatuhan material TPU membantu
mengurangi efek pantulan (*ricochet*) yang kerap menggagalkan mekanisme kaku.

### 2.2.8 Komunikasi Nirkabel dan Streaming MJPEG (ESP32-CAM)

Citra diperoleh dari modul **ESP32-CAM** yang memuat SoC ESP32 dengan WiFi
(802.11 b/g/n) dan kamera OV2640 terpasang tetap. ESP32-CAM menjalankan
*web server* yang menyediakan aliran video **Motion JPEG** (MJPEG) dan
*endpoint* perintah. MJPEG mengirim tiap *frame* sebagai citra JPEG mandiri
melalui respons HTTP (*multipart/x-mixed-replace*), sehingga setiap *frame*
dapat langsung digambar tanpa ketergantungan antar-*frame* seperti pada H.264;
konsekuensinya MJPEG sederhana dan kompatibel, tetapi boros *bandwidth* [36].
Karena berjalan di atas HTTP/TCP, keandalannya baik namun latensi transport dan
*buffering* dapat lebih besar dibanding protokol seperti UDP.

Latensi ujung-ke-ujung dapat diuraikan menjadi komponen:

$$
T_{\text{e2e}} = T_{\text{capture}} + T_{\text{encode}} + T_{\text{network}} + T_{\text{decode}} + T_{\text{render}}.
$$

Pada sistem teleoperasi robot, pengukuran latensi video menjadi penting karena
kendali waktu nyata bergantung pada kesegaran umpan balik visual [37]. Dengan
demikian, posisi MJPEG-over-HTTP pada penelitian ini adalah **pilihan pragmatis**
yang sederhana dan kompatibel untuk purwarupa, bukan solusi yang paling optimal
secara latensi; protokol berlatensi rendah seperti UDP diposisikan sebagai arah
pengembangan. Perintah gerak dikirim dari laptop melalui *HTTP GET* ke
ESP32-CAM, lalu diteruskan via jalur serial **UART** ke Arduino Uno yang
menjalankan kinematika dan PWM [38].

### 2.2.9 Sistem Terdistribusi dan Ground Station (Flask + WebSocket)

Arsitektur sistem berupa **sistem terdistribusi** yang memisahkan beban kerja:
persepsi visual dan antarmuka pengguna ditempatkan pada laptop (*ground
station*), akuisisi citra pada ESP32-CAM, dan aktuasi waktu nyata pada Arduino
Uno. Pemisahan ini membuat mikrokontroler cukup fokus pada I/O dan aktuasi,
sementara komputasi persepsi yang lebih berat ditangani laptop. *Ground station*
dibangun dengan **Flask**, sebuah *framework* web WSGI ringan untuk Python yang
sesuai untuk membangun dasbor kalibrasi, *overlay* video, telemetri, dan
pencatatan [39].

Untuk komunikasi waktu nyata antara server dan klien dasbor digunakan
**WebSocket** (RFC 6455), kanal dua arah di atas satu koneksi TCP [41], yang
diakses praktis melalui pustaka **Flask-SocketIO** [40]. Dengan pola
*event-driven* ini, dasbor dapat menampilkan status *finite state machine*,
telemetri, parameter HSV, dan kendali manual tanpa *polling* HTTP yang boros.
Arsitektur terdistribusi semacam ini juga memudahkan penyertaan fitur
keselamatan: simpul aktuator dapat dirancang berhenti otomatis (*watchdog*) bila
tidak menerima pembaruan perintah dalam selang tertentu, dan *ground station*
mengirim perintah gerak secara berkala (*heartbeat*) selama tombol kendali
ditahan agar *watchdog* tidak keliru menghentikan motor. Pola pemisahan jalur
video dan jalur perintah juga mempermudah penelusuran kesalahan dan
pengeksporan data eksperimen (mis. log CSV).

### 2.2.10 Finite State Machine dan P-Controller untuk Navigasi Visual

Perilaku robot dikoordinasikan oleh **Finite State Machine** (FSM), yaitu
struktur yang menyimpan keadaan saat ini, aturan transisi, dan aksi pada tiap
keadaan [42]. FSM sesuai untuk tugas yang bersifat *behavior-driven*: ketika
belum ada target robot mencari, ketika target terlihat robot mendekat, dan
ketika target cukup dekat robot mengumpulkan. Penelitian ini menggunakan empat
keadaan: **IDLE → SEARCH → APPROACH → COLLECT**. Keunggulan FSM adalah mudah
dijelaskan, mudah ditelusuri kesalahannya, dan cocok dipadukan dengan sensor
yang kadang berderau.

Pada keadaan APPROACH, koreksi arah dilakukan dengan **kendali proporsional**
(*P-controller*) berbasis galat citra. Galat didefinisikan sebagai selisih
posisi horizontal *centroid* bola terhadap pusat *frame*,
$e_{x}=c_{x}-x_{\text{tengah}}$, dan sinyal kemudi dihitung sebagai

$$
u_{\text{steer}} = K_{p}\,e_{x}.
$$

Sinyal $u_{\text{steer}}$ dipadukan dengan perintah maju dasar untuk menghasilkan
$\omega$ pada robot. Pemilihan *P-controller* memadai karena tugasnya hanya
mengurangi galat arah secara proporsional; komponen integral dan derivatif belum
diperlukan selama gerak pendekatan masih sederhana. Karena kamera terpasang
tetap, kendali ini merupakan **kemudi badan robot** (*body steering*), bukan
pelacakan kamera (*pan-tilt*). Perlu dicatat bahwa latensi *streaming* MJPEG
menambah keterlambatan fasa pada lingkar kendali, sehingga nilai $K_{p}$ tidak
boleh terlalu agresif untuk menghindari osilasi (*hunting*) [37], [43].

## 2.3 Kerangka Berpikir

Kerangka berpikir penelitian ini berangkat dari permasalahan pengumpulan bola
ping-pong secara manual yang menyita waktu dan tenaga, lalu mengusulkan solusi
berupa robot pengumpul bola otonom dengan arsitektur terdistribusi yang
pragmatis dan terukur. Alur berpikirnya adalah sebagai berikut.

**Masukan.** Kondisi arena latihan dengan sejumlah bola ping-pong yang
tersebar pada lantai datar di dalam ruangan.

**Proses.** Kamera ESP32-CAM mengirim citra melalui *streaming* MJPEG ke
*ground station* (laptop). Di laptop, citra diproses dengan **segmentasi warna
HSV** untuk mendeteksi bola dan menghitung *centroid* serta galat posisinya
(YOLOv8 dievaluasi terpisah secara luring sebagai pembanding). Galat posisi
diolah oleh **finite state machine** dengan koreksi arah **P-controller**,
menghasilkan perintah kecepatan sasis ($v_{x}, v_{y}, \omega$). Perintah dikirim
ke ESP32-CAM lalu diteruskan ke Arduino Uno, yang menghitung **kinematika invers
Mecanum** dan membangkitkan sinyal PWM untuk keempat motor melalui *driver*
DRV8833. Setelah robot cukup dekat, **gripper cetak 3D** digerakkan servo untuk
mencengkeram bola. Seluruh proses diawasi fitur keselamatan (*watchdog* dan
*heartbeat*).

**Keluaran.** Bola berhasil dikumpulkan secara otomatis ke penampung, sehingga
mengurangi beban kerja manual selama latihan.

[Gambar 2.1: Diagram kerangka berpikir penelitian — alur Masukan → Proses →
Keluaran sebagaimana diuraikan di atas.]
