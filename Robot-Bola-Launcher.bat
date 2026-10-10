@echo off
setlocal enableextensions
title Robot Pengumpul Bola - Launcher

REM =====================================================================
REM  LAUNCHER MANDIRI - Robot Pengumpul Bola (Ground Station)
REM  Cukup kirim FILE INI SAJA ke siapa pun, lalu DOUBLE-KLIK. Script akan:
REM   1. Pertama kali  : mengunduh kode dari GitHub ke folder
REM                      %USERPROFILE%\ball-collector
REM   2. Klik berikutnya: mengecek versi baru di GitHub, menawarkan update
REM                      (kalau offline, langsung pakai versi yang ada)
REM   3. Menjalankan start_ground_station.bat: memasang Python + library
REM      bila perlu, lalu membuka web controller di browser.
REM  Tidak butuh git. Butuh internet saat pertama kali.
REM =====================================================================

set "REPO=kutilz/ball-collector"
set "BRANCH=master"
set "DEST=%USERPROFILE%\ball-collector"
set "ZIPURL=https://github.com/%REPO%/archive/refs/heads/%BRANCH%.zip"
set "APIURL=https://api.github.com/repos/%REPO%/commits/%BRANCH%"
set "VERFILE=%DEST%\.versi-launcher"
set "DLDIR=%TEMP%\ball-collector-unduh"

echo ===================================================
echo   Robot Pengumpul Bola - Launcher
echo   Lokasi kode: %DEST%
echo ===================================================
echo.

REM ------------------------------------------------------------------
REM  Cek versi terbaru di GitHub (kosong bila offline / GitHub tak bisa)
REM ------------------------------------------------------------------
echo Mengecek versi terbaru di GitHub...
set "LATEST="
for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (Invoke-RestMethod -UseBasicParsing -TimeoutSec 15 -Uri '%APIURL%').sha } catch { }"`) do set "LATEST=%%S"

if not exist "%DEST%\start_ground_station.bat" goto :FIRST_INSTALL

if not defined LATEST (
    echo      Tidak bisa mengecek GitHub ^(offline?^). Memakai versi yang sudah ada.
    goto :RUN
)
set "CURRENT="
if exist "%VERFILE%" set /p CURRENT=<"%VERFILE%"
if "%CURRENT%"=="%LATEST%" (
    echo      Kode sudah versi terbaru.
    goto :RUN
)
echo.
echo      Ada versi baru di GitHub.
echo      Catatan: update menimpa file kode ^(mis. config.py^), venv tetap dipakai.
choice /C YN /T 15 /D Y /M "     Update sekarang"
if errorlevel 2 goto :RUN
call :DOWNLOAD
if errorlevel 1 (
    echo      [PERINGATAN] Update gagal. Memakai versi yang sudah ada.
)
goto :RUN

:FIRST_INSTALL
echo.
echo Kode belum ada di komputer ini. Mengunduh dari GitHub ^(sekitar 40 MB^)...
call :DOWNLOAD
if errorlevel 1 (
    echo.
    echo [ERROR] Gagal mengunduh kode dari GitHub.
    echo Pastikan komputer tersambung ke internet, lalu jalankan file ini lagi.
    echo Alamat yang diunduh: %ZIPURL%
    echo.
    pause
    exit /b 1
)

:RUN
echo.
call "%DEST%\start_ground_station.bat"
exit /b %errorlevel%


REM =====================================================================
REM  SUBRUTIN
REM =====================================================================

:DOWNLOAD
REM Unduh zip repo -> ekstrak -> salin ke DEST (venv/logs lama tidak dihapus).
if exist "%DLDIR%" rmdir /s /q "%DLDIR%" >nul 2>&1
mkdir "%DLDIR%" >nul 2>&1
powershell -NoProfile -Command "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri '%ZIPURL%' -OutFile '%DLDIR%\kode.zip'; Expand-Archive -Force -Path '%DLDIR%\kode.zip' -DestinationPath '%DLDIR%\x' } catch { Write-Host ('      ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 exit /b 1

set "SRC="
for /d %%D in ("%DLDIR%\x\*") do set "SRC=%%~fD"
if not defined SRC exit /b 1
if not exist "%SRC%\start_ground_station.bat" exit /b 1

echo      Menyalin kode ke %DEST% ...
robocopy "%SRC%" "%DEST%" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 exit /b 1

REM Pastikan file .bat ber-line-ending CRLF (cmd bisa salah baca bila LF saja).
powershell -NoProfile -Command "Get-ChildItem -LiteralPath '%DEST%' -Filter *.bat | ForEach-Object { $t = [IO.File]::ReadAllText($_.FullName); [IO.File]::WriteAllText($_.FullName, ($t -replace '\r?\n', ([string][char]13 + [char]10))) }"

if defined LATEST (
    (echo %LATEST%)> "%VERFILE%"
) else (
    (echo tidak-diketahui)> "%VERFILE%"
)
rmdir /s /q "%DLDIR%" >nul 2>&1
echo      Kode siap.
exit /b 0
