@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Bot izleyici: kod degisince tamamla_ocak_abone otomatik yeniden baslar.
echo Durdurmak: bu pencerede Ctrl+C
echo.
set PYTHONUNBUFFERED=1
python bot_izle.py
pause
