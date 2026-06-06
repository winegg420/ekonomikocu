@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
set PYTHONUNBUFFERED=1
echo.
echo === SIRA: 2026 %%100 -^> 2025 ===
echo.
pause
python kod\tara_sira.py
pause
