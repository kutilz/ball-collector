# Riset Literatur untuk Skripsi Implementasi Computer Vision dan Kinematika Roda Mecanum pada Otomasi Robot Pengumpul Bola Ping-Pong

## Ruang lingkup dan cara membaca hasil riset ini

Laporan ini disusun dengan sengaja **mengunci ruang lingkup pada sistem
yang benar-benar dibangun**: deteksi utama berbasis **HSV segmentation
di OpenCV pada laptop**, **YOLOv8 hanya sebagai pembanding offline**,
sasis **4WD Mecanum** dengan **inverse kinematics di Arduino Uno**,
heading dari **integrasi gyro sumbu-Z MPU6050**, kamera **ESP32-CAM
fixed** dengan **MJPEG over HTTP/WiFi**, perintah gerak melalui **HTTP
GET ke ESP32 lalu UART ke Arduino**, intake berbasis **servo sweep**,
kontrol otonom berbentuk **Finite State Machine** dengan steering
**P-controller**, dan ground station **Flask + WebSocket** dengan
overlay, telemetri, logging, serta fitur keselamatan seperti watchdog,
heartbeat, dan clamp PWM. Karena itu, teori tentang **UDP low-latency,
pan-tilt + PID tracking, silinder rotasi kontinu, dan complementary
filter** saya masukkan hanya sebagai **pembanding teori atau arah
pengembangan**, bukan sebagai deskripsi sistem yang sudah berjalan.

Secara isi, bagian pertama memetakan **state of the art** agar dapat
dipakai untuk BAB I dan BAB II.1, lalu bagian kedua memaparkan
**landasan teori** yang langsung sejajar dengan blok sistem nyata Anda.
Setiap subbab memuat sintesis yang bisa langsung diadaptasi ke naskah
akademik, disertai persamaan kunci dan sumber yang nyata serta dapat
diverifikasi. Jika suatu metadata bibliografis tidak sepenuhnya dapat
dipastikan dari sumber yang saya akses, saya tandai **\[PERLU
VERIFIKASI\]** sesuai permintaan Anda.

## Penelitian terdahulu tentang robot pengumpul bola olahraga

### Robot pengumpul bola olahraga dan keterbatasannya

Literatur robot pengumpul bola olahraga menunjukkan bahwa kebutuhan
utamanya relatif konsisten: mendeteksi bola kecil yang tersebar,
menentukan arah pendekatan, lalu mengumpulkannya secara mekanis ke dalam
wadah. Akan tetapi, cara realisasinya sangat beragam. Wu, Cheng, dan Hsu
mengembangkan robot pengumpul bola golf dengan **bird-view camera** yang
dipasang di atas area latihan, sehingga persepsi robot sangat ditopang
oleh perspektif top-view, bukan kamera rendah yang berada pada robot;
arsitektur seperti ini kuat untuk pemetaan area luas, tetapi tidak
langsung cocok untuk robot low-cost dengan kamera tetap di bodi. Yun,
Moon, dan Ko kemudian mengembangkan navigasi berbasis stereo untuk robot
pengumpul bola golf, lagi-lagi menunjukkan bahwa banyak solusi terdahulu
mengandalkan konfigurasi penginderaan yang relatif "lebih nyaman"
daripada kamera tunggal fixed di robot. Pada ranah tenis meja, Yeon dkk.
merancang robot pengumpul bola tenis meja otonom, sedangkan Sato dkk.
pada 2024 menampilkan robot pengumpul bola tenis meja dengan
**differential-drive platform**, kamera RGB onboard, serta mekanisme
**rotating elastic blades**. Garis besar ini penting untuk BAB I:
mayoritas studi terdahulu berfokus pada fungsi pengumpulan, tetapi tidak
selalu menekankan kombinasi **fixed monocular camera + distributed
processing + Mecanum holonomic base** yang menjadi ciri sistem Anda.
[\[1\]](https://www.researchgate.net/publication/321821433_System_design_for_autonomous_table_tennis_ball_collecting_robot)

Keterbatasan yang berulang pada penelitian-penelitian tersebut juga
cukup jelas. Pada robot golf berbasis visi, keterandalan sering
diasumsikan pada kondisi yang "baik", misalnya prototipe Olsson dibuat
untuk menguji prinsip dasar dan secara eksplisit dibatasi pada kondisi
ideal, dengan kamera yang tidak tertutup hujan atau lumpur dan struktur
yang belum cukup tahan untuk kondisi lapangan sesungguhnya. Pada
karya-karya tenis dan tenis meja, tantangan yang muncul adalah **bola
berukuran kecil**, **occlusion atau overlap**, **variasi pencahayaan**,
dan kebutuhan mekanisme intake yang tetap efektif ketika posisi bola
tidak ideal. Gu dkk. menegaskan bahwa deteksi bola tenis dengan model
deep learning pada perangkat mobile terhambat oleh ukuran model,
kebutuhan data latih, dan kecepatan inferensi; pada robot tenis mereka,
YOLOv3 tanpa GPU bahkan dilaporkan terlalu lambat untuk operasi robotik
praktis. Studi proyek tingkat sarjana tentang robot pengumpul bola tenis
juga secara eksplisit menyebut bahwa metode berbasis warna dan bentuk
dipilih sebagai alternatif yang lebih realistis ketika waktu, data
sampel, dan keahlian untuk membangun metode yang lebih canggih terbatas.
Kumpulan temuan ini sangat berguna sebagai dasar **gap analysis**:
masalah utamanya bukan sekadar "membuat robot memungut bola", tetapi
**menjaga robustnes deteksi dan efektivitas pengumpulan pada platform
low-cost yang komputasinya terbatas**.
[\[2\]](https://www.diva-portal.org/smash/get/diva2%3A957828/FULLTEXT01.pdf)

Untuk konteks bola ping-pong secara lebih dekat, Cheng melaporkan robot
pengumpul bola ping-pong berbasis embedded vision yang menghitung posisi
relatif bola dalam citra lalu mengirim hasilnya ke motion controller.
Ini menunjukkan bahwa pendekatan visi tertanam untuk bola ping-pong
memang sudah ada, tetapi literatur tersebut tidak sekaligus menempatkan
**HSV sebagai detektor online utama** dan **YOLOv8 sebagai pembanding
offline** yang dievaluasi dengan precision, recall, F1, mAP, dan FPS
dalam arsitektur terdistribusi laptop--ESP32--Arduino seperti sistem
Anda. Dengan kata lain, novelty skripsi Anda lebih aman diframe sebagai
**integrasi arsitektur low-cost yang pragmatis, terukur, dan sesuai
deployment nyata**, bukan sekadar klaim "robot pengumpul bola pertama".
[\[3\]](https://www.scientific.net/AMM.511-512.838)

Sumber yang paling layak disitir untuk subbab ini: Yeon dkk., *System
Design for Autonomous Table Tennis Ball Collecting Robot*, ICCAS 2017,
DOI 10.23919/ICCAS.2017.8204354; Sato dkk., *Design and System
Integration of Table Tennis Ball-Collecting Robot*, SII 2024, DOI
10.1109/SII58957.2024.10417471; Yun dkk., *Vision Based Navigation for
Golf Ball Collecting Mobile Robot*, ICCAS 2013, DOI
10.1109/ICCAS.2013.6703893; Wu dkk., *Design and Implementation of a
Prototype Vision-Guided Golf-Ball Collecting Mobile Robot*, IEEE ICM
2005, URL tersedia; Cheng, *Research on Ping-Pong Balls Collecting Robot
Based on Embedded Vision Processing System*, *Applied Mechanics and
Materials*, 2014, DOI 10.4028/www.scientific.net/AMM.511-512.838.

### Deteksi bola dengan YOLO dan deep learning pada robot atau aplikasi olahraga

Untuk deteksi bola berbasis deep learning, literatur menunjukkan dua
pola. Pola pertama adalah **detektor yang sangat spesifik untuk bola
kecil**, seperti *DeepBall*, yang memodifikasi one-stage detection agar
lebih cocok untuk small-object detection pada video olahraga jarak jauh;
karya ini menekankan pentingnya konteks visual multi-level karena bola
sering sangat kecil, bergerak cepat, dan mudah tertukar dengan elemen
latar. Pola kedua adalah **adaptasi YOLO untuk robot olahraga**,
misalnya *xYOLO* pada robot humanoid sepak bola low-end, yang dirancang
agar tetap bisa mendeteksi bola dan tiang gawang sekitar 10 FPS pada
Raspberry Pi 3. Dua contoh ini penting bagi skripsi Anda karena
sama-sama menunjukkan bahwa deteksi bola merupakan kasus yang menuntut:
objek kecil, real-time, dan sering harus berkompromi antara akurasi dan
komputasi. [\[4\]](https://arxiv.org/pdf/1902.07304)

Pada aplikasi robot tenis, Gu dkk. mengembangkan robot pengumpul bola
tenis berbasis deep learning yang diimplementasikan pada Jetson TX1, dan
pada artikel lanjutannya mereka menunjukkan bahwa YOLOv3 standar terlalu
berat untuk kebutuhan robot mobile, sehingga mereka mengganti backbone
ke MobileNetv1 dan memodifikasi arsitektur agar lebih ringan. Mereka
juga menekankan biaya nyata dari pendekatan deep learning: perlu data
latih yang relevan dengan sudut pandang robot, perlu iterasi pelatihan,
dan kecepatan inferensi tetap menjadi persoalan saat komputasi terbatas.
Bagi sistem Anda, temuan ini sangat berguna untuk argumentasi mengapa
**YOLOv8 masuk akal dijadikan pembanding offline**, tetapi tidak
otomatis bijak dijadikan **detektor utama real-time** pada platform
low-cost berbasis streaming WiFi dan mikrokontroler.
[\[5\]](https://ieeexplore.ieee.org/iel7/8425581/8452219/08452263.pdf)

Sumber yang paling layak disitir untuk subbab ini: Komorowski dkk.,
*DeepBall: Deep Neural-Network Ball Detector*, arXiv:1902.07304; Bruce
dkk., *xYOLO: A Model for Real-Time Object Detection in Humanoid Soccer
on Low-End Hardware*, arXiv:1910.03159; Gu dkk., *A Deep Learning Tennis
Ball Collection Robot and the Implementation on NVIDIA Jetson TX1
Board*, AIM 2018, URL IEEE; Gu dkk., *Intelligent Tennis Robot Based on
a Deep Neural Network*, *Applied Sciences*, 2019, DOI
10.3390/app9183746.

## Penelitian terdahulu tentang platform Mecanum dan perbandingan metode visi

### Robot mobil berbasis roda Mecanum

Literatur Mecanum secara konsisten menyatakan bahwa keunggulan utamanya
adalah **omnidirectional mobility**: translasi longitudinal,
transversal, dan rotasi dapat dibentuk dari kombinasi kecepatan empat
roda yang masing-masing memiliki roller miring, lazimnya **45°**.
Taheri, Qiao, dan Ghaeminezhad menunjukkan model kinematika robot 4-roda
Mecanum dan menurunkan relasi forward--inverse kinematics untuk
kecepatan sasis dan kecepatan roda. Hernández dkk. pada 2024 juga
menempatkan kinematic control Mecanum sebagai basis simulasi dan
eksperimen, menegaskan bahwa akurasi gerak Mecanum sangat dipengaruhi
model kinematika, sign convention, dan realitas lapangan seperti slip.
Artinya, untuk BAB II, Anda aman menempatkan roda Mecanum bukan hanya
sebagai "roda yang bisa strafing", tetapi sebagai **platform holonomik**
yang secara matematis memungkinkan pemisahan komponen $v_{x}$, $v_{y}$,
dan $\omega$, meskipun implementasi otonom Anda saat ini memilih mode
**maju + rotasi** sebagai strategi navigasi utama.
[\[6\]](https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf)

Di sisi state of the art, poin pentingnya justru bukan bahwa Mecanum itu
baru, melainkan bahwa **banyak robot pengumpul bola olahraga sebelumnya
tidak memanfaatkan Mecanum**. Sato dkk. 2024 masih menggunakan
differential drive untuk pengumpul bola tenis meja; Olsson menggunakan
Ackermann steering untuk demonstrator pengumpul bola golf; dan beberapa
robot tenis mengandalkan konfigurasi non-holonomik lain. Ini membuka
celah argumentatif yang kuat: penggunaan Mecanum pada skripsi Anda bukan
sekadar variasi mekanik, tetapi **pilihan desain** yang memperluas
kemampuan gerak manual dan potensi manuver di arena sempit, meskipun
pada mode otonom penuh Anda sengaja membatasi strategi ke **approach
sederhana** demi kestabilan sistem.
[\[7\]](https://tohoku.elsevierpure.com/en/publications/design-and-system-integration-of-table-tennis-ball-collecting-rob/)

Sumber yang paling layak disitir untuk subbab ini: Taheri dkk.,
*Kinematic Model of a Four Mecanum Wheeled Mobile Robot*, *International
Journal of Computer Applications*, 2015; Hernández dkk., *Kinematic
control in a four-wheeled Mecanum mobile robot*, *The Journal of
Engineering*, 2024, DOI 10.1049/tje2.70006; Tlale dan de Villiers,
*Kinematics and Dynamics Modelling of a Mecanum Wheeled Mobile
Platform*, IEEE, 2008, URL IEEE; Salih dkk., *Designing Omni-Directional
Mobile Robot with Mecanum Wheel*, *American Journal of Applied
Sciences*, 2006, URL tersedia.

### Studi perbandingan segmentasi warna klasik dan deteksi berbasis CNN atau deep learning

Dari sudut pandang metodologis, literatur pembanding antara visi klasik
dan deep learning hampir selalu berakhir pada kompromi yang sama:
**metode klasik lebih ringan dan cepat**, sedangkan **deep learning
lebih robust terhadap variasi kondisi**. Pada studi deteksi tomat rumah
kaca, Moreira dkk. membandingkan model berbasis deep learning seperti
SSD MobileNet v2 dan YOLOv4 dengan model berbasis HSV; mereka
menunjukkan bahwa model deep learning lebih kuat untuk skenario
kompleks, tetapi model HSV tetap relevan ketika tugas klasifikasi warna
sangat dominan dan kebutuhan komputasi lebih ketat. Pada studi deteksi
tanaman jagung, Liu dkk. membandingkan color index--based methods dengan
YOLOv3 dan YOLOv3-tiny; hasilnya menunjukkan bahwa metode DL lebih baik
dalam akurasi dan robustnes pada kondisi kompleks, sedangkan metode
berbasis warna lebih cepat dalam FPS.
[\[8\]](https://www.mdpi.com/2073-4395/12/2/356)

Bagi skripsi Anda, dua temuan ini sangat langsung kegunaannya. Pertama,
secara ilmiah Anda punya dasar untuk mengatakan bahwa **HSV layak
dipilih sebagai detektor utama** bila target berwarna relatif kontras,
kebutuhan inferensinya ringan, dan sistem harus cukup responsif pada
arsitektur laptop--WiFi--mikrokontroler. Kedua, Anda juga punya dasar
ilmiah untuk menguji **YOLOv8 sebagai pembanding offline**, justru untuk
menunjukkan secara terukur apa yang diperoleh dan apa yang dikorbankan:
robustnes vs kompleksitas, akurasi vs FPS, dan kebutuhan dataset vs
kemudahan kalibrasi. Dengan framing ini, skripsi Anda tidak terjebak
pada narasi "metode klasik kalah modern", melainkan "metode klasik
dipilih karena paling cocok dengan **konteks deployment** sistem nyata".
[\[9\]](https://www.mdpi.com/2073-4395/12/2/356)

Sumber yang paling layak disitir untuk subbab ini: Moreira dkk.,
*Benchmark of Deep Learning and a Proposed HSV Colour Space Models for
the Detection and Classification of Greenhouse Tomato*, *Agronomy*,
2022, DOI 10.3390/agronomy12020356; Liu dkk., *Application of Color
Featuring and Deep Learning in Maize Plant Detection*, *Remote Sensing*,
2020, DOI 10.3390/rs12142229; Padilla dkk., *A Comparative Analysis of
Object Detection Metrics with a Companion Open-Source Toolkit*,
*Electronics*, 2021, DOI 10.3390/electronics10030279.

## Landasan teori sistem persepsi dan evaluasi deteksi

### Computer vision dan ruang warna HSV

Pada sistem Anda, blok persepsi utama lebih tepat dijelaskan sebagai
**pipeline segmentasi warna berbasis HSV** daripada "object detection"
dalam arti deep learning. Secara teoritis, HSV memisahkan informasi
warna menjadi **Hue**, **Saturation**, dan **Value**, sehingga pemilihan
warna target dapat dilakukan lebih intuitif dibandingkan langsung
bekerja pada BGR/RGB. OpenCV mendokumentasikan alur paling lazim untuk
tugas ini: citra diubah dari BGR ke HSV dengan `cvtColor`, lalu piksel
target dipilih dengan `inRange` berdasarkan batas bawah--atas pada tiga
kanal tersebut. Dalam konteks bola ping-pong berwarna yang relatif
kontras terhadap lantai atau latar, pendekatan ini sangat wajar karena
Anda dapat melakukan kalibrasi threshold secara langsung di lapangan
melalui slider runtime tanpa perlu training dataset baru. Literatur
pengolahan citra klasik juga mendukung pilihan ini: pemisahan warna dan
intensitas memang membuat thresholding warna lebih operasional untuk
aplikasi real-time yang sumber dayanya terbatas.
[\[10\]](https://opencv24-python-tutorials.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_colorspaces/py_colorspaces.html)

Secara matematis, hasil `inRange` dapat dipandang sebagai mask biner

$$M(x,y) = \left\{ \begin{matrix}
1, & \text{jika }H \in \left\lbrack H_{\min},H_{\max} \right\rbrack,\ S \in \left\lbrack S_{\min},S_{\max} \right\rbrack,\ V \in \left\lbrack V_{\min},V_{\max} \right\rbrack \\
0, & \text{lainnya}
\end{matrix} \right.\ $$

yang kemudian dibersihkan melalui operasi morfologi. Pada citra biner,
**erosi** mengikis foreground kecil dan noise terisolasi, sedangkan
**dilasi** memperbesar kembali area target; dalam notasi himpunan, erosi
dan dilasi dapat ditulis sebagai $A \ominus B$ dan $A \oplus B$, dengan
$B$ sebagai structuring element. OpenCV mendokumentasikan `erode`,
`dilate`, dan `morphologyEx` sebagai operator dasar untuk merapikan
hasil segmentasi, misalnya menghilangkan bintik kecil atau menutup celah
pada blob target. Untuk aplikasi Anda, langkah ini krusial karena
pipeline `inRange → erode/dilate → findContours` membuat hasil deteksi
HSV menjadi cukup stabil walau streaming berasal dari kamera WiFi yang
noisynya bisa naik-turun.
[\[11\]](https://docs.opencv.org/master/javadoc/org/opencv/imgproc/Imgproc.html)

Setelah mask terbentuk, objek target ditentukan dari kontur hasil
`findContours`. OpenCV juga mendokumentasikan `moments()` untuk
menghitung momen hingga orde ketiga; pada kontur non-degenerat, momen
nol $m_{00}$ merepresentasikan luas, sedangkan pusat massa atau centroid
dihitung dari

$$c_{x} = \frac{m_{10}}{m_{00}},\quad\quad c_{y} = \frac{m_{01}}{m_{00}}.$$

Dalam sistem Anda, centroid inilah yang kemudian dibandingkan dengan
titik tengah frame untuk menghasilkan **offset horizontal** sebagai
error steering. Ini sangat sesuai dengan prinsip visual servoing
sederhana: kamera tidak perlu melakukan estimasi pose 3D penuh, karena
untuk task **search--approach--collect** cukup diketahui apakah target
berada di kiri, kanan, atau dekat pusat citra. Secara praktis,
pendekatan ini jauh lebih ringan daripada running detector CNN secara
kontinu pada robot.
[\[12\]](https://docs.opencv.org/master/javadoc/org/opencv/imgproc/Imgproc.html)

Sumber yang paling layak disitir untuk subbab ini: OpenCV, *Changing
Colorspaces*, URL resmi; OpenCV, *Imgproc* documentation untuk
`inRange`, `erode`, `dilate`, `findContours`, dan `moments`, URL resmi;
Bradski dan Kaehler, *Learning OpenCV*, O'Reilly, 2008; Gonzalez dan
Woods, *Digital Image Processing*, 4th ed., Pearson, 2018.

### Object detection deep learning, CNN, single-stage detector, dan YOLOv8

Berbeda dari HSV segmentation yang berbasis aturan, deteksi objek deep
learning bertumpu pada **Convolutional Neural Network** yang belajar
langsung dari data berlabel. Secara umum, CNN mengekstraksi fitur
bertingkat: layer awal menangkap tepi dan pola lokal, layer menengah
menangkap tekstur dan bentuk, lalu layer lebih dalam membentuk
representasi yang lebih abstrak. Dalam taksonomi deteksi objek, keluarga
YOLO berada pada kelompok **single-stage detectors**, yaitu model yang
langsung memprediksi lokasi dan kelas objek dalam satu lintasan
inferensi tanpa tahap proposal region terpisah seperti keluarga R-CNN.
Konsekuensinya, single-stage detectors lazim dipilih ketika targetnya
real-time, meskipun trade-off speed--accuracy tetap bergantung pada
ukuran model, data, dan perangkat keras.
[\[13\]](https://arxiv.org/pdf/1902.07304)

Untuk **YOLOv8**, dokumentasi resmi Ultralytics menekankan beberapa ciri
yang relevan untuk BAB II. Pertama, YOLOv8 memakai **anchor-free split
head**, sehingga prediksi tidak lagi sangat bergantung pada anchor boxes
predefined seperti versi YOLO lama. Kedua, backbone dan neck-nya memakai
blok **C2f**, yang menurut dokumentasi Ultralytics dirancang untuk
memperbaiki gradient flow dan representasi fitur tanpa menambah beban
komputasi secara berlebihan. Ketiga, YOLOv8 tetap berada dalam keluarga
one-stage detector yang ditujukan untuk real-time use, sehingga cocok
sebagai **algoritma pembanding** ketika Anda ingin mengukur seberapa
jauh detektor modern dapat meningkatkan precision/recall/mAP pada
dataset bola yang sama. Karena dokumentasi resmi YOLOv8 berasal dari
pengembang framework, sumber ini sahih untuk deskripsi implementasi,
meskipun secara akademik tetap baik jika dipasangkan dengan review
evolusi YOLO. [\[14\]](https://docs.ultralytics.com/models/yolov8)

Dalam training, model YOLO belajar dengan meminimalkan loss total yang
pada praktiknya merupakan kombinasi loss klasifikasi dan loss
lokalisasi, yang secara konseptual dapat ditulis sebagai

$$L_{\text{total}} = L_{\text{cls}} + L_{\text{box}} + L_{\text{aux}},$$

dengan $L_{\text{aux}}$ pada implementasi YOLO modern biasanya mencakup
komponen tambahan seperti distribusi koordinat atau quality-aware
regression. Dokumentasi Ultralytics juga menjelaskan bahwa training mode
mereka memanfaatkan augmentasi seperti **Mosaic, MixUp, CutMix, flips,
random perspective**, serta jitter warna **HSV**. Bagi skripsi Anda,
bagian ini penting untuk menunjukkan bahwa **YOLOv8 offline** tetap
menuntut tahap dataset curation, labeling, training, dan evaluasi
terpisah, berbeda jauh dari HSV yang dapat dikalibrasi langsung di
lapangan. Inilah alasan metodologis yang kuat mengapa YOLOv8 lebih tepat
Anda tempatkan sebagai **baseline pembanding**, bukan detektor utama
deployed di robot. [\[15\]](https://docs.ultralytics.com/modes/train)

Sumber yang paling layak disitir untuk subbab ini: Ultralytics, *Explore
Ultralytics YOLOv8*, URL resmi; Ultralytics, *Model Training with
Ultralytics YOLO*, URL resmi; Ultralytics, *Data Augmentation using
Ultralytics YOLO*, URL resmi; Terven dkk., *A Comprehensive Review of
YOLO Architectures in Computer Vision*, *Machine Learning and Knowledge
Extraction*, 2023, DOI 10.3390/make5040083.

### Metrik evaluasi deteksi

Karena Anda membandingkan HSV dan YOLOv8, BAB II perlu menegaskan bahwa
performa tidak boleh dinilai dari "terlihat bagus" saja, tetapi harus
melalui metrik yang membedakan **ketepatan klasifikasi**, **ketepatan
lokasi**, dan **kecepatan inferensi**. Padilla dkk. mendefinisikan
**precision** sebagai proporsi prediksi positif yang benar, dan
**recall** sebagai proporsi ground truth yang berhasil ditemukan. Dalam
bentuk sederhana,

$$\text{Precision} = \frac{TP}{TP + FP},\quad\quad\text{Recall} = \frac{TP}{TP + FN}.$$

Jika dua metrik ini ingin diseimbangkan menjadi satu angka, dipakai
**F1-score**,

$$F_{1} = \frac{2PR}{P + R}.$$

Formula ini sangat relevan untuk skripsi Anda karena HSV dan YOLOv8
dapat gagal dengan pola yang berbeda: HSV bisa cepat tetapi rentan false
positive pada warna mirip, sedangkan YOLOv8 bisa lebih robust tetapi
belum tentu lebih cepat.
[\[16\]](https://www.mdpi.com/2079-9292/10/3/279)

Untuk kualitas lokalisasi bounding box, metrik dasarnya adalah
**Intersection over Union** atau

$$IoU = \frac{\text{area}\left( B_{p} \cap B_{gt} \right)}{\text{area}\left( B_{p} \cup B_{gt} \right)}.$$

VOC challenge menjadikan overlap ini dasar penentuan benar-salah
deteksi, dan secara historis threshold 0,5 sering dipakai untuk menilai
apakah suatu deteksi cukup tepat. Dari kurva precision--recall yang
dihasilkan pada berbagai confidence threshold, dihitung **Average
Precision**, lalu dirata-ratakan antar kelas menjadi **mAP**. Walaupun
dalam skripsi Anda kelas objek mungkin hanya sedikit, struktur metrik
ini tetap penting karena ia memisahkan dua hal yang sering tercampur:
model bisa saja "sering menemukan bola" tetapi lokasinya longgar, atau
sebaliknya sangat presisi namun banyak miss.
[\[17\]](https://homepages.inf.ed.ac.uk/ckiw/postscript/ijcv_voc09.pdf)

Selain itu, untuk analisis operasional, Anda juga perlu memakai
**confusion matrix** dan **FPS**. Confusion matrix merangkum jumlah TP,
FP, FN, dan TN, sehingga mudah dipakai untuk menjelaskan pola error
dalam bahasa yang lebih intuitif. Di sisi lain, Ultralytics sendiri
menempatkan **FPS** sebagai indikator penting untuk kemampuan real-time.
Ini sangat sentral bagi narasi skripsi Anda: karena YOLOv8 adalah
pembanding offline, maka hasil evaluasinya harus dibaca bukan hanya dari
mAP, tetapi juga dari konsekuensi komputasionalnya terhadap deployment
nyata. Dengan demikian, simpulan yang diambil nantinya dapat lebih
jujur: "metode A lebih akurat", "metode B lebih feasible untuk sistem
berjalan", atau "metode A layak untuk pengembangan tahap berikutnya jika
perangkat keras dinaikkan".
[\[18\]](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html)

Sumber yang paling layak disitir untuk subbab ini: Padilla dkk., *A
Comparative Analysis of Object Detection Metrics with a Companion
Open-Source Toolkit*, *Electronics*, 2021, DOI
10.3390/electronics10030279; Everingham dkk., *The PASCAL Visual Object
Classes (VOC) Challenge*, *IJCV*, 2010, DOI 10.1007/s11263-009-0275-4;
Lin dkk., *Microsoft COCO: Common Objects in Context*, ECCV 2014, URL;
scikit-learn documentation untuk `confusion_matrix`,
`precision_recall_fscore_support`, dan `f1_score`, URL resmi;
Ultralytics, *YOLO Performance Metrics*, URL resmi.

## Landasan teori gerak, aktuasi, sensing, dan kendali

### Kinematika roda Mecanum

Prinsip dasar roda Mecanum terletak pada roller yang dipasang miring,
lazimnya **45°**, sehingga gaya kontak tiap roda dapat diuraikan menjadi
komponen longitudinal dan transversal. Jika empat roda disusun saling
berpasangan pada keempat sudut sasis, maka superposisi gaya dari semua
roda memungkinkan robot bergerak maju--mundur, menyamping, dan berotasi
tanpa mekanisme steering aktif. Taheri dkk. menurunkan bentuk Jacobian
untuk robot 4WD Mecanum dan menunjukkan bahwa kecepatan masing-masing
roda merupakan fungsi linear dari $v_{x}$, $v_{y}$, dan $\omega_{z}$.
Dalam notasi umum,

$$\mathbf{\omega} = \frac{1}{r}\mathbf{J}\begin{bmatrix}
v_{x} \\
v_{y} \\
\omega_{z}
\end{bmatrix},$$

dengan $r$ jari-jari roda dan $\mathbf{J}$ bergantung pada geometri
sasis serta konvensi urutan roda.
[\[19\]](https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf)

Untuk konfigurasi 4WD simetris, salah satu bentuk inverse kinematics
yang sangat lazim adalah

$$\begin{bmatrix}
\omega_{FL} \\
\omega_{FR} \\
\omega_{RL} \\
\omega_{RR}
\end{bmatrix} = \frac{1}{r}\begin{bmatrix}
1 & - 1 & - \left( l_{x} + l_{y} \right) \\
1 & 1 & \left( l_{x} + l_{y} \right) \\
1 & 1 & - \left( l_{x} + l_{y} \right) \\
1 & - 1 & \left( l_{x} + l_{y} \right)
\end{bmatrix}\begin{bmatrix}
v_{x} \\
v_{y} \\
\omega_{z}
\end{bmatrix},$$

sementara bentuk forward kinematics-nya diperoleh dari pseudoinverse
Jacobian. Di skripsi Anda, bentuk implementasinya disederhanakan menjadi
**FL =** $v_{x} + v_{y} + \omega$, **FR =** $v_{x} - v_{y} - \omega$,
**RL =** $v_{x} - v_{y} + \omega$, dan **RR =** $v_{x} + v_{y} - \omega$
setelah normalisasi skala dan penetapan konvensi tanda. Secara akademik,
ini sah selama Anda menjelaskan bahwa persamaan tersebut adalah **bentuk
implementatif tereduksi** dari model umum yang telah dimap ke orientasi
motor dan arah putaran pada robot Anda.
[\[20\]](https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf)

Hubungan ke PWM/RPM dapat dijelaskan sebagai pendekatan praktis: inverse
kinematics menghasilkan **perintah kecepatan roda relatif**, lalu nilai
ini dipetakan ke PWM motor DC dengan saturasi dan clamp sesuai batas
aktuator. Pada robot riil, relasi PWM--RPM tidak sepenuhnya linear
karena dipengaruhi tegangan baterai, beban, dan gesekan, sehingga
implementasi tanpa closed-loop wheel encoder lebih tepat disebut
**quasi-kinematic control** daripada velocity control ideal. Ini justru
memperkuat alasan mengapa model otonom awal Anda memilih skema manuver
sederhana. [\[21\]](https://www.ti.com/lit/gpn/DRV8833)

Sumber yang paling layak disitir untuk subbab ini: Taheri dkk.,
*Kinematic Model of a Four Mecanum Wheeled Mobile Robot*, *IJCA*, 2015;
Hernández dkk., *Kinematic control in a four-wheeled Mecanum mobile
robot*, *The Journal of Engineering*, 2024, DOI 10.1049/tje2.70006;
Gfrerrer, *Geometry and Kinematics of the Mecanum Wheel*, PDF TU Graz,
URL tersedia.

### IMU MPU6050 dan estimasi heading

MPU6050 mengintegrasikan **3-axis gyroscope** dan **3-axis
accelerometer**, masing-masing dengan ADC 16-bit. Datasheet resmi
menyebut rentang gyro yang dapat diprogram pada **±250, ±500, ±1000, dan
±2000 °/s**, dengan faktor sensitivitas yang bergantung pada pengaturan
full-scale range. Dalam konteks skripsi Anda, yang paling penting bukan
seluruh orientasi 3D, melainkan **heading relatif** dari sumbu-z untuk
mendukung state **SEARCH** dan referensi rotasi sederhana. Karena itu,
penggunaan gyro z secara langsung merupakan pilihan desain yang masuk
akal untuk prototype low-cost, selama Anda jujur menjelaskan
keterbatasannya.
[\[22\]](https://cdn.sparkfun.com/datasheets/Components/General%20IC/PS-MPU-6000A.pdf)

Secara diskrit, heading dapat diperkirakan dengan integrasi

$$\theta_{k} = \theta_{k - 1} + \left( \omega_{z} - b_{z} \right)\Delta t,$$

dengan $\omega_{z}$ laju sudut terukur, $b_{z}$ bias gyro, dan
$\Delta t$ interval sampling. Problem utamanya adalah **drift**.
Literatur dead-reckoning IMU menegaskan bahwa bias yang tidak
dikompensasi akan menghasilkan error sudut yang tumbuh terhadap waktu;
Eger dkk. menulis secara eksplisit bahwa pada gyroscope, bias tak
terkompensasi memunculkan error sudut yang proporsional terhadap waktu.
Studi dead-reckoning berbasis IMU untuk wheeled robot juga menunjukkan
bahwa bias gyro dapat stabil hanya untuk interval tertentu, lalu drift
meningkat ketika kondisi getaran atau gangguan mekanik memburuk. Maka,
untuk naskah Anda, posisi teoretis yang paling aman adalah: **integrasi
gyro-z dipilih karena sederhana dan ringan**, tetapi ia hanya cukup
andal untuk horizon waktu pendek atau tugas heading relatif, bukan
navigasi absolut jangka panjang.
[\[23\]](https://lcv.fee.unicamp.br/wp-content/images/BTSym-22-Brasil/papers/paper_057.pdf)

Di sini Anda juga bisa menempatkan **complementary filter** secara
tepat: bukan bagian dari sistem yang berjalan, melainkan **konteks
pembanding** karena secara teori ia memadukan kestabilan jangka panjang
accelerometer dengan respons cepat gyroscope. Namun, untuk robot
pengumpul bola Anda, complementary filter belum dipakai karena
kompleksitas tambahan itu belum diperlukan untuk state machine sederhana
yang sangat mengandalkan penglihatan. Dengan framing tersebut, BAB II
tetap kuat secara teoritis tanpa "mengklaim" fitur yang belum
diimplementasikan.
[\[24\]](https://worldscientificnews.com/wp-content/uploads/2025/01/WSN-199-2025-218-234.pdf)

Sumber yang paling layak disitir untuk subbab ini: InvenSense, *MPU-6000
and MPU-6050 Product Specification*, URL; Eger dkk., *A good-practices
guideline for 6-DoF IMU-based dead-reckoning*, PDF URL \[PERLU
VERIFIKASI venue\]; *A Wheel-mounted MEMS IMU-based Dead Reckoning
Method for Wheeled Mobile Robots*, arXiv:1912.07805, URL.

### Aktuator gerak, motor DC, DRV8833, dan PWM

Pada level aktuasi, motor DC brushed tetap menjadi pilihan lazim untuk
mobile robot low-cost karena konstruksinya sederhana, murah, dan mudah
digerakkan dengan H-bridge. Secara praktis, kecepatan rata-rata motor
dapat dikendalikan melalui **Pulse Width Modulation**, yakni dengan
mengubah duty cycle sinyal pada tegangan suplai tetap. Dalam pendekatan
sederhana,

$$V_{\text{avg}} \approx D \cdot V_{s},$$

dengan $D$ duty cycle dan $V_{s}$ tegangan sumber, sehingga kenaikan
duty cycle umumnya menaikkan kecepatan rata-rata motor. White paper ROHM
menekankan bahwa PWM lebih efisien daripada kontrol linear karena
mengurangi disipasi daya pada driver, sekaligus memberi respons yang
lebih baik untuk speed control motor DC.
[\[25\]](https://www.rohm.com/documents/11303/41217/100260.H-BRDG_WP_Jan09.pdf)

Untuk driver, **DRV8833** sangat cocok dengan platform Anda karena
merupakan dual H-bridge terintegrasi untuk motor DC brushed atau stepper
bipolar. Datasheet Texas Instruments menyebut supply **2,7--10,8 V**,
kemampuan hingga **1,5 A RMS** per H-bridge, antarmuka PWM sederhana,
serta proteksi **overcurrent, short-circuit, undervoltage lockout, dan
overtemperature**. Dengan dua buah DRV8833, empat motor DC pada sasis
4WD Mecanum dapat dikendalikan secara terpisah. Ini juga memberi dasar
teknis bagi fitur keselamatan di sistem Anda seperti **clamp PWM** dan
**watchdog timeout**, karena aktuator robot memang perlu dibatasi secara
eksplisit untuk menghindari runaway motion saat komunikasi putus.
[\[26\]](https://www.ti.com/lit/gpn/DRV8833)

Dalam penulisan BAB II, hubungan antara inverse kinematics dan aktuasi
dapat dijelaskan sebagai rantai pemrosesan: kinematika menghasilkan
target kecepatan roda, lalu target tersebut dipetakan ke arah putar dan
duty cycle PWM pada masing-masing kanal H-bridge. Karena sistem Anda
memakai Arduino Uno dan bukan closed-loop motor controller industrial,
naskah akan lebih kuat bila menyebut bahwa PWM di sini merupakan
**kontrol masukan aktuator**, bukan jaminan kecepatan absolut yang
presisi. [\[27\]](https://www.ti.com/lit/gpn/DRV8833)

Sumber yang paling layak disitir untuk subbab ini: Texas Instruments,
*DRV8833 Dual H-Bridge Motor Driver datasheet*, URL resmi; ROHM
Semiconductor, *Controlling DC Brush Motors with H-bridge Driver ICs*,
white paper, URL; MathWorks, *Control DC Motor with PWM Voltage Source
and H-Bridge*, URL.

### Servo dan mekanisme pengumpul serta material TPU

Untuk mekanisme intake, sistem Anda lebih tepat diposisikan sebagai
**mekanisme sweep** berbasis **standard hobby servo** daripada roller
atau silinder rotasi kontinu. Prinsip kerja servo hobi adalah **position
control**: sudut poros ditentukan oleh lebar pulsa kendali periodik,
sehingga aktuator sangat cocok untuk gerakan buka--tutup atau ayun
bolak-balik yang terdefinisi. Literatur dasar servo menunjukkan bahwa
sinyal PWM pada servo bukan terutama mengatur daya rata-rata seperti
pada motor DC, tetapi mengkodekan **setpoint posisi**. Karena itu, untuk
mekanisme pengumpul bola ping-pong, servo sweep lebih masuk akal
dijelaskan sebagai aktuator yang **menggerakkan lengan atau pintu intake
secara periodik** untuk memandu bola masuk ke area penampung.
[\[28\]](https://www.princeton.edu/~mae412/TEXT/NTRAK2002/292-302.pdf)

Jika Anda ingin membahas **TPU**, posisinya sebaiknya jelas: **bukan
mekanisme yang sedang dipakai sebagai silinder rotasi kontinu**,
melainkan bahan yang menarik secara teoritis untuk elemen yang
memerlukan **elastisitas, compliance, dan ketahanan aus**. Panduan
material dan studi material TPU menunjukkan bahwa sifat elastomeriknya
berasal dari kombinasi soft segment dan hard segment, sehingga TPU
menawarkan fleksibilitas, toughness, dan pada banyak aplikasi juga
ketahanan abrasi yang baik. Studi TPU cetak 3D juga menunjukkan bahwa
sifat mekaniknya sangat dipengaruhi proses manufaktur, sedangkan studi
tribologi TPU menggarisbawahi bahwa koefisien gesek dan wear behavior
TPU cukup relevan untuk komponen kontak mekanik. Dalam konteks skripsi
Anda, pembahasan TPU sebaiknya dijadikan argumen bahwa material
lunak-komplians dapat berguna pada kontak dengan bola ringan seperti
ping-pong, tetapi **mekanisme sweep servo** tetap menjadi fokus sistem
yang benar-benar berjalan.
[\[29\]](https://www.mdpi.com/2073-4360/12/12/3010)

Sumber yang paling layak disitir untuk subbab ini: *Hobby Servo
Fundamentals*, PDF URL; Autsou dkk., *Principles and Methods of
Servomotor Control*, *Applied Sciences*, 2024, URL; Xu dkk., *Mechanical
Properties of Additively Manufactured TPU Material Affected by Various
Processing Parameters*, *Polymers*, 2020, DOI 10.3390/polym12123010;
Huntsman, *A Guide to Thermoplastic Polyurethanes*, PDF URL; Pinedo
dkk., studi tribologi TPU, PDF URL.

### Finite State Machine dan P-controller untuk navigasi visual

**Finite State Machine** cocok untuk robot pengumpul bola karena
tugasnya sangat behavior-driven: ketika belum ada target, robot mencari;
ketika target terlihat, robot mendekat; ketika target sangat dekat,
robot melakukan pengumpulan. Ben-Ari menjelaskan FSM sebagai struktur
yang menyimpan state saat ini, aturan perpindahan state, dan aksi yang
dijalankan pada tiap state. Ini persis sejalan dengan desain Anda:
**IDLE → SEARCH → APPROACH → COLLECT**. Dalam penulisan BAB II,
keunggulan FSM dapat diuraikan menjadi tiga: mudah dijelaskan, mudah
di-debug, dan cocok untuk integrasi dengan sensor yang kadang-kadang
noisy. Pendekatan ini juga lazim dalam robotika pendidikan dan
prototyping ketika tujuan utamanya adalah kestabilan logika, bukan
optimal control.
[\[30\]](https://link.springer.com/chapter/10.1007/978-3-319-62533-1_4)

Untuk aksi steering pada state **APPROACH**, dasar teoretis yang paling
pas adalah **visual servoing sederhana** berbasis error citra. Tutorial
visual servo klasik oleh Hutchinson, Hager, dan Corke menempatkan
informasi visual sebagai feedback langsung untuk membentuk input kontrol
robot. Dalam implementasi Anda, error tidak perlu kompleks: cukup offset
horizontal target dari pusat frame. Maka, steering dapat ditulis sebagai

$$u_{\text{steer}} = K_{p}\, e_{x},$$

dengan $e_{x} = x_{\text{bola}} - x_{\text{tengah-frame}}$. Nilai
$u_{\text{steer}}$ kemudian dipadukan dengan komando maju dasar untuk
menghasilkan beda kecepatan roda kiri--kanan atau kombinasi velocity
setpoint pada Mecanum. Penggunaan **P-controller** di sini sangat masuk
akal karena tugasnya hanya mengurangi error arah secara proporsional;
belum perlu integral maupun derivatif selama gerak pendekatan masih
sederhana dan target tidak dipasang pada pan-tilt camera.
[\[31\]](https://ieeexplore.ieee.org/document/538972/)

Secara strategis, ini juga konsisten dengan sistem nyata Anda: karena
kamera fixed, steering berbasis P-controller lebih tepat dipahami
sebagai **robot-body steering**, bukan **camera-tracking control**. Di
sinilah penting untuk tidak mencampurkan pembahasan dengan PID pan-tilt.
Dalam skripsi Anda, subsystem yang berjalan adalah body-centric
approaching berbasis offset citra, sementara pan-tilt + PID bisa disebut
sebagai pengembangan tahap berikutnya.
[\[32\]](https://ieeexplore.ieee.org/document/538972/)

Sumber yang paling layak disitir untuk subbab ini: Hutchinson, Hager,
dan Corke, *A Tutorial on Visual Servo Control*, *IEEE Transactions on
Robotics and Automation*, 1996, URL/IEEE; Ben-Ari, *Finite State
Machines*, dalam *Elements of Robotics*, 2017, DOI
10.1007/978-3-319-62533-1_4; Tsai dan Huang, *Implementation of a
real-time moving object tracking and visual servoing control system*,
*Robotica*, DOI 10.1017/S0263574703005332.

## Landasan teori komunikasi, arsitektur terdistribusi, dan sintesis gap

### WiFi, MJPEG streaming, latensi end-to-end, dan ESP32-CAM

Karena kamera Anda adalah **ESP32-CAM fixed** yang mengalirkan video
melalui **MJPEG over HTTP**, BAB II perlu menjelaskan bahwa keputusan
ini adalah kompromi yang rasional antara kesederhanaan implementasi dan
performa. White paper Axis menyebut bahwa MJPEG sering memiliki
**latensi decoding dan display yang rendah**, karena setiap frame dapat
digambar langsung tanpa ketergantungan time-code seperti pada H.264.
Namun, MJPEG juga boros bandwidth karena tiap frame dikirim sebagai JPEG
tersendiri. Di sisi lain, HTTP server ESP-IDF berjalan di atas trafik
HTTP/TCP, sehingga reliabilitasnya bagus dan integrasinya mudah untuk
browser/OpenCV/web dashboard, tetapi konsekuensinya latensi transport
dan buffering bisa lebih besar dibanding solusi video yang lebih "keras"
seperti UDP/WebRTC. Jadi, posisi teoritis yang tepat untuk sistem Anda
adalah: **MJPEG-over-HTTP dipilih karena sederhana, kompatibel, dan
cukup untuk prototype**, bukan karena ia selalu latency-optimal.
[\[33\]](https://whitepapers.axis.com/en-us/latency-in-live-network-video-surveillance)

Secara konseptual, latensi ujung-ke-ujung dapat dituliskan sebagai

$$T_{\text{e2e}} = T_{\text{capture}} + T_{\text{encode}} + T_{\text{network}} + T_{\text{decode}} + T_{\text{render}}.$$

Kaknjo dkk. menegaskan bahwa pada sistem robot teleoperation, pengukuran
parameter latency video menjadi wajib karena kontrol real-time sangat
bergantung pada kualitas umpan balik visual. Untuk konteks ESP32, FAQ
Espressif juga menegaskan bahwa dukungan video pada lini ini sangat
terkait dengan MJPEG dan kemampuan hardware encoding yang terbatas;
bahkan pada ESP32-S3, H.264/H.265 tidak didukung secara hardware dan
jika ingin dipakai harus melalui software encoder yang dapat menurunkan
frame rate. Temuan-temuan ini mendukung justifikasi Anda mengapa sistem
saat ini memakai **MJPEG sederhana** dan mengapa **UDP low-latency**
lebih tepat diposisikan sebagai bahan saran pengembangan BAB V, bukan
fitur yang diklaim sudah berjalan.
[\[34\]](https://pure.ul.ie/en/publications/real-time-video-latency-measurement-between-a-robot-and-its-remot/)

Sumber yang paling layak disitir untuk subbab ini: Axis Communications,
*Latency in Live Network Video Surveillance*, white paper, URL; Kaknjo
dkk., *Real-Time Video Latency Measurement between a Robot and Its
Remote Control Station: Causes and Mitigation*, *Wireless Communications
and Mobile Computing*, 2018, DOI 10.1155/2018/8638019; Espressif,
*Camera Application - ESP-FAQ*, URL resmi; Espressif, *HTTP Server -
ESP-IDF Programming Guide*, URL resmi.

### Sistem terdistribusi, arsitektur client--server, Flask, dan WebSocket

Arsitektur sistem Anda sangat tepat dijelaskan sebagai **sistem robotik
terdistribusi** atau **client--server split architecture**. Persepsi dan
UI ditempatkan pada laptop/ground station, sementara akuisisi gambar
dilakukan oleh ESP32-CAM dan aktuasi real-time dijalankan oleh
Arduino/ESP32. Flask sendiri didokumentasikan sebagai **lightweight WSGI
web application framework**, sehingga cocok untuk membangun dashboard
kalibrasi, overlay, telemetri, dan logging tanpa beban framework yang
terlalu besar. Dari sisi komunikasi real-time, RFC 6455 mendefinisikan
WebSocket sebagai kanal komunikasi dua arah di atas koneksi TCP tunggal,
sedangkan Flask-SocketIO memberi antarmuka praktis untuk komunikasi
bi-directional latency-rendah antara server Flask dan klien. Dengan
kombinasi ini, dashboard Anda dapat menampilkan status sistem, parameter
HSV, dan kontrol manual dalam pola update event-driven, bukan polling
HTTP biasa yang lebih boros overhead.
[\[35\]](https://flask.palletsprojects.com/)

Dari kacamata rekayasa sistem, pendekatan ini punya beberapa keuntungan
akademik yang layak disebutkan. Pertama, beban komputasi persepsi berat
dipindah ke laptop, sehingga mikrokontroler cukup fokus pada I/O dan
aktuasi. Kedua, pemisahan jalur video dan jalur komando membuat
debugging lebih mudah: jika video macet, subsistem motor dan UART masih
bisa diuji terpisah. Ketiga, secara software engineering, pola ini
mendukung **runtime calibration**, **telemetry replay**, dan **CSV
logging** yang penting untuk eksperimen skripsi. Bahkan fitur
keselamatan seperti **watchdog motor** dan **motion heartbeat** sangat
cocok ditempatkan dalam arsitektur seperti ini, karena node aktuator
dapat dibuat berhenti otomatis bila tidak menerima pembaruan perintah
selama interval tertentu. Untuk BAB II, cukup tekankan bahwa semua itu
adalah konsekuensi logis dari desain terdistribusi yang memisahkan layer
persepsi, komunikasi, dan aktuasi.
[\[36\]](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/protocols/esp_http_server.html)

Sumber yang paling layak disitir untuk subbab ini: Flask documentation,
URL resmi; Flask-SocketIO documentation, URL resmi; IETF RFC 6455, *The
WebSocket Protocol*, URL resmi; Espressif, *HTTP Server - ESP-IDF
Programming Guide*, URL resmi.

### Sintesis gap yang paling relevan untuk BAB I

Jika diringkas untuk BAB I, gap terkuat skripsi Anda bukan pada klaim
"belum pernah ada robot pemungut bola", melainkan pada **kombinasi
desain sistem** yang belum banyak dipotret secara utuh di literatur:
robot pengumpul bola ping-pong otonom yang memakai **deteksi online
berbasis HSV di laptop**, **kamera ESP32-CAM fixed melalui MJPEG/HTTP**,
**aktuasi 4WD Mecanum dengan inverse kinematics di Arduino**, dan
**ground station berbasis Flask--WebSocket** dalam arsitektur
terdistribusi low-cost. Banyak penelitian terdahulu memang telah
mengerjakan sebagian komponen itu---ada yang fokus pada pengumpul bola
tenis meja, ada yang fokus pada deteksi bola dengan YOLO, ada yang fokus
pada Mecanum, dan ada yang fokus pada navigasi visi---tetapi tidak
banyak yang menyatukan semuanya persis dalam konfigurasi pragmatis yang
Anda deploy. [\[37\]](https://ieeexplore.ieee.org/document/10417471/)

Gap kedua adalah gap **deployment realism**. Literatur sports-ball robot
cukup sering menampilkan deep learning sebagai pusat sistem persepsi,
tetapi Gu dkk. dan studi-studi pembanding metode dengan jelas
menunjukkan bahwa deep learning membawa beban komputasi, kebutuhan
dataset, dan overhead engineering yang tidak kecil. Sebaliknya, studi
perbandingan HSV/color-feature vs deep learning menunjukkan bahwa metode
klasik masih memiliki keunggulan kuat dalam hal FPS dan kemudahan
deployment pada sumber daya terbatas, walaupun robustnes-nya umumnya
kalah di kondisi kompleks. Karena itu, skripsi Anda dapat diposisikan
sebagai penelitian yang **menguji secara adil** apakah pemilihan HSV
sebagai detektor utama benar-benar rasional untuk sistem berjalan,
sambil menggunakan YOLOv8 sebagai tolok ukur performa yang lebih modern.
Ini adalah framing yang jauh lebih kuat secara akademik daripada sekadar
mengatakan "YOLO lebih bagus" atau "HSV lebih ringan".
[\[38\]](https://www.mdpi.com/2076-3417/9/18/3746)

Gap ketiga adalah gap **arsitektur kendali dan keselamatan sistem**.
Banyak artikel fokus pada deteksi atau mekanisme pickup, tetapi tidak
terlalu rinci membahas dashboard kalibrasi, streaming, telemetry,
timeout safety, dan integrasi multi-node. Padahal untuk robot low-cost
yang beroperasi melalui WiFi, isu seperti latensi video, timeout
perintah, heartbeat gerak, dan pemisahan jalur persepsi--aktuasi sangat
menentukan keberhasilan implementasi. Inilah area yang membuat skripsi
Anda kuat sebagai karya **rekayasa sistem**: kontribusinya bukan hanya
algoritma tunggal, tetapi **integrasi end-to-end** yang dapat berjalan,
diuji, dan diargumentasikan secara terukur.
[\[39\]](https://pure.ul.ie/en/publications/real-time-video-latency-measurement-between-a-robot-and-its-remot/)

Dengan demikian, untuk perumusan kontribusi di BAB I, Anda dapat
menegaskan tiga nilai utama penelitian: **pemilihan metode deteksi yang
sesuai konteks deployment**, **implementasi kinematika Mecanum pada
arsitektur mikrokontroler low-cost**, dan **integrasi sistem
terdistribusi yang aman serta dapat dikalibrasi saat runtime**. Tiga
poin ini paling sejalan dengan sistem nyata yang Anda bangun, dan tidak
tergelincir ke narasi aspirasional seperti UDP low-latency,
complementary filter, atau pan-tilt tracking yang belum menjadi
subsistem operasional.
[\[40\]](https://www.mdpi.com/2072-4292/12/14/2229)

## Daftar pustaka gabungan bergaya IEEE

1.  S. H. Yeon, D. Kim, G. Ryou, dan Y. Sim, "System Design for
    Autonomous Table Tennis Ball Collecting Robot," dalam *Proceedings
    of the 17th International Conference on Control, Automation and
    Systems (ICCAS)*, 2017. doi: 10.23919/ICCAS.2017.8204354.

2.  T. Sato, K. Irie, S. Takaishi, dan H. Kawamoto, "Design and System
    Integration of Table Tennis Ball-Collecting Robot," dalam *2024
    IEEE/SICE International Symposium on System Integration (SII)*, pp.
    1357--1362, 2024. doi: 10.1109/SII58957.2024.10417471.

3.  C.-H. Yun, Y.-S. Moon, dan N.-Y. Ko, "Vision Based Navigation for
    Golf Ball Collecting Mobile Robot," dalam *2013 13th International
    Conference on Control, Automation and Systems (ICCAS)*, pp.
    201--203, 2013. doi: 10.1109/ICCAS.2013.6703893.

4.  S.-L. Wu, M.-Y. Cheng, dan W.-C. Hsu, "Design and Implementation of
    a Prototype Vision-Guided Golf-Ball Collecting Mobile Robot," dalam
    *Proceedings of the IEEE International Conference on Mechatronics*,
    pp. 959--963, 2005. URL:
    https://www.ee.ncku.edu.tw/teacher/index2.php?teacher_id=143

5.  S. Gu, X. Chen, W. Zeng, dan X. Wang, "A Deep Learning Tennis Ball
    Collection Robot and the Implementation on NVIDIA Jetson TX1 Board,"
    dalam *2018 IEEE/ASME International Conference on Advanced
    Intelligent Mechatronics (AIM)*, pp. 170--175, 2018. URL:
    https://ieeexplore.ieee.org/document/8452263/

6.  S. Gu, X. Chen, W. Zeng, dan X. Wang, "Intelligent Tennis Robot
    Based on a Deep Neural Network," *Applied Sciences*, vol. 9, no. 18,
    art. 3746, 2019. doi: 10.3390/app9183746.

7.  J. Komorowski, G. Kurzejamski, dan G. Sarwas, "DeepBall: Deep
    Neural-Network Ball Detector," arXiv:1902.07304, 2019. URL:
    https://arxiv.org/abs/1902.07304

8.  B. J. Bruce *et al.*, "xYOLO: A Model for Real-Time Object Detection
    in Humanoid Soccer on Low-End Hardware," arXiv:1910.03159, 2019.
    URL: https://arxiv.org/abs/1910.03159

9.  H. Taheri, B. Qiao, dan N. Ghaeminezhad, "Kinematic Model of a Four
    Mecanum Wheeled Mobile Robot," *International Journal of Computer
    Applications*, vol. 113, no. 3, pp. 6--9, 2015. URL:
    https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf

10. J. C. O. Hernández, E. Orozco-Rosas, dan G. A. Pérez-Soto,
    "Kinematic control in a four-wheeled Mecanum mobile robot:
    simulation and experimentation," *The Journal of Engineering*, 2024,
    e70006. doi: 10.1049/tje2.70006.

11. M. Everingham, L. Van Gool, C. K. I. Williams, J. Winn, dan A.
    Zisserman, "The PASCAL Visual Object Classes (VOC) Challenge,"
    *International Journal of Computer Vision*, vol. 88, pp.
    303--338, 2010. doi: 10.1007/s11263-009-0275-4.

12. T.-Y. Lin *et al.*, "Microsoft COCO: Common Objects in Context,"
    dalam *European Conference on Computer Vision (ECCV)*, 2014, pp.
    740--755. URL: https://arxiv.org/abs/1405.0312

13. R. Padilla, S. L. Netto, dan E. A. B. da Silva, "A Comparative
    Analysis of Object Detection Metrics with a Companion Open-Source
    Toolkit," *Electronics*, vol. 10, no. 3, art. 279, 2021. doi:
    10.3390/electronics10030279.

14. G. Bradski dan A. Kaehler, *Learning OpenCV: Computer Vision with
    the OpenCV Library*. Sebastopol, CA, USA: O'Reilly Media, 2008. URL:
    https://www.oreilly.com/library/view/learning-opencv/9780596516130/

15. R. C. Gonzalez dan R. E. Woods, *Digital Image Processing*, 4th ed.
    Pearson, 2018. URL:
    https://www.pearson.com/en-us/subject-catalog/p/Gonzalez-Digital-Image-Processing-4th-Edition/P200000003224

16. OpenCV, "Changing Colorspaces," OpenCV-Python Tutorials. URL:
    https://opencv24-python-tutorials.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_colorspaces/py_colorspaces.html

17. OpenCV, "Imgproc Documentation: `moments`, `morphologyEx`,
    `findContours`," OpenCV Documentation. URL:
    https://docs.opencv.org/master/javadoc/org/opencv/imgproc/Imgproc.html

18. J. Terven, D.-M. Córdova-Esparza, dan J.-A. Romero-González, "A
    Comprehensive Review of YOLO Architectures in Computer Vision: From
    YOLOv1 to YOLOv8 and Beyond," *Machine Learning and Knowledge
    Extraction*, vol. 5, no. 4, art. 83, 2023. doi: 10.3390/make5040083.

19. Ultralytics, "Explore Ultralytics YOLOv8," Ultralytics
    Documentation. URL: https://docs.ultralytics.com/models/yolov8

20. Ultralytics, "Model Training with Ultralytics YOLO," Ultralytics
    Documentation. URL: https://docs.ultralytics.com/modes/train

21. Ultralytics, "Data Augmentation using Ultralytics YOLO," Ultralytics
    Documentation. URL:
    https://docs.ultralytics.com/guides/yolo-data-augmentation

22. H. Liu, H. Shi, M. Li, dan M. Iseki, "Application of Color Featuring
    and Deep Learning in Maize Plant Detection," *Remote Sensing*, vol.
    12, no. 14, art. 2229, 2020. doi: 10.3390/rs12142229.

23. G. Moreira *et al.*, "Benchmark of Deep Learning and a Proposed HSV
    Colour Space Models for the Detection and Classification of
    Greenhouse Tomato," *Agronomy*, vol. 12, no. 2, art. 356, 2022. doi:
    10.3390/agronomy12020356.

24. InvenSense, "MPU-6000 and MPU-6050 Product Specification," 2011.
    URL:
    https://cdn.sparkfun.com/datasheets/Components/General%20IC/PS-MPU-6000A.pdf

25. J. S. Eger *et al.*, "A good-practices guideline for 6-DoF IMU-based
    dead-reckoning," 2022. URL:
    https://lcv.fee.unicamp.br/wp-content/images/BTSym-22-Brasil/papers/paper_057.pdf
    \[PERLU VERIFIKASI venue\].

26. "A Wheel-mounted MEMS IMU-based Dead Reckoning Method for Wheeled
    Mobile Robots," arXiv:1912.07805, 2019. URL:
    https://arxiv.org/abs/1912.07805

27. Texas Instruments, "DRV8833 Dual H-Bridge Motor Driver datasheet,"
    Rev. E. URL: https://www.ti.com/lit/gpn/DRV8833

28. ROHM Semiconductor, "Controlling DC Brush Motors with H-bridge
    Driver ICs," White Paper. URL:
    https://www.rohm.com/documents/11303/41217/100260.H-BRDG_WP_Jan09.pdf

29. T. Xu, W. Shen, X. Lin, dan Y. M. Xie, "Mechanical Properties of
    Additively Manufactured Thermoplastic Polyurethane (TPU) Material
    Affected by Various Processing Parameters," *Polymers*, vol. 12, no.
    12, art. 3010, 2020. doi: 10.3390/polym12123010.

30. Huntsman Polyurethanes, "A Guide to Thermoplastic Polyurethanes
    (TPU)," PDF Guide. URL:
    https://www.aerospheres.com/Assets/Documents/Huntsman%20PU_Elastomers_Guide_to_TPU.pdf

31. B. Pinedo, J. Rodríguez, dan A. T. Dibenedetto, "Frictional heating
    in TPU elastomers during dynamic sealing applications," *Tribology
    International*, 2018. URL:
    https://radar.brookes.ac.uk/radar/file/40de43dc-ccd9-4e9e-b5e5-c9ef79ff6c5a/1/1-s2.0-S0301679X18302603-main.pdf
    \[PERLU VERIFIKASI halaman lengkap\].

32. Axis Communications, "Latency in Live Network Video Surveillance,"
    White Paper. URL:
    https://whitepapers.axis.com/en-us/latency-in-live-network-video-surveillance

33. A. Kaknjo, M. Rao, E. Omerdic, L. Robinson, D. Toal, dan T. Newe,
    "Real-Time Video Latency Measurement between a Robot and Its Remote
    Control Station: Causes and Mitigation," *Wireless Communications
    and Mobile Computing*, vol. 2018, art. 8638019, 2018. doi:
    10.1155/2018/8638019.

34. Espressif Systems, "Camera Application - ESP-FAQ," Espressif
    Documentation. URL:
    https://docs.espressif.com/projects/esp-faq/en/latest/application-solution/camera-application.html

35. Espressif Systems, "HTTP Server - ESP-IDF Programming Guide,"
    Espressif Documentation. URL:
    https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/protocols/esp_http_server.html

36. Flask, "Welcome to Flask," Flask Documentation. URL:
    https://flask.palletsprojects.com/

37. M. Grinberg, "Flask-SocketIO," Documentation. URL:
    https://flask-socketio.readthedocs.io/

38. IETF, "RFC 6455: The WebSocket Protocol," 2011. URL:
    https://datatracker.ietf.org/doc/html/rfc6455

39. S. Hutchinson, G. D. Hager, dan P. I. Corke, "A Tutorial on Visual
    Servo Control," *IEEE Transactions on Robotics and Automation*, vol.
    12, no. 5, pp. 651--670, 1996. URL:
    https://ieeexplore.ieee.org/document/538972/

40. M. Ben-Ari, "Finite State Machines," dalam *Elements of Robotics*.
    Cham: Springer, 2017. doi: 10.1007/978-3-319-62533-1_4.

41. M.-C. Tsai dan A.-C. Huang, "Implementation of a real-time moving
    object tracking and visual servoing control system,"
    *Robotica*, 2003. doi: 10.1017/S0263574703005332.

42. S. Cheng, "Research on Ping-Pong Balls Collecting Robot Based on
    Embedded Vision Processing System," *Applied Mechanics and
    Materials*, vols. 511--512, pp. 838--841, 2014. doi:
    10.4028/www.scientific.net/AMM.511-512.838.

43. scikit-learn developers, "`confusion_matrix`," scikit-learn
    Documentation. URL:
    https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html

44. scikit-learn developers, "`precision_recall_fscore_support`,"
    scikit-learn Documentation. URL:
    https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html

45. scikit-learn developers, "`f1_score`," scikit-learn Documentation.
    URL:
    https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html

46. Ultralytics, "YOLO Performance Metrics," Ultralytics Documentation.
    URL: https://docs.ultralytics.com/guides/yolo-performance-metrics

------------------------------------------------------------------------

[\[1\]](https://www.researchgate.net/publication/321821433_System_design_for_autonomous_table_tennis_ball_collecting_robot)
https://www.researchgate.net/publication/321821433_System_design_for_autonomous_table_tennis_ball_collecting_robot

<https://www.researchgate.net/publication/321821433_System_design_for_autonomous_table_tennis_ball_collecting_robot>

[\[2\]](https://www.diva-portal.org/smash/get/diva2%3A957828/FULLTEXT01.pdf)
https://www.diva-portal.org/smash/get/diva2%3A957828/FULLTEXT01.pdf

<https://www.diva-portal.org/smash/get/diva2%3A957828/FULLTEXT01.pdf>

[\[3\]](https://www.scientific.net/AMM.511-512.838)
https://www.scientific.net/AMM.511-512.838

<https://www.scientific.net/AMM.511-512.838>

[\[4\]](https://arxiv.org/pdf/1902.07304)
[\[13\]](https://arxiv.org/pdf/1902.07304)
https://arxiv.org/pdf/1902.07304

<https://arxiv.org/pdf/1902.07304>

[\[5\]](https://ieeexplore.ieee.org/iel7/8425581/8452219/08452263.pdf)
https://ieeexplore.ieee.org/iel7/8425581/8452219/08452263.pdf

<https://ieeexplore.ieee.org/iel7/8425581/8452219/08452263.pdf>

[\[6\]](https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf)
[\[19\]](https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf)
[\[20\]](https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf)
https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf

<https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf>

[\[7\]](https://tohoku.elsevierpure.com/en/publications/design-and-system-integration-of-table-tennis-ball-collecting-rob/)
https://tohoku.elsevierpure.com/en/publications/design-and-system-integration-of-table-tennis-ball-collecting-rob/

<https://tohoku.elsevierpure.com/en/publications/design-and-system-integration-of-table-tennis-ball-collecting-rob/>

[\[8\]](https://www.mdpi.com/2073-4395/12/2/356)
[\[9\]](https://www.mdpi.com/2073-4395/12/2/356)
https://www.mdpi.com/2073-4395/12/2/356

<https://www.mdpi.com/2073-4395/12/2/356>

[\[10\]](https://opencv24-python-tutorials.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_colorspaces/py_colorspaces.html)
https://opencv24-python-tutorials.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_colorspaces/py_colorspaces.html

<https://opencv24-python-tutorials.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_colorspaces/py_colorspaces.html>

[\[11\]](https://docs.opencv.org/master/javadoc/org/opencv/imgproc/Imgproc.html)
[\[12\]](https://docs.opencv.org/master/javadoc/org/opencv/imgproc/Imgproc.html)
https://docs.opencv.org/master/javadoc/org/opencv/imgproc/Imgproc.html

<https://docs.opencv.org/master/javadoc/org/opencv/imgproc/Imgproc.html>

[\[14\]](https://docs.ultralytics.com/models/yolov8)
https://docs.ultralytics.com/models/yolov8

<https://docs.ultralytics.com/models/yolov8>

[\[15\]](https://docs.ultralytics.com/modes/train)
https://docs.ultralytics.com/modes/train

<https://docs.ultralytics.com/modes/train>

[\[16\]](https://www.mdpi.com/2079-9292/10/3/279)
https://www.mdpi.com/2079-9292/10/3/279

<https://www.mdpi.com/2079-9292/10/3/279>

[\[17\]](https://homepages.inf.ed.ac.uk/ckiw/postscript/ijcv_voc09.pdf)
https://homepages.inf.ed.ac.uk/ckiw/postscript/ijcv_voc09.pdf

<https://homepages.inf.ed.ac.uk/ckiw/postscript/ijcv_voc09.pdf>

[\[18\]](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html)
https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html

<https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html>

[\[21\]](https://www.ti.com/lit/gpn/DRV8833)
[\[26\]](https://www.ti.com/lit/gpn/DRV8833)
[\[27\]](https://www.ti.com/lit/gpn/DRV8833)
https://www.ti.com/lit/gpn/DRV8833

<https://www.ti.com/lit/gpn/DRV8833>

[\[22\]](https://cdn.sparkfun.com/datasheets/Components/General%20IC/PS-MPU-6000A.pdf)
https://cdn.sparkfun.com/datasheets/Components/General%20IC/PS-MPU-6000A.pdf

<https://cdn.sparkfun.com/datasheets/Components/General%20IC/PS-MPU-6000A.pdf>

[\[23\]](https://lcv.fee.unicamp.br/wp-content/images/BTSym-22-Brasil/papers/paper_057.pdf)
https://lcv.fee.unicamp.br/wp-content/images/BTSym-22-Brasil/papers/paper_057.pdf

<https://lcv.fee.unicamp.br/wp-content/images/BTSym-22-Brasil/papers/paper_057.pdf>

[\[24\]](https://worldscientificnews.com/wp-content/uploads/2025/01/WSN-199-2025-218-234.pdf)
https://worldscientificnews.com/wp-content/uploads/2025/01/WSN-199-2025-218-234.pdf

<https://worldscientificnews.com/wp-content/uploads/2025/01/WSN-199-2025-218-234.pdf>

[\[25\]](https://www.rohm.com/documents/11303/41217/100260.H-BRDG_WP_Jan09.pdf)
https://www.rohm.com/documents/11303/41217/100260.H-BRDG_WP_Jan09.pdf

<https://www.rohm.com/documents/11303/41217/100260.H-BRDG_WP_Jan09.pdf>

[\[28\]](https://www.princeton.edu/~mae412/TEXT/NTRAK2002/292-302.pdf)
https://www.princeton.edu/\~mae412/TEXT/NTRAK2002/292-302.pdf

<https://www.princeton.edu/~mae412/TEXT/NTRAK2002/292-302.pdf>

[\[29\]](https://www.mdpi.com/2073-4360/12/12/3010)
https://www.mdpi.com/2073-4360/12/12/3010

<https://www.mdpi.com/2073-4360/12/12/3010>

[\[30\]](https://link.springer.com/chapter/10.1007/978-3-319-62533-1_4)
https://link.springer.com/chapter/10.1007/978-3-319-62533-1_4

<https://link.springer.com/chapter/10.1007/978-3-319-62533-1_4>

[\[31\]](https://ieeexplore.ieee.org/document/538972/)
[\[32\]](https://ieeexplore.ieee.org/document/538972/)
https://ieeexplore.ieee.org/document/538972/

<https://ieeexplore.ieee.org/document/538972/>

[\[33\]](https://whitepapers.axis.com/en-us/latency-in-live-network-video-surveillance)
https://whitepapers.axis.com/en-us/latency-in-live-network-video-surveillance

<https://whitepapers.axis.com/en-us/latency-in-live-network-video-surveillance>

[\[34\]](https://pure.ul.ie/en/publications/real-time-video-latency-measurement-between-a-robot-and-its-remot/)
[\[39\]](https://pure.ul.ie/en/publications/real-time-video-latency-measurement-between-a-robot-and-its-remot/)
https://pure.ul.ie/en/publications/real-time-video-latency-measurement-between-a-robot-and-its-remot/

<https://pure.ul.ie/en/publications/real-time-video-latency-measurement-between-a-robot-and-its-remot/>

[\[35\]](https://flask.palletsprojects.com/)
https://flask.palletsprojects.com/

<https://flask.palletsprojects.com/>

[\[36\]](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/protocols/esp_http_server.html)
https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/protocols/esp_http_server.html

<https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/protocols/esp_http_server.html>

[\[37\]](https://ieeexplore.ieee.org/document/10417471/)
https://ieeexplore.ieee.org/document/10417471/

<https://ieeexplore.ieee.org/document/10417471/>

[\[38\]](https://www.mdpi.com/2076-3417/9/18/3746)
https://www.mdpi.com/2076-3417/9/18/3746

<https://www.mdpi.com/2076-3417/9/18/3746>

[\[40\]](https://www.mdpi.com/2072-4292/12/14/2229)
https://www.mdpi.com/2072-4292/12/14/2229

<https://www.mdpi.com/2072-4292/12/14/2229>
