@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
title TARAMA DURDUR
echo.
echo === TUM TARAMA DURDURULUYOR ===
echo Python ve kilit dosyasi temizleniyor.
echo Chrome pencerelerini SIZ kapatın (Ctrl+W veya X).
echo.
taskkill /F /IM python.exe /T 2>nul
if exist "log\tara_chrome.lock" del /F /Q "log\tara_chrome.lock"
echo.
echo Bitti. Simdi:
echo   1) Tum Chrome pencerelerini kapatin
echo   2) CHROME_X.bat — tek Chrome acin
echo   3) TARA_TUM_FLOOD.bat — tek CMD acin
echo.
pause
