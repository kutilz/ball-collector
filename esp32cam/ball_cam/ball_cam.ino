// ============================================================================
// ROBOT PENGUMPUL BOLA - FIRMWARE ESP32-CAM
// ============================================================================
// Deskripsi : Modul kamera dan WiFi untuk robot pengumpul bola
// Hardware  : ESP32-CAM (AI-Thinker), koneksi UART ke Arduino Uno
// Fitur     : MJPEG streaming, web control, relay perintah ke Arduino
// Tanggal   : 2026-06-26
// ============================================================================

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// === KONFIGURASI DEBUG ===
#define DEBUG 1

#if DEBUG
  #define DBG_PRINT(x)   Serial.print(x)
  #define DBG_PRINTLN(x) Serial.println(x)
  #define DBG_PRINTF(...) Serial.printf(__VA_ARGS__)
#else
  #define DBG_PRINT(x)
  #define DBG_PRINTLN(x)
  #define DBG_PRINTF(...)
#endif

// ============================================================================
// KONFIGURASI WIFI
// ============================================================================
// Ganti dengan SSID dan password jaringan WiFi Anda
#define WIFI_SSID     "NamaWiFi_Anda"
#define WIFI_PASSWORD "PasswordWiFi_Anda"

// Batas waktu koneksi WiFi (detik)
#define WIFI_TIMEOUT_SEC  15

// Interval pengecekan ulang koneksi WiFi (ms)
#define WIFI_CHECK_INTERVAL 10000

// ============================================================================
// KONFIGURASI PIN ESP32-CAM (AI-THINKER)
// ============================================================================
// Pin mapping khusus untuk modul AI-Thinker ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1   // Tidak digunakan
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26   // I2C SDA kamera
#define SIOC_GPIO_NUM     27   // I2C SCL kamera
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// --- LED Flash bawaan ---
#define LED_FLASH_PIN      4

// ============================================================================
// KONFIGURASI UART KE ARDUINO
// ============================================================================
// ESP32-CAM menggunakan Serial default (GPIO 1=TX, 3=RX)
// untuk komunikasi dengan Arduino Uno.
// CATATAN: Saat upload firmware, pastikan kabel UART ke Arduino DILEPAS
// agar tidak bentrok dengan programmer.
#define UART_BAUD 115200

// ============================================================================
// KONFIGURASI KAMERA
// ============================================================================
#define CAM_FRAME_SIZE    FRAMESIZE_QVGA   // 320x240 piksel
#define CAM_JPEG_QUALITY  12               // Kualitas JPEG (10=terbaik, 63=terburuk)
#define CAM_FB_COUNT      2                // Jumlah frame buffer (2 untuk streaming lancar)
#define CAM_XCLK_FREQ     20000000         // Frekuensi clock kamera (20MHz)

// ============================================================================
// VARIABEL GLOBAL
// ============================================================================
WebServer server(80);

// --- Statistik ---
unsigned long bootTime      = 0;    // Waktu boot (ms)
unsigned long frameCount    = 0;    // Total frame yang di-stream
unsigned long lastFpsCalc   = 0;    // Waktu kalkulasi FPS terakhir
float currentFps            = 0.0f; // FPS saat ini
unsigned long fpsFrameCount = 0;    // Counter frame untuk kalkulasi FPS

// --- Waktu pengecekan WiFi ---
unsigned long lastWifiCheck = 0;

// --- Buffer telemetri dari Arduino ---
char arduinoTelemetry[128]  = "TEL:0.0,0";
char telemetryBuf[128];
uint8_t telemetryIdx        = 0;

// --- Status LED flash ---
bool ledFlashOn = false;

// ============================================================================
// INISIALISASI KAMERA
// ============================================================================
bool initKamera() {
  camera_config_t config;

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;

  config.xclk_freq_hz = CAM_XCLK_FREQ;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = CAM_FRAME_SIZE;
  config.jpeg_quality = CAM_JPEG_QUALITY;
  config.fb_count     = CAM_FB_COUNT;
  config.grab_mode    = CAMERA_GRAB_LATEST;  // Ambil frame terbaru

  // Inisialisasi driver kamera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    DBG_PRINTF("GAGAL inisialisasi kamera! Error: 0x%x\n", err);
    return false;
  }

  // Pengaturan sensor tambahan
  sensor_t *s = esp_camera_sensor_get();
  if (s) {
    s->set_brightness(s, 0);     // Kecerahan default
    s->set_contrast(s, 0);       // Kontras default
    s->set_saturation(s, 0);     // Saturasi default
    s->set_hmirror(s, 0);        // Mirror horizontal: 0=mati
    s->set_vflip(s, 0);          // Flip vertikal: 0=mati
    DBG_PRINTLN(F("Sensor kamera dikonfigurasi."));
  }

  DBG_PRINTLN(F("Kamera berhasil diinisialisasi."));
  DBG_PRINTLN(F("Resolusi: QVGA (320x240), JPEG quality: 12"));
  return true;
}

// ============================================================================
// KONEKSI WIFI
// ============================================================================
bool connectWifi() {
  DBG_PRINT(F("Menghubungkan ke WiFi: "));
  DBG_PRINTLN(WIFI_SSID);

  WiFi.mode(WIFI_STA);           // Mode station (client)
  WiFi.setSleep(false);           // Nonaktifkan power save untuk latensi rendah
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  // Tunggu koneksi dengan timeout
  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - startAttempt >= WIFI_TIMEOUT_SEC * 1000UL) {
      DBG_PRINTLN(F("\nGAGAL: Timeout koneksi WiFi!"));
      return false;
    }
    delay(500);
    DBG_PRINT(F("."));
  }

  DBG_PRINTLN();
  DBG_PRINTLN(F("WiFi terhubung!"));
  DBG_PRINT(F("Alamat IP: "));
  DBG_PRINTLN(WiFi.localIP());
  DBG_PRINT(F("RSSI: "));
  DBG_PRINT(WiFi.RSSI());
  DBG_PRINTLN(F(" dBm"));

  return true;
}

// ============================================================================
// HANDLER: HALAMAN UTAMA (/)
// ============================================================================
// Menampilkan halaman HTML sederhana dengan status dan link ke stream
void handleRoot() {
  String html = F(
    "<!DOCTYPE html>"
    "<html><head>"
    "<meta charset='UTF-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Robot Pengumpul Bola</title>"
    "<style>"
    "body{font-family:sans-serif;background:#1a1a2e;color:#e0e0e0;"
    "display:flex;flex-direction:column;align-items:center;margin:0;padding:20px;}"
    "h1{color:#00d4ff;text-shadow:0 0 10px rgba(0,212,255,0.5);}"
    ".card{background:#16213e;border-radius:12px;padding:20px;margin:10px;"
    "box-shadow:0 4px 15px rgba(0,0,0,0.3);max-width:400px;width:100%;}"
    ".card h2{color:#0f3460;margin-top:0;}"
    "a{color:#00d4ff;text-decoration:none;}"
    "a:hover{text-decoration:underline;}"
    ".btn{display:inline-block;background:#0f3460;color:#fff;padding:10px 20px;"
    "border-radius:8px;margin:5px;transition:background 0.3s;}"
    ".btn:hover{background:#00d4ff;color:#1a1a2e;text-decoration:none;}"
    "img{max-width:100%;border-radius:8px;}"
    ".status{font-size:0.9em;color:#888;}"
    "</style>"
    "</head><body>"
    "<h1>&#x1F916; Robot Pengumpul Bola</h1>"
    "<div class='card'>"
    "<h2 style='color:#00d4ff;'>&#x1F4F9; Live Stream</h2>"
    "<img src='/stream' alt='Stream kamera' />"
    "</div>"
    "<div class='card'>"
    "<h2 style='color:#00d4ff;'>&#x1F3AE; Kontrol</h2>"
    "<a class='btn' href='/cmd?q=CMD:100,0,0'>&#x2B06; Maju</a>"
    "<a class='btn' href='/cmd?q=CMD:-100,0,0'>&#x2B07; Mundur</a><br>"
    "<a class='btn' href='/cmd?q=CMD:0,100,0'>&#x2B05; Kiri</a>"
    "<a class='btn' href='/cmd?q=CMD:0,-100,0'>&#x27A1; Kanan</a><br>"
    "<a class='btn' href='/cmd?q=CMD:0,0,100'>&#x21BA; Putar Kiri</a>"
    "<a class='btn' href='/cmd?q=CMD:0,0,-100'>&#x21BB; Putar Kanan</a><br>"
    "<a class='btn' href='/cmd?q=CMD:0,0,0'>&#x23F9; Stop</a>"
    "<a class='btn' href='/cmd?q=COLLECT'>&#x1F3BE; Collect</a>"
    "</div>"
    "<div class='card'>"
    "<h2 style='color:#00d4ff;'>&#x1F4CA; Info</h2>"
    "<p><a href='/status'>Status JSON</a> | "
    "<a href='/stream'>Stream Langsung</a></p>"
  );

  // Tambahkan info dinamis
  html += "<p class='status'>IP: " + WiFi.localIP().toString()
        + " | RSSI: " + String(WiFi.RSSI()) + " dBm"
        + " | Uptime: " + String(millis() / 1000) + "s"
        + " | FPS: " + String(currentFps, 1)
        + "</p>";

  html += F(
    "<p class='status'>Telemetri Arduino: <span id='tel'></span></p>"
    "</div>"
    "</body></html>"
  );

  server.send(200, "text/html", html);
}

// ============================================================================
// HANDLER: MJPEG STREAMING (/stream)
// ============================================================================
// Mengirim video sebagai aliran MJPEG (multipart/x-mixed-replace).
// Setiap frame dikirim sebagai bagian JPEG terpisah.
void handleStream() {
  WiFiClient client = server.client();

  // Header MJPEG multipart
  String response = F(
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
    "Access-Control-Allow-Origin: *\r\n"
    "Cache-Control: no-cache, no-store, must-revalidate\r\n"
    "\r\n"
  );
  client.print(response);

  DBG_PRINTLN(F("Client streaming terhubung."));

  // Loop streaming - terus kirim frame sampai client disconnect
  while (client.connected()) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      DBG_PRINTLN(F("GAGAL ambil frame dari kamera!"));
      delay(100);
      continue;
    }

    // Kirim boundary dan header untuk frame ini
    String partHeader = F("--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ");
    partHeader += String(fb->len);
    partHeader += F("\r\n\r\n");

    client.print(partHeader);
    client.write(fb->buf, fb->len);
    client.print(F("\r\n"));

    // Lepaskan frame buffer agar bisa dipakai lagi
    esp_camera_fb_return(fb);

    // Update counter frame
    frameCount++;
    fpsFrameCount++;

    // Hitung FPS setiap detik
    unsigned long now = millis();
    if (now - lastFpsCalc >= 1000) {
      currentFps = (float)fpsFrameCount * 1000.0f / (float)(now - lastFpsCalc);
      fpsFrameCount = 0;
      lastFpsCalc = now;
    }

    // Yield agar WiFi stack dan watchdog ESP32 tidak timeout
    delay(1);
  }

  DBG_PRINTLN(F("Client streaming terputus."));
}

// ============================================================================
// HANDLER: PERINTAH ROBOT (/cmd?q=...)
// ============================================================================
// Menerima perintah via HTTP GET dan meneruskan ke Arduino melalui UART.
// Contoh: /cmd?q=CMD:100,0,0 → kirim "CMD:100,0,0\n" ke Arduino
void handleCommand() {
  if (!server.hasArg("q")) {
    server.send(400, "application/json",
      "{\"error\":\"Parameter 'q' tidak ditemukan. Contoh: /cmd?q=CMD:100,0,0\"}");
    return;
  }

  String cmd = server.arg("q");

  // Kirim perintah ke Arduino via UART
  Serial.println(cmd);

  DBG_PRINT(F("Perintah dikirim ke Arduino: "));
  DBG_PRINTLN(cmd);

  // Respon JSON
  String json = "{\"ok\":true,\"cmd\":\"" + cmd + "\","
              + "\"telemetry\":\"" + String(arduinoTelemetry) + "\"}";
  server.send(200, "application/json", json);
}

// ============================================================================
// HANDLER: STATUS (/status)
// ============================================================================
// Mengembalikan status sistem dalam format JSON
void handleStatus() {
  unsigned long uptime = (millis() - bootTime) / 1000;

  String json = "{";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"rssi\":" + String(WiFi.RSSI()) + ",";
  json += "\"uptime_sec\":" + String(uptime) + ",";
  json += "\"fps\":" + String(currentFps, 1) + ",";
  json += "\"total_frames\":" + String(frameCount) + ",";
  json += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  json += "\"wifi_ssid\":\"" + String(WIFI_SSID) + "\",";
  json += "\"flash_led\":" + String(ledFlashOn ? "true" : "false") + ",";
  json += "\"arduino_telemetry\":\"" + String(arduinoTelemetry) + "\"";
  json += "}";

  server.send(200, "application/json", json);
}

// ============================================================================
// HANDLER: LED FLASH (/led?state=on|off)
// ============================================================================
// Mengontrol LED flash bawaan ESP32-CAM (GPIO 4)
void handleLed() {
  if (server.hasArg("state")) {
    String state = server.arg("state");
    if (state == "on") {
      digitalWrite(LED_FLASH_PIN, HIGH);
      ledFlashOn = true;
    } else {
      digitalWrite(LED_FLASH_PIN, LOW);
      ledFlashOn = false;
    }
  } else {
    // Toggle jika tidak ada parameter
    ledFlashOn = !ledFlashOn;
    digitalWrite(LED_FLASH_PIN, ledFlashOn ? HIGH : LOW);
  }

  String json = "{\"led\":" + String(ledFlashOn ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}

// ============================================================================
// HANDLER: 404 NOT FOUND
// ============================================================================
void handleNotFound() {
  String msg = "{\"error\":\"Endpoint tidak ditemukan: " + server.uri() + "\","
             + "\"endpoints\":[\"/\",\"/stream\",\"/cmd?q=...\",\"/status\",\"/led?state=on|off\"]}";
  server.send(404, "application/json", msg);
}

// ============================================================================
// BACA TELEMETRI DARI ARDUINO
// ============================================================================
// Membaca data serial dari Arduino dan menyimpan telemetri terakhir.
// Format yang diharapkan: "TEL:heading,vbat\n"
void bacaTelemetriArduino() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (telemetryIdx > 0) {
        telemetryBuf[telemetryIdx] = '\0';

        // Simpan jika formatnya TEL:...
        if (strncmp(telemetryBuf, "TEL:", 4) == 0) {
          strncpy(arduinoTelemetry, telemetryBuf, sizeof(arduinoTelemetry) - 1);
          arduinoTelemetry[sizeof(arduinoTelemetry) - 1] = '\0';
        }

        telemetryIdx = 0;
      }
    } else {
      if (telemetryIdx < sizeof(telemetryBuf) - 1) {
        telemetryBuf[telemetryIdx++] = c;
      } else {
        telemetryIdx = 0;  // Buffer penuh, reset
      }
    }
  }
}

// ============================================================================
// PENGECEKAN ULANG KONEKSI WIFI
// ============================================================================
// Otomatis reconnect jika WiFi terputus
void cekKoneksiWifi(unsigned long now) {
  if (now - lastWifiCheck < WIFI_CHECK_INTERVAL) return;
  lastWifiCheck = now;

  if (WiFi.status() != WL_CONNECTED) {
    DBG_PRINTLN(F("WiFi terputus! Mencoba reconnect..."));
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    // Tunggu sebentar (non-blocking pada iterasi berikutnya)
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 5000) {
      delay(250);
    }

    if (WiFi.status() == WL_CONNECTED) {
      DBG_PRINT(F("WiFi terhubung kembali! IP: "));
      DBG_PRINTLN(WiFi.localIP());
    } else {
      DBG_PRINTLN(F("Reconnect gagal, coba lagi nanti..."));
    }
  }
}

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  // Inisialisasi serial (UART ke Arduino)
  Serial.begin(UART_BAUD);
  delay(100);

  DBG_PRINTLN(F("\n=== ESP32-CAM Robot Pengumpul Bola ==="));
  DBG_PRINTLN(F("Inisialisasi dimulai..."));

  // --- LED Flash ---
  pinMode(LED_FLASH_PIN, OUTPUT);
  digitalWrite(LED_FLASH_PIN, LOW);

  // --- Inisialisasi kamera ---
  if (!initKamera()) {
    DBG_PRINTLN(F("FATAL: Kamera gagal! Restart dalam 5 detik..."));
    delay(5000);
    ESP.restart();
  }

  // --- Koneksi WiFi ---
  if (!connectWifi()) {
    DBG_PRINTLN(F("PERINGATAN: WiFi gagal, coba lagi nanti via auto-reconnect."));
  }

  // --- Setup web server ---
  server.on("/",       HTTP_GET, handleRoot);
  server.on("/stream", HTTP_GET, handleStream);
  server.on("/cmd",    HTTP_GET, handleCommand);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/led",    HTTP_GET, handleLed);
  server.onNotFound(handleNotFound);

  // Izinkan CORS untuk akses dari browser/aplikasi lain
  server.enableCORS(true);

  server.begin();

  bootTime    = millis();
  lastFpsCalc = millis();

  DBG_PRINTLN(F("Web server aktif!"));
  DBG_PRINTLN(F("Endpoint tersedia:"));
  DBG_PRINTLN(F("  /        - Halaman kontrol"));
  DBG_PRINTLN(F("  /stream  - MJPEG live stream"));
  DBG_PRINTLN(F("  /cmd?q=  - Kirim perintah ke robot"));
  DBG_PRINTLN(F("  /status  - Status JSON"));
  DBG_PRINTLN(F("  /led     - Kontrol LED flash"));
  DBG_PRINT(F("Akses di: http://"));
  DBG_PRINTLN(WiFi.localIP());

  // Kedipkan LED flash tanda siap
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_FLASH_PIN, HIGH);
    delay(100);
    digitalWrite(LED_FLASH_PIN, LOW);
    delay(100);
  }
}

// ============================================================================
// LOOP UTAMA
// ============================================================================
void loop() {
  unsigned long now = millis();

  // Layani permintaan HTTP
  server.handleClient();

  // Baca telemetri dari Arduino
  bacaTelemetriArduino();

  // Cek dan reconnect WiFi jika perlu
  cekKoneksiWifi(now);

  // Yield kecil agar watchdog ESP32 tidak timeout
  delay(1);
}
