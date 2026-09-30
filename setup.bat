@echo off
REM =====================================================================
REM  SETUP - Robot Pengumpul Bola (Ground Station)
REM  File ini hanya MENYIAPKAN: mendeteksi/memasang Python, membuat
REM  virtual environment, dan memasang library -- TANPA menjalankan aplikasi.
REM  Semua logika cerdas ada di start_ground_station.bat (argumen SETUP_ONLY).
REM
REM  Catatan: sebenarnya kamu tidak wajib menjalankan file ini lagi,
REM  karena start_ground_station.bat sudah otomatis menyiapkan semuanya.
REM =====================================================================
call "%~dp0start_ground_station.bat" SETUP_ONLY
