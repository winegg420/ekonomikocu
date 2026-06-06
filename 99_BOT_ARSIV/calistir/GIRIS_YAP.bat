@echo off
chcp 65001 >nul
set PYTHONUNBUFFERED=1
cd /d "%~dp0"
echo.
echo === ONEMLI ===
echo Normal Chrome DEGIL — acilacak TEK Chromium penceresi.
echo X'e buradan girin. Bitince pencereyi kapatin.
echo.
python tweet_tara.py --prep
python tweet_tara.py --login-only
pause
