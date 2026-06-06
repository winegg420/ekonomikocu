@echo off

chcp 65001 >nul

cd /d "%~dp0"

python claude_paket_olustur.py

echo.

echo Claude'a AT — 6 dosya sirayla:

echo   01_CLAUDE_BURADAN_BASLA.md

echo   08_AI_MENTOR_REHBERI.md

echo   02_ekonomikocu_hafiza_CLAUDE.md

echo   03_cekilen_tweetler_CLAUDE.jsonl

echo   04_CLAUDE_GRAFIKLER.zip

echo   05_CLAUDE_ANALIZ.md

echo.

explorer "%~dp0"

pause


