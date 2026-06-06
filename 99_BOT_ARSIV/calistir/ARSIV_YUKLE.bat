@echo off

chcp 65001 >nul

set PYTHONUNBUFFERED=1

cd /d "%~dp0"

if not exist "x_arsiv" mkdir "x_arsiv"

python arsiv_import.py

python rapor_durum.py

pause

