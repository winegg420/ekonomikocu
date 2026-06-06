@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title ALINTI FLOOD TUM YILLAR
echo.
echo === ALINTI FLOOD — TUM YILLAR ===
echo Her is_quote satiri icin status flood cekilir.
echo 1) CHROME_X.bat acik — x.com/ekonomikocu
echo 2) Bu pencereyi KAPATMA
echo.
curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version 2>nul
if errorlevel 1 (
  echo Chrome 9222 yok — CHROME_X.bat aciliyor...
  call "%~dp0CHROME_X.bat"
  timeout /t 20 /nobreak >nul
)
python -u kod\alinti_flood_tara.py --yil tum --attach-port 9222 --max-scroll 50 --discover 500 --no-pack
pause
