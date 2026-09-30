@echo off
setlocal enableextensions
title Robot Pengumpul Bola - Ground Station

REM =====================================================================
REM  LAUNCHER CERDAS - Ground Station Robot Pengumpul Bola
REM  Cukup DOUBLE-KLIK file ini. Script akan otomatis:
REM   1. Mencari Python (py launcher / PATH / lokasi instalasi umum)
REM   2. Kalau Python belum ada -> memasang otomatis dari python.org
REM   3. Membuat virtual environment + memasang library yang dibutuhkan
REM   4. Menjalankan aplikasi & membuka browser
REM  Kalau ada yang tidak bisa otomatis, akan muncul petunjuk manual.
REM
REM  Catatan: setup.bat memanggil file ini dengan argumen SETUP_ONLY
REM  (menyiapkan saja, tanpa menjalankan aplikasi).
REM =====================================================================

set "PYVER=3.11.9"
set "PYURL=https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe"
set "ROOT=%~dp0"
set "APPDIR=%ROOT%ground-station"

set "SETUP_ONLY=0"
if /I "%~1"=="SETUP_ONLY" set "SETUP_ONLY=1"

echo ===================================================
echo   Robot Pengumpul Bola - Ground Station
echo ===================================================
echo.

if not exist "%APPDIR%\app.py" (
    echo [ERROR] Folder "ground-station" atau file app.py tidak ditemukan.
    echo Pastikan file .bat ini berada di folder utama project ^(ball-collector^).
    echo Lokasi yang dicek: %APPDIR%
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------------
REM  1) Cari Python
REM ------------------------------------------------------------------
echo [1/4] Memeriksa Python...
call :FIND_PYTHON
if not defined PYCMD (
    echo      Python belum terpasang di komputer ini.
    echo      Mencoba memasang Python secara otomatis...
    echo.
    call :INSTALL_PYTHON
    call :FIND_PYTHON
)
if not defined PYCMD goto :PY_MANUAL
echo      Python siap dipakai: %PYCMD%
echo.

REM ------------------------------------------------------------------
REM  2) Virtual environment
REM ------------------------------------------------------------------
echo [2/4] Menyiapkan virtual environment...
set "VENVPY=%APPDIR%\venv\Scripts\python.exe"
if exist "%VENVPY%" (
    "%VENVPY%" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo      venv lama tidak cocok dengan komputer ini, membuat ulang...
        rmdir /s /q "%APPDIR%\venv" >nul 2>&1
    )
)
if not exist "%VENVPY%" (
    if exist "%APPDIR%\venv" rmdir /s /q "%APPDIR%\venv" >nul 2>&1
    echo      Membuat virtual environment baru...
    %PYCMD% -m venv "%APPDIR%\venv"
)
if not exist "%VENVPY%" (
    echo.
    echo [ERROR] Gagal membuat virtual environment.
    echo Coba jalankan ulang file ini. Jika tetap gagal, install ulang Python.
    echo.
    pause
    exit /b 1
)
echo      OK.
echo.

REM ------------------------------------------------------------------
REM  3) Dependencies (library)
REM ------------------------------------------------------------------
echo [3/4] Memeriksa library yang dibutuhkan...
"%VENVPY%" -c "import flask, flask_socketio, eventlet, cv2, numpy, requests" >nul 2>&1
if errorlevel 1 (
    echo      Memasang library ^(perlu internet, mohon tunggu 1-3 menit^)...
    "%VENVPY%" -m pip install --upgrade pip >nul 2>&1
    "%VENVPY%" -m pip install -r "%APPDIR%\requirements.txt"
    if errorlevel 1 (
        echo.
        echo [ERROR] Gagal memasang library.
        echo Kemungkinan besar tidak ada koneksi internet.
        echo Solusi: sambungkan komputer ke internet, lalu jalankan file ini lagi.
        echo.
        pause
        exit /b 1
    )
) else (
    echo      Semua library sudah terpasang.
)
echo.

if "%SETUP_ONLY%"=="1" (
    echo ===================================================
    echo   Setup selesai!
    echo   Jalankan start_ground_station.bat untuk memulai.
    echo ===================================================
    echo.
    pause
    exit /b 0
)

REM ------------------------------------------------------------------
REM  4) Jalankan aplikasi
REM ------------------------------------------------------------------
echo [4/4] Menjalankan aplikasi...
echo.
echo ===================================================
echo   Aplikasi berjalan di:  http://localhost:5000
echo   Browser akan terbuka otomatis beberapa detik lagi.
echo   Untuk berhenti: tutup jendela ini atau tekan Ctrl+C.
echo ===================================================
echo.

REM Buka browser SETELAH server sempat menyala (hindari halaman gagal dimuat).
start "" /min cmd /c "ping -n 5 127.0.0.1 >nul & start http://localhost:5000"

cd /d "%APPDIR%"
"%VENVPY%" app.py

echo.
echo Aplikasi berhenti.
pause
exit /b 0


REM =====================================================================
REM  SUBRUTIN
REM =====================================================================

:FIND_PYTHON
REM Mengisi PYCMD dengan perintah Python yang bisa dipakai; kosong bila tidak ada.
set "PYCMD="
REM 1) Python launcher "py" (paling andal, tidak terpengaruh PATH)
where py >nul 2>&1
if not errorlevel 1 (
    py -3.11 -c "import sys" >nul 2>&1 && ( set "PYCMD=py -3.11" & exit /b 0 )
    py -3 -c "import sys" >nul 2>&1 && ( set "PYCMD=py -3" & exit /b 0 )
)
REM 2) "python" di PATH (jalankan kode singkat agar bukan stub Microsoft Store)
python -c "import sys" >nul 2>&1 && ( set "PYCMD=python" & exit /b 0 )
REM 3) Lokasi instalasi umum (kalau Python ada tapi tidak masuk PATH)
for %%D in (
    "%LocalAppData%\Programs\Python\Python311"
    "%LocalAppData%\Programs\Python\Python312"
    "%LocalAppData%\Programs\Python\Python310"
    "%ProgramFiles%\Python311"
    "%ProgramFiles%\Python312"
) do (
    if not defined PYCMD if exist "%%~D\python.exe" (
        "%%~D\python.exe" -c "import sys" >nul 2>&1 && set "PYCMD=%%~D\python.exe"
    )
)
if defined PYCMD set PYCMD="%PYCMD%"
exit /b 0


:INSTALL_PYTHON
REM Mengunduh installer resmi python.org lalu memasang senyap (per-user + PATH).
set "PYSETUP=%TEMP%\python-%PYVER%-setup.exe"
echo      Mengunduh Python %PYVER% dari python.org ...
powershell -NoProfile -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYURL%' -OutFile '%PYSETUP%' } catch { exit 1 }"
if not exist "%PYSETUP%" (
    echo      Gagal mengunduh Python ^(koneksi internet bermasalah?^).
    exit /b 1
)
echo      Memasang Python ^(mohon tunggu, bisa 1-3 menit, jangan ditutup^)...
start "" /wait "%PYSETUP%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0
del "%PYSETUP%" >nul 2>&1
exit /b 0


:PY_MANUAL
echo.
echo ===================================================
echo   PYTHON BELUM BISA DIPASANG OTOMATIS
echo ===================================================
echo Silakan pasang Python secara manual ^(mudah, sekali saja^):
echo   1. Buka:  https://www.python.org/downloads/
echo   2. Unduh "Python 3.11" versi Windows 64-bit.
echo   3. Saat memasang, WAJIB centang "Add Python to PATH".
echo   4. Klik Install, tunggu selesai.
echo   5. Jalankan lagi file start_ground_station.bat ini.
echo.
pause
exit /b 1
