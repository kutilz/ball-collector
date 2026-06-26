# 🤖 Arduino Uno - Kontroler Robot Pengumpul Bola

Firmware utama yang mengendalikan 4 motor mecanum, servo pengumpul, dan sensor gyro MPU6050.

---

## 📋 Daftar Komponen

| Komponen | Jumlah | Keterangan |
|----------|--------|------------|
| Arduino Uno R3 | 1 | Mikrokontroler utama |
| DRV8833 Motor Driver | 2 | Driver H-bridge dual |
| Motor DC + Roda Mecanum | 4 | Motor N20/GA12 atau sejenisnya |
| MPU6050 | 1 | Sensor gyroscope/accelerometer |
| Servo SG90/MG90S | 1 | Mekanisme pengumpul bola |
| ESP32-CAM | 1 | Modul kamera (lihat folder esp32cam/) |

---

## 🔌 Diagram Koneksi (Wiring)

### Pin Arduino Uno

```
                    ARDUINO UNO
              ┌─────────────────────┐
              │  [USB]              │
              │                     │
   UART TX ←──┤ D0 (TX)    D13 ├── LED Indikator (opsional)
   UART RX ──→┤ D1 (RX)    D12 ├──→ DRV8833 #2: Motor RR DIR
  Servo    ←──┤ D2          D11~├──→ DRV8833 #2: Motor RR PWM
  FL PWM   ──→┤ D3~         D10~├── (JANGAN PAKAI - Timer1/Servo)
  FL DIR   ──→┤ D4          D9~ ├── (JANGAN PAKAI - Timer1/Servo)
  FR PWM   ──→┤ D5~         D8  ├──→ DRV8833 #2: Motor RL DIR
  RL PWM   ──→┤ D6~         D7  ├──→ DRV8833 #1: Motor FR DIR
              │              D6~├── (sudah dipakai di atas)
              │                     │
  MPU SDA  ←─→┤ A4 (SDA)    5V  ├── VCC MPU6050, VCC DRV8833 Logic
  MPU SCL  ──→┤ A5 (SCL)    GND ├── GND Bersama
  (kosong)    ┤ A0           VIN ├── 
  (kosong)    ┤ A1               │
  (kosong)    ┤ A2               │
  (kosong)    ┤ A3               │
              └─────────────────────┘

~ = Pin PWM
```

### Koneksi DRV8833 #1 (Motor Depan)

```
DRV8833 #1              Arduino Uno
┌──────────────┐
│ AIN1 ←───────┼─── D3 (PWM) → Motor FL Kecepatan
│ AIN2 ←───────┼─── D4        → Motor FL Arah
│ BIN1 ←───────┼─── D5 (PWM) → Motor FR Kecepatan
│ BIN2 ←───────┼─── D7        → Motor FR Arah
│              │
│ AOUT1 ──→ Motor FL (+)
│ AOUT2 ──→ Motor FL (-)
│ BOUT1 ──→ Motor FR (+)
│ BOUT2 ──→ Motor FR (-)
│              │
│ VCC ←────────┼─── 5V (logic)
│ GND ←────────┼─── GND
│ VM  ←────────┼─── Baterai Motor (+) (6-12V)
│ GND ←────────┼─── Baterai Motor (-)
└──────────────┘
```

### Koneksi DRV8833 #2 (Motor Belakang)

```
DRV8833 #2              Arduino Uno
┌──────────────┐
│ AIN1 ←───────┼─── D6 (PWM) → Motor RL Kecepatan
│ AIN2 ←───────┼─── D8        → Motor RL Arah
│ BIN1 ←───────┼─── D11 (PWM) → Motor RR Kecepatan
│ BIN2 ←───────┼─── D12        → Motor RR Arah
│              │
│ AOUT1 ──→ Motor RL (+)
│ AOUT2 ──→ Motor RL (-)
│ BOUT1 ──→ Motor RR (+)
│ BOUT2 ──→ Motor RR (-)
│              │
│ VCC ←────────┼─── 5V (logic)
│ GND ←────────┼─── GND
│ VM  ←────────┼─── Baterai Motor (+) (6-12V)
│ GND ←────────┼─── Baterai Motor (-)
└──────────────┘
```

### Koneksi MPU6050

```
MPU6050          Arduino Uno
┌────────┐
│ VCC ───┼───→ 5V (atau 3.3V jika modul tanpa regulator)
│ GND ───┼───→ GND
│ SDA ───┼───→ A4 (SDA)
│ SCL ───┼───→ A5 (SCL)
│ INT    │    (tidak digunakan)
└────────┘
```

### Koneksi UART ke ESP32-CAM

```
Arduino Uno        ESP32-CAM
┌─────────┐      ┌─────────┐
│ TX (D1) ├─────→┤ RX (GPIO 3)
│ RX (D0) ├←─────┤ TX (GPIO 1)
│ GND     ├──────┤ GND
└─────────┘      └─────────┘

⚠️ PENTING: Gunakan voltage divider (5V → 3.3V) pada jalur
Arduino TX → ESP32 RX untuk melindungi pin ESP32!

  Arduino TX (D1) ───[1kΩ]───┬───→ ESP32 RX (GPIO 3)
                              │
                           [2kΩ]
                              │
                             GND
```

### Koneksi Servo

```
Servo SG90       Arduino Uno
┌─────────┐
│ Signal ──┼───→ D2
│ VCC    ──┼───→ 5V (atau power supply terpisah jika servo besar)
│ GND    ──┼───→ GND
└─────────┘
```

---

## 📦 Software yang Dibutuhkan

### Arduino IDE
- **Versi**: 2.x (disarankan) atau 1.8.x
- **Download**: https://www.arduino.cc/en/software

### Board Package
- **Arduino AVR Boards** (biasanya sudah terinstall default)
- Cek di: *Tools → Board → Arduino AVR Boards → Arduino Uno*

### Library yang Dibutuhkan
| Library | Sumber | Keterangan |
|---------|--------|------------|
| Wire.h | Built-in | Komunikasi I2C untuk MPU6050 |
| Servo.h | Built-in | Kontrol servo motor |

> ✅ **Tidak perlu install library tambahan!** Semua library sudah built-in di Arduino IDE.

---

## 📤 Cara Upload Firmware

### Langkah 1: Persiapan
1. Buka Arduino IDE
2. Hubungkan Arduino Uno ke komputer via kabel USB
3. **LEPASKAN kabel UART dari pin D0/D1** (TX/RX) sebelum upload!
   - Pin 0 dan 1 dipakai bersama untuk USB dan UART
   - Jika kabel ESP32-CAM masih terhubung, upload akan gagal

### Langkah 2: Konfigurasi Arduino IDE
1. Pilih board: *Tools → Board → Arduino AVR Boards → Arduino Uno*
2. Pilih port: *Tools → Port → COMx (Arduino Uno)*
3. Pastikan programmer: *Tools → Programmer → AVRISP mkII*

### Langkah 3: Buka dan Edit Kode
1. Buka file `robot_controller/robot_controller.ino`
2. Periksa konfigurasi `FLIP_xx` jika ada motor yang berputar terbalik
3. Sesuaikan `DEBUG` (1=aktif, 0=nonaktif)

### Langkah 4: Upload
1. Klik tombol **Upload** (→) atau tekan `Ctrl+U`
2. Tunggu hingga muncul "Done uploading."
3. Buka Serial Monitor (Ctrl+Shift+M) dengan baud rate **115200**
4. Anda harus melihat pesan "=== Robot Pengumpul Bola ==="

### Langkah 5: Pasang Kembali UART
1. Setelah upload berhasil, pasang kembali kabel UART ke ESP32-CAM
2. Pastikan koneksi: Arduino TX→ESP32 RX, Arduino RX→ESP32 TX

---

## 🔧 Protokol Serial

### Perintah Masuk (dari ESP32-CAM)
| Perintah | Format | Contoh | Keterangan |
|----------|--------|--------|------------|
| Gerak | `CMD:vx,vy,omega\n` | `CMD:100,0,0\n` | vx=maju/mundur, vy=kiri/kanan, omega=putar |
| Servo | `SERVO:sudut\n` | `SERVO:90\n` | Sudut 0-180 derajat |
| Collect | `COLLECT\n` | `COLLECT\n` | Jalankan sekuens pengumpulan |

### Data Keluar (ke ESP32-CAM)
| Data | Format | Contoh | Keterangan |
|------|--------|--------|------------|
| Telemetri | `TEL:heading,vbat\n` | `TEL:45.2,0\n` | heading=derajat, vbat=placeholder |

### Rentang Nilai
- `vx`: -255 (mundur) sampai 255 (maju)
- `vy`: -255 (kanan) sampai 255 (kiri)
- `omega`: -255 (putar kanan) sampai 255 (putar kiri)

---

## 🐛 Troubleshooting

### Upload Gagal
- ❌ **"avrdude: stk500_getsync(): not in sync"**
  - Pastikan kabel UART (pin 0,1) sudah DILEPAS saat upload
  - Cek port COM yang benar di Tools → Port
  - Coba tekan tombol reset di Arduino sebelum upload

- ❌ **"Board not found"**
  - Pasang driver CH340 jika Arduino clone (unduh dari ch340 driver website)
  - Coba kabel USB lain (beberapa kabel hanya charge, tidak ada data)

### Motor Tidak Bergerak
- 🔍 Cek tegangan baterai motor (6-12V)
- 🔍 Cek koneksi kabel DRV8833
- 🔍 Pastikan pin PWM dan DIR benar
- 🔍 Kirim perintah test manual via Serial Monitor: `CMD:200,0,0`

### Motor Berputar Arah Salah
- 🔧 Ubah define `FLIP_xx` di kode:
  ```cpp
  #define FLIP_FL true   // Balik arah motor FL
  ```
- 🔧 Atau tukar kabel motor di terminal DRV8833

### Robot Belok Saat Maju Lurus
- 🔍 Ini normal jika motor tidak identik → gyro heading correction akan membantu
- 🔧 Kalibrasi dead zone gyro (default 1.0°/s)
- 🔧 Cek roda mecanum terpasang dengan pola yang benar:
  ```
  Dilihat dari atas:
  FL: /    FR: \
  RL: \    RR: /
  (roller membentuk huruf X)
  ```

### MPU6050 Tidak Terdeteksi
- 🔍 Cek koneksi I2C: SDA=A4, SCL=A5
- 🔍 Jalankan I2C scanner untuk verifikasi alamat (harus 0x68)
- 🔍 Cek apakah modul mendapat power 5V/3.3V

### Heading Drift (Bergeser Sendiri)
- Ini normal untuk integrasi gyro tanpa filter
- 🔧 Tingkatkan dead zone di kode jika perlu
- 🔧 Pastikan robot diam saat pertama kali dinyalakan (kalibrasi awal)

---

## ⚠️ Catatan Penting

1. **Timer1 dan Servo**: Library Servo.h menggunakan Timer1 yang menonaktifkan PWM di pin 9 dan 10. Jangan gunakan pin tersebut untuk motor.

2. **Voltage Divider**: ESP32-CAM beroperasi di 3.3V. Gunakan voltage divider pada jalur Arduino TX → ESP32 RX.

3. **Power Supply Motor**: Jangan catu motor dari pin 5V Arduino! Gunakan power supply/baterai terpisah. Hubungkan GND bersama.

4. **Urutan Nyala**: Nyalakan Arduino dulu, baru ESP32-CAM. Arduino akan menunggu perintah dari serial.
