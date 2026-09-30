# BAB V — SIMPULAN DAN SARAN

> **Catatan penulisan (hapus saat dipindah ke Word):**
> - Judul bab mengikuti pedoman UPI: **"Simpulan dan Saran"**.
> - **5.1 Simpulan** menjawab ketiga rumusan masalah BAB I. Prosa sudah lengkap;
>   yang tersisa hanya **mengisi angka** — tiap `⟨…⟩` diisi dari hasil BAB IV
>   (jangan mengarang; lengkapi setelah pengujian). Kurung siku `[…]` = pilihan
>   kata yang harus disesuaikan dengan arah hasil.
> - **5.2 Saran** berisi butir nyata (fitur yang sengaja tidak diimplementasikan
>   + arah peningkatan). Butir bertanda **(opsional)** boleh dibuang saat bimbingan.

---

## 5.1 Simpulan

Berdasarkan hasil perancangan, implementasi, dan pengujian, diperoleh simpulan
sebagai berikut.

1. **(Menjawab rumusan masalah 1 — deteksi.)** Sistem deteksi bola ping-pong
   berbasis segmentasi warna HSV pada arsitektur terdistribusi berhasil
   diimplementasikan dan berjalan *real-time* di *ground station*, dengan
   *precision* ⟨…⟩, *recall* ⟨…⟩, *F1-score* ⟨…⟩, dan ⟨…⟩ FPS. Dibandingkan
   secara luring dengan YOLOv8 (*precision* ⟨…⟩, *recall* ⟨…⟩, *F1* ⟨…⟩, ⟨…⟩
   FPS), metode HSV [lebih cepat / lebih ringan / dst. — sesuaikan hasil],
   sehingga [lebih/kurang] sesuai untuk dijalankan sebagai detektor daring pada
   konteks sistem ini.

2. **(Menjawab rumusan masalah 2 — navigasi.)** Kinematika invers roda Mecanum
   (4WD) berhasil diformulasikan dan diimplementasikan pada Arduino Uno serta
   diubah menjadi sinyal PWM, sehingga robot dapat bergerak holonomik dan
   mendekati bola dengan koreksi arah *P-controller*. Hasil pengujian
   menunjukkan galat posisi berhenti rata-rata ⟨…⟩ cm dan *drift* saat *strafe*
   berkurang dari ⟨…⟩ cm (tanpa IMU) menjadi ⟨…⟩ cm (dengan koreksi IMU).

3. **(Menjawab rumusan masalah 3 — intake & sistem.)** Mekanisme *intake*
   berupa gripper cetak 3D berbahan TPU yang digerakkan servo berhasil dibangun
   dan diuji, dengan tingkat keberhasilan cengkeram ⟨…⟩ % dan waktu ⟨…⟩ s per
   bola. Pada tingkat sistem terintegrasi, robot mampu mengumpulkan bola dengan
   tingkat keberhasilan *clear* lapangan ⟨…⟩ % dalam waktu ⟨…⟩ s untuk ⟨N⟩ bola,
   didukung arsitektur kendali *finite state machine* dan fitur keselamatan
   (*watchdog* dan *heartbeat*) yang menjaga keandalan operasi.

## 5.2 Saran

Untuk pengembangan selanjutnya, disarankan hal-hal berikut.

1. **Transport video berlatensi rendah.** Mengganti/menambah *streaming*
   MJPEG-over-HTTP dengan protokol berlatensi lebih rendah (mis. UDP atau WebRTC)
   untuk menekan latensi *end-to-end* dan memungkinkan navigasi yang lebih agresif.
2. **Estimasi heading yang lebih stabil.** Menerapkan *complementary filter*
   atau fusi sensor (giroskop + akselerometer/magnetometer) untuk mengurangi
   *drift* dibanding integrasi giroskop tunggal.
3. **Kendali roda tertutup (*closed-loop*).** Menambahkan *encoder* roda agar
   kecepatan motor terkendali secara *closed-loop*, sehingga akurasi navigasi
   dan *odometry* meningkat dan selip Mecanum dapat dikompensasi.
4. **Pelacakan kamera aktif.** Menambahkan dudukan *pan-tilt* dengan kendali PID
   agar kamera dapat melacak bola secara proaktif dan memperluas jangkauan
   deteksi.
5. **Deteksi berbasis machine learning secara daring.** Bila perangkat keras
   memadai, mengintegrasikan YOLOv8 sebagai detektor daring untuk kondisi yang
   lebih kompleks (bola banyak, warna beragam, oklusi), serta memperbesar dan
   memperkaya dataset pelatihan.
6. **Navigasi holonomik penuh.** Memanfaatkan kemampuan *strafe* Mecanum pada
   mode otonom (tidak hanya maju + rotasi) untuk pendekatan bola yang lebih
   efisien.
7. **Perluasan pengujian.** Menguji pada arena lebih besar, jenis lantai
   beragam, dan jumlah bola lebih banyak untuk menilai skalabilitas sistem.

> **(opsional — panduan pemangkasan saat bimbingan.)** Butir 1–3 (transport
> latensi rendah, estimasi *heading* stabil, kendali roda tertutup) paling erat
> menaut ke keterbatasan yang teridentifikasi di Subbab 4.6.4, sehingga paling
> layak dipertahankan. Butir 4–7 bersifat pengembangan lanjutan dan dapat
> dipangkas atau digabung bila dosen menilai daftar terlalu panjang. Jumlah
> saran lazimnya diselaraskan dengan jumlah keterbatasan yang benar-benar
> muncul pada hasil pengujian.
