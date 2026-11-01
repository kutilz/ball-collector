// ============================================================================
// ROBOT PENGUMPUL BOLA - FIRMWARE ARDUINO UNO
// ============================================================================
// Deskripsi : Kontroler utama robot mecanum 4WD dengan pengumpul bola
// Hardware  : Arduino Uno, 2x TB6612FNG, MPU6050, Servo, ESP32-CAM (UART)
// Protokol  : Serial 115200 baud, format "CMD:vx,vy,omega\n"
// Tanggal   : 2026-06-26
// ============================================================================

#include <Wire.h>
#include <Servo.h>
#include <avr/wdt.h>
#include <EEPROM.h>

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
//   - Setiap motor butuh 1 pin PWM (kecepatan) + 2 pin digital (IN1/IN2 arah).
//   - STBY kedua TB6612 di pin 9 (digital saja, PWM-nya dipakai Servo).
//
// Motor FL (Depan-Kiri)   : TB#1 A  PWM=3,  IN1=4,  IN2=A0
// Motor FR (Depan-Kanan)  : TB#1 B  PWM=5,  IN1=7,  IN2=A1
// Motor RL (Belakang-Kiri): TB#2 A  PWM=6,  IN1=8,  IN2=A2
// Motor RR (Belakang-Kanan): TB#2 B PWM=11, IN1=12, IN2=A3
// Servo pengumpul: pin 2
// MPU6050: SDA=A4, SCL=A5 (I2C hardware)
// Serial UART ke ESP32-CAM: pin 0 (RX), pin 1 (TX)
// Tersedia: 10

// --- Motor Depan-Kiri (FL) ---
#define PIN_FL_PWM  3
#define PIN_FL_IN1  4
#define PIN_FL_IN2  A0

// --- Motor Depan-Kanan (FR) ---
#define PIN_FR_PWM  5
#define PIN_FR_IN1  7
#define PIN_FR_IN2  A1

// --- Motor Belakang-Kiri (RL) ---
#define PIN_RL_PWM  6
#define PIN_RL_IN1  8
#define PIN_RL_IN2  A2

// --- Motor Belakang-Kanan (RR) ---
#define PIN_RR_PWM  11
#define PIN_RR_IN1  12
#define PIN_RR_IN2  A3

// --- Standby kedua TB6612 (LOW = semua output mati) ---
#define PIN_STBY    9

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
#define FLIP_RL true
#define FLIP_RR true

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

// --- Kontrol heading (feedback MPU) ---
// Konvensi: heading positif = arah putar omega positif (searah jarum jam
// dilihat dari atas, seperti kompas). Arah sensor disamakan lewat DIRCAL.
#define GYRO_DEADZONE_DPS   0.3f   // Noise sisa setelah bias dikalibrasi
#define CTRL_INTERVAL       20     // Periode loop kontrol (ms) = 50 Hz
#define HOLD_MAX_OMEGA      100    // Batas koreksi heading hold (PWM)
#define TURN_MIN_OMEGA      70     // Minimal PWM putar supaya motor tidak macet
#define TURN_MAX_OMEGA      160
#define TURN_TOLERANCE_DEG  2.0f
#define TURN_SETTLE_MS      200    // Harus tenang selama ini baru dianggap selesai
#define TURN_TIMEOUT_MS     6000
#define CAL_SAMPLES         400    // Sampel kalibrasi bias (~1 detik)
#define CAL_MAX_SPREAD      400    // Selisih raw maks; lebih dari ini = robot bergerak
#define DIRCAL_OMEGA        120
#define DIRCAL_MS           700
#define SETTINGS_MAGIC      0xBC01

// ============================================================================
// VARIABEL GLOBAL
// ============================================================================
Servo servoPengumpul;

// --- Pengaturan yang disimpan di EEPROM ---
struct Settings {
  uint16_t magic;
  float gyroBias;    // Offset raw gyro Z saat diam
  int8_t gyroSign;   // +1/-1 hasil DIRCAL, 0 = belum dikalibrasi
  float kp;          // Heading hold: PWM per derajat error
  float kd;          // Heading hold & turn: PWM per derajat/detik
  float kpTurn;      // Putar ke sudut: PWM per derajat error
  uint8_t holdOn;    // Heading hold aktif saat robot jalan
};
Settings cfg;

// --- Status kontrol heading ---
float gyroRate       = 0.0f;   // derajat/detik, konvensi omega
float targetHeading  = 0.0f;
bool turnActive      = false;
unsigned long turnStart   = 0;
unsigned long settleStart = 0;
unsigned long lastCtrl    = 0;

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
  wdt_disable();  // Matikan dulu, baru diaktifkan di akhir setup

  // Inisialisasi serial untuk komunikasi dengan ESP32-CAM
  Serial.begin(SERIAL_BAUD);

  DBG_PRINTLN(F("=== Robot Pengumpul Bola ==="));
  DBG_PRINTLN(F("Inisialisasi dimulai..."));

  // --- Konfigurasi pin motor ---
  pinMode(PIN_STBY, OUTPUT);
  digitalWrite(PIN_STBY, LOW);
  pinMode(PIN_FL_PWM, OUTPUT);
  pinMode(PIN_FL_IN1, OUTPUT);
  pinMode(PIN_FL_IN2, OUTPUT);
  pinMode(PIN_FR_PWM, OUTPUT);
  pinMode(PIN_FR_IN1, OUTPUT);
  pinMode(PIN_FR_IN2, OUTPUT);
  pinMode(PIN_RL_PWM, OUTPUT);
  pinMode(PIN_RL_IN1, OUTPUT);
  pinMode(PIN_RL_IN2, OUTPUT);
  pinMode(PIN_RR_PWM, OUTPUT);
  pinMode(PIN_RR_IN1, OUTPUT);
  pinMode(PIN_RR_IN2, OUTPUT);

  // Pastikan semua motor mati saat startup, baru keluar dari standby
  stopAllMotors();
  digitalWrite(PIN_STBY, HIGH);

  // --- LED indikator ---
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  // --- Inisialisasi servo ---
  servoPengumpul.attach(PIN_SERVO);
  servoPengumpul.write(SERVO_CENTER);
  DBG_PRINTLN(F("Servo terpasang di pin 2"));

  // --- Inisialisasi MPU6050 via I2C mentah ---
  Wire.begin();
  // Tanpa timeout, gangguan listrik motor di bus I2C bisa membuat Wire macet
  // selamanya dan loop() berhenti (motor terkunci di perintah terakhir).
  Wire.setWireTimeout(3000, true);  // 3 ms, reset bus otomatis
  initMPU6050();
  muatSettings();

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

  // Watchdog hardware: kalau loop() macet >500 ms, Uno reset dan motor mati
  // (STBY TB6612 punya pull-down, jadi motor diam selama reset).
  wdt_enable(WDTO_500MS);

  DBG_PRINTLN(F("Inisialisasi selesai. Menunggu perintah..."));
}

// ============================================================================
// LOOP UTAMA
// ============================================================================
void loop() {
  wdt_reset();
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
  // TURN dikecualikan karena berjalan sendiri dan punya timeout sendiri.
  if (!turnActive && now - lastCmdTime >= WATCHDOG_TIMEOUT) {
    if (currentVx != 0 || currentVy != 0 || currentOmega != 0) {
      DBG_PRINTLN(F("WATCHDOG: Timeout, motor dihentikan!"));
      currentVx = 0;
      currentVy = 0;
      currentOmega = 0;
      stopAllMotors();
    }
  }

  // --- 5. Loop kontrol heading (hold / turn) ---
  updateKontrol(now);
}

// ============================================================================
// KONTROL HEADING
// ============================================================================
float wrap180(float a) {
  while (a > 180.0f)  a -= 360.0f;
  while (a < -180.0f) a += 360.0f;
  return a;
}

void selesaiTurn(const __FlashStringHelper* alasan) {
  turnActive = false;
  currentVx = currentVy = currentOmega = 0;
  stopAllMotors();
  targetHeading = heading;
  Serial.print(F("MSG:TURN "));
  Serial.print(alasan);
  Serial.print(F(" heading="));
  Serial.println(heading, 1);
}

// Dipanggil tiap loop; menghitung omega koreksi lalu menulis ke motor.
void updateKontrol(unsigned long now) {
  if (now - lastCtrl < CTRL_INTERVAL) return;
  lastCtrl = now;

  if (turnActive) {
    float err = wrap180(targetHeading - heading);
    if (fabs(err) < TURN_TOLERANCE_DEG && fabs(gyroRate) < 15.0f) {
      if (settleStart == 0) settleStart = now;
      else if (now - settleStart >= TURN_SETTLE_MS) { selesaiTurn(F("selesai")); return; }
    } else {
      settleStart = 0;
    }
    if (now - turnStart >= TURN_TIMEOUT_MS) { selesaiTurn(F("timeout")); return; }

    float w = 0.0f;
    if (fabs(err) >= TURN_TOLERANCE_DEG) {
      w = cfg.kpTurn * err - cfg.kd * gyroRate;
      w = constrain(w, -TURN_MAX_OMEGA, TURN_MAX_OMEGA);
      if (fabs(w) < TURN_MIN_OMEGA) w = (err > 0) ? TURN_MIN_OMEGA : -TURN_MIN_OMEGA;
    }
    jalankanMecanum(0, 0, (int16_t)w);
    return;
  }

  int16_t omega = currentOmega;
  bool jalan = (currentVx != 0 || currentVy != 0);
  if (cfg.holdOn && cfg.gyroSign != 0 && jalan && omega == 0) {
    float err = wrap180(targetHeading - heading);
    float w = cfg.kp * err - cfg.kd * gyroRate;
    omega = (int16_t)constrain(w, -HOLD_MAX_OMEGA, HOLD_MAX_OMEGA);
  } else {
    // Diam atau diputar manual: target ikut heading sekarang, supaya saat
    // mulai jalan lurus robot menahan arah terakhirnya.
    targetHeading = heading;
  }
  jalankanMecanum(currentVx, currentVy, omega);
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
  // Watchdog hanya di-reset oleh perintah valid, supaya baris sampah/debug
  // yang ikut masuk UART tidak membuat motor terus jalan.

  // --- Perintah gerak: CMD:vx,vy,omega ---
  if (strncmp(cmd, "CMD:", 4) == 0) {
    lastCmdTime = millis();
    turnActive = false;  // Perintah manual membatalkan TURN
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

    // Motor ditulis oleh updateKontrol() (plus koreksi heading hold);
    // lastCtrl = 0 memaksanya jalan di iterasi loop berikutnya.
    lastCtrl = 0;
  }
  // --- Perintah servo: SERVO:sudut ---
  else if (strncmp(cmd, "SERVO:", 6) == 0) {
    lastCmdTime = millis();
    int sudut = atoi(cmd + 6);
    sudut = constrain(sudut, 0, 180);

    servoPengumpul.write(sudut);

    DBG_PRINT(F("Servo diatur ke: "));
    DBG_PRINTLN(sudut);
  }
  // --- Perintah collect: COLLECT ---
  else if (strcmp(cmd, "COLLECT") == 0) {
    lastCmdTime = millis();
    DBG_PRINTLN(F("Memulai sekuens pengumpulan bola..."));
    jalankanCollect();
  }
  // --- Kalibrasi bias gyro (robot harus diam): CAL ---
  else if (strcmp(cmd, "CAL") == 0) {
    kalibrasiGyro();
  }
  // --- Deteksi arah sensor (robot di lantai, akan berputar): DIRCAL ---
  else if (strcmp(cmd, "DIRCAL") == 0) {
    kalibrasiArah();
  }
  // --- Nol-kan heading: ZERO ---
  else if (strcmp(cmd, "ZERO") == 0) {
    heading = 0.0f;
    targetHeading = 0.0f;
    Serial.println(F("MSG:Heading di-nol-kan"));
  }
  // --- Heading hold on/off: HOLD:1 / HOLD:0 ---
  else if (strncmp(cmd, "HOLD:", 5) == 0) {
    cfg.holdOn = atoi(cmd + 5) ? 1 : 0;
    simpanSettings();
    Serial.print(F("MSG:Heading hold "));
    Serial.println(cfg.holdOn ? F("ON") : F("OFF"));
  }
  // --- Gain kontrol: GAIN:kp,kd,kpTurn ---
  else if (strncmp(cmd, "GAIN:", 5) == 0) {
    const char* p = cmd + 5;
    float kp = atof(p);
    p = strchr(p, ',');
    float kd = p ? atof(++p) : cfg.kd;
    p = p ? strchr(p, ',') : NULL;
    float kpt = p ? atof(++p) : cfg.kpTurn;
    cfg.kp = constrain(kp, 0.0f, 50.0f);
    cfg.kd = constrain(kd, 0.0f, 20.0f);
    cfg.kpTurn = constrain(kpt, 0.0f, 50.0f);
    simpanSettings();
    kirimConfig();
  }
  // --- Putar relatif sekian derajat: TURN:deg ---
  else if (strncmp(cmd, "TURN:", 5) == 0) {
    if (cfg.gyroSign == 0) {
      Serial.println(F("MSG:GAGAL TURN, jalankan DIRCAL dulu"));
      return;
    }
    float deg = constrain(atof(cmd + 5), -360.0f, 360.0f);
    lastCmdTime = millis();
    currentVx = currentVy = currentOmega = 0;
    targetHeading = wrap180(heading + deg);
    turnStart = millis();
    settleStart = 0;
    turnActive = true;
    Serial.print(F("MSG:TURN mulai ke "));
    Serial.println(targetHeading, 1);
  }
  // --- Tampilkan konfigurasi: GET ---
  else if (strcmp(cmd, "GET") == 0) {
    kirimConfig();
  }
  else {
    DBG_PRINT(F("Perintah tidak dikenal: "));
    DBG_PRINTLN(cmd);
  }
}

// ============================================================================
// PENGATURAN EEPROM
// ============================================================================
void muatSettings() {
  EEPROM.get(0, cfg);
  if (cfg.magic != SETTINGS_MAGIC) {
    cfg.magic    = SETTINGS_MAGIC;
    cfg.gyroBias = 0.0f;
    cfg.gyroSign = 0;
    cfg.kp       = 4.0f;
    cfg.kd       = 0.3f;
    cfg.kpTurn   = 3.0f;
    cfg.holdOn   = 1;
    DBG_PRINTLN(F("Settings default (belum ada di EEPROM)."));
  } else {
    DBG_PRINTLN(F("Settings dimuat dari EEPROM."));
  }
  kirimConfig();
}

void simpanSettings() {
  EEPROM.put(0, cfg);  // put() hanya menulis byte yang berubah
}

void kirimConfig() {
  Serial.print(F("MSG:CFG bias="));
  Serial.print(cfg.gyroBias, 1);
  Serial.print(F(" sign="));
  Serial.print(cfg.gyroSign);
  Serial.print(F(" kp="));
  Serial.print(cfg.kp, 2);
  Serial.print(F(" kd="));
  Serial.print(cfg.kd, 2);
  Serial.print(F(" kpTurn="));
  Serial.print(cfg.kpTurn, 2);
  Serial.print(F(" hold="));
  Serial.println(cfg.holdOn);
}

// ============================================================================
// KALIBRASI
// ============================================================================
// Rata-rata gyro Z saat diam = bias. Ditolak kalau sebarannya besar (robot goyang).
void kalibrasiGyro() {
  turnActive = false;
  currentVx = currentVy = currentOmega = 0;
  stopAllMotors();
  Serial.println(F("MSG:Kalibrasi gyro... jangan sentuh robot"));
  delay(300);
  wdt_reset();

  long sum = 0;
  int16_t lo = 32767, hi = -32768;
  int n = 0;
  for (int i = 0; i < CAL_SAMPLES; i++) {
    int16_t raw;
    if (bacaGyroRaw(raw)) {
      sum += raw;
      if (raw < lo) lo = raw;
      if (raw > hi) hi = raw;
      n++;
    }
    delay(2);
    wdt_reset();
  }

  if (n < CAL_SAMPLES / 2) {
    Serial.println(F("MSG:GAGAL kalibrasi, MPU tidak terbaca"));
  } else if (hi - lo > CAL_MAX_SPREAD) {
    Serial.print(F("MSG:GAGAL kalibrasi, robot bergerak (spread="));
    Serial.print(hi - lo);
    Serial.println(F("), ulangi"));
  } else {
    cfg.gyroBias = (float)sum / n;
    simpanSettings();
    heading = 0.0f;
    targetHeading = 0.0f;
    Serial.print(F("MSG:Kalibrasi OK, bias="));
    Serial.print(cfg.gyroBias, 1);
    Serial.print(F(" spread="));
    Serial.println(hi - lo);
  }
  lastGyroRead = millis();
  lastCmdTime = millis();
}

// Putar sebentar dengan omega positif, lihat tanda gyro, simpan sebagai gyroSign.
void kalibrasiArah() {
  turnActive = false;
  currentVx = currentVy = currentOmega = 0;
  Serial.println(F("MSG:Deteksi arah... robot akan berputar"));

  float sudut = 0.0f;
  unsigned long t0 = millis();
  unsigned long tPrev = t0;
  jalankanMecanum(0, 0, DIRCAL_OMEGA);
  while (millis() - t0 < DIRCAL_MS + 300) {  // +300 ms untuk sisa putaran
    if (millis() - t0 >= DIRCAL_MS) stopAllMotors();
    int16_t raw;
    unsigned long t = millis();
    if (bacaGyroRaw(raw)) {
      sudut += (raw - cfg.gyroBias) / GYRO_SENSITIVITY * (t - tPrev) / 1000.0f;
    }
    tPrev = t;
    delay(5);
    wdt_reset();
  }
  stopAllMotors();

  if (fabs(sudut) < 10.0f) {
    Serial.print(F("MSG:GAGAL deteksi arah, robot hampir tidak berputar ("));
    Serial.print(sudut, 1);
    Serial.println(F(" deg). Robot harus di lantai."));
  } else {
    cfg.gyroSign = (sudut > 0) ? 1 : -1;
    simpanSettings();
    Serial.print(F("MSG:Arah OK, sign="));
    Serial.print(cfg.gyroSign);
    Serial.print(F(" (putar "));
    Serial.print(fabs(sudut), 1);
    Serial.println(F(" deg)"));
  }
  heading = 0.0f;
  targetHeading = 0.0f;
  lastGyroRead = millis();
  lastCmdTime = millis();
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
// dipetakan ke PWM (kecepatan) + IN1/IN2 (arah putar).
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
  setMotor(PIN_FL_PWM, PIN_FL_IN1, PIN_FL_IN2, fl, FLIP_FL);
  setMotor(PIN_FR_PWM, PIN_FR_IN1, PIN_FR_IN2, fr, FLIP_FR);
  setMotor(PIN_RL_PWM, PIN_RL_IN1, PIN_RL_IN2, rl, FLIP_RL);
  setMotor(PIN_RR_PWM, PIN_RR_IN1, PIN_RR_IN2, rr, FLIP_RR);
}

// ============================================================================
// SET MOTOR INDIVIDUAL
// ============================================================================
// Mengatur satu motor dengan nilai kecepatan bertanda (signed speed).
// Nilai positif = maju, negatif = mundur.
// Parameter 'flip' membalik arah jika motor terpasang terbalik.
void setMotor(uint8_t pinPwm, uint8_t pinIn1, uint8_t pinIn2, int16_t speed, bool flip) {
  // Terapkan flip jika perlu
  if (flip) {
    speed = -speed;
  }

  // TB6612: IN1/IN2 menentukan arah, PWM murni besar kecepatan.
  if (speed > 0) {
    digitalWrite(pinIn1, HIGH);
    digitalWrite(pinIn2, LOW);
  } else if (speed < 0) {
    digitalWrite(pinIn1, LOW);
    digitalWrite(pinIn2, HIGH);
  } else {
    // Diam: IN1=IN2=LOW -> output mati (coast)
    digitalWrite(pinIn1, LOW);
    digitalWrite(pinIn2, LOW);
  }
  analogWrite(pinPwm, constrain(abs(speed), 0, 255));
}

// ============================================================================
// HENTIKAN SEMUA MOTOR
// ============================================================================
void stopAllMotors() {
  analogWrite(PIN_FL_PWM, 0);
  analogWrite(PIN_FR_PWM, 0);
  analogWrite(PIN_RL_PWM, 0);
  analogWrite(PIN_RR_PWM, 0);

  digitalWrite(PIN_FL_IN1, LOW);
  digitalWrite(PIN_FL_IN2, LOW);
  digitalWrite(PIN_FR_IN1, LOW);
  digitalWrite(PIN_FR_IN2, LOW);
  digitalWrite(PIN_RL_IN1, LOW);
  digitalWrite(PIN_RL_IN2, LOW);
  digitalWrite(PIN_RR_IN1, LOW);
  digitalWrite(PIN_RR_IN2, LOW);
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

  int16_t gyroZ_raw;
  if (bacaGyroRaw(gyroZ_raw)) {
    // Konversi ke derajat per detik, setelah dikurangi bias hasil kalibrasi
    float gyroZ_dps = (gyroZ_raw - cfg.gyroBias) / GYRO_SENSITIVITY;

    // Dead zone: abaikan noise kecil
    if (fabs(gyroZ_dps) < GYRO_DEADZONE_DPS) {
      gyroZ_dps = 0.0f;
    }

    // Samakan arah dengan omega (sign 0 = belum DIRCAL, pakai arah mentah)
    gyroRate = (cfg.gyroSign < 0) ? -gyroZ_dps : gyroZ_dps;

    // Integrasi sederhana: heading += kecepatan_sudut × delta_waktu
    heading = wrap180(heading + gyroRate * dt);
  }
}

// Baca raw gyro Z (int16). false kalau MPU tidak menjawab.
bool bacaGyroRaw(int16_t &raw) {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(MPU6050_GYRO_Z_H);  // Mulai dari register high byte
  if (Wire.endTransmission(false) != 0) return false;  // Repeated start

  if (Wire.requestFrom((uint8_t)MPU6050_ADDR, (uint8_t)2, (uint8_t)true) != 2) return false;
  uint8_t hi = Wire.read();  // Dibaca terpisah: urutan evaluasi a<<8|b tidak dijamin
  uint8_t lo = Wire.read();
  raw = (int16_t)((hi << 8) | lo);
  return true;
}

// ============================================================================
// KIRIM TELEMETRI
// ============================================================================
// Format: "TEL:heading,vbat,rate,target,hold,turn,sign\n"
// heading/target = derajat, rate = derajat/detik, vbat = placeholder 0.
// Dua field pertama tetap sama supaya parser lama (ground station) tidak rusak.
void kirimTelemetri() {
  Serial.print(F("TEL:"));
  Serial.print(heading, 1);  // 1 desimal cukup
  Serial.print(F(",0,"));    // Placeholder tegangan baterai
  Serial.print(gyroRate, 1);
  Serial.print(',');
  Serial.print(targetHeading, 1);
  Serial.print(',');
  Serial.print(cfg.holdOn);
  Serial.print(',');
  Serial.print(turnActive ? 1 : 0);
  Serial.print(',');
  Serial.println(cfg.gyroSign);
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
    wdt_reset();  // Reset sebelum tiap delay (masing-masing < 500 ms)
    servoPengumpul.write(SERVO_MIN_ANGLE);
    delay(SERVO_COLLECT_DELAY);

    // Sapu ke kanan (sudut maksimum)
    wdt_reset();
    servoPengumpul.write(SERVO_MAX_ANGLE);
    delay(SERVO_COLLECT_DELAY);

    // Cek apakah ada perintah baru masuk selama collect
    bacaSerial();
  }

  // Kembali ke posisi tengah
  wdt_reset();
  servoPengumpul.write(SERVO_CENTER);
  delay(200);

  collectRunning = false;
  digitalWrite(PIN_LED, LOW);

  DBG_PRINTLN(F("Sekuens pengumpulan selesai."));
}
