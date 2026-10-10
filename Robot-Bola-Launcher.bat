@echo off
setlocal enableextensions
title Robot Pengumpul Bola - Launcher

REM =====================================================================
REM  LAUNCHER MANDIRI - Robot Pengumpul Bola (Ground Station)
REM  Cukup kirim FILE INI SAJA ke siapa pun, lalu DOUBLE-KLIK. Script akan:
REM   1. Menentukan folder project:
REM      - kalau file ini ada DI DALAM folder project (ada
REM        start_ground_station.bat + ground-station\app.py) -> folder itu
REM      - selain itu -> %USERPROFILE%\ball-collector (dibuat bila belum ada)
REM   2. Folder belum ada  : mengunduh kode dari GitHub (tanpa git)
REM      Folder sudah ada  : mengecek versi baru dan menawarkan update
REM        - hasil git clone -> git pull (perubahan lokal tidak ditimpa)
REM        - hasil unduhan   -> salin ulang kode (venv/logs tetap)
REM      Kalau offline, langsung pakai versi yang sudah ada.
REM   3. Menjalankan start_ground_station.bat: memasang Python + library
REM      bila perlu, lalu membuka web controller di browser.
REM =====================================================================

REM File ini bisa ikut ter-update saat proses update. cmd membaca .bat
REM sambil jalan, jadi jalankan salinan di %TEMP% supaya tidak kacau.
REM (Tanpa "call": kendali pindah ke salinan dan tidak kembali ke sini.)
if /I not "%~1"=="--dari-temp" (
    copy /y "%~f0" "%TEMP%\robot-bola-launcher.bat" >nul 2>&1 && "%TEMP%\robot-bola-launcher.bat" --dari-temp "%~dp0."
)
REM HERE = folder tempat file launcher ASLI berada.
if /I "%~1"=="--dari-temp" (
    set "HERE=%~f2"
) else (
    for %%I in ("%~dp0.") do set "HERE=%%~fI"
)

set "REPO=kutilz/ball-collector"
set "BRANCH=master"
set "ZIPURL=https://github.com/%REPO%/archive/refs/heads/%BRANCH%.zip"
set "APIURL=https://api.github.com/repos/%REPO%/commits/%BRANCH%"
set "DLDIR=%TEMP%\ball-collector-unduh"

REM ------------------------------------------------------------------
REM  Tentukan folder project
REM ------------------------------------------------------------------
call :IS_PROJECT "%HERE%"
if not errorlevel 1 (
    set "DEST=%HERE%"
) else (
    set "DEST=%USERPROFILE%\ball-collector"
)
set "VERFILE=%DEST%\.versi-launcher"

echo ===================================================
echo   Robot Pengumpul Bola - Launcher
echo   Folder project: %DEST%
echo ===================================================
echo.

call :IS_PROJECT "%DEST%"
if not errorlevel 1 goto :UPDATE

REM Folder belum jadi project. Kalau ternyata sudah berisi file lain,
REM jangan ditimpa -- minta pengguna memindahkannya dulu.
if exist "%DEST%\" (
    dir /b /a "%DEST%" 2>nul | findstr "^" >nul
    if not errorlevel 1 (
        echo [ERROR] Folder "%DEST%" sudah ada dan berisi file lain,
        echo         tapi bukan folder project Robot Pengumpul Bola.
        echo Solusi: ganti nama / pindahkan folder itu, lalu jalankan file ini lagi.
        echo.
        pause
        exit /b 1
    )
)

echo Kode belum ada di komputer ini. Mengunduh dari GitHub ^(sekitar 40 MB^)...
call :GET_LATEST
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
goto :RUN

REM ------------------------------------------------------------------
REM  Folder project sudah ada -> cek & tawarkan update
REM ------------------------------------------------------------------
:UPDATE
echo Mengecek versi terbaru di GitHub...
if exist "%DEST%\.git\" goto :UPDATE_GIT

call :GET_LATEST
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
echo      Ada versi baru di GitHub.
echo      Catatan: update menimpa file kode ^(mis. config.py^), venv tetap dipakai.
choice /C YN /T 15 /D Y /M "     Update sekarang"
if errorlevel 2 goto :RUN
call :DOWNLOAD
if errorlevel 1 echo      [PERINGATAN] Update gagal. Memakai versi yang sudah ada.
goto :RUN

:UPDATE_GIT
REM Folder hasil git clone: update lewat git supaya perubahan lokal aman.
where git >nul 2>&1
if errorlevel 1 (
    echo      Folder ini repo git, tapi program git tidak ditemukan. Update dilewati.
    goto :RUN
)
git -C "%DEST%" fetch -q origin %BRANCH% >nul 2>&1
if errorlevel 1 (
    echo      Tidak bisa mengecek GitHub ^(offline?^). Memakai versi yang sudah ada.
    goto :RUN
)
git -C "%DEST%" merge-base --is-ancestor FETCH_HEAD HEAD >nul 2>&1
if not errorlevel 1 (
    echo      Kode sudah versi terbaru.
    goto :RUN
)
echo      Ada versi baru di GitHub ^(update lewat git pull^).
choice /C YN /T 15 /D Y /M "     Update sekarang"
if errorlevel 2 goto :RUN
git -C "%DEST%" pull --ff-only origin %BRANCH%
if errorlevel 1 (
    echo      [PERINGATAN] git pull gagal ^(ada perubahan lokal yang bentrok?^).
    echo      Memakai versi yang sudah ada.
)

:RUN
echo.
call "%DEST%\start_ground_station.bat"
exit /b %errorlevel%


REM =====================================================================
REM  SUBRUTIN
REM =====================================================================

:IS_PROJECT
REM errorlevel 0 bila folder %1 adalah folder project ground station.
if exist "%~1\start_ground_station.bat" if exist "%~1\ground-station\app.py" exit /b 0
exit /b 1

:GET_LATEST
REM Isi LATEST dengan SHA commit terbaru di GitHub (kosong bila offline).
set "LATEST="
for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (Invoke-RestMethod -UseBasicParsing -TimeoutSec 15 -Uri '%APIURL%').sha } catch { }"`) do set "LATEST=%%S"
exit /b 0

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
