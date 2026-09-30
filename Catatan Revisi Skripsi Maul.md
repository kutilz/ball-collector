# Catatan Revisi — Skripsi Maul

File hasil: **`Skripsi Maul - revisi.docx`**. File asli `Skripsi Maul.docx` tidak diubah. Untuk melihat semua perbedaan di Word, buka **Review → Compare**, lalu pilih file asli dan file revisi.

Di dalam dokumen:

- **Sorotan kuning** menandai bagian yang wajib diisi atau dicek penulis (data hasil, tanggal, pilihan yang belum pasti).
- **Komentar "Claude (review)"** (21 buah) menjelaskan alasan perubahan dan hal yang perlu dikonfirmasi.
- **Daftar isi, daftar gambar, dan daftar tabel** berupa field otomatis. Saat dokumen dibuka, Word menawarkan pembaruan; bisa juga klik kanan lalu pilih **Update Field**.

Metodologi, urutan tahapan, angka pengujian, dan isi diagram lama tidak diubah.

## 1. Bagian awal

- Judul: "Automasi" diganti "Otomasi" (KBBI; sama dengan nama prodi) di sampul, lembar pengesahan, pernyataan, dan ucapan terima kasih.
- Ucapan Terima Kasih sebelumnya memuat judul skripsi lain. Sudah diganti dengan judul skripsi ini.
- Ejaan: resiko → risiko, kehadirat → ke hadirat, Progam → Program, penuilis → penulis, Staff → staf, "M.T. Selaku" → "M.T., selaku", "karya sendiri" → "karya saya sendiri", "Oleh :" → "Oleh:".
- Tahun di sampul diubah menjadi 2026. Tanggal pada pernyataan dan ucapan terima kasih diganti isian `[bulan] 2026` yang disorot.
- Abstrak dan Abstract ditulis ulang dari isi naskah, tidak lagi Lorem ipsum. Hasil pengujian masih berupa `[ISI]`. Kata kunci juga sudah diisi.
- Ditambahkan **Daftar Singkatan** (diwajibkan Pedoman UPI 2024) dan field otomatis untuk daftar isi, gambar, dan tabel.

## 2. Sitasi: IEEE → APA (Pedoman UPI)

- Semua sitasi `[n]` diubah ke format (Nama, Tahun). Aturan UPI yang dipakai:
  - dua penulis: selalu keduanya;
  - 3–5 penulis: semua nama pada penyebutan pertama, lalu "dkk.";
  - lebih dari 5 penulis: "dkk." sejak awal;
  - sitasi dalam satu kurung diurutkan menurut abjad.
- Kalimat naratif ikut disesuaikan, misalnya "Yeon, Kim, Ryou dan Sim (2017) merancang …".
- Daftar pustaka disusun ulang dalam gaya APA: urut abjad, *hanging indent*, nama jurnal dan volume dicetak miring.
- **Metadata dicek ulang lewat penelusuran web**, dan beberapa entri di draf ternyata salah:

| Rujukan | Di draf | Setelah dicek |
|---|---|---|
| Gu dkk. (2019) | S. Gu, X. Chen, W. Zeng, X. Wang | Gu, Zeng, Jia, & Yan |
| Liu dkk. (2020) | H. Liu, H. Shi, M. Li, M. Iseki | Liu, Sun, Li, & Iida |
| xYOLO (2019) | "B. J. Bruce et al." | Barry, Shah, Keijsers, Khan, & Hopman |
| *Soft gripper* (2017) | "N. Tawk et al." | Mutlu, Tawk, Alici, & Sariyildiz; IECON 2017, hlm. 6235–6240 |
| Mecanum (J. Eng., 2024) | judul "…simulation and experimentation", penulis lain | "Kinematic control … for trajectory tracking", Hernández & Almeida |
| Padilla dkk. (2021) | 3 penulis | 5 penulis (Passos dan Dias ditambahkan) |
| Wijaya dkk. | 2025 | 2024, vol. 15(2) |
| Wu dkk. (2005) | hlm. 959–963 | hlm. 611–615 |
| Yeon dkk. (2017) | tanpa halaman | hlm. 909–914 |
| Terven dkk. (2023) | judul "…and Beyond" | "…YOLOv8 and YOLO-NAS", hlm. 1680–1716 |
| Compliant gripper (2023) | tanpa penulis | Bingham, Hessler, Lama, & Deemyad |
| Putri dkk. (2025) | belum lengkap | Putri, Saputra, & Deviana; IJIRSE 5(2), 168–175 |
| Mangkusasmito dkk. (2020) | tanpa jurnal | *Ultima Computing* 12(2), 91–95 |
| OpenCV "[18]" | judul gabungan, URL tidak cocok | dipecah jadi *Contour features* dan *Morphological transformations* |
| "[29]" dead reckoning | tidak pernah dikutip | dihapus |

- Masih perlu dicek manual (disorot kuning):
  - **Heryunanda (2025)**: judul di repositori PNJ adalah "Pemprogram Navigasi Robot Pengumpul Bola Pingpong Otomatis Berbasis Sensor Pixy2", dan URL-nya perlu dicocokkan;
  - halaman artikel **Wijaya dkk. (2024)**.

## 3. Penulisan di Bab I–V

- "ping-pong" → pingpong (KBBI), "WiFi" → Wi-Fi, "odometry" → odometri, "real-time" → waktu nyata, "teoritis" → teoretis.
- "kepatuhan (compliance)" → kelenturan (*compliance*); "mendeformasi" → mengalami deformasi.
- §2.1: "gripper … PLA+" disamakan dengan bagian lain menjadi TPU. Ada komentar untuk dikonfirmasi.
- Kutip-penakut ("lebih nyaman", "membuat robot … pertama") diganti kalimat lugas.
- §2.2.1: tanda baca aposisi diperbaiki ("…, yaitu kepekaan …, dimitigasi").
- §3.3.4 butir d: "Komunikasi laptop→robot" diganti "Komunikasi antara laptop dan robot".
- Nama variabel kode di dalam teks (`KP_STEERING`, `MIN_CONTOUR_AREA`, `AREA_*`, `VIDEO_SOURCE`, "(dari config.py)") diganti simbol atau uraian.
- Catatan penulis "(Menjawab rumusan masalah n — …)" di Simpulan dihapus.
- Istilah asing dicetak miring secara konsisten (sekitar 490 tempat). Huruf tebal untuk penegasan di tengah kalimat dihapus (116 tempat), karena Pedoman UPI meminta penegasan memakai huruf miring. Label di awal paragraf tetap tebal.

## 4. Format

- Tingkat judul Bab II diperbaiki: 2.2.1–2.2.10 kini Heading 3, sehingga §2.2.6–2.2.10 ikut masuk daftar isi. Subbab 4.6.1–4.6.4 dijadikan judul sendiri.
- "1.6 3.1 Metode Penelitian" dan "5.2 Saran" tidak lagi mendapat nomor otomatis ganda.
- Penomoran Simpulan dan Saran kini mulai dari 1. Sebelumnya menyambung dari daftar di §3.1.
- Halaman kosong sebelum BAB III dan BAB IV dihapus (sebelumnya ada dua pemisah halaman berurutan).
- Keterangan tabel ditaruh di atas tabel dan keterangan gambar di bawah gambar, dengan format "Tabel 3.1 Judul Tabel". Keduanya memakai gaya *Keterangan Tabel/Gambar* agar daftar otomatis bisa dibuat.
- Margin atas 4 cm (Pedoman UPI 2024). Heading 3/4 memakai Times New Roman hitam, bukan Calibri biru. Isi sel tabel dan daftar pustaka rata kiri.

## 5. Gambar baru (dari isi naskah dan kode repo)

| No. | Isi | Menggantikan |
|---|---|---|
| 2.1 | Pola putaran roda Mecanum untuk maju, menyamping, dan berputar (diturunkan dari persamaan tereduksi) | baru |
| 2.2 | Kerangka berpikir (masukan–proses–keluaran) | "Gambar 4." |
| 3.1 | Alur metode R&D/prototyping dengan iterasi | penanda |
| 3.2 | Blok diagram arsitektur (laptop ↔ ESP32-CAM ↔ Arduino) | penanda |
| 3.4 | Arsitektur daya (rel motor dan rel 5 V) | penanda |
| 3.5 | Koneksi antarmodul (dari Tabel 3.3) | penanda "skematik" |
| 3.6 | Diagram alir *pipeline* HSV | baru |
| 3.7 | Diagram FSM | penanda |
| 3.8 | Urutan protokol + *watchdog*/*heartbeat* | penanda |
| 3.9 | Diagram alir lingkar utama *ground station* (sesuai `app.py`) | baru |
| 3.11 | Alur pengujian bertahap | baru |

Foto dan tangkapan layar (3.3, 3.10, 4.1–4.7) tidak bisa dibuat tanpa bahan asli, jadi dibiarkan sebagai tempat bersorot kuning lengkap dengan keterangannya.

Sumber gambar ada di `docs/skripsi/gambar/`. Untuk mengubah dan merender ulang: `python3 diagrams.py && node render.js`.

## 6. Yang belum bisa diputuskan tanpa penulis (lihat komentar)

1. Apakah ada koreksi *heading* IMU saat *strafe*? Di kode repo fitur ini tidak ada, padahal Tabel 4.7, §4.6.2, dan Simpulan butir 2 bergantung padanya.
2. Model YOLOv8 pembanding: yolov8n pralatih COCO atau hasil latih sendiri? `YOLO_IMGSZ = 416`, sedangkan naskah menyebut 640×480.
3. Telemetri `vbat` belum punya perangkat keras pengukur (nilainya masih 0 di kode).
4. Rumusan masalah 3 menyebut "menguji fitur keselamatan", tetapi belum ada prosedur uji *watchdog*.
5. Pola rol O atau X; dosen pembimbing satu atau dua; tempat dan waktu penelitian.
6. Nilai bersorot di Subbab 3.4 (rentang n, "mis.", "atau") perlu diganti dengan yang benar-benar dipakai.
7. Seluruh data di Bab IV–V.

**Ralat atas review sebelumnya:** matriks kinematika di §2.2.4 ternyata **benar**. Tanda minusnya disimpan sebagai *phantom* (untuk perataan), sehingga pembacaan teks otomatis keliru menampilkannya seperti empat baris sama. Hal yang sama berlaku untuk "mask biner :", karena di antaranya ada rumus. Keduanya tidak diubah.
