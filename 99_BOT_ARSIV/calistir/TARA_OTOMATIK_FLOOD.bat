@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title TARAMA OTOMATIK FLOOD
echo.
echo === OTOMATIK FLOOD TARAMA ===
curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version
if errorlevel 1 (
  call "%~dp0CHROME_X.bat"
  timeout /t 25 /nobreak >nul
)
python -u kod\tara_otomatik.py --script tum_flood_tara.py --log tum_flood_out.txt --stall-sec 420
pause
