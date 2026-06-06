@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title FLOOD MEDYA INDIR
echo.
echo === FLOOD GORSEL INDIR ===
echo Flood parcalarinda eksik jpg/png dosyalarini indirir.
echo.
curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version 2>nul
if errorlevel 1 (
  echo Chrome 9222 yok — CHROME_X.bat aciliyor...
  call "%~dp0CHROME_X.bat"
  timeout /t 20 /nobreak >nul
)
python -u kod\flood_medya_indir.py %*
pause
