// ============================================================================
// ROBOT PENGUMPUL BOLA - FIRMWARE ARDUINO UNO
// ============================================================================
// Deskripsi : Kontroler utama robot mecanum 4WD dengan pengumpul bola
// Hardware  : Arduino Uno, 2x DRV8833, MPU6050, Servo, ESP32-CAM (UART)
// Protokol  : Serial 115200 baud, format "CMD:vx,vy,omega\n"
// Tanggal   : 2026-06-26
// ============================================================================

#include <Wire.h>
#include <Servo.h>

// === KONFIGURASI DEBUG ===
// Set ke 0 untuk nonaktifkan pesan debug (hemat memori & bandwidth serial)
#define DEBUG 1

#if DEBUG
  #define DBG_PRINT(x)   Serial.print(x)
  #define DBG_PRINTLN(x) Serial.println(x)
#else
  #define DBG_PRINT(x)
  #define DBG_PRINTLN(x)
#endif

// ============================================================================
// PIN MAPPING
// ============================================================================
// Strategi pin:
//   - Servo menggunakan Timer1, yang menonaktifkan PWM di pin 9 dan 10.
//   - Sisa pin PWM: 3, 5, 6, 11 (dari Timer0 dan Timer2).
//   - Setiap motor butuh 1 pin PWM (kecepatan) + 1 pin digital (arah).
//
// Motor FL (Depan-Kiri) : PWM=3,  DIR=4
// Motor FR (Depan-Kanan): PWM=5,  DIR=7
// Motor RL (Belakang-Kiri): PWM=6,  DIR=8
// Motor RR (Belakang-Kanan): PWM=11, DIR=12
// Servo pengumpul: pin 2
// MPU6050: SDA=A4, SCL=A5 (I2C hardware)
// Serial UART ke ESP32-CAM: pin 0 (RX), pin 1 (TX)
// Tersedia: 13 (LED), A0, A1, A2, A3

// --- Motor Depan-Kiri (FL) ---
#define PIN_FL_PWM  3
#define PIN_FL_DIR  4

// --- Motor Depan-Kanan (FR) ---
#define PIN_FR_PWM  5
#define PIN_FR_DIR  7

// --- Motor Belakang-Kiri (RL) ---
#define PIN_RL_PWM  6
#define PIN_RL_DIR  8

// --- Motor Belakang-Kanan (RR) ---
#define PIN_RR_PWM  11
#define PIN_RR_DIR  12

// --- Servo Pengumpul ---
#define PIN_SERVO   2

// --- LED Indikator ---
#define PIN_LED     13

// ============================================================================
// KONFIGURASI ARAH MOTOR (FLIP)
// ============================================================================
// Ubah ke 'true' jika motor terpasang terbalik.
// Ini membalik arah putar tanpa perlu tukar kabel.
#define FLIP_FL false
#define FLIP_FR false
#define FLIP_RL false
#define FLIP_RR false

// ============================================================================
// KONSTANTA
// ============================================================================
#define SERIAL_BAUD     115200

// Alamat I2C MPU6050
#define MPU6050_ADDR    0x68
#define MPU6050_PWR_MGMT  0x6B
#define MPU6050_GYRO_Z_H  0x47  // Register gyro sumbu Z (high byte)
#define MPU6050_GYRO_Z_L  0x48  // Register gyro sumbu Z (low byte)

// Sensitivitas gyro: ±250°/s → 131 LSB/°/s (konfigurasi default)
#define GYRO_SENSITIVITY 131.0f

// Interval telemetri (ms)
#define TELEMETRY_INTERVAL 100

// Timeout watchdog motor (ms) - jika tidak ada perintah, motor berhenti
#define WATCHDOG_TIMEOUT   500

// Ukuran buffer serial
#define SERIAL_BUF_SIZE    64

// Konfigurasi servo pengumpul
#define SERVO_MIN_ANGLE    30   // Sudut minimum sweep
#define SERVO_MAX_ANGLE    150  // Sudut maksimum sweep
#define SERVO_CENTER       90   // Posisi tengah/istirahat
#define SERVO_COLLECT_DELAY 300 // Delay antar langkah sweep (ms)
#define SERVO_COLLECT_STEPS 3   // Jumlah siklus sweep saat COLLECT

// ============================================================================
// VARIABEL GLOBAL
// ============================================================================
Servo servoPengumpul;

// --- Buffer serial ---
char serialBuf[SERIAL_BUF_SIZE];
uint8_t serialIdx = 0;

// --- Timing ---
unsigned long lastCmdTime     = 0;  // Waktu perintah terakhir diterima
unsigned long lastTelemetry   = 0;  // Waktu telemetri terakhir dikirim
unsigned long lastGyroRead    = 0;  // Waktu pembacaan gyro terakhir

// --- Heading dari gyro ---
float heading = 0.0f;              // Heading kumulatif dalam derajat

// --- Status motor saat ini ---
int16_t currentVx    = 0;
int16_t currentVy    = 0;
int16_t currentOmega = 0;

// --- Flag untuk sekuens collect ---
bool collectRunning = false;

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  // Inisialisasi serial untuk komunikasi dengan ESP32-CAM
  Serial.begin(SERIAL_BAUD);

  DBG_PRINTLN(F("=== Robot Pengumpul Bola ==="));
  DBG_PRINTLN(F("Inisialisasi dimulai..."));

  // --- Konfigurasi pin motor ---
  pinMode(PIN_FL_PWM, OUTPUT);
  pinMode(PIN_FL_DIR, OUTPUT);
  pinMode(PIN_FR_PWM, OUTPUT);
  pinMode(PIN_FR_DIR, OUTPUT);
  pinMode(PIN_RL_PWM, OUTPUT);
  pinMode(PIN_RL_DIR, OUTPUT);
  pinMode(PIN_RR_PWM, OUTPUT);
  pinMode(PIN_RR_DIR, OUTPUT);

  // Pastikan semua motor mati saat startup
  stopAllMotors();

  // --- LED indikator ---
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  // --- Inisialisasi servo ---
  servoPengumpul.attach(PIN_SERVO);
  servoPengumpul.write(SERVO_CENTER);
  DBG_PRINTLN(F("Servo terpasang di pin 2"));

  // --- Inisialisasi MPU6050 via I2C mentah ---
  Wire.begin();
  initMPU6050();

  // --- Tandai waktu awal ---
  lastCmdTime   = millis();
  lastTelemetry = millis();
  lastGyroRead  = millis();

  // Kedipkan LED tanda siap
  for (uint8_t i = 0; i < 3; i++) {
    digitalWrite(PIN_LED, HIGH);
    delay(100);
    digitalWrite(PIN_LED, LOW);
    delay(100);
  }

  DBG_PRINTLN(F("Inisialisasi selesai. Menunggu perintah..."));
}

// ============================================================================
// LOOP UTAMA
// ============================================================================
void loop() {
  unsigned long now = millis();

  // --- 1. Baca data serial masuk ---
  bacaSerial();

  // --- 2. Update gyro heading ---
  updateGyro(now);

  // --- 3. Kirim telemetri berkala ---
  if (now - lastTelemetry >= TELEMETRY_INTERVAL) {
    kirimTelemetri();
    lastTelemetry = now;
  }

  // --- 4. Watchdog: hentikan motor jika tidak ada perintah ---
  if (now - lastCmdTime >= WATCHDOG_TIMEOUT) {
    if (currentVx != 0 || currentVy != 0 || currentOmega != 0) {
      DBG_PRINTLN(F("WATCHDOG: Timeout, motor dihentikan!"));
      currentVx = 0;
      currentVy = 0;
      currentOmega = 0;
      stopAllMotors();
    }
  }
}

// ============================================================================
// PEMBACAAN SERIAL
// ============================================================================
// Membaca karakter dari serial dan memproses baris lengkap (diakhiri '\n').
void bacaSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (serialIdx > 0) {
        serialBuf[serialIdx] = '\0';  // Null-terminate string
        prosesPerintah(serialBuf);
        serialIdx = 0;
      }
    } else {
      if (serialIdx < SERIAL_BUF_SIZE - 1) {
        serialBuf[serialIdx++] = c;
      } else {
        // Buffer penuh, reset (perintah terlalu panjang)
        DBG_PRINTLN(F("PERINGATAN: Buffer serial penuh, reset"));
        serialIdx = 0;
      }
    }
  }
}

// ============================================================================
// PROSES PERINTAH
// ============================================================================
// Format yang didukung:
//   CMD:vx,vy,omega   → gerakkan robot (nilai -255 s/d 255)
//   SERVO:sudut        → atur posisi servo (0-180)
//   COLLECT            → jalankan sekuens pengumpulan bola
void prosesPerintah(const char* cmd) {
  lastCmdTime = millis();  // Reset watchdog timer

  // --- Perintah gerak: CMD:vx,vy,omega ---
  if (strncmp(cmd, "CMD:", 4) == 0) {
    int vx = 0, vy = 0, omega = 0;

    // Parse tiga nilai integer dipisahkan koma
    const char* ptr = cmd + 4;
    vx = atoi(ptr);

    ptr = strchr(ptr, ',');
    if (ptr) {
      ptr++;
      vy = atoi(ptr);
      ptr = strchr(ptr, ',');
      if (ptr) {
        ptr++;
        omega = atoi(ptr);
      }
    }

    // Batasi range
    vx    = constrain(vx,    -255, 255);
    vy    = constrain(vy,    -255, 255);
    omega = constrain(omega, -255, 255);

    currentVx    = vx;
    currentVy    = vy;
    currentOmega = omega;

    DBG_PRINT(F("CMD diterima: vx="));
    DBG_PRINT(vx);
    DBG_PRINT(F(" vy="));
    DBG_PRINT(vy);
    DBG_PRINT(F(" omega="));
    DBG_PRINTLN(omega);

    // Hitung dan terapkan kinematika mecanum
    jalankanMecanum(vx, vy, omega);
  }
  // --- Perintah servo: SERVO:sudut ---
  else if (strncmp(cmd, "SERVO:", 6) == 0) {
    int sudut = atoi(cmd + 6);
    sudut = constrain(sudut, 0, 180);

    servoPengumpul.write(sudut);

    DBG_PRINT(F("Servo diatur ke: "));
    DBG_PRINTLN(sudut);
  }
  // --- Perintah collect: COLLECT ---
  else if (strcmp(cmd, "COLLECT") == 0) {
    DBG_PRINTLN(F("Memulai sekuens pengumpulan bola..."));
    jalankanCollect();
  }
  else {
    DBG_PRINT(F("Perintah tidak dikenal: "));
    DBG_PRINTLN(cmd);
  }
}

// ============================================================================
// KINEMATIKA INVERS MECANUM
// ============================================================================
// Rumus mecanum 4-roda:
//   FL = vx + vy + omega
//   FR = vx - vy - omega
//   RL = vx - vy + omega
//   RR = vx + vy - omega
//
// Hasilnya dinormalisasi jika ada yang melebihi 255, lalu
// dipetakan ke PWM (kecepatan) + DIR (arah putar).
void jalankanMecanum(int16_t vx, int16_t vy, int16_t omega) {
  // Hitung kecepatan tiap roda (bisa negatif = mundur)
  int16_t fl = vx + vy + omega;
  int16_t fr = vx - vy - omega;
  int16_t rl = vx - vy + omega;
  int16_t rr = vx + vy - omega;

  // Normalisasi: cari nilai absolut terbesar
  int16_t maxVal = max(max(abs(fl), abs(fr)), max(abs(rl), abs(rr)));

  // Jika ada yang lebih dari 255, skalakan semua proporsional
  if (maxVal > 255) {
    fl = (int16_t)((int32_t)fl * 255 / maxVal);
    fr = (int16_t)((int32_t)fr * 255 / maxVal);
    rl = (int16_t)((int32_t)rl * 255 / maxVal);
    rr = (int16_t)((int32_t)rr * 255 / maxVal);
  }

  // Terapkan ke motor masing-masing
  setMotor(PIN_FL_PWM, PIN_FL_DIR, fl, FLIP_FL);
  setMotor(PIN_FR_PWM, PIN_FR_DIR, fr, FLIP_FR);
  setMotor(PIN_RL_PWM, PIN_RL_DIR, rl, FLIP_RL);
  setMotor(PIN_RR_PWM, PIN_RR_DIR, rr, FLIP_RR);
}

// ============================================================================
// SET MOTOR INDIVIDUAL
// ============================================================================
// Mengatur satu motor dengan nilai kecepatan bertanda (signed speed).
// Nilai positif = maju, negatif = mundur.
// Parameter 'flip' membalik arah jika motor terpasang terbalik.
void setMotor(uint8_t pinPwm, uint8_t pinDir, int16_t speed, bool flip) {
  // Terapkan flip jika perlu
  if (flip) {
    speed = -speed;
  }

  if (speed >= 0) {
    // Maju: DIR=LOW, PWM=kecepatan
    digitalWrite(pinDir, LOW);
    analogWrite(pinPwm, constrain(speed, 0, 255));
  } else {
    // Mundur: DIR=HIGH, PWM=255-|kecepatan| (inversi untuk DRV8833)
    // Catatan: Untuk DRV8833 dengan skema 1-pin PWM + 1-pin DIR,
    // DIR=HIGH berarti arah terbalik, PWM tetap magnitude.
    digitalWrite(pinDir, HIGH);
    analogWrite(pinPwm, constrain(-speed, 0, 255));
  }
}

// ============================================================================
// HENTIKAN SEMUA MOTOR
// ============================================================================
void stopAllMotors() {
  analogWrite(PIN_FL_PWM, 0);
  analogWrite(PIN_FR_PWM, 0);
  analogWrite(PIN_RL_PWM, 0);
  analogWrite(PIN_RR_PWM, 0);

  digitalWrite(PIN_FL_DIR, LOW);
  digitalWrite(PIN_FR_DIR, LOW);
  digitalWrite(PIN_RL_DIR, LOW);
  digitalWrite(PIN_RR_DIR, LOW);
}

// ============================================================================
// INISIALISASI MPU6050 (TANPA LIBRARY EKSTERNAL)
// ============================================================================
// Menggunakan Wire.h langsung untuk komunikasi I2C.
// Hanya mengaktifkan sensor dan baca gyro Z untuk heading.
void initMPU6050() {
  // Bangunkan MPU6050 dari mode sleep
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(MPU6050_PWR_MGMT);  // Register power management
  Wire.write(0x00);               // Set ke 0 = bangun dari sleep
  uint8_t error = Wire.endTransmission(true);

  if (error == 0) {
    DBG_PRINTLN(F("MPU6050 terdeteksi dan aktif."));
  } else {
    DBG_PRINT(F("GAGAL koneksi MPU6050! Error: "));
    DBG_PRINTLN(error);
  }

  // Konfigurasi gyro: ±250°/s (default, register 0x1B = 0x00)
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x1B);  // GYRO_CONFIG register
  Wire.write(0x00);  // FS_SEL=0 → ±250°/s
  Wire.endTransmission(true);

  // Konfigurasi DLPF (Digital Low Pass Filter) untuk mengurangi noise
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x1A);  // CONFIG register
  Wire.write(0x03);  // DLPF_CFG=3 → bandwidth 44Hz, delay 4.9ms
  Wire.endTransmission(true);

  DBG_PRINTLN(F("MPU6050 dikonfigurasi: ±250°/s, DLPF=44Hz"));
}

// ============================================================================
// BACA GYRO Z DAN UPDATE HEADING
// ============================================================================
// Membaca register gyro sumbu Z (yaw) dan mengintegrasikan terhadap waktu
// untuk mendapatkan heading kumulatif dalam derajat.
void updateGyro(unsigned long now) {
  // Hitung delta waktu sejak pembacaan terakhir
  unsigned long dt_ms = now - lastGyroRead;

  // Baca minimal setiap 10ms (100Hz) untuk akurasi integrasi
  if (dt_ms < 10) return;

  lastGyroRead = now;
  float dt = dt_ms / 1000.0f;  // Konversi ke detik

  // Minta 2 byte dari register gyro Z
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(MPU6050_GYRO_Z_H);  // Mulai dari register high byte
  Wire.endTransmission(false);   // Repeated start

  uint8_t bytesReceived = Wire.requestFrom((uint8_t)MPU6050_ADDR, (uint8_t)2, (uint8_t)true);

  if (bytesReceived == 2) {
    int16_t gyroZ_raw = (Wire.read() << 8) | Wire.read();

    // Konversi ke derajat per detik
    float gyroZ_dps = gyroZ_raw / GYRO_SENSITIVITY;

    // Dead zone: abaikan noise kecil (di bawah 1°/s)
    if (abs(gyroZ_dps) < 1.0f) {
      gyroZ_dps = 0.0f;
    }

    // Integrasi sederhana: heading += kecepatan_sudut × delta_waktu
    heading += gyroZ_dps * dt;

    // Normalisasi heading ke range -180 s/d 180
    while (heading > 180.0f)  heading -= 360.0f;
    while (heading < -180.0f) heading += 360.0f;
  }
}

// ============================================================================
// KIRIM TELEMETRI
// ============================================================================
// Format: "TEL:heading,vbat\n"
// heading = sudut orientasi saat ini (derajat)
// vbat = tegangan baterai (placeholder 0 untuk sekarang)
void kirimTelemetri() {
  Serial.print(F("TEL:"));
  Serial.print(heading, 1);  // 1 desimal cukup
  Serial.print(F(",0"));     // Placeholder tegangan baterai
  Serial.println();
}

// ============================================================================
// SEKUENS PENGUMPULAN BOLA
// ============================================================================
// Menggerakkan servo menyapu bolak-balik untuk mengumpulkan bola.
// Selama sekuens ini, motor tetap berjalan sesuai perintah terakhir.
void jalankanCollect() {
  collectRunning = true;
  digitalWrite(PIN_LED, HIGH);  // Nyalakan LED selama collect

  for (uint8_t siklus = 0; siklus < SERVO_COLLECT_STEPS; siklus++) {
    // Sapu ke kiri (sudut minimum)
    servoPengumpul.write(SERVO_MIN_ANGLE);
    delay(SERVO_COLLECT_DELAY);

    // Sapu ke kanan (sudut maksimum)
    servoPengumpul.write(SERVO_MAX_ANGLE);
    delay(SERVO_COLLECT_DELAY);

    // Cek apakah ada perintah baru masuk selama collect
    bacaSerial();
  }

  // Kembali ke posisi tengah
  servoPengumpul.write(SERVO_CENTER);
  delay(200);

  collectRunning = false;
  digitalWrite(PIN_LED, LOW);

  DBG_PRINTLN(F("Sekuens pengumpulan selesai."));
}
