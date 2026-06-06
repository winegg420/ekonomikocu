@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
echo.
echo === 2026 GUNCEL TARAMA (%%100 hedef) ===
echo - Yeni tweetler hemen kayda
echo - Abone + alinti + #FLOOD tamamlama
echo.
echo 1) CHROME_X.bat — Chrome AC, pencereyi KAPATMA
echo 2) x.com giris + @ekonomikocu ABONE oturumu
echo 3) Enter
echo.
pause
python kod\tara_2026_guncel.py
echo.
echo Rapor: TARAMA_2026.md
pause
