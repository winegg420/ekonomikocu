@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title ALINTI GECMIS FLOOD
echo.
echo === ALINTI GECMIS FLOOD (2025 -^> 2019) ===
echo 2025'te alintilanan gecmis tweetlerin TUM flood zinciri.
echo Tam 2025 arsivi DEGIL — sadece alinti + geriye BFS.
echo Takilinca otomatik yeniden baslar.
echo.
echo 1) Chrome acik — x.com/ekonomikocu
echo 2) Bu pencereyi KAPATMA
echo.

if exist "log\tara_chrome.lock" del /F /Q "log\tara_chrome.lock"
if not exist "log" mkdir log

curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version 2>nul
if errorlevel 1 (
  echo Chrome 9222 yok — CHROME_X.bat aciliyor...
  call "%~dp0CHROME_X.bat"
  timeout /t 25 /nobreak >nul
)

echo Basliyor: %date% %time%
echo.
python -u kod\tara_otomatik.py --script tara_alinti_gecmis.py --log alinti_gecmis_out.txt --stall-sec 420
echo.
echo Bitti: %date% %time%
pause
