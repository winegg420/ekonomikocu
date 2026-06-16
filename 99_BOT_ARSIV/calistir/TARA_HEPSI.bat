@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
title TARA HEPSI (hizli + eksiksiz)
echo.
echo === TEK KOMUT: HIZLI + EKSIKSIZ TARAMA ===
echo Yeni tweet + flood + alinti + ABONE metin — dakikalar icinde.
echo Chrome kapaliysa ABONE profilli SESSIZ otomatik acilir.
echo Bu pencereyi KAPATMA.
echo.
python -u kod\tara_hizli_tam.py
echo.
echo Bitti.
pause
