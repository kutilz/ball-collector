# 📷 ESP32-CAM - Modul Kamera Robot Pengumpul Bola

Firmware ESP32-CAM yang menyediakan streaming video MJPEG, web control, dan jembatan UART ke Arduino Uno.

---

## 📋 Daftar Komponen

| Komponen                 | Jumlah     | Keterangan            |
| ------------------------ | ---------- | --------------------- |
| ESP32-CAM (AI-Thinker)   | 1          | Modul kamera + WiFi   |
| FTDI/CH340 USB-to-Serial | 1          | Untuk upload firmware |
| Jumper wire              | Secukupnya | Untuk koneksi         |

---

## 🔌 Diagram Koneksi (Wiring)

### Koneksi Upload Firmware (FTDI → ESP32-CAM)

```
FTDI Programmer        ESP32-CAM
┌──────────────┐     ┌──────────────────────┐
│ 5V  ─────────┼────→┤ 5V                   │
│ GND ─────────┼────→┤ GND                  │
│ TX  ─────────┼────→┤ U0R (GPIO 3 / RX)    │
│ RX  ─────────┼←───┤ U0T (GPIO 1 / TX)    │
└──────────────┘     │                      │
                      │ GPIO 0 ──→ GND       │ ← HUBUNGKAN SAAT UPLOAD!
                      │ (Lepas setelah upload)│
                      └──────────────────────┘

⚠️ PENTING:
- GPIO 0 HARUS dihubungkan ke GND saat upload (mode flash)
- GPIO 0 HARUS DILEPAS dari GND saat running normal
- Tekan tombol RST setelah menghubungkan GPIO 0 ke GND
```

### Koneksi Operasional (ESP32-CAM → Arduino Uno)

```
ESP32-CAM              Arduino Uno
┌──────────────┐     ┌──────────────┐
│ U0T (GPIO 1) ├────→┤ RX (D0)      │
│ U0R (GPIO 3) ├←─┬──┤ TX (D1)      │
│              │   │  │              │
│ GND          ├───┼──┤ GND          │
└──────────────┘   │  └──────────────┘
                    │
              Voltage Divider:
              Arduino TX (5V) ──[1kΩ]──┬──→ ESP32 RX (3.3V)
                                        │
                                     [2kΩ]
                                        │
                                       GND

⚠️ Voltage divider WAJIB! ESP32 pin RX tidak toleran 5V.
```

### Diagram Pin ESP32-CAM (AI-Thinker)

```
        ┌────────────────────────────────┐
        │         [Kamera OV2640]        │
        │         ┌──────────┐           │
        │         │          │           │
        │         └──────────┘           │
        │                                │
  5V ───┤ 5V                     GPIO 0  ├─── Boot Mode (GND=flash)
 GND ───┤ GND                   GPIO 2  ├─── (internal, LED merah)
GPIO16──┤ IO16                   GPIO 4  ├─── LED Flash (putih terang)
GPIO 0 ─┤ IO0                   GPIO 12 ├─── (HS2_DATA2)
GPIO 2 ─┤ IO2                   GPIO 13 ├─── (HS2_DATA3)
GPIO14──┤ IO14                  GPIO 15 ├─── (HS2_CMD)
GPIO15──┤ IO15                  GPIO 14 ├─── (HS2_CLK)
GPIO13──┤ IO13                         │
        │                                │
  3.3V──┤ 3V3        U0R (GPIO 3 / RX) ├─── Serial RX ← Arduino TX
 GND ───┤ GND        U0T (GPIO 1 / TX) ├─── Serial TX → Arduino RX
        │                                │
        └────────────────────────────────┘

Pin yang dipakai kamera (JANGAN GUNAKAN):
GPIO 0, 2, 4*, 5, 12, 13, 14, 15, 18, 19, 21, 22, 23, 25, 26, 27, 32, 34, 35, 36, 39

*GPIO 4 = LED Flash, bisa dipakai sebagai output LED
```

---

## 📦 Software yang Dibutuhkan

### Arduino IDE

- **Versi**: 2.x (disarankan) atau 1.8.x
- **Download**: https://www.arduino.cc/en/software

### Board Package ESP32

1. Buka Arduino IDE
2. Pergi ke *File → Preferences*
3. Di kolom **"Additional Board Manager URLs"**, tambahkan:
   
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
4. Klik **OK**
5. Pergi ke *Tools → Board → Boards Manager*
6. Cari **"esp32"** oleh Espressif Systems
7. Install versi **terbaru** (disarankan 2.x atau 3.x)
8. Tunggu instalasi selesai

### Library yang Dibutuhkan

| Library      | Sumber                         | Keterangan           |
| ------------ | ------------------------------ | -------------------- |
| esp_camera.h | Built-in (ESP32 board package) | Driver kamera OV2640 |
| WiFi.h       | Built-in (ESP32 board package) | Koneksi WiFi         |
| WebServer.h  | Built-in (ESP32 board package) | HTTP server          |

> ✅ **Tidak perlu install library tambahan!** Semua sudah termasuk dalam ESP32 board package.

---

## 📤 Cara Upload Firmware

### Langkah 1: Konfigurasi WiFi

1. Buka file `ball_cam/ball_cam.ino`
2. Ubah SSID dan password WiFi di baris:
   
   ```cpp
   #define WIFI_SSID     "NamaWiFi_Anda"
   #define WIFI_PASSWORD "PasswordWiFi_Anda"
   ```
3. Simpan file

### Langkah 2: Koneksi Hardware untuk Upload

1. Hubungkan FTDI/CH340 ke ESP32-CAM sesuai diagram di atas
2. **HUBUNGKAN GPIO 0 ke GND** (mode flash/download)
3. Tekan tombol **RST** pada modul ESP32-CAM
4. Colok FTDI/CH340 ke USB komputer

### Langkah 3: Konfigurasi Arduino IDE

1. Pilih board: *Tools → Board → ESP32 Arduino → AI Thinker ESP32-CAM*
2. Pilih port: *Tools → Port → COMx*
3. Konfigurasi lainnya:
   
   | Setting          | Nilai                            |
   | ---------------- | -------------------------------- |
   | CPU Frequency    | 240MHz (WiFi/BT)                 |
   | Flash Frequency  | 80MHz                            |
   | Flash Mode       | QIO                              |
   | Partition Scheme | Huge APP (3MB No OTA/1MB SPIFFS) |
   | Upload Speed     | 115200                           |

### Langkah 4: Upload

1. Klik tombol **Upload** (→) atau tekan `Ctrl+U`
2. Tunggu hingga muncul "Connecting........" di output
   - Jika tidak konek, tekan tombol **RST** pada ESP32-CAM
3. Tunggu hingga proses upload selesai ("Done uploading.")

### Langkah 5: Jalankan

1. **LEPASKAN GPIO 0 dari GND** (mode running normal)
2. Tekan tombol **RST** untuk restart
3. Buka Serial Monitor (115200 baud)
4. Anda akan melihat:
   
   ```
   === ESP32-CAM Robot Pengumpul Bola ===
   Kamera berhasil diinisialisasi.
   Menghubungkan ke WiFi: NamaWiFi_Anda
   WiFi terhubung!
   Alamat IP: 192.168.x.x
   Web server aktif!
   ```
5. Buka alamat IP tersebut di browser

### Langkah 6: Pasang ke Robot

1. Lepaskan FTDI/CH340
2. Hubungkan ESP32-CAM ke Arduino Uno via UART (lihat diagram koneksi operasional)
3. Catu daya ESP32-CAM dari 5V Arduino atau power supply terpisah

---

## 🌐 Endpoint Web Server

| Endpoint                 | Metode | Keterangan                                          |
| ------------------------ | ------ | --------------------------------------------------- |
| `/`                      | GET    | Halaman utama dengan live stream dan tombol kontrol |
| `/stream`                | GET    | MJPEG streaming video langsung                      |
| `/cmd?q=CMD:vx,vy,omega` | GET    | Kirim perintah gerak ke Arduino                     |
| `/cmd?q=SERVO:sudut`     | GET    | Atur posisi servo (0-180)                           |
| `/cmd?q=COLLECT`         | GET    | Jalankan sekuens pengumpulan bola                   |
| `/status`                | GET    | Status sistem dalam format JSON                     |
| `/led?state=on`          | GET    | Nyalakan LED flash                                  |
| `/led?state=off`         | GET    | Matikan LED flash                                   |

### Contoh Penggunaan via Browser atau curl

```bash
# Maju
curl "http://192.168.1.100/cmd?q=CMD:100,0,0"

# Berhenti
curl "http://192.168.1.100/cmd?q=CMD:0,0,0"

# Geser ke kiri
curl "http://192.168.1.100/cmd?q=CMD:0,100,0"

# Putar di tempat
curl "http://192.168.1.100/cmd?q=CMD:0,0,150"

# Kumpulkan bola
curl "http://192.168.1.100/cmd?q=COLLECT"

# Cek status
curl "http://192.168.1.100/status"
```

### Format Response /status

```json
{
  "ip": "192.168.1.100",
  "rssi": -45,
  "uptime_sec": 3600,
  "fps": 15.2,
  "total_frames": 54720,
  "free_heap": 120000,
  "wifi_ssid": "NamaWiFi",
  "flash_led": false,
  "arduino_telemetry": "TEL:45.2,0"
}
```

---

## 🐛 Troubleshooting

### Upload Gagal

- ❌ **"Failed to connect to ESP32: Timed out"**
  
  - Pastikan GPIO 0 terhubung ke GND
  - Tekan tombol RST saat muncul "Connecting..."
  - Cek koneksi FTDI: TX→RX, RX→TX (cross)
  - Coba kabel USB lain

- ❌ **"A serial exception error occurred"**
  
  - Port COM sedang dipakai program lain → tutup Serial Monitor dulu
  - Coba port USB lain

- ❌ **"Sketch too large"**
  
  - Ubah Partition Scheme ke "Huge APP (3MB No OTA/1MB SPIFFS)"

### Kamera Gagal

- ❌ **"GAGAL inisialisasi kamera! Error: 0x20001"**
  
  - Ribbon cable kamera longgar → pasang ulang dengan hati-hati
  - Coba reset modul (cabut-pasang power)

- ❌ **"GAGAL ambil frame dari kamera!"**
  
  - Kurang daya → gunakan power supply 5V 1A minimum
  - Coba kurangi resolusi ke FRAMESIZE_QQVGA (160x120)

### WiFi Gagal

- ❌ **"Timeout koneksi WiFi!"**
  
  - Cek SSID dan password (case-sensitive!)
  - Pastikan router menyala dan dalam jangkauan
  - ESP32-CAM hanya support WiFi 2.4GHz (BUKAN 5GHz)
  - Coba dekatkan modul ke router saat testing

- ❌ **WiFi sering disconnect**
  
  - Antena ESP32-CAM kecil → dekatkan ke router
  - Jika ada antena eksternal (konektor IPEX), pasang dan pindahkan jumper ke posisi antena eksternal
  - Kurangi `CAM_JPEG_QUALITY` ke 15-20 untuk bandwidth lebih rendah

### Streaming Lambat / Putus-putus

- 🔧 Kurangi resolusi: ubah `FRAMESIZE_QVGA` ke `FRAMESIZE_QQVGA`
- 🔧 Naikkan JPEG quality number (15-20) = ukuran file lebih kecil
- 🔧 Pastikan ESP32-CAM mendapat daya 5V stabil (min 500mA)
- 🔧 Jangan buka banyak tab stream bersamaan

### UART ke Arduino Tidak Berfungsi

- 🔍 Pastikan kabel UART tidak tertukar (TX↔RX cross connection)
- 🔍 Cek voltage divider pada jalur Arduino TX → ESP32 RX
- 🔍 Baud rate harus sama: 115200 di kedua sisi
- 🔍 GND Arduino dan GND ESP32-CAM HARUS terhubung
- 🔍 **Lepas kabel UART saat upload firmware** (baik ke Arduino maupun ESP32-CAM)

---

## ⚠️ Catatan Penting

1. **GPIO 0 untuk Boot Mode**:
   
   - GND = Flash/Download mode (untuk upload firmware)
   - Floating/HIGH = Normal run mode
   - SELALU lepaskan GPIO 0 dari GND setelah upload!

2. **LED Flash (GPIO 4)**:
   
   - LED putih sangat terang! Hati-hati mata.
   - Juga dipakai internal untuk HS2_DATA1. Jika ada masalah SD card, matikan LED.

3. **Power Supply**:
   
   - ESP32-CAM butuh minimum 500mA pada 5V
   - Saat streaming + WiFi aktif, konsumsi bisa 300-400mA
   - Power dari FTDI biasanya cukup untuk test, tapi untuk operasi gunakan power supply terpisah

4. **Pin Terbatas**:
   
   - Hampir semua GPIO dipakai kamera. Hanya GPIO 1, 3 (UART) dan GPIO 4 (LED) yang bisa dipakai.
   - Jangan gunakan pin kamera untuk fungsi lain!

5. **WiFi 2.4GHz Only**:
   
   - ESP32 TIDAK mendukung WiFi 5GHz
   - Pastikan router Anda punya band 2.4GHz yang aktif
