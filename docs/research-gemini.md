# Analisis Literatur: Implementasi Computer Vision dan Kinematika Roda Mecanum pada Otomasi Robot Pengumpul Bola Ping-Pong

## BAB I: PENELITIAN TERDAHULU DAN TINGKAT KEMUTAKHIRAN TEKNOLOGI (*STATE OF THE ART*)

Analisis terhadap lanskap teknologi dan literatur terdahulu merupakan fondasi esensial untuk mengidentifikasi celah penelitian (*research gap*) serta memberikan justifikasi akademis terhadap pilihan arsitektur sistem terdistribusi yang dibangun pada robot pengumpul bola ping-pong otonom ini.

### 1.1 Sistem Robot Pengumpul Bola Olahraga dan Keterbatasannya

Kebutuhan terhadap otomasi dalam pemungutan bola olahraga telah mengilhami serangkaian purwarupa akademik dan produk komersial, baik untuk tenis lapangan maupun tenis meja. Solusi komersial konvensional seperti seri Pongbot berfokus pada pendekatan mekanis pasif berbentuk jaring teleskopis yang bertujuan untuk meringankan beban ergonomis manusia, namun sepenuhnya meniadakan sistem otonomi lokomotorik maupun kecerdasan buatan. Dalam ranah paten mekanis dan robotika akademik, sistem pemungut mulai mengadopsi mekanisme *propeller* putar berkecepatan tinggi atau silinder rotasi kontinu di bagian proksimal (*intake*) robot untuk menyapu bola ke dalam kompartemen penampungan.   

Evaluasi mendalam terhadap literatur *state-of-the-art* mengungkapkan keterbatasan mendasar yang bermuara pada dua faktor: kerentanan mekanis dan keandalan titik buta visual (*blind spot*). Dalam studi implementasi robot berbasis mekanisme pengumpul rotasi kontinu, kendala mekanis yang paling persisten adalah kebisingan akustik motor tingkat tinggi, inefisiensi daya yang mendegradasi siklus hidup baterai secara drastis, serta anomali dinamika pantul. Fenomena dinamika pantul ini terjadi ketika bola yang bersentuhan dengan aktuator *propeller* berbahan kaku (seperti PLA/ABS) yang terus berputar justru memantul kembali (*bounce off*) atau terlempar secara acak akibat momentum tumbukan yang melampaui koefisien restitusi yang diizinkan.   

Lebih jauh, robot otonom berbiaya rendah dengan pemasangan kamera statis yang bersudut pandang rendah umumnya menderita kendala persepsi proksimal. Bola ping-pong sering menghilang dari pandangan resolusi lensa (*Field of View*) ketika robot mendekat pada jarak krusial (kurang dari 10 cm), menyebabkan penghentian sekuensial yang memaksa sistem kehilangan target apabila mekanisme *sweeper* gagal mengeksekusi *intake* pada percobaan pertama. Keterbatasan ini memicu urgensi adopsi mekanisme sapuan terbatas (*servo sweep*) yang digerakkan oleh material elastomerik serta algoritma *state machine* yang mampu mempertahankan memori posisi target sesaat sebelum bola memasuki titik buta.   

| Judul Artikel / Sumber                                                | Penulis            | Tahun | Jurnal / Venue            |
| --------------------------------------------------------------------- | ------------------ | ----- | ------------------------- |
| Ping Pong Ball Collector Robot                                        | Instructables      | 2024  | Platform Instructables    |
| Robot for collecting table tennis balls                               | X. Jian et al.     | 2010  | US Patent US7674196B2     |
| Rancang Bangun Robot Pengumpul Bola Pingpong Menggunakan Sistem Vakum | H. Y. Putri et al. | 2025  | IJIRSE                    |
| Rancang Bangun Robot Pengumpul Bola Pingpong Otomatis                 | M. A. Abhinaya     | 2025  | Politeknik Negeri Jakarta |

### 1.2 Deteksi Bola Menggunakan Arsitektur *Deep Learning* pada Aplikasi Olahraga

Pergeseran paradigma dalam deteksi objek visual olahraga saat ini didominasi oleh arsitektur *Convolutional Neural Network* (CNN), khususnya varian *You Only Look Once* (YOLO). Sebagai detektor satu tahap, algoritma keluarga YOLO membuktikan superioritasnya dalam melacak target berdimensi spasial amat kecil yang bergerak secara dinamis, sembari mengeliminasi oklusi latar belakang yang kompleks. Evaluasi terhadap pengenalan bola tenis lapangan maupun tenis meja menunjukkan bahwa generasi terbaru seperti YOLOv8 sukses menaikkan performa pelacakan secara eksponensial. Pada eksperimen spesifik untuk robot sepak bola beroda (*wheeled soccer robot*), arsitektur YOLOv8 yang dijalankan pada koprosesor mutakhir mampu menghasilkan tingkat akurasi observasi hingga 100% dan nilai *recall* 94%, memperlihatkan korelasi luar biasa untuk menyaring artefak visual pada lapangan olahraga.   

Meskipun metrik presisi CNN absolut melampaui algoritma pengolahan citra heuristik klasik, adaptasi komputasi *real-time* model YOLO secara tertanam (*embedded*) menimbulkan hambatan teknis yang mematikan bagi mikrokontroler tingkat konsumen. Pengeksekusian inferensi *deep learning* menuntut ketersediaan memori tensor dan unit pemrosesan grafis (GPU) paralel yang tidak tersedia pada perangkat seperti ESP32-CAM atau bahkan laptop sentral tanpa GPU diskrit. Memaksakan model berbobot jutaan parameter pada sistem terdistribusi nirkabel latensi-sedang hanya akan menciptakan *bottleneck* pengolahan antarmuka, menekan *Frame Per Second* (FPS) ke tingkat yang mengancam stabilitas sistem kendali linier. Oleh karena itu, pendekatan yang paling logis adalah memanfaatkan metode *deep learning* murni sebagai pembanding eksperimental di luar jaringan (*offline baseline comparator*). Dengan melatih model YOLOv8 pada *dataset* bola ping-pong lokal dan mengevaluasi presisi teoretisnya, peneliti dapat menyajikan argumen komparatif yang menjustifikasi kompromi latensi dan akurasi terhadap metode deterministik konvensional.   

| Judul Artikel / Sumber                                                          | Penulis             | Tahun | Jurnal / Venue                                    |
| ------------------------------------------------------------------------------- | ------------------- | ----- | ------------------------------------------------- |
| Tennis Ball Detection using YOLOv8 for Mobile Robot Ball Collection             | Y. Zhao et al.      | 2024  | Conference Paper / ResearchGate                   |
| Ball Detection in Wheeled Soccer Robot Using the YOLOv8 Model                   | A. T. A. HAT et al. | 2025  | Int. J. of Electrical and Intelligent Engineering |
| Ball-type Small Objection Algorithm based on YOLOv8                             | Luo, Quan, & Liu    | 2024  | Conference Documentation                          |
| Real-time Detection and Trajectory Tracking of Balls in Table Tennis using YOLO | W. Yan              | 2025  | IGI Book Chapter                                  |

### 1.3 Navigasi dan Kinematika Robot Mobil Berbasis Roda Mecanum

Robot mobil omnidireksional dengan roda Mecanum menghadirkan terobosan mobilitas tanpa mengharuskan modifikasi sudut gandar (*steering axle*). Dengan menempatkan empat unit roda (4WD) yang memiliki jajaran rol diagonal bersudut 45∘ di sepanjang tepinya, sistem mentransformasi perputaran motor aktuator yang sepenuhnya maju-mundur menjadi gaya translasi bebas berdimensi penuh. Dalam aplikasi pengumpulan objek kecil yang menuntut orientasi penyelarasan (*alignment*) berakurasi tinggi, adopsi sasis Mecanum memfasilitasi translasi lateral proksimal (*strafing*) secara independen dari orientasi sudut *yaw*.   

Riset kontemporer mengenai implementasi matriks kinematika invers pada unit mikrokontroler telah memperlihatkan efisiensi dalam menerjemahkan vektor kecepatan spasial linier dan angular dari komando pusat menuju modul penyalur tegangan PWM pada *motor driver*. Walaupun menawarkan kebebasan manuver yang superior untuk pendekatan *visual servoing*, literatur juga membedah defisiensi inherent arsitektur Mecanum. Roda ini sangat rentan terhadap ketidaksempurnaan slip traksi pada permukaan berfriksi rendah (seperti interaksi rol plastik terhadap material lantai lapangan olahraga) dan defisiensi torsi linear apabila keluaran motor tidak terkalibrasi seragam secara komutatif. Konsekuensi logis dari fenomena slip ini adalah ketidakandalan navigasi berbasis *odometry* murni (*dead-reckoning*), yang secara tak langsung mewajibkan robot bergantung penuh pada koreksi berkelanjutan dari sensor inersial (IMU) serta umpan balik penglihatan (*visual loop closure*) untuk mempertahankan garis lintasan lurus.   

| Judul Artikel / Sumber                                                 | Penulis             | Tahun | Jurnal / Venue                        |
| ---------------------------------------------------------------------- | ------------------- | ----- | ------------------------------------- |
| Kinematic Model of a Four Mecanum Wheeled Mobile Robot                 | S. N. Yilmaz et al. | 2015  | Int. Journal of Computer Applications |
| Kinematics of Mobile Robot (Inverse Kinematics of Four Mecanum Wheels) | S. Shimraz          | 2024  | GitHub Repository                     |
| Kinematics Modeling and Simulation of Holonomic Wheeled Mobile Robot   | M. N. Al-Nima       | 2024  | Journal of Engineering                |
| Perancangan Wheel Mobile Robot Sebagai Modul Praktikum Mikrokontroler  | M. Iqbal et al.     | 2014  | Simetris: Jurnal Teknik Mesin         |

### 1.4 Studi Komparatif: Segmentasi Warna Klasik (HSV) vs Deteksi Berbasis CNN

Sinergi dan pertukaran kerugian (*trade-off*) operasional antara segmentasi piksel deterministik dengan segmentasi saraf kognitif membelah paradigma desain sistem persepsi robotika otonom. Metode deteksi berbasis ruang warna *Hue, Saturation, Value* (HSV) menawarkan beban instruksi CPU memori yang sangat ringan, mengizinkan algoritma untuk melintasi frekuensi analisis tinggi (*high frame rates*) secara mulus pada perangkat keras stasiun kontrol sentral konvensional. Efisiensi ini krusial saat aliran transmisi video diangkut melalui arsitektur nirkabel Wi-Fi (*Motion JPEG over HTTP*) yang secara inheren menginduksi latensi paket. Kelemahan klasik segmentasi warna, yaitu kerapuhan akurasi saat iluminasi foton lingkungan meredup atau memantul (*specular reflection*), dapat dimitigasi melalui penyediaan antarmuka kalibrasi ambang batas (*runtime slider*) komprehensif yang dioperasikan sebelum fase otonomi.   

Sebaliknya, analisis studi komparatif—termasuk penelitian paralel pada pengukuran densitas lalu lintas dan penyortiran buah agrikultur—menyimpulkan bahwa meskipun model sekelas YOLOv8 sangat resisten terhadap perubahan cahaya sporadis dan menghasilkan pembungkus *bounding box* yang tak tertandingi di tengah lingkungan padat (*cluttered*), biaya inferensi temporalnya memicu *delay* aktuasi motorik yang membahayakan robot bermanuver cepat. Pada sistem otomasi yang mengandalkan algoritma penyetir proporsional berulang (*closed-loop P-Controller*), kelambatan akuisisi data sekecil apapun akan diterjemahkan sebagai perpindahan fase (*phase lag*) ke dalam dinamika aktuator, yang memicu osilasi tak teredam (*hunting behavior*). Oleh karena itu, pengangkatan segmentasi HSV sebagai detektor utama operasi *real-time* sembari mempekerjakan YOLOv8 secara *offline* untuk mendapatkan data metrik presisi analitis merupakan metodologi valid yang menyeimbangkan tuntutan realitas fisis dan pembuktian teoretis akademis.   

| Judul Artikel / Sumber                                                         | Penulis                   | Tahun | Jurnal / Venue                                |
| ------------------------------------------------------------------------------ | ------------------------- | ----- | --------------------------------------------- |
| Comparative Analysis of YOLOv8 and HSV Methods for Traffic Density Measurement | I. G. P. S. Wijaya et al. | 2025  | Lontar Komputer: Jurnal Ilmiah TI             |
| Penerapan Metode Segmentasi Warna HSV untuk Deteksi Objek Berbasis Warna       | R. Rizka et al.           | 2025  | Router: Jurnal Teknik Informatika Dan Terapan |
| Deteksi Warna Dasar Menggunakan Metode Thresholding HSV dengan OpenCV          | Z. Akbar et al.           | 2025  | Neptunus: Jurnal Ilmu Komputer                |
| Klasifikasi Kematangan Menggunakan YOLOv8 dan Konversi RGB ke HSV              | S. H. Seran et al.        | 2024  | Proceeding UNP Kediri                         |

## BAB II: LANDASAN TEORI

Bab ini merumuskan derivasi analitis, model fisis matematis, serta prinsip operasional rekayasa yang membentuk setiap komponen di dalam arsitektur perangkat lunak dan perangkat keras robot pengumpul bola ping-pong terdistribusi.

### 2.1 Computer Vision dan Ruang Warna HSV

*Computer Vision* (Visi Komputer) mengekstraksi parameter numerik spasial dari lingkungan berdimensi melalui matrikulasi piksel citra digital. Dalam hierarki pemrosesan *real-time* berbasis beban stasiun darat (*ground station*), algoritma segmentasi diskrit pada ruang warna *Hue, Saturation, Value* (HSV) difungsikan sebagai ekstraktor informasi semantik utama. Transformasi non-linear dari format matriks aditif merah-hijau-biru (RGB atau BGR pada pustaka OpenCV) ke format HSV merupakan mekanisme untuk memisahkan properti warna intinsik dari gangguan iluminasi foton. Dimensi *Hue* (H) melingkupi derajat kemurnian kromatografi spektral, *Saturation* (S) mendefinisikan dominasi kejenuhan pigmen terhadap cahaya putih, dan *Value* (V) mengkuantifikasi kecerahan absolut. Pemisahan ini memampukan fungsionalitas `cv2.inRange()` di dalam sintaks OpenCV mengeksekusi operasi logika *thresholding* (ambang batas) murni terhadap spektrum bola ping-pong (oranye atau putih solid) yang jauh lebih tahan banting terhadap bayangan proksimal dibandingkan segmentasi RGB konvensional.   

Citra hasil seleksi direpresentasikan sebagai himpunan matriks biner (*masking*). Mengingat transmisi *streaming* MJPEG secara nirkabel rentan mendistribusikan *noise* digital (berupa percikan piksel liar dan celah oklusi), operasi morfologi struktural matematika harus diterapkan untuk merekonstruksi integritas piksel. Tahap erosi (*erosion*) diterapkan untuk menggerus nilai tepi objek, efektif menghilangkan bintik putih artefak terisolasi di latar belakang. Proses dilasi (*dilation*) kemudian menyusul untuk memulihkan dan menggembungkan kembali kelengkungan tepi piksel target yang mengalami konstriksi, menutup lubang internal pada area bola yang terdistorsi oleh pantulan cahaya spesifik (*specular reflection*).   

Setelah pembersihan morfologis, identifikasi batas topologis objek dieksekusi melalui algoritma penelusuran batas kontur (`cv2.findContours`). Dengan memfilter susunan kontur berdasar area geometris maksimal, area biner bola terbesar diisolasi. Pusat gravitas spasial pada kontur tersebut dilacak menggunakan teorema komputasi Momen Citra (*Image Moments*). Momen spasial orde dasar Mpq​ dari fungsi sebaran intensitas piksel I(x,y) dirumuskan melalui:

Mpq​=x∑​y∑​xpyqI(x,y)

Koordinat sentroid spasial horizontal (Cx​) dan vertikal (Cy​) diderivasi dari perbandingan bobot momen orde pertama terhadap massa orde nol:

Cx​=M00​M10​​,Cy​=M00​M01​​

Kalkulasi sentroid sentral (Cx​,Cy​) menjadi dasar navigasi otonom absolut. Selisih skalar antara posisi aktual Cx​ dengan titik pusat resolusi absis dari matriks resolusi kamera (misal 320 untuk *frame* selebar 640 piksel) menghasilkan nilai galat pergeseran (*offset error*). Sinyal *offset* tersebut direpresentasikan secara matematis dan diekstraksi ke sistem *controller* proporsional untuk memantik respon reaktif berupa modifikasi matriks kecepatan rotasi sasis robot.   

| Judul Artikel / Sumber                                                   | Penulis         | Tahun | Jurnal / Venue                    |
| ------------------------------------------------------------------------ | --------------- | ----- | --------------------------------- |
| Visual Servoing using OpenCV (Centroid tracking & P-Controller)          | A. Bhowmik      | 2024  | GitHub Repository                 |
| Deteksi Warna Dasar Menggunakan Metode Thresholding HSV dengan OpenCV    | Z. Akbar et al. | 2025  | Neptunus: Jurnal Ilmu Komputer    |
| Penerapan Metode Segmentasi Warna HSV untuk Deteksi Objek Berbasis Warna | R. Rizka et al. | 2025  | Router: Jurnal Teknik Informatika |

### 2.2 Object Detection Berbasis Deep Learning (Arsitektur YOLOv8)

Di ranah arsitektur kecerdasan buatan, keluarga *You Only Look Once* (YOLO) memprakarsai metodologi konvolusional satu-tahap (*single-stage detector*), meruntuhkan supremasi pendeteksi usulan-wilayah (*region-proposal*) berlatensi tinggi. YOLO secara unik meregresikan batasan ruang kordinat (*bounding box*) bersisian dengan probabilitas klasifikasi semantik melalui jaringan evaluasi tunggal yang sangat efisien. Edisi mutakhir dari paradigma ini, YOLOv8, menyertakan rekayasa struktural yang mempertajam ekstraksi fitur berlapis, meningkatkan presisi identifikasi terhadap target mungil seperti bola tenis yang diproyeksikan dari sudut kamera *ground-level*.   

Struktur fundamental YOLOv8 disegmentasikan ke dalam trilogi saraf: *Backbone*, *Neck*, dan *Head*. *Backbone* ditugaskan merangkum pola topologis melalui penerapan blok *Cross Stage Partial Network* yang berevolusi menjadi modul komputasi C2f (CSPLayer dengan 2 konvolusi). Modul C2f menstimulasi aliran perambatan balik gradien numerik yang padat sembari menekan parameter inersia bobot jaringan. Subsistem *Neck* mensintesis fitur spasial lintas resolusi memanfaatkan skema *Path Aggregation Network* (PANet) ganda, menjamin bahwa representasi fitur mikroskopis dari bola berdiameter 40 mm pada proksimitas jauh tidak menguap saat resolusi grafis dikonvolusi mengecil. Integrasi radikal terbesar diinisiasi pada rancangan modul *Head* yang diimplementasikan sebagai *Anchor-Free* (bebas parameter jangkar referensi tetap) dan *Decoupled* (persimpangan regresi koordinat dan kelas yang dipisahkan secara topologis). Mekanisme bebas-jangkar ini meniadakan keharusan bagi sistem untuk menebak deformasi aspek rasio kotak pembatas, secara dinamis mengakomodasi variansi visual bola yang berubah tajam mengikuti momentum pantulan kinetik di arena.   

Selama fase proses pelatihan (*training process*), kekuatan model dikokohkan dengan manipulasi augmentasi citra. Metodologi augmentasi generatif menyuntikkan rotasi geometris sintetis, pemotongan, serta osilasi kecerahan/saturasi secara stokastik ke dalam *dataset* bola, memperkuat resistensi variansi model. Untuk skenario otomasi robot ini, YOLOv8 dijalankan sepenuhnya dalam kapasitas analitis *offline* sekunder, difungsikan guna menetapkan tolok ukur teoretis maksimum perihal seberapa presisi identifikasi bola dapat dicapai jika komputasi perangkat lunak didukung oleh tenaga silikon yang mumpuni tanpa konstrain *bandwidth*.

| Judul Artikel / Sumber                                                      | Penulis            | Tahun | Jurnal / Venue                        |
| --------------------------------------------------------------------------- | ------------------ | ----- | ------------------------------------- |
| Table Tennis Ball Detection using YOLO models                               | W. Yan             | 2025  | IGI Book Chapter                      |
| Skripsi: Arsitektur YOLOv8 (Backbone, Neck, Head)                           | K. Sari            | 2024  | Digilib UNILA                         |
| Development of Ball Detection System with YOLOv3 in a Humanoid Soccer Robot | M. L. Hakim et al. | 2021  | Journal of Physics: Conference Series |
| XNOR-YOLO: The High Precision of The Ball and Goal Detecting                | S. Susanto et al.  | 2020  | ICAE Proceedings                      |

### 2.3 Metrik Evaluasi Deteksi Visi

Pembandingan kompetensi detektor deterministik HSV melawan probabilitas spasial dari jaringan konvolusional menuntut landasan kuantifikasi matematis universal. Dalam ranah evaluasi deteksi visi, akurasi lokalisasi dinilai melalui populasi elemen dalam *Confusion Matrix*. Instrumen ini mengkategorikan inferensi prediksi menjadi *True Positives* (TP) apabila bola secara tepat dikurung algoritma, *False Positives* (FP) apabila artefak latar belakang dideklarasikan sebagai bola secara keliru, dan *False Negatives* (FN) apabila bola yang eksis secara material gagal dipindai.   

Dua pilar rasio turunan dari matriks tersebut mengkarakterisasi ketajaman algoritma. *Precision* mengukur ketepatan kognitif sistem yang mengisyaratkan bahwa setiap prediksi positif memuat kemungkinan sangat besar untuk tepat sasaran:

Precision=TP+FPTP​

Di sisi berseberangan, probabilitas sensitivitas menyeluruh (*Recall*) merepresentasikan kemampuan algoritma menyisir setiap artefak target valid di medan lensa:

Recall=TP+FNTP​

*F1-Score* kemudian menghimpun rata-rata harmonik dari *Precision* dan *Recall*, menciptakan skor tunggal penyeimbang untuk detektor yang memiliki dispersi kesalahan asimetris. Untuk mengkalibrasi toleransi kedekatan geometri *bounding box* hasil inferensi dengan koordinat kebenaran lapangan aktual (*ground truth*), rasio irisan terhadap gabungan spasial didefinisikan sebagai *Intersection over Union* (IoU).

Integrasi *Precision-Recall* pada spektrum persentil keyakinan menghasilkan kalkulasi agregasi *Mean Average Precision* (mAP), dengan mAP@0.5 merujuk pada standar ambang IoU lebih dari 50%. Selain metrik ketelitian statis, latensi perangkat lunak diestimasikan melalui perhitungan *Frames Per Second* (FPS). Variabel FPS sangat mendikte stabilitas fisis kontrol robotika. Berkurangnya laju sirkulasi bingkai akibat komputasi berat akan menginjeksikan penundaan fase asimtotik ke dalam kontrol kemudi, membuktikan mengapa penggunaan HSV untuk *deployment real-time* jauh melampaui kelayakan fungsional dibandingkan CNN berat di subsistem *controller* utama.   

| Judul Artikel / Sumber                                             | Penulis                   | Tahun | Jurnal / Venue                  |
| ------------------------------------------------------------------ | ------------------------- | ----- | ------------------------------- |
| Comparison between YOLO and Traditional Evaluation Metrics         | Vet. Sci. Frontiers       | 2026  | Frontiers in Veterinary Science |
| Ball Detection in Sports: A Review                                 | C. Moreira et al.         | 2024  | Sports Analytics Systems        |
| Comparative Analysis of YOLOv8 and HSV Methods for Traffic Density | I. G. P. S. Wijaya et al. | 2025  | Lontar Komputer                 |

### 2.4 Kinematika Invers Roda Mecanum (4WD)

Kendaraan robotik *holonomic* berpelengkapan empat unit roda Mecanum (4WD) mendobrak limitasi orientasi linier konvensional dengan memanipulasi vektor aksial torsi pada platform dua dimensi (memungkinkan rotasi, pergeseran ortogonal, serta pergerakan translasi bujur secara bersamaan tanpa menggeser poros sasis). Kemampuan manuver holonomik ini dimanifestasikan secara arsitektural oleh sederet rol pasif yang terikat mengelilingi radius roda penggerak dengan sudut defleksi statis sebesar γ=45∘ dari sumbu putaran. Dalam operasi pelacakan bola target yang fluktuatif, rotasi diferensial setiap ban tidak hanya mendorong propulsi mekanis longitudinal, tetapi merangsang reaksi komponen gaya melintang yang menyebabkan sasis menyamping mendatar (*strafe*) secara halus.   

Rasionalisasi komando motor berbasis matriks dipandu oleh pemetaan kinematika invers. Transformasi matematis ini mendikte kecepatan perputaran radial diskrit masing-masing aktuator (ωi​) berdasarkan kehendak vektor gerakan pusat massa sasis robot: kecepatan longitudinal lurus (vx​), kecepatan translasi menyamping transversa (vy​), dan putaran kecepatan sudut sasis *yaw* (ωz​). Hukum resolusi kinematika matriks ini disuntikkan secara komputasional ke dalam logika memori mikrokontroler Arduino Uno:

![](data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="0.667em" height="4.800em" viewBox="0 0 667 4800"><path d="M403 1759 V84 H666 V0 H319 V1759 v1200 v1759 h347 v-84%0AH403z M403 1759 V0 H319 V1759 v1200 v1759 h84z"></path></svg>)​ωFL​ωFR​ωRL​ωRR​​![](data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="0.667em" height="4.800em" viewBox="0 0 667 4800"><path d="M347 1759 V0 H0 V84 H263 V1759 v1200 v1759 H0 v84 H347z%0AM347 1759 V0 H263 V1759 v1200 v1759 h84z"></path></svg>)​=r1​![](data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="0.667em" height="4.800em" viewBox="0 0 667 4800"><path d="M403 1759 V84 H666 V0 H319 V1759 v1200 v1759 h347 v-84%0AH403z M403 1759 V0 H319 V1759 v1200 v1759 h84z"></path></svg>)​1111​−111−1​−(lx​+ly​)+(lx​+ly​)−(lx​+ly​)+(lx​+ly​)​![](data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="0.667em" height="4.800em" viewBox="0 0 667 4800"><path d="M347 1759 V0 H0 V84 H263 V1759 v1200 v1759 H0 v84 H347z%0AM347 1759 V0 H263 V1759 v1200 v1759 h84z"></path></svg>)​![](data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="0.667em" height="3.600em" viewBox="0 0 667 3600"><path d="M403 1759 V84 H666 V0 H319 V1759 v0 v1759 h347 v-84%0AH403z M403 1759 V0 H319 V1759 v0 v1759 h84z"></path></svg>)​vx​vy​ωz​​![](data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="0.667em" height="3.600em" viewBox="0 0 667 3600"><path d="M347 1759 V0 H0 V84 H263 V1759 v0 v1759 H0 v84 H347z%0AM347 1759 V0 H263 V1759 v0 v1759 h84z"></path></svg>)​

Variabel ωFL​,ωFR​,ωRL​,ωRR​ berturut-turut merupakan velositas radial aktuator Depan-Kiri (*Front-Left*), Depan-Kanan, Belakang-Kiri, dan Belakang-Kanan. Nilai r melambangkan jari-jari pelek efektif struktur roda, sementara lx​ dan ly​ mengkuantifikasi separuh interval dimensi gandar as roda proksimal longitudinal dan transversa dari proyeksi sumbu tengah silang pusat sasis.   

Setelah persamaan trigonometri mengekstraksi nilai komando kecepatan rotasi teoretis (dalam radian per detik), mikrokontroler selanjutnya menerjemahkan rentang kecepatan ini melalui fungsi penalaan linier menuju lebar pulsa regulasi sinyal *Pulse Width Modulation* (PWM). Representasi 8-bit resolusi mikrokontroler (dari nilai skalar 0 hingga 255) dialokasikan merata merepresentasikan ekuivalensi tenaga RPM (*Revolutions Per Minute*) rotasi pada tegangan penuh motor penggerak, menciptakan korelasi kausal di mana modifikasi rasio tugas (*duty-cycle*) akan membangkitkan proporsi traksi spesifik di atas sirkuit pengemudi roda.   

| Judul Artikel / Sumber                                                 | Penulis       | Tahun | Jurnal / Venue         |
| ---------------------------------------------------------------------- | ------------- | ----- | ---------------------- |
| Kinematics of Mobile Robot (Inverse Kinematics of Four Mecanum Wheels) | S. Shimraz    | 2024  | GitHub Repository      |
| Geometry of Mecanum Wheels                                             | G. Frerrer    | 2024  | TU Graz Publications   |
| Tutorials: Mechanical Mecanum Wheels Kinematics                        | ECAM Eurobot  | 2024  | GitHub.io              |
| Kinematics Modeling and Simulation of Holonomic Wheeled Mobile Robot   | M. N. Al-Nima | 2024  | Journal of Engineering |

### 2.5 IMU MPU6050, Giroskop, dan Estimasi Heading

Pemantapan kesadaran orientasi azimut (*heading*) kompas fiktif adalah pra-syarat fundamental untuk mengamankan stabilitas *Visual Servoing* agar lintasan vektor translasi sasis roda Mecanum tidak terdeviasi akibat friksi tak terkendali maupun benturan (*skewing*). Persepsi navigasi inersial direalisasikan dengan pemasangan komponen *Inertial Measurement Unit* (IMU) jenis MPU6050. Modul ini menyematkan sistem mekanis terpadu akselerometer 3-sumbu dan *micro-electromechanical systems* (MEMS) giroskop 3-sumbu berskala milimetris, memancarkan transmisi paket telemetri data mentah beresolusi komprehensif 16-bit melewati jaringan sinkron ganda *Inter-Integrated Circuit* (I²C).   

Sensitivitas giroskop mendayagunakan manipulasi resonansi akibat efek gaya fiktif Coriolis untuk merumuskan kalkulasi fluktuasi sudut laju kecepatan (ωgyro​ dalam satuan derajat per detik). Pada skenario pembentukan orientasi gerak rotasional bidang 2D (*Yaw*), mikrokontroler mengeksploitasi teorema komputasi integral diferensial dasar (*dead-reckoning*) dengan memakumulasi secara diskrit area luasan di bawah grafik kecepatan rotasi sumbu-Z (ωz​) menyusuri perambatan interupsi waktu (Δt):

θyaw​(t)=θyaw​(t−1)+(ωz​(t)−ωbias​)⋅Δt

Karena perangkat IMU komersial tingkat-konsumen dibayangi derau kelistrikan suhu konstan serta inakurasi kalibrasi fotolitografi fabrikasi silikon mekanis, akuisisi sinyal giroskop dijangkiti anomali *steady-state error* statis, di mana pembacaan tetap merekam impuls kecepatan pseudo meski benda dalam diam mutlak. Kekeliruan ini membengkak seiring iterasi penambahan delta komputasi waktu yang disebut akumulasi *gyroscopic drift*.   

Sebagai bentuk mitigasi piranti lunak primer (di mana arsitektur fusi *Complementary filter* kompleks menggunakan magnetometer kompas murni secara sadar ditiadakan), skenario peluncuran mesin robot memandatkan fase stasioner. Selama inisiasi milidetik *boot-up*, algoritma menghisap dan mendata ratusan rerata sampel hening untuk mengkuantifikasi parameter nilai residu *bias* konstan (ωbias​). Pada setiap siklus perulangan aktif gerak rotasi berikutnya, deviasi *bias* ini dikurangkan dari sinyal mentah giroskop demi memperlambat regresi *drift* secara deterministik. Ketidakhadiran *filter* fusi yang sempurna ini memicu konsekuensi arsitektural spesifik pada mesin keadaaan robot (*Finite State Machine*), di mana mode pelacakan visual mutlak mengambil alih peran *heading* inersial saat bola tertangkap pandangan, menganulir kompas giroskopik seutuhnya sebagai kompensasi dari degradasi sudut *dead-reckoning*.   

| Judul Artikel / Sumber                                                 | Penulis              | Tahun | Jurnal / Venue |
| ---------------------------------------------------------------------- | -------------------- | ----- | -------------- |
| Yaw stabilization and heading-hold using MPU6050 and TB6612FNG         | H. Pimpalkar         | 2026  | IJRSI          |
| Peningkatan Akurasi Sensor GY-521 MPU-6050 dengan Koreksi Faktor Drift | Mangkusasmito et al. | 2020  | Jurnal Riset   |
| MPU6050 Calibration and Angles (Integration of angular velocity)       | M. J. White          | 2024  | Technical Blog |
| Implementasi ESP32 dan MPU6050 pada Robot Keseimbangan                 | Dhea dkk.            | 2024  | JITET          |

### 2.6 Aktuator Penggerak Motor DC dan Driver H-Bridge (DRV8833)

Dinamika lokomotorik dari propulsi platform *holonomic robot* mengonsumsi energi putaran kinetik bersumber dari empat unit motor sikat arus searah bertorsi tinggi (*Brushed DC Motor* magnet permanen) dengan reduksi kotak persneling bawaan untuk mendongkrak torsi asimut pada gulungan pelek roda Mecanum. Mikrokontroler, dengan ambang pasokan arus yang rentan (di bawah 40 miliampere), tidak dapat secara langsung menyuplai tenaga. Oleh sebab itu, transistor saklar solid-state daya menangani beban arus menggunakan topologi kontrol modul IC *Dual H-Bridge Motor Driver* DRV8833 buatan Texas Instruments.   

Struktur modul DRV8833 menandai diferensiasi rekayasa fisis masif ketimbang modul monolitik usang warisan seri bipolar L298N. Modul DRV8833 dikonstruksi secara esensial mempekerjakan tatanan sirkuit saklar *Metal Oxide Semiconductor Field Effect Transistors* tipe kanal-N (N-channel MOSFETs). Arsitektur silikon ini membukukan indeks hambat-hidup internal (*ON-Resistance* atau RDS(on)​) di kisaran fraksi minimal absolut, yakni 360 m$\Omega$. Efisiensi radikal resistensi komutasi semikonduktor ini membungkam kebocoran kehilangan drop daya termal tegangan hingga tersisa ekuivalen ∼0.3V di bawah batas beban puncak. Dampak ekologis kelistrikan dari fitur ini menggaransi mayoritas arus disipasi catu sel lipo dihantarkan nyaris tanpa hambatan ke induktor jangkar motor, mempertahankan durabilitas manuver mekanik optimal seraya mengeliminasi kebutuhan pendingin radiator sirip logam aluminium berat yang menjangkit L298N.   

Setiap cip sirkuit H-bridge DRV8833 mampu mencerna rentang tegangan kustom teramat luas (dari batas baterai 2,7V hingga 10,8V) sembari melepaskan arus RMS toleransi kontinu 1,5 Ampere tiap salurannya. Parameter gerak direkayasa menggunakan kompensasi sekuens asimetris terminal logika antarmuka `IN1/IN2`. Modifikasi asimetris status kutub TINGGI/RENDAH mendikte inversi traksi kumparan bolak-balik motor (*forward/reverse direction*) seketika. Manipulasi rentang velositas kecepatan sirkulasi spindel bergantung terhadap sinyal interupsi pulsa osilasi tegangan periodik *Pulse Width Modulation* (PWM). Kecepatan translasi linier aktual adalah parameter turunan sebanding terhadap persentase rata-rata perbandingan jendela siklus waktu menyala ketimbang siklus mati pulsa kontrol digital (*duty cycle*). Perlindungan integral (*overcurrent protection* / OCP, ambang suhu krisis penguncian daya TSD, batas sirkuit pendek protektif) tertanam pada *wafers* silikon mengamankan operabilitas H-bridge selama transisi tegangan kejut jika terjadi stall friksi mekanik dari pergesekan as roda robot.   

| Judul Artikel / Sumber                                        | Penulis               | Tahun | Jurnal / Venue    |
| ------------------------------------------------------------- | --------------------- | ----- | ----------------- |
| DRV8833 Dual-H-Bridge Current-Control Motor Driver Data Sheet | Texas Instruments     | 2024  | TI Documentation  |
| DRV8833 Motor Driver Dual DC Motor Control                    | Zbotic                | 2024  | Hardware Tutorial |
| Controlling DC Motors with DRV8833 Motor Driver and Arduino   | Last Minute Engineers | 2024  | Technical Blog    |
| Guide to Choosing the Best DC Motor Drivers for Arduino       | Scribd (Community)    | 2024  | Scribd Repository |

### 2.7 Komunikasi Nirkabel dan Streaming MJPEG (ESP32-CAM)

Kinerja sistem komputasi visual terdistribusi mempersyaratkan pembentukan terowongan konektivitas antarmuka *wireless* nirkabel inter-lokal berkesinambungan, yang sepenuhnya bergantung kepada cip SoC ESP32-CAM. Mikrokontroler arsitektur inti ganda asimetris ini melengkapi dirinya dengan transmiter radio terpadu Wi-Fi (802.11 b/g/n) seraya merekatkan antarmuka modul kamera standar Omnivision OV2640 berfiksasi absolut (*fixed mount* tanpa penyemat aktuator kemudi arah *pan-tilt* vertikal maupun horisontal mekanik). Transistor peranti Wi-Fi ESP32 mendedikasikan mode stasiun (WLAN Station) untuk memancarkan komputasi peladen web HTTP (*web server*) yang terbagi dua titik: *endpoint server Motion JPEG* (MJPEG) pada rute Port 81 dan *endpoint* komunikasi perintah kemudi di Port 80.   

Protokol kompresi algoritma MJPEG merumuskan aliran visual bukan sebagai kontinum enkoder *video codec* berat (seperti H.264), melainkan mengirim ulang antrean seri deretan matrikulasi gambar ekstensi JPEG tunggal kompresi mandiri ke rute jaringan web [*multipart/x-mixed-replace HTTP response headers*]. Menyingkirkan *User Datagram Protocol* (UDP) berlatensi ultrarendah atau *Real-Time Streaming Protocol* (RTSP)—yang menghendaki instalasi dekoder rumit di antarmuka sistem darat—transmisi MJPEG over HTTP menyuguhkan implementasi arsitektur peramban murni (*browser-native stream*). Implikasi fatalistik dari arsitektur *Transmission Control Protocol* (TCP/HTTP) ini mendikte kemunculan waktu penundaan transit jaringan total (*end-to-end network latency delay*) bernilai di rentang deviasi atenuasi ekstrem sekitar 142 ms hingga 251 ms, dengan rata-rata pelambatan berfluktuasi searah interferensi kualitas daya hambat kekuatan sinyal lokal.   

Transmisi pemanggilan instruksi gerak lokomotor maupun telemetri manuver FSM dieksekusi mengintervensi rute sirkuit spesifik mempergunakan fungsi *RESTful HTTP GET requests* dari laptop pangkalan ke alamat sasaran (e.g., `http://192.168.x.x/action?go=left&speed=150`). Meskipun protokol GET dipandang menumpuk kelebihan kapasitas komunikasi paket data kotor akibat sintaks *stateless server*, ia menghadirkan keselarasan *handshake* garansi penerimaan sebelum didaur ulang mikrokontroler internal ESP32 menjauhi format jaringan dan diterjemahkan membelah saluran kabel biner serial fisik asinkron *Universal Asynchronous Receiver-Transmitter* (UART) ke Arduino pengendali komputasi kinematika PWM roda. Hubungan saling memengaruhi antara latensi protokol MJPEG dengan responsivitas *P-Controller* mewajibkan regulasi matematis yang cermat dalam membatasi gain kendali putar.   

| Judul Artikel / Sumber                                         | Penulis         | Tahun | Jurnal / Venue        |
| -------------------------------------------------------------- | --------------- | ----- | --------------------- |
| Web-controlled tank robot using ESP32-CAM with real-time MJPEG | M. A. FokaKefir | 2024  | GitHub Repo           |
| Mobile AR Control System with ESP32-CAM (MJPEG Stream Latency) | AIRCC           | 2024  | CS & IT Journal       |
| ESP32-CAM Video Streaming Web Server                           | S. Santos       | 2019  | Random Nerd Tutorials |
| ESP32 WiFi RC Car Control                                      | Grokipedia      | 2024  | Tech Encyclopedia     |

### 2.8 Servo dan Mekanisme Pengumpul Berbahan TPU

Pengambilan keputusan desain antarmuka lokomotor pemungut objek (*intake mechanism*) dilandaskan pada efisiensi ruang dan kelistrikan, menyingkirkan konstruksi berotasi silinder kontinu bertenaga motor kecepatan tinggi (*continuous roller*) yang umum dipakai robot komersial, karena menuntut pengorbanan voltase dan meningkatkan probabilitas akustik bising. Sebaliknya, pengumpulan objek dieksekusi secara fungsional asimetris diskrit meminjam presisi sudut dari aktuator modul motor servo limitasi-putaran standar (*sweep servo limited limit angles*). Mekanisme pendorong berosilasi membuka tutup laksana struktur lengan penarik tuas untuk merangkul bola sejajar kompartemen.   

Kepala sikat sapuan (*sweeping fingers arm*) dari alat ini dimanufaktur fusi aditif berbasis lelehan filamen komersial fleksibel kelas elastomer, *Thermoplastic Polyurethane* (TPU) dengan indeks rasio kekerasan minimal yang mendominasi kategori lembut (e.g., kelas Shore Hardness 60A, 70A, hingga maksimum 85A). Struktur makromolekul polimer blok TPU menghidangkan paduan simetris luar biasa di antara resistensi keletihan tegangan regangan dan ketidaksetaraan kepatuhan (*mechanical compliance material modulus*) serta koefisien gesekan seret traksi yang masif. Manakala lengan putar servo memaksa kerangka merenggut lintasan spasial area bola ping-pong plastik rapuh yang terekam, kepatuhan (*compliance*) deformasi material kelenturan sirip jari poliuretan TPU mendeformasikan wujud permukaannya beradaptasi menghimpit objek sferikal melengkung, mengeliminasi energi hantaman pergerakan kinetik bola. Hal ini memusnahkan gejala reaksi pemantulan seketika lari objek keluar gawang kolektor (*ricochet bouncing effect*) dan abrasi friksi berlebihan yang secara empiris identik mengagalkan sistem *hard-plastic* kaku purwarupa pendahulu berbahan ABS atau PLA murni.   

| Judul Artikel / Sumber                                                                 | Penulis              | Tahun | Jurnal / Venue      |
| -------------------------------------------------------------------------------------- | -------------------- | ----- | ------------------- |
| A 3D printed monolithic soft gripper with adjustable stiffness                         | N. G. J. Tawk et al. | 2017  | ResearchGate        |
| Materials and Methods for Designing 3D-Printed Soft Robot Grippers in Low-Hardness TPU | ACS Publications     | 2024  | Chemical Reviews    |
| Compressibility of 3D-printed TPU for Flexible Gripper                                 | MDPI                 | 2023  | Applied Sciences    |
| Deformation Potential and Directional Locking Behaviour of TPU                         | V. Hanzlik           | 2026  | CAADRIA Proceedings |

### 2.9 Sistem Terdistribusi dan Ground Station (Flask + WebSocket)

Struktur operasional arsitektural asimetris mengisolasi prosesor Arduino murni untuk mengelola putaran kendali kinematika loop-tertutup mikroskopis dan pemicuan gerbang interval PWM kelistrikan (*low-level*). Kapasitas penalaran logika observasi citra HSV yang berat dan interpretasi pemetaan kemudi terabstraksi melintasi perbatasan gelombang nirkabel menuju peranti sentral stasiun landasan laptop PC darat (*Ground Control Station* / GCS).

Landasan ekosistem aplikasi peladen di baliknya (*backend Web Server*) dibangun membungkus tulang punggung perpustakaan rute *micro-framework* Python, yakni antarmuka API Flask. Mengurai penyumbatan konvensional dari gaya sinkronisasi kaku inkuiri pemanggilan *HTTP short-polling* periodik yang akan meremukkan perputaran FPS kamera sasis, implementasi real-time digembungkan melewati modifikasi ekstensi komponen pustaka antarmuka sinkron asinkron, *Flask-SocketIO*. Protokol *WebSocket* merekayasa kelangsungan pipa komunikasi dupleks simetris terbuka dua-arah berjangka panjang, mengakomodasi transmisi umpan balik status FSM otonom, *telemetry payload data event-driven* jarak, dan proyeksi pembaruan koordinat parameter FSM langsung ke *UI Dashboard browser* interaktif pada latensi konvergensi lokal sepersekian milidetik setelah membelah memori RAM peladen. Dasbor fungsional meramu instrumen integrasi manipulasi *slider runtime* kalibrasi matriks nilai rentang ambang kromatografi selektif HSV visual, hamparan tayangan ulang kamera log *overlay bounding box*, kendali manuver pengganti otonomi hibrida intervensi *joystick* proksimal, serta sistem akuisisi ekspor rekam catatan historis telemetri berekstensi *Comma-Separated Values* (CSV).   

Kelemahan konektivitas nir-protokol UDP pada sirkuit transmisi visual mereduksi jaminan probabilitas keselamatan navigasi FSM sewaktu putusnya ikatan pemancar *Wi-Fi* di ruang olahraga akibat distorsi jarak. Karenanya, subsistem pertahanan peranti lunak rekayasa asuransi logika (*safety runtime interlocks*) dinamakan *Watchdog Timer Protocol* ditegakkan di kompilator pengendali Arduino lokal. Metode ini mencacah siklus penyesuaian perhitungan denominasi ekspektasi instruksi kedipan jantung pulsa (*motion-heartbeat connection signal* paket ekspektasi interupsi ∼0,15 detik berulang kali). Jikalau transmisi latensi HTTP interkoneksi GCS tumpul membisu serta gagal diidentifikasi melampaui kerangka tenggat kelonggaran krisis (*timeout delay limit >500 ms*), subsistem rutinitas pemotongan mikrokontroler memaksa mengisolasi aliran gelombang komutasi tegangan *duty-cycle* gerbang PWM kemudi roda (membekukan aktuasi perputaran *H-bridge driver clamp constraint parameter* sasis). Reaksi putus hubungan isolatif seketika ini memblokir robot melampaui perimeter pelarian liar menabrak obstruksi arena (*runaway vehicle catastrophe*).   

| Judul Artikel / Sumber                                                                                       | Penulis         | Tahun | Jurnal / Venue    |
| ------------------------------------------------------------------------------------------------------------ | --------------- | ----- | ----------------- |
| R'DASH: Robot Information Telemetry Transport Dashboard (Flask+Socket.IO)                                    | V. Karnam       | 2024  | GitHub Repository |
| WebGCS - Web-Based Ground Control Station                                                                    | P. J. Burke     | 2024  | GitHub Repository |
| Cloud-enabled communication and lightweight web servers using Flask architecture for real-time UAV telemetry | T. S. V. et al. | 2024  | MDPI Symmetry     |
| Real-time Anomaly Detection Web UI (Flask integration)                                                       | V. Hanzlik      | 2024  | CTU Prague Thesis |

### 2.10 *Finite State Machine* (FSM) dan Navigasi Visual P-Controller

Pengkoordinasian manuver navigasi reaktif otomasi pengumpul ping-pong dirumuskan dengan disiplin alur kendali *Finite State Machine* (FSM) state-dependen berbatas siklik. Algoritma ini menyeleksi serta menetapkan hirarki eksklusif perpindahan lintas keadaan operasional diskrit pencegah tabrakan:   

1. **IDLE**: Berdiam statis pra-operasi penginisiasi kalibrasi nilai *bias offset gyroscopic* MPU6050, menunggu komunikasi jabat-tangan konektivitas IP peladen TCP serta pembacaan inkuiri status *slider parameter tuning HSV*.

2. **SEARCH**: Ekspedisi perburuan citra optikal berkelanjutan di mana FSM memerintahkan sasis memutar orientasi sentral tempat secara gradual pergeseran pelan (yaw), memanfaatkan pemindaian kontur warna target lensa optik FOV yang bersiap sedia hingga area bola teridentifikasi masuk menembus cakupan koordinat biner ambang batas pandang.   

3. **APPROACH**: Skema pelacakan reaktif penyesuaian sudut memburu konvergensi objek. State interupsi menavigasikan penggabungan fungsi laju skalar translasi maju mekanis tetap lintasan roda (vx​) dan dibarengi modulasi penyesuaian kontrol dinamik belokan matriks kelurusan arah berpadanan umpan balik pandang proyeksi spasial (*Image-based Visual Servoing*) memusatkan garis sasis sejajar target bola di lapangan pandang.   

4. **COLLECT**: Pengaktifan terminal akuisisi final sesudah perhitungan dimensi ambang batas sumbu piksel jarak-Y vertikal (*y-pixel bounding ratio constraint centroid*) di layar telah menerobos zona minimum konvergensi kamera sasis bawah, menyalakan fungsi tuas interupsi mekanisme bukaan servo sapuan limit ekstrim (*sweep constraint cycle*) untuk menarik peluru kompartemen tertutup, pasca itu iterasi reset kembali berpindah alih ke siklus state **SEARCH**.

Pengendalian orientasi kompensasi rotasi asimetrik vektor arah sumbu belok penyimpangan Z (ωz​) di fase kejar **APPROACH** tidak didelegasikan dengan PID komplet (*Proportional-Integral-Derivative*) seperti di mekanik kamera gimbal *pan-tilt axis* kompleks robot komersial, berhubung platform ini mengeksekusi visi penglihatan sasis kaku linier *fixed mount*. Pengendalian diformat menyempit memanggil regulasi kontrol proporsional kendali lingkar-tertutup balikan, didefinisikan sebagai *P-Controller*. Matriks perhitungan pengoreksi simpangan ini diringkas:

u(t)=Kp​⋅e(t)

Variabel operasional dinamis dari instrumen kesalahan error e(t) dikalkulasi matematis melalui perbedaan skalar linear kuadrat resolusi antara posisi perpindahan geser titik pusat matriks warna ekstrak sentroid target (Cx​) dan sumbu persimpangan lensa fiksasi horizontal asimetris pembagian dua tengah *Frame Width/2* (sebagai contoh resolusi 640p menghasilkan rumus offset linear galat e(t)=Cx​−320). Pengganda kompensasi proporsional parameter bobot konstan redaman sentral (Kp​) harus disetel (*tuning*) mengkompensasi distorsi pelambatan keterlambatan transmisi tangkapan video *MJPEG stream network latency propagation*. Waktu penundaan transmisi ini merepresentasikan fasa keterlambatan induksi waktu asimtotis (*phase lag shift*) dalam dinamika responsif kompensasi lingkar pengontrolan proporsional motor H-Bridge PWM H-Bridge. Keterlambatan visual ini merampas probabilitas pengaplikasian rasio nilai Kp​ agresif masif maksimum, mengharuskan nilai kompensasi proporsional diredam untuk meruntuhkan potensi eksitasi berlebihan serta guncangan getaran manuver simpang pembelokan robot di luar kendali yang tak mampu teredam harmonis (*unstable control hunting oscillatory limit loop wobble behavior* akibat delay pengamatan sentroid penglihatan).   

| Judul Artikel / Sumber                                                           | Penulis          | Tahun | Jurnal / Venue           |
| -------------------------------------------------------------------------------- | ---------------- | ----- | ------------------------ |
| Visual Servoing using OpenCV (Centroid tracking & P-Controller)                  | A. Bhowmik       | 2024  | GitHub Repository        |
| Fuzzy Logic Controller for an Autonomous Mobile Robot (P-Control FSM Navigation) | V. M. Peri       | 2002  | Auburn University Thesis |
| Hybrid ELM-PID visual tracking control scheme                                    | MDPI             | 2022  | Sensors Journal          |
| Visual Servoing for Target Tracking Using a Non-linear 2 DOF System              | B. Bilgin        | 2024  | METU Thesis              |
| Vision based controller for maneuverable mobile robot                            | TUM Publications | 2024  | TUM Repository           |

*This is for informational purposes only. For medical advice or diagnosis, consult a professional.*

[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fstore.pongbotsports.com%2Fproducts%2Ftable-tennis-ball-picker)

store.pongbotsports.com

Table Tennis Ball Picker | Easy Ball Collection - pongbot

Terbuka di jendela baru](https://store.pongbotsports.com/products/table-tennis-ball-picker)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.aliexpress.com%2Fw%2Fwholesale-tennis-ball-collector-robot.html)

aliexpress.com

tennis ball collector robot - AliExpress

Terbuka di jendela baru](https://www.aliexpress.com/w/wholesale-tennis-ball-collector-robot.html)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.ebay.com%2Fitm%2F397456398581)

ebay.com

Table Tennis Robot Balls Picker Ping Pong Auto Ball Training Machine T | eBay

Terbuka di jendela baru](https://www.ebay.com/itm/397456398581)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fpatents.google.com%2Fpatent%2FUS7674196B2%2Fen)

patents.google.com

US7674196B2 - Robot for collecting table tennis balls - Google Patents

Terbuka di jendela baru](https://patents.google.com/patent/US7674196B2/en)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.instructables.com%2FPing-Pong-Ball-Collector-Robot%2F)

instructables.com

Ping Pong Ball Collector Robot : 12 Steps (with Pictures) - Instructables

Terbuka di jendela baru](https://www.instructables.com/Ping-Pong-Ball-Collector-Robot/)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fjournal.irpi.or.id%2Findex.php%2Fijirse%2Farticle%2Fview%2F2292)

journal.irpi.or.id

Robot Pengumpul Bola Pingpong Otomatis Menggunakan Sistem Vakum dan Raspberry Pi Berbasis Deteksi Kamera | Indonesian Journal of Informatic Research and Software Engineering (IJIRSE)

Terbuka di jendela baru](https://journal.irpi.or.id/index.php/ijirse/article/view/2292)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Frepository.pnj.ac.id%2F29518%2F1%2FHalaman%2520Identitas.pdf)

repository.pnj.ac.id

Rancang Bangun Robot Pengumpul Bola Pingpong Otomatis Menggunakan Sistem Vacuum berbasis Sensor Pixy2 TUGAS AKHIR AGUSTI HERYUNA - Repository PNJ - Politeknik Negeri Jakarta

Terbuka di jendela baru](https://repository.pnj.ac.id/29518/1/Halaman%20Identitas.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F398522299_Materials_and_Methods_for_Designing_3D-Printed_Soft_Robot_Grippers_in_Low-Hardness_TPU_60A-70A)

researchgate.net

Materials and Methods for Designing 3D-Printed Soft Robot Grippers in Low-Hardness TPU (60A-70A) - ResearchGate

Terbuka di jendela baru](https://www.researchgate.net/publication/398522299_Materials_and_Methods_for_Designing_3D-Printed_Soft_Robot_Grippers_in_Low-Hardness_TPU_60A-70A)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F356740235_Development_of_Ball_Detection_System_with_YOLOv3_in_a_Humanoid_Soccer_Robot)

researchgate.net

(PDF) Development of Ball Detection System with YOLOv3 in a Humanoid Soccer Robot - ResearchGate

Terbuka di jendela baru](https://www.researchgate.net/publication/356740235_Development_of_Ball_Detection_System_with_YOLOv3_in_a_Humanoid_Soccer_Robot)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.semanticscholar.org%2Fpaper%2FXNOR-YOLO%253A-The-High-Precision-of-The-Ball-and-Goal-Susanto-Putra%2Fcd9e8f262c3c62432a80743c459aa5c5b8038e00)

semanticscholar.org

XNOR-YOLO: The High Precision of The Ball and Goal Detecting on The Barelang-FC Robot Soccer | Semantic Scholar

Terbuka di jendela baru](https://www.semanticscholar.org/paper/XNOR-YOLO%3A-The-High-Precision-of-The-Ball-and-Goal-Susanto-Putra/cd9e8f262c3c62432a80743c459aa5c5b8038e00)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fcerv.aut.ac.nz%2Fwp-content%2Fuploads%2F2025%2F07%2FIGI_BookChapter_TableTennis-wyan-revised.pdf)

cerv.aut.ac.nz

Precise Ball Detection in Table Tennis Games Using Deep Learning and Stereo Vision

Terbuka di jendela baru](https://cerv.aut.ac.nz/wp-content/uploads/2025/07/IGI_BookChapter_TableTennis-wyan-revised.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Flouis.uah.edu%2Fcgi%2Fviewcontent.cgi%3Farticle%3D1507%26context%3Drceu-hcr)

louis.uah.edu

Exploring AI in Table Tennis Video Analytics using YOLOv8 Real-Time Object Detection Models - LOUIS

Terbuka di jendela baru](https://louis.uah.edu/cgi/viewcontent.cgi?article=1507&context=rceu-hcr)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fejournal.uin-malang.ac.id%2Findex.php%2Fijeie%2Farticle%2Fdownload%2F39317%2F13320)

ejournal.uin-malang.ac.id

Ball Detection in Wheeled Soccer Robot Using the YOLOv8 Model - E-Journal UIN Malang

Terbuka di jendela baru](https://ejournal.uin-malang.ac.id/index.php/ijeie/article/download/39317/13320)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F387383006_Tennis_Ball_Detection_using_YOLOv8_for_Mobile_Robot_Ball_Collection)

researchgate.net

Tennis Ball Detection using YOLOv8 for Mobile Robot Ball Collection - ResearchGate

Terbuka di jendela baru](https://www.researchgate.net/publication/387383006_Tennis_Ball_Detection_using_YOLOv8_for_Mobile_Robot_Ball_Collection)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fconferences.ulbsibiu.ro%2Ficdd%2F2025%2Ffiles%2FProceedings_ICDD2025.pdf)

conferences.ulbsibiu.ro

Proceedings of the International Conference on Applied Informatics, ICDD May 29th – 31th, 2025 Sibiu, Romania

Terbuka di jendela baru](https://conferences.ulbsibiu.ro/icdd/2025/files/Proceedings_ICDD2025.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F384094926_Ball-type_Small_Objection_Algorithm_based_on_YOLOv8)

researchgate.net

Ball-type Small Objection Algorithm based on YOLOv8 - ResearchGate

Terbuka di jendela baru](https://www.researchgate.net/publication/384094926_Ball-type_Small_Objection_Algorithm_based_on_YOLOv8)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F276344731_Kinematic_Model_of_a_Four_Mecanum_Wheeled_Mobile_Robot)

researchgate.net

Kinematic Model of a Four Mecanum Wheeled Mobile Robot - ResearchGate

Terbuka di jendela baru](https://www.researchgate.net/publication/276344731_Kinematic_Model_of_a_Four_Mecanum_Wheeled_Mobile_Robot)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fecam-eurobot.github.io%2FTutorials%2Fmechanical%2Fmecanum.html)

ecam-eurobot.github.io

Mecanum wheels - Ecam Eurobot

Terbuka di jendela baru](https://ecam-eurobot.github.io/Tutorials/mechanical/mecanum.html)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.geometrie.tugraz.at%2Fgfrerrer%2Fpublications%2Fmecanum.pdf)

geometrie.tugraz.at

Geometry and Kinematics of the Mecanum Wheel

Terbuka di jendela baru](https://www.geometrie.tugraz.at/gfrerrer/publications/mecanum.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fjournal.ugm.ac.id%2Fjuliet%2Farticle%2Fdownload%2F74760%2F34298)

journal.ugm.ac.id

Implementasi Kinematika Trajectory Lingkaran pada Robot Roda Mecanum - Jurnal Universitas Gadjah Mada

Terbuka di jendela baru](https://journal.ugm.ac.id/juliet/article/download/74760/34298)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fgithub.com%2FShimraz%2FKinematics-of-Mobile-Robot%2Fblob%2Fmain%2FREADME.md)

github.com

Kinematics-of-Mobile-Robot/README.md at main - GitHub

Terbuka di jendela baru](https://github.com/Shimraz/Kinematics-of-Mobile-Robot/blob/main/README.md)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fejournal.itn.ac.id%2Findex.php%2Fmagnetika%2Farticle%2Fdownload%2F8613%2F4485)

ejournal.itn.ac.id

SIMULASI GERAK ROBOT SOCCER BERODA MENGGUNAKAN KINEMATIKA OMNIDIREKTIONAL RODA EMPAT

Terbuka di jendela baru](https://ejournal.itn.ac.id/index.php/magnetika/article/download/8613/4485)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fme.uotechnology.edu.iq%2Fwp-content%2Fuploads%2F2024%2F12%2F15.pdf)

me.uotechnology.edu.iq

Kinematics Modeling and Simulation of Holonomic Wheeled Mobile Robot with Mecanum Wheels

Terbuka di jendela baru](https://me.uotechnology.edu.iq/wp-content/uploads/2024/12/15.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fjournal.arteii.or.id%2Findex.php%2FNeptunus%2Farticle%2Fview%2F1020)

journal.arteii.or.id

Deteksi Warna Dasar Menggunakan Metode Thresholding HSV dengan OpenCV | Neptunus: Jurnal Ilmu Komputer Dan Teknologi Informasi

Terbuka di jendela baru](https://journal.arteii.or.id/index.php/Neptunus/article/view/1020)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F388635914_Comparative_Analysis_of_YOLOv8_and_HSV_Methods_for_Traffic_Density_Measurement)

researchgate.net

Comparative Analysis of YOLOv8 and HSV Methods for Traffic Density Measurement

Terbuka di jendela baru](https://www.researchgate.net/publication/388635914_Comparative_Analysis_of_YOLOv8_and_HSV_Methods_for_Traffic_Density_Measurement)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fjournal.aptii.or.id%2Findex.php%2FRouter%2Farticle%2Fview%2F706)

journal.aptii.or.id

Penerapan Metode Segmentasi Warna HSV untuk Deteksi Objek Berbasis Warna pada Citra Digital | Router : Jurnal Teknik Informatika dan Terapan

Terbuka di jendela baru](https://journal.aptii.or.id/index.php/Router/article/view/706)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fproceeding.unpkediri.ac.id%2Findex.php%2Fstains%2Farticle%2Fview%2F9054)

proceeding.unpkediri.ac.id

Klasifikasi Tingkat Kematangan Buah Tomat Berbasis Pengolahan Citra Dengan Metode YoloV8 | Seminar Nasional Teknologi & Sains - unp kediri

Terbuka di jendela baru](https://proceeding.unpkediri.ac.id/index.php/stains/article/view/9054)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=http%3A%2F%2Fwww.pertanika.upm.edu.my%2Fresources%2Ffiles%2FPertanika%2520PAPERS%2FJST%2520Vol.%252033%2520%286%29%2520Oct.%25202025%2F17%2520JST-5674-2024.pdf)

pertanika.upm.edu.my

RGB vs. HSV for Kitchen Fire Detection with YOLOv5 - Pertanika

Terbuka di jendela baru](http://www.pertanika.upm.edu.my/resources/files/Pertanika%20PAPERS/JST%20Vol.%2033%20(6)%20Oct.%202025/17%20JST-5674-2024.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Flibrary.kab.ac.ug%2FRecord%2Fdoaj-art-52b0fda4f990459d9fb1704b121527d4%3Fsid%3D5703541)

library.kab.ac.ug

Comparative Analysis of YOLOv8 and HSV Methods for Traffic Density Measurement

Terbuka di jendela baru](https://library.kab.ac.ug/Record/doaj-art-52b0fda4f990459d9fb1704b121527d4?sid=5703541)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fgithub.com%2Fabhimanyubhowmik%2FVisual_Servoing)

github.com

Image-Based Visual Servoing Control (IBVS) - GitHub

Terbuka di jendela baru](https://github.com/abhimanyubhowmik/Visual_Servoing)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=http%3A%2F%2Fdigilib.unila.ac.id%2F92294%2F3%2F3.%2520SKRIPSI%2520TANPA%2520BAB%2520PEMBAHASAN%2520-%2520KARTIKA%2520SARI.pdf)

digilib.unila.ac.id

DETEKSI DAN KLASIFIKASI PENYAKIT PADA DAUN KENTANG DENGAN PENDEKATAN WATERSHED-IMPROVED SEGMENTATION DAN ALGORITMA YOLOv8 (Skrip - Digilib Unila

Terbuka di jendela baru](http://digilib.unila.ac.id/92294/3/3.%20SKRIPSI%20TANPA%20BAB%20PEMBAHASAN%20-%20KARTIKA%20SARI.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.frontiersin.org%2Fjournals%2Fveterinary-science%2Farticles%2F10.3389%2Ffvets.2026.1772252%2Ffull)

frontiersin.org

Performance comparison of YOLO, Faster R-CNN, and HRNet architectures for bull sperm viability assessment - Frontiers

Terbuka di jendela baru](https://www.frontiersin.org/journals/veterinary-science/articles/10.3389/fvets.2026.1772252/full)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.db-thueringen.de%2Fservlets%2FMCRFileNodeServlet%2Fdbt_derivate_00049732%2F1521-4001_99_2019_12_e201900173.pdf)

db-thueringen.de

Dynamics of a four-wheeled mobile robot with Mecanum wheels

Terbuka di jendela baru](https://www.db-thueringen.de/servlets/MCRFileNodeServlet/dbt_derivate_00049732/1521-4001_99_2019_12_e201900173.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Frsisinternational.org%2Fjournals%2Fijrsi%2Fuploads%2Fvol13-iss1-pg274-286-202601_pdf.pdf)

rsisinternational.org

Gyro-Stabilized Straight-Line Robot Using Mpu6050 Feedback Control - RSIS International

Terbuka di jendela baru](https://rsisinternational.org/journals/ijrsi/uploads/vol13-iss1-pg274-286-202601_pdf.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.ic-components.com%2Fblog%2Fmpu-6050-working-principle%2Capplication-and-package.jsp)

ic-components.com

MPU-6050 Working Principle, Application and Package - IC Components

Terbuka di jendela baru](https://www.ic-components.com/blog/mpu-6050-working-principle,application-and-package.jsp)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F348902341_Peningkatan_Akurasi_Sensor_GY-521_MPU-6050_dengan_Metode_Koreksi_Faktor_Drift)

researchgate.net

Peningkatan Akurasi Sensor GY-521 MPU-6050 dengan Metode Koreksi Faktor Drift

Terbuka di jendela baru](https://www.researchgate.net/publication/348902341_Peningkatan_Akurasi_Sensor_GY-521_MPU-6050_dengan_Metode_Koreksi_Faktor_Drift)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Findustrialmonitordirect.com%2Fblogs%2Fknowledgebase%2Fmpu6050-gyro-drift-fix-dmp-kalman-filter-and-i2cdevlib-setup)

industrialmonitordirect.com

MPU6050 Gyro Drift: DMP & Kalman Filter Solutions - Industrial Monitor Direct

Terbuka di jendela baru](https://industrialmonitordirect.com/blogs/knowledgebase/mpu6050-gyro-drift-fix-dmp-kalman-filter-and-i2cdevlib-setup)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fmjwhite8119.github.io%2FRobots%2Fmpu6050)

mjwhite8119.github.io

The MPU6050 Explained | Programming Robots

Terbuka di jendela baru](https://mjwhite8119.github.io/Robots/mpu6050)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fgithub.com%2Fkriswiner%2FMPU6050%2Fblob%2Fmaster%2FMPU6050Library%2FMPU6050IMU.ino)

github.com

MPU6050/MPU6050Library/MPU6050IMU.ino at master - GitHub

Terbuka di jendela baru](https://github.com/kriswiner/MPU6050/blob/master/MPU6050Library/MPU6050IMU.ino)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.ti.com%2Flit%2Fgpn%2FDRV8833)

ti.com

DRV8833 Dual H-Bridge Motor Driver datasheet (Rev. E) - Texas Instruments

Terbuka di jendela baru](https://www.ti.com/lit/gpn/DRV8833)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fcircuitdigest.com%2Fmicrocontroller-projects%2Finterface-drv8833-dual-motor-driver-module-with-arduino)

circuitdigest.com

Interfacing DRV8833 Dual Motor Driver Module with Arduino - Circuit Digest

Terbuka di jendela baru](https://circuitdigest.com/microcontroller-projects/interface-drv8833-dual-motor-driver-module-with-arduino)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fzbotic.in%2Fdrv8833-motor-driver-dual-dc-motor-control-for-esp32%2F)

zbotic.in

DRV8833 Motor Driver: Dual DC Motor Control for ESP32 - Zbotic

Terbuka di jendela baru](https://zbotic.in/drv8833-motor-driver-dual-dc-motor-control-for-esp32/)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.scribd.com%2Fdocument%2F879996845%2FGuide-to-Choosing-the-Best-DC-Motor-Drivers-for-Arduino)

scribd.com

Choosing Arduino Motor Drivers: TB6612FNG & DRV8833 | PDF | Mosfet - Scribd

Terbuka di jendela baru](https://www.scribd.com/document/879996845/Guide-to-Choosing-the-Best-DC-Motor-Drivers-for-Arduino)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Flastminuteengineers.com%2Fdrv8833-arduino-tutorial%2F)

lastminuteengineers.com

Controlling DC Motors with DRV8833 Motor Driver and Arduino - Last Minute Engineers

Terbuka di jendela baru](https://lastminuteengineers.com/drv8833-arduino-tutorial/)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fgithub.com%2FCircuit-Digest%2Finterfacing-DRV8833-dual-motor-driver-module-with-arduino%2F)

github.com

Circuit-Digest/interfacing-DRV8833-dual-motor-driver-module-with-arduino - GitHub

Terbuka di jendela baru](https://github.com/Circuit-Digest/interfacing-DRV8833-dual-motor-driver-module-with-arduino/)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fhub360.cc%2Fshop%2F2535-drv8833-motor-driver-module-16791)

hub360.cc

DRV8833 motor driver module - Hub360

Terbuka di jendela baru](https://hub360.cc/shop/2535-drv8833-motor-driver-module-16791)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Flearn.adafruit.com%2Fadafruit-drv8833-dc-stepper-motor-driver-breakout-board%2Farduino-dc-motor)

learn.adafruit.com

Arduino DC Motor | Adafruit DRV8833 DC/Stepper Motor Driver Breakout Board

Terbuka di jendela baru](https://learn.adafruit.com/adafruit-drv8833-dc-stepper-motor-driver-breakout-board/arduino-dc-motor)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fthinkrobotics.com%2Fblogs%2Ftutorials%2Ftest-blog)

thinkrobotics.com

ESP32-CAM Video Streaming Robot: A Complete Guide - ThinkRobotics.com

Terbuka di jendela baru](https://thinkrobotics.com/blogs/tutorials/test-blog)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fdocs.keyestudio.com%2Fprojects%2FKS5023%2Fen%2Flatest%2Fdocs%2F2WD%2520Camera%2520Robot%2520Car.html)

docs.keyestudio.com

ESP32 Cam 2WD Camera Robot Car - keyestudio docs documentation

Terbuka di jendela baru](https://docs.keyestudio.com/projects/KS5023/en/latest/docs/2WD%20Camera%20Robot%20Car.html)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fgithub.com%2FFokaKefir%2FESP32-robot)

github.com

GitHub - FokaKefir/ESP32-robot: Web-controlled tank robot using ESP32-CAM with real-time MJPEG video streaming. Features differential drive control via L298N H-bridge, intuitive web interface, and wireless operation over Wi-Fi. Perfect for robotics education and IoT experimentation. Supports 8-directional movement with live camera feed.

Terbuka di jendela baru](https://github.com/FokaKefir/ESP32-robot)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Frandomnerdtutorials.com%2Fesp32-cam-video-streaming-web-server-camera-home-assistant%2F)

randomnerdtutorials.com

ESP32-CAM Video Streaming Web Server (works with Home Assistant)

Terbuka di jendela baru](https://randomnerdtutorials.com/esp32-cam-video-streaming-web-server-camera-home-assistant/)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Faircconline.com%2Fcsit%2Fpapers%2Fvol16%2Fcsit160511.pdf)

aircconline.com

an integrated augmented reality mobile control system for esp32- based robot cars using opencv

Terbuka di jendela baru](https://aircconline.com/csit/papers/vol16/csit160511.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fgrokipedia.com%2Fpage%2FESP32_WiFi_RC_Car_Control)

grokipedia.com

ESP32 WiFi RC Car Control - Grokipedia

Terbuka di jendela baru](https://grokipedia.com/page/ESP32_WiFi_RC_Car_Control)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fadvanced.onlinelibrary.wiley.com%2Fdoi%2F10.1002%2Fadvs.202524237)

advanced.onlinelibrary.wiley.com

Pellet Printing for Soft Robotic Devices - Wu - 2026 - The Advanced Portfolio - Wiley

Terbuka di jendela baru](https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202524237)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fpapers.cumincad.org%2Fdata%2Fworks%2Fatt%2Fcaadria2026_51.pdf)

papers.cumincad.org

TPU-Based Flexible Strip Interlocking System Material-Informed Geometric Generation and Robotic Additive Fabrication for Flex- i - CumInCAD

Terbuka di jendela baru](https://papers.cumincad.org/data/works/att/caadria2026_51.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fpubs.acs.org%2Fdoi%2F10.1021%2Facs.chemrev.4c00749)

pubs.acs.org

Fabrication of Soft Robotics by Additive Manufacturing: From Materials to Applications | Chemical Reviews - ACS Publications

Terbuka di jendela baru](https://pubs.acs.org/doi/10.1021/acs.chemrev.4c00749)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Feprints.tarc.edu.my%2F27468%2F)

eprints.tarc.edu.my

Design and Fabrication of Universal Soft Robotic Gripper - TAR UMT Institutional Repository

Terbuka di jendela baru](https://eprints.tarc.edu.my/27468/)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.mdpi.com%2F2076-3417%2F13%2F17%2F9677)

mdpi.com

Design and Implementation of a Compliant Gripper for Form Closure of Diverse Objects

Terbuka di jendela baru](https://www.mdpi.com/2076-3417/13/17/9677)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F321987084_A_3D_printed_monolithic_soft_gripper_with_adjustable_stiffness)

researchgate.net

A 3D printed monolithic soft gripper with adjustable stiffness | Request PDF - ResearchGate

Terbuka di jendela baru](https://www.researchgate.net/publication/321987084_A_3D_printed_monolithic_soft_gripper_with_adjustable_stiffness)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fbuilder.aws.com%2Fcontent%2F39pQRgWDhijhuAlgN7PGgKgRoKm%2Faideas-caligo-dynamics-ai-powered-autonomous-drone-swarm-for-emergency-response)

builder.aws.com

AIdeas: Caligo Dynamics - AI Powered Autonomous Drone Swarm for Emergency Response | AWS Builder Center

Terbuka di jendela baru](https://builder.aws.com/content/39pQRgWDhijhuAlgN7PGgKgRoKm/aideas-caligo-dynamics-ai-powered-autonomous-drone-swarm-for-emergency-response)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fmedium.com%2F%40writeronepagecode%2Farchitecting-a-robust-trading-bot-in-python-782d850888a7)

medium.com

Architecting a Robust Trading Bot in Python | by Saurav - Medium

Terbuka di jendela baru](https://medium.com/@writeronepagecode/architecting-a-robust-trading-bot-in-python-782d850888a7)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.mdpi.com%2F2073-8994%2F18%2F4%2F548)

mdpi.com

UAV-Based QR Code Scanning and Inventory Synchronization System with Safe Trajectory Planning - MDPI

Terbuka di jendela baru](https://www.mdpi.com/2073-8994/18/4/548)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F34778961%2Fflask-and-flask-socketio)

stackoverflow.com

Flask and Flask-SocketIO - python - Stack Overflow

Terbuka di jendela baru](https://stackoverflow.com/questions/34778961/flask-and-flask-socketio)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fgithub.com%2Fvamsi-karnam%2Frdash)

github.com

vamsi-karnam/rdash: R'DASH (Robot Information Telemetry Transport Dashboard) is an ... - GitHub

Terbuka di jendela baru](https://github.com/vamsi-karnam/rdash)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fdspace.cvut.cz%2Fbitstreams%2Ff8a1670a-74d0-4159-9972-93ff1ae6bea8%2Fdownload)

dspace.cvut.cz

Edge AI Integration for Anomaly Detection in Assembly using Delta Robot - DSpace Repository

Terbuka di jendela baru](https://dspace.cvut.cz/bitstreams/f8a1670a-74d0-4159-9972-93ff1ae6bea8/download)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.mdpi.com%2F2075-1702%2F10%2F9%2F782)

mdpi.com

Adaptive Neural-PID Visual Servoing Tracking Control via Extreme Learning Machine

Terbuka di jendela baru](https://www.mdpi.com/2075-1702/10/9/782)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.techrxiv.org%2Fdoi%2Fpdf%2F10.36227%2Ftechrxiv.177219991.19899921)

techrxiv.org

Integrated Navigation Framework for Autonomous Ackermann-Steered Competition Robots - TechRxiv

Terbuka di jendela baru](https://www.techrxiv.org/doi/pdf/10.36227/techrxiv.177219991.19899921)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fetd.lib.metu.edu.tr%2Fupload%2F12624309%2Findex.pdf)

etd.lib.metu.edu.tr

VISUAL SERVOING FOR TARGET TRACKING USING A NON-LINEAR 2 DEGREE OF FREEDOM SYSTEM A THESIS SUBMITTED TO THE GRADUATE SCHOOL OF N

Terbuka di jendela baru](https://etd.lib.metu.edu.tr/upload/12624309/index.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fwww.eng.auburn.edu%2F%7Etroppel%2Fcourses%2F5530%25202011C%2520Robots%2520Fall%252011%2Fliterature%2FMohan%2520Thesis%2520fuzzy%2520logic%2520wall%2520follow.pdf)

eng.auburn.edu

FUZZY LOGIC CONTROLLER FOR AN AUTONOMOUS MOBILE ROBOT VAMSI MOHAN PERI

Terbuka di jendela baru](https://www.eng.auburn.edu/~troppel/courses/5530%202011C%20Robots%20Fall%2011/literature/Mohan%20Thesis%20fuzzy%20logic%20wall%20follow.pdf)[

![](https://t0.gstatic.com/faviconV2?client=BARD&type=FAVICON&size=256&fallback_opts=TYPE,SIZE,URL&url=https%3A%2F%2Fmediatum.ub.tum.de%2Fdoc%2F1281584%2F419623.pdf)

mediatum.ub.tum.de

Direct Homography Control for Highly Maneuverable Vehicle

](https://mediatum.ub.tum.de/doc/1281584/419623.pdf)
