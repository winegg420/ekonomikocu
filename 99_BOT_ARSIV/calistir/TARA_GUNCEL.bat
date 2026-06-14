@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title GUNCEL TARAMA (sessiz)
echo.
echo === GUNCEL TARAMA (HIZLI / X API) ===
echo Son taramadan bugune TUM yeni tweet + flood + alinti — dakikalar icinde.
echo Chrome SESSIZ acilir (ekran disinda) — onune gelmez.
echo Bu pencereyi KAPATMA.
echo.

if exist "log\tara_chrome.lock" del /F /Q "log\tara_chrome.lock"
if not exist "log" mkdir log

curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version 2>nul
if errorlevel 1 (
  echo Chrome 9222 yok — sessiz Chrome aciliyor...
  call "%~dp0CHROME_X_SESSIZ.bat"
  timeout /t 18 /nobreak >nul
)

echo Basliyor: %date% %time%
echo.
python -u kod\tara_api.py
echo.
echo Analiz/zenginlestirme...
python kod\analiz_devam.py
echo.
echo Bitti: %date% %time%
pause
