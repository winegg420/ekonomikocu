@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUNBUFFERED=1
echo.
echo === ABONE TWEET METNI KAYDI ===
echo 1) CHROME_X.bat — Chrome AC, pencereyi KAPATMA
echo 2) x.com giris + @ekonomikocu ABONE oturumu
echo 3) Enter
echo.
pause
python abone_tamamla.py --since 2026-04-01 --per-round 400 --max-rounds 50
pause
