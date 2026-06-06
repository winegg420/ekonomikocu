@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Eski oturum siliniyor — acilan pencerede X'e tekrar gir.
python tweet_tara.py --prep
python tweet_tara.py --fresh-profile --login-only
pause
