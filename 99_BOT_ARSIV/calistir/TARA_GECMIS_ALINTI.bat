@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title GECMIS ALINTI 2019
echo.
echo === GECMIS ALINTI TARAMA (2019'a kadar) ===
echo Koçun eski tweetleri + her alintinin flood'u.
echo SAATLER surebilir — Chrome ve bu pencere acik kalsin.
echo.
curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version 2>nul
if errorlevel 1 (
  echo Chrome 9222 yok — CHROME_X.bat aciliyor...
  call "%~dp0CHROME_X.bat"
  timeout /t 20 /nobreak >nul
)
python -u kod\tara_gecmis_alinti.py
pause
