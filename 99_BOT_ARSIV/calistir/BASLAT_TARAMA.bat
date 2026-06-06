@echo off

chcp 65001 >nul

cd /d "%~dp0\.."

set PYTHONUNBUFFERED=1

title EKONOMIKOCU TARAMA

echo.

echo === TARAMA BASLAT ===

echo Bu pencereyi KAPATMA. Kapatirsan bot durur.

echo.



if exist "log\tara_chrome.lock" del /F /Q "log\tara_chrome.lock"



powershell -NoProfile -Command "try { Invoke-WebRequest 'http://127.0.0.1:9222/json/version' -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"

if errorlevel 1 (

  echo Chrome aciliyor...

  call "%~dp0CHROME_X.bat"

  timeout /t 12 /nobreak >nul

)



if not exist "log" mkdir log

echo Tarama basliyor: %date% %time%

echo.

python -u kod\tara_izle.py

echo.

echo Bot durdu. Bu dosyaya tekrar cift tikla.

pause

