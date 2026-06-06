@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title SABITLE + FLOOD
echo.
echo === SABITLENMIS TWEET + #FLOOD ===
echo 1) CHROME_X.bat acik — x.com/ekonomikocu
echo 2) Bu pencereyi KAPATMA
echo.
curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version 2>nul
if errorlevel 1 (
  echo Chrome 9222 yok — CHROME_X.bat aciliyor...
  call "%~dp0CHROME_X.bat"
  timeout /t 20 /nobreak >nul
)
python -u kod\pin_flood_tara.py --attach-port 9222
pause
