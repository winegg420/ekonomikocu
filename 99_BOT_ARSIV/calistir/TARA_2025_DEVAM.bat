@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title TARAMA 2025
echo.
echo === 2025 TAM TARAMA ===
echo Ana tweet + abone + alinti + alinti FLOOD + #FLOOD
echo.
echo 1) Chrome acik kalsin — x.com/ekonomikocu
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

echo Takilinca otomatik yeniden baslar (7 dk sessizlik = restart).
echo Basliyor: %date% %time%
echo.
python -u kod\tara_otomatik.py --script tara_2025_devam.py --log tara_2025_devam_out.txt --stall-sec 420
echo.
echo Bitti: %date% %time%
pause
