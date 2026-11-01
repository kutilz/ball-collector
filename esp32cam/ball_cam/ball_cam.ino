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
#include <ESPmDNS.h>
#include "esp_http_server.h"
#include <ArduinoOTA.h>

// Nama di jaringan: http://ballcollector.local dan nama perangkat di router/hotspot
#define HOSTNAME "ballcollector"

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
// Daftar SSID/password (urut prioritas) ada di wifi_secrets.h (di-gitignore).
// Kalau belum ada, pakai contoh supaya tetap bisa di-compile.
#if __has_include("wifi_secrets.h")
#include "wifi_secrets.h"
#else
#include "wifi_secrets.example.h"
#endif
const int WIFI_COUNT = sizeof(WIFI_LIST) / sizeof(WIFI_LIST[0]);

// Password OTA (upload firmware lewat WiFi), diisi di wifi_secrets.h
#ifndef OTA_PASSWORD
#define OTA_PASSWORD "ballcollector"
#endif

// Batas waktu koneksi per jaringan (detik)
#define WIFI_TIMEOUT_SEC  10

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

// --- Pesan terakhir dari Arduino (baris "MSG:...", mis. hasil kalibrasi) ---
char arduinoMsg[128]        = "";
uint32_t arduinoMsgId       = 0;   // Naik tiap ada pesan baru, untuk halaman /tune

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
// Coba satu jaringan sampai terhubung atau timeout.
bool cobaWifi(const WifiCred &w) {
  DBG_PRINT(F("Menghubungkan ke WiFi: "));
  DBG_PRINTLN(w.ssid);

  WiFi.disconnect();
  WiFi.begin(w.ssid, (w.pass && w.pass[0]) ? w.pass : nullptr);

  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - startAttempt >= WIFI_TIMEOUT_SEC * 1000UL) {
      DBG_PRINTLN(F("\nGAGAL: Timeout koneksi WiFi!"));
      return false;
    }
    delay(500);
    DBG_PRINT(F("."));
  }
  return true;
}

// Kedip LED flash n kali (pendek supaya tidak menyilaukan).
void kedipFlash(int n, int onMs = 80, int offMs = 350) {
  for (int i = 0; i < n; i++) {
    digitalWrite(LED_FLASH_PIN, HIGH);
    delay(onMs);
    digitalWrite(LED_FLASH_PIN, LOW);
    delay(offMs);
  }
  digitalWrite(LED_FLASH_PIN, ledFlashOn ? HIGH : LOW);
}

// Scan dulu, lalu sambung ke jaringan terlihat dengan prioritas tertinggi
// (urutan WIFI_LIST). Kalau gagal, lanjut ke prioritas berikutnya.
// Indikator: flash kedip 1/2/3x = terhubung ke WIFI_LIST[0/1/2];
// satu nyala panjang = tidak ada yang tersambung.
bool connectWifi() {
  WiFi.setHostname(HOSTNAME);    // Harus sebelum mode()/begin()
  WiFi.mode(WIFI_STA);           // Mode station (client)
  WiFi.setSleep(false);           // Nonaktifkan power save untuk latensi rendah

  DBG_PRINTLN(F("Scan WiFi..."));
  int n = WiFi.scanNetworks();
  int idx = -1;
  for (int i = 0; i < WIFI_COUNT && idx < 0; i++) {
    bool terlihat = false;
    for (int j = 0; j < n; j++) {
      if (WiFi.SSID(j) == WIFI_LIST[i].ssid) { terlihat = true; break; }
    }
    if (!terlihat) {
      DBG_PRINT(F("Tidak terlihat: "));
      DBG_PRINTLN(WIFI_LIST[i].ssid);
      continue;
    }
    if (cobaWifi(WIFI_LIST[i])) idx = i;
  }
  WiFi.scanDelete();

  if (idx < 0) {
    DBG_PRINTLN(F("GAGAL: tidak ada WiFi dari daftar yang bisa disambung."));
    kedipFlash(1, 1000, 200);
    return false;
  }
  kedipFlash(idx + 1);

  DBG_PRINTLN();
  DBG_PRINT(F("WiFi terhubung ke "));
  DBG_PRINTLN(WiFi.SSID());

  // mDNS: robot bisa dibuka lewat http://ballcollector.local tanpa tahu IP
  MDNS.end();
  if (MDNS.begin(HOSTNAME)) {
    MDNS.addService("http", "tcp", 80);
    DBG_PRINTLN(F("mDNS: http://" HOSTNAME ".local"));
  }
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
    "<p><a href='/tune'>Kalibrasi &amp; Tuning MPU</a> | "
    "<a href='/status'>Status JSON</a> | "
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
// STREAM MJPEG (port 81, task terpisah)
// ============================================================================
// Stream dilayani esp_http_server di task FreeRTOS sendiri, jadi WebServer
// port 80 (/cmd, /tune, /tel) tetap responsif selama video ditonton.
// JANGAN pakai Serial di sini: Serial = UART ke Arduino, tulisan dari dua task
// bisa menyela baris perintah "CMD:..." dan merusaknya.
#define STREAM_PORT 81
#define PART_BOUNDARY "123456789000000000000987654321"
static const char* STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

esp_err_t streamHandler(httpd_req_t *req) {
  esp_err_t res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
  if (res != ESP_OK) return res;
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  httpd_resp_set_hdr(req, "Cache-Control", "no-cache, no-store, must-revalidate");

  char part[64];
  while (true) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      vTaskDelay(pdMS_TO_TICKS(100));
      continue;
    }

    size_t hlen = snprintf(part, sizeof(part), STREAM_PART, (unsigned)fb->len);
    res = httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, part, hlen);
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    if (res != ESP_OK) break;  // Client putus

    // Update counter frame & FPS tiap detik
    frameCount++;
    fpsFrameCount++;
    unsigned long now = millis();
    if (now - lastFpsCalc >= 1000) {
      currentFps = (float)fpsFrameCount * 1000.0f / (float)(now - lastFpsCalc);
      fpsFrameCount = 0;
      lastFpsCalc = now;
    }
  }
  return res;
}

void startStreamServer() {
  httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
  cfg.server_port = STREAM_PORT;
  cfg.ctrl_port = 32769;  // Default 32768 bisa bentrok dengan instance lain

  httpd_uri_t uri;
  memset(&uri, 0, sizeof(uri));
  uri.uri = "/stream";
  uri.method = HTTP_GET;
  uri.handler = streamHandler;

  httpd_handle_t h = NULL;
  if (httpd_start(&h, &cfg) == ESP_OK) {
    httpd_register_uri_handler(h, &uri);
    DBG_PRINTLN(F("Stream server aktif di port 81."));
  } else {
    DBG_PRINTLN(F("GAGAL start stream server port 81!"));
  }
}

// /stream di port 80 dialihkan ke port 81 (kompatibel dengan link lama)
void handleStream() {
  server.sendHeader("Location",
                    "http://" + WiFi.localIP().toString() + ":" + String(STREAM_PORT) + "/stream");
  server.send(302, "text/plain", "");
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
  json += "\"wifi_ssid\":\"" + WiFi.SSID() + "\",";
  json += "\"flash_led\":" + String(ledFlashOn ? "true" : "false") + ",";
  json += "\"arduino_telemetry\":\"" + String(arduinoTelemetry) + "\"";
  json += "}";

  server.send(200, "application/json", json);
}

// ============================================================================
// HANDLER: TELEMETRI RINGAN (/tel) untuk halaman /tune
// ============================================================================
void handleTel() {
  String json = "{\"tel\":\"" + String(arduinoTelemetry) + "\",";
  json += "\"msg\":\"" + String(arduinoMsg) + "\",";
  json += "\"msgId\":" + String(arduinoMsgId) + ",";
  json += "\"ssid\":\"" + WiFi.SSID() + "\",";
  json += "\"rssi\":" + String(WiFi.RSSI()) + "}";
  server.send(200, "application/json", json);
}

// ============================================================================
// HANDLER: HALAMAN KALIBRASI & TUNING MPU (/tune)
// ============================================================================
// Halaman tanpa stream kamera (stream ada di port 81, task terpisah).
const char TUNE_HTML[] PROGMEM = R"rawliteral(<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tuning MPU</title>
<style>
body{font-family:system-ui,sans-serif;background:#111827;color:#e5e7eb;margin:0;padding:12px;max-width:720px;margin:auto}
h1{font-size:1.2em;margin:4px 0 10px}h2{font-size:1em;margin:0 0 8px;color:#93c5fd}
.card{background:#1f2937;border-radius:10px;padding:12px;margin-bottom:12px}
.big{font-size:2.4em;font-weight:700;font-variant-numeric:tabular-nums}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.kv{font-variant-numeric:tabular-nums;color:#9ca3af;font-size:.9em}
button{background:#374151;color:#fff;border:0;border-radius:8px;padding:10px 14px;font-size:1em;touch-action:none;user-select:none}
button:active,button.on{background:#2563eb}.warn{background:#b45309}.stop{background:#b91c1c}
.pad{display:grid;grid-template-columns:repeat(3,64px);gap:6px}.pad button{height:56px;padding:0}
input[type=number]{width:70px;background:#111827;color:#fff;border:1px solid #4b5563;border-radius:6px;padding:6px}
canvas{width:100%;height:160px;background:#111827;border-radius:8px}
#msg{color:#fde68a;min-height:1.2em}#log{font-size:.8em;color:#9ca3af;max-height:110px;overflow:auto;white-space:pre-wrap}
.ok{color:#86efac}.bad{color:#fca5a5}small{color:#9ca3af}
</style></head><body>
<h1>Kalibrasi &amp; Tuning MPU</h1>

<div class="card">
<div class="row" style="justify-content:space-between">
<div><div class="big" id="hd">--</div><div class="kv">heading (&deg;)</div></div>
<div class="kv">target <b id="tg">--</b>&deg;<br>rate <b id="rt">--</b>&deg;/s<br>hold <b id="ho">--</b> &middot; turn <b id="tu">--</b><br>arah sensor <b id="sg">--</b></div>
</div>
<canvas id="cv" width="680" height="160"></canvas>
<small>Biru = heading, kuning = target. <span id="net"></span></small>
<div id="msg"></div>
</div>

<div class="card">
<h2>1. Kalibrasi</h2>
<div class="row">
<button onclick="send('CAL')">Kalibrasi gyro</button><small>robot diam total ~1 detik</small></div>
<div class="row" style="margin-top:8px">
<button class="warn" onclick="if(confirm('Robot akan berputar ~0,7 detik. Robot di lantai?'))send('DIRCAL')">Deteksi arah putar</button><small>robot di lantai, akan berputar</small></div>
<div class="row" style="margin-top:8px">
<button onclick="send('ZERO')">Nol-kan heading</button>
<button onclick="send('GET')">Baca setting</button></div>
</div>

<div class="card">
<h2>2. Gerak (tahan tombol)</h2>
<div class="row" style="gap:16px;align-items:flex-start">
<div class="pad">
<button data-m="0,0,-1">&#x21BA;</button><button data-m="1,0,0">&#x25B2;</button><button data-m="0,0,1">&#x21BB;</button>
<button data-m="0,1,0">&#x25C0;</button><button class="stop" onclick="stopNow()">&#x25A0;</button><button data-m="0,-1,0">&#x25B6;</button>
<span></span><button data-m="-1,0,0">&#x25BC;</button><span></span>
</div>
<div>
<label>Kecepatan <b id="spv">120</b><br><input id="sp" type="range" min="40" max="255" value="120" oninput="spv.textContent=this.value"></label><br><br>
<label><input type="checkbox" id="hold" onchange="send('HOLD:'+(this.checked?1:0))"> Heading hold (jalan lurus pakai MPU)</label><br>
<small>Keyboard: W/S maju-mundur, A/D geser, Q/E putar, spasi stop</small>
</div></div>
<div class="row" style="margin-top:10px">
<button onclick="send('TURN:-90')">-90&deg;</button><button onclick="send('TURN:-45')">-45&deg;</button>
<button onclick="send('TURN:45')">+45&deg;</button><button onclick="send('TURN:90')">+90&deg;</button><button onclick="send('TURN:180')">180&deg;</button>
</div>
<div class="row" style="margin-top:10px">
<button onclick="ujiLurus()">Uji lurus</button><input id="dur" type="number" value="3" min="1" max="10" step="1"><small>detik, maju dengan kecepatan di atas</small>
</div>
<div id="uji" class="kv"></div>
</div>

<div class="card">
<h2>3. Tuning gain</h2>
<div class="row">
<label>Kp <input id="kp" type="number" step="0.1" value="4"></label>
<label>Kd <input id="kd" type="number" step="0.05" value="0.3"></label>
<label>Kp putar <input id="kpt" type="number" step="0.1" value="3"></label>
<button onclick="send('GAIN:'+kp.value+','+kd.value+','+kpt.value)">Terapkan &amp; simpan</button>
</div>
<small>Robot berkelok-kelok/gemetar saat jalan lurus &rarr; turunkan Kp atau naikkan Kd. Masih melenceng pelan &rarr; naikkan Kp. Putar kelewatan &rarr; turunkan Kp putar / naikkan Kd.</small>
</div>

<div class="card"><h2>Log</h2><div id="log"></div></div>

<script>
const $=id=>document.getElementById(id);
let T={h:0,r:0,t:0,hold:0,turn:0,sign:0},lastMsg=-1,hist=[],driveTimer=null,uji=null,holdInit=false;
function log(s){const l=$('log');l.textContent=new Date().toLocaleTimeString()+'  '+s+'\n'+l.textContent;}
function send(q){log('> '+q);return fetch('/cmd?q='+encodeURIComponent(q)).catch(()=>log('! gagal kirim'));}
function cmd(vx,vy,w){fetch('/cmd?q='+encodeURIComponent('CMD:'+vx+','+vy+','+w)).catch(()=>{});}
function startDrive(m){stopDrive(false);const s=+$('sp').value;const v=m.split(',').map(x=>Math.round(+x*s));
 cmd(...v);driveTimer=setInterval(()=>cmd(...v),150);}
function stopDrive(sendStop=true){if(driveTimer){clearInterval(driveTimer);driveTimer=null;}if(sendStop){cmd(0,0,0);setTimeout(()=>cmd(0,0,0),80);}}
function stopNow(){if(uji){clearInterval(uji.timer);uji=null;}stopDrive(true);}
document.querySelectorAll('[data-m]').forEach(b=>{
 b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);startDrive(b.dataset.m);});
 ['pointerup','pointercancel','lostpointercapture'].forEach(ev=>b.addEventListener(ev,()=>stopDrive(true)));});
const KEYS={w:'1,0,0',s:'-1,0,0',a:'0,1,0',d:'0,-1,0',q:'0,0,-1',e:'0,0,1'};let keyDown=null;
addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;const k=e.key.toLowerCase();
 if(k===' '){e.preventDefault();stopNow();return;}if(KEYS[k]&&keyDown!==k){keyDown=k;startDrive(KEYS[k]);}});
addEventListener('keyup',e=>{if(e.key.toLowerCase()===keyDown){keyDown=null;stopDrive(true);}});
addEventListener('blur',()=>stopDrive(true));
function wrap(a){while(a>180)a-=360;while(a<-180)a+=360;return a;}
function ujiLurus(){if(uji)return;const s=+$('sp').value,d=+$('dur').value*1000,h0=T.h;let maxDev=0,t0=Date.now();
 uji={timer:setInterval(()=>{const dev=wrap(T.h-h0);if(Math.abs(dev)>Math.abs(maxDev))maxDev=dev;
  if(Date.now()-t0>=d){clearInterval(uji.timer);uji=null;stopDrive(true);
   const end=wrap(T.h-h0);$('uji').innerHTML='Selesai: simpangan akhir <b>'+end.toFixed(1)+'&deg;</b>, maks <b>'+maxDev.toFixed(1)+'&deg;</b> (hold '+(T.hold?'ON':'OFF')+')';
   log('uji lurus: akhir '+end.toFixed(1)+' maks '+maxDev.toFixed(1));return;}
  cmd(s,0,0);},150)};$('uji').textContent='Berjalan...';}
function parseCfg(m){const g=k=>{const r=new RegExp(k+'=(-?[\\d.]+)').exec(m);return r?r[1]:null;};
 if(g('kp'))$('kp').value=g('kp');if(g('kd'))$('kd').value=g('kd');if(g('kpTurn'))$('kpt').value=g('kpTurn');}
function draw(){const c=$('cv'),x=c.getContext('2d'),W=c.width,H=c.height;x.clearRect(0,0,W,H);if(hist.length<2)return;
 let lo=Infinity,hi=-Infinity;hist.forEach(p=>{lo=Math.min(lo,p.h,p.t);hi=Math.max(hi,p.h,p.t);});
 if(hi-lo<10){const m=(hi+lo)/2;lo=m-5;hi=m+5;}const pad=(hi-lo)*.1;lo-=pad;hi+=pad;
 const Y=v=>H-(v-lo)/(hi-lo)*H,X=i=>i/(150-1)*W;
 x.fillStyle='#6b7280';x.font='11px sans-serif';x.fillText(hi.toFixed(0)+'°',4,12);x.fillText(lo.toFixed(0)+'°',4,H-4);
 [['t','#facc15'],['h','#60a5fa']].forEach(([k,col])=>{x.strokeStyle=col;x.lineWidth=2;x.beginPath();
  hist.forEach((p,i)=>i?x.lineTo(X(i),Y(p[k])):x.moveTo(X(i),Y(p[k])));x.stroke();});}
async function poll(){try{const r=await fetch('/tel');const j=await r.json();const p=j.tel.slice(4).split(',').map(Number);
 T={h:p[0]||0,r:p[2]||0,t:p[3]||0,hold:p[4]||0,turn:p[5]||0,sign:p[6]||0};
 $('hd').textContent=T.h.toFixed(1);$('tg').textContent=T.t.toFixed(1);$('rt').textContent=T.r.toFixed(1);
 $('ho').textContent=T.hold?'ON':'OFF';$('tu').textContent=T.turn?'jalan':'-';
 $('sg').innerHTML=T.sign?'<span class="ok">OK ('+T.sign+')</span>':'<span class="bad">belum (DIRCAL)</span>';
 if(!holdInit&&p.length>4){$('hold').checked=!!T.hold;holdInit=true;}
 $('net').textContent='WiFi '+j.ssid+' ('+j.rssi+' dBm)';
 if(j.msgId!==lastMsg){if(lastMsg>=0||j.msg){$('msg').textContent=j.msg;log('< '+j.msg);}if(j.msg.startsWith('CFG'))parseCfg(j.msg);lastMsg=j.msgId;}
 hist.push({h:T.h,t:T.t});if(hist.length>150)hist.shift();draw();}catch(e){$('net').textContent='koneksi putus...';}
 setTimeout(poll,200);}
poll();setTimeout(()=>send('GET'),500);
</script></body></html>)rawliteral";

void handleTune() {
  server.send_P(200, "text/html", TUNE_HTML);
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
        } else if (strncmp(telemetryBuf, "MSG:", 4) == 0) {
          strncpy(arduinoMsg, telemetryBuf + 4, sizeof(arduinoMsg) - 1);
          arduinoMsg[sizeof(arduinoMsg) - 1] = '\0';
          arduinoMsgId++;
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
    // Blocking beberapa detik; aman karena Arduino menghentikan motor sendiri
    // (watchdog 500 ms) kalau perintah berhenti datang.
    DBG_PRINTLN(F("WiFi terputus! Mencoba reconnect..."));
    if (connectWifi()) {
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
  server.on("/tel",    HTTP_GET, handleTel);
  server.on("/tune",   HTTP_GET, handleTune);
  server.onNotFound(handleNotFound);

  // Izinkan CORS untuk akses dari browser/aplikasi lain
  server.enableCORS(true);

  server.begin();
  startStreamServer();

  // --- OTA: update firmware lewat WiFi (tanpa USB-TTL & jumper IO0) ---
  // Motor aman selama update: perintah berhenti -> watchdog Arduino stop motor.
  ArduinoOTA.setHostname(HOSTNAME);
  ArduinoOTA.setPassword(OTA_PASSWORD);
  ArduinoOTA.onStart([]() { esp_camera_deinit(); });  // Bebaskan RAM & DMA kamera
  ArduinoOTA.begin();

  bootTime    = millis();
  lastFpsCalc = millis();

  DBG_PRINTLN(F("Web server aktif!"));
  DBG_PRINTLN(F("Endpoint tersedia:"));
  DBG_PRINTLN(F("  /        - Halaman kontrol"));
  DBG_PRINTLN(F("  :81/stream - MJPEG live stream (/stream dialihkan ke sini)"));
  DBG_PRINTLN(F("  /cmd?q=  - Kirim perintah ke robot"));
  DBG_PRINTLN(F("  /status  - Status JSON"));
  DBG_PRINTLN(F("  /led     - Kontrol LED flash"));
  DBG_PRINTLN(F("  /tune    - Kalibrasi & tuning MPU"));
  DBG_PRINT(F("Akses di: http://"));
  DBG_PRINTLN(WiFi.localIP());
  // (Kedip "siap" lama dihapus: kedip flash sekarang menandakan WiFi mana yang tersambung.)
}

// ============================================================================
// LOOP UTAMA
// ============================================================================
void loop() {
  unsigned long now = millis();

  // Layani permintaan HTTP
  server.handleClient();
  ArduinoOTA.handle();

  // Baca telemetri dari Arduino
  bacaTelemetriArduino();

  // Cek dan reconnect WiFi jika perlu
  cekKoneksiWifi(now);

  // Yield kecil agar watchdog ESP32 tidak timeout
  delay(1);
}
