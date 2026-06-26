@echo off
echo ===================================================
echo Memulai Ground Station - Robot Pengumpul Bola
echo ===================================================
echo.

cd /d "%~dp0ground-station"

if not exist "venv" (
    echo Virtual Environment belum dibuat. Silakan jalankan setup.bat terlebih dahulu!
    pause
    exit /b
)

echo Mengaktifkan Virtual Environment...
call venv\Scripts\activate.bat

echo Membuka browser...
start http://localhost:5000

echo Memulai aplikasi web (Flask)...
echo.
python app.py

pause
