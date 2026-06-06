@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title ALINTI FLOOD 2025
echo.
echo === ALINTI FLOOD 2025 ===
echo 1) Chrome acik — x.com/ekonomikocu
echo 2) Bu pencereyi KAPATMA
echo.

if exist "log\tara_chrome.lock" del /F /Q "log\tara_chrome.lock"
if not exist "log" mkdir log

curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version 2>nul
if errorlevel 1 (
  echo Chrome 9222 yok — CHROME_X.bat aciliyor...
  call "%~dp0CHROME_X.bat"
  timeout /t 20 /nobreak >nul
)

echo Basliyor: %date% %time%
echo.
python -u kod\alinti_flood_tara.py --yil gecmis --attach-port 9222 --max-scroll 50 --discover 2500 --kesif-yillar 2025,2026
echo.
echo Bitti: %date% %time%
pause
