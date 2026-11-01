// Contoh daftar WiFi. Salin jadi wifi_secrets.h (di-gitignore) lalu isi.
// Urutan = prioritas: jaringan paling atas yang terlihat saat scan dipakai duluan.
// Password kosong ("") untuk jaringan terbuka.
#pragma once

struct WifiCred {
  const char* ssid;
  const char* pass;
};

static const WifiCred WIFI_LIST[] = {
  {"NamaWiFi_Utama",    "PasswordUtama"},
  {"NamaWiFi_Cadangan", "PasswordCadangan"},
};

// Password upload firmware lewat WiFi (OTA)
#define OTA_PASSWORD "GantiPasswordOTA"
