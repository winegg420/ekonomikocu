@echo off

chcp 65001 >nul

cd /d "%~dp0\.."

set PYTHONUNBUFFERED=1

echo.

echo === 2026 IZLEME MODU ===

echo Chrome kapanirsa otomatik yeniden acar, %%100 olana kadar devam eder.

echo Bu pencereyi KAPATMA.

echo.

if not exist "log" mkdir log

python kod\tara_izle.py >> log\tara_izle_stdout.txt 2>&1

pause

