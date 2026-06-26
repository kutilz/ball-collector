@echo off
echo ===================================================
echo Setup Ground Station - Robot Pengumpul Bola
echo ===================================================
echo.

cd /d "%~dp0ground-station"

echo [1/3] Memeriksa instalasi Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python tidak ditemukan! Harap install Python dan pastikan ditambahkan ke PATH.
    pause
    exit /b
)

echo [2/3] Membuat Virtual Environment (venv)...
if not exist "venv" (
    python -m venv venv
) else (
    echo Virtual Environment sudah ada.
)

echo [3/3] Menginstal dependencies dari requirements.txt...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Gagal menginstal dependencies!
    pause
    exit /b
)

echo.
echo ===================================================
echo Setup selesai! Anda sekarang bisa menjalankan program
echo dengan mengklik file: start_ground_station.bat
echo ===================================================
pause
