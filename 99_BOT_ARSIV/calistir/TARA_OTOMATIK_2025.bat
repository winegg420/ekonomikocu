@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title TARAMA OTOMATIK 2025
echo.
echo === OTOMATIK 2025 TARAMA ===
echo Takilinca veya Chrome kopunca kendini yeniden baslatir.
echo Chrome: once CHROME_X.bat (bir kez) — sonra bu pencere acik kalsin.
echo.
curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version
if errorlevel 1 (
  echo Chrome 9222 yok — CHROME_X.bat aciliyor...
  call "%~dp0CHROME_X.bat"
  timeout /t 25 /nobreak >nul
)
python -u kod\tara_otomatik.py --script tara_2025_devam.py --log tara_2025_devam_out.txt --stall-sec 420
pause
