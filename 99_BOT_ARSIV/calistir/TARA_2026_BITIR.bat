@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
echo.
echo === 2026 %%100 TAMAMLAMA ===
echo Tweet + abone + alinti + FLOOD — hepsi bitene kadar
echo 2025 taramasi BU SCRIPTTE YOK (2026 bitince TARA_2025_DEVAM.bat)
echo.
echo 1) CHROME_X.bat — Chrome AC, abone oturumu
echo 2) Bu pencereyi KAPATMA — log: log\tara_2026_bitir_stdout.txt
echo.
if not exist "log" mkdir log
python kod\tara_2026_bitir.py >> log\tara_2026_bitir_stdout.txt 2>&1
echo.
echo Bitti — log\tara_2026_bitir_stdout.txt
pause
