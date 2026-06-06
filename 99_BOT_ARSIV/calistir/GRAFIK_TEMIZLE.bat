@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Alakasiz grafikler temizleniyor (hisse logosu, onizleme fotosu)...
python temiz_alakasiz_grafik.py
pause
