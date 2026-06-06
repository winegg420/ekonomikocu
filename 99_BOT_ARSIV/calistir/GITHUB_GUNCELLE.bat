@echo off
chcp 65001 >nul
cd /d "%~dp0\..\.."
echo Paket uretiliyor...
python "99_BOT_ARSIV\kod\claude_paket_olustur.py"
echo GitHub'a gonderiliyor...
python "99_BOT_ARSIV\kod\github_guncelle.py"
pause
