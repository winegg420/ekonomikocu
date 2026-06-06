@echo off

chcp 65001 >nul

set PYTHONUNBUFFERED=1

cd /d "%~dp0"

curl.exe -s -m 2 http://127.0.0.1:9222/json/version >nul 2>&1

if errorlevel 1 start "" cmd /c "CHROME_X.bat" & timeout /t 10 /nobreak >nul

python tweet_tara.py --attach-port 9222 --require-cdp --max-scroll 300 --pause 2000

python analiz_devam.py

python rapor_durum.py

pause

