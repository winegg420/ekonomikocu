@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title TUM FLOOD TARAMA
echo.
echo === TUM FLOOD: sabitle + alinti flood + #FLOOD ===
echo ONEMLI: Bu dosyayi SADECE BIR KEZ acin.
echo Once CHROME_X.bat ile tek Chrome acik olmali.
echo.
if exist "log\tara_chrome.lock" (
  echo HATA: Baska tarama calisiyor. Once DURDUR_TARAMA.bat calistirin.
  pause
  exit /b 1
)
curl.exe -s -o nul -m 3 http://127.0.0.1:9222/json/version
if errorlevel 1 (
  echo HATA: Chrome 9222 yok. Once CHROME_X.bat calistirin — bu dosya Chrome ACMAZ.
  pause
  exit /b 1
)
if not exist "log" mkdir log
echo Basliyor: %date% %time%
python -u kod\tum_flood_tara.py >> log\tum_flood_stdout.txt 2>&1
echo.
echo Bitti: %date% %time%
echo Log: log\tum_flood_stdout.txt ve alinti_flood_tara_tum.log
pause
