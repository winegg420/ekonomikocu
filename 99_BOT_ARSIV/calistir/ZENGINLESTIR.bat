@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title VERI ZENGINLESTIRME
echo.
echo === VERI ZENGINLESTIRME (yeni veri toplamaz) ===
echo 1) kaynak etiketle  2) cagri cikar  3) grafik vision
echo.
python -u kod\enrichment\calistir_hepsi.py
pause
