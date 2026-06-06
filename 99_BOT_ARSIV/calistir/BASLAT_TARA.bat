@echo off

chcp 65001 >nul

set PYTHONUNBUFFERED=1

cd /d "%~dp0"

pip install -r requirements.txt -q 2>nul

echo.

echo 1) CHROME_X.bat — x.com/ekonomikocu acik kalsin, pencereyi KAPATMA
echo    Ustte "Abonelere ozel" normal; Retry varsa tikla

echo 2) Enter'a bas

echo.

pause

if exist "x_arsiv\*.zip" (
  echo Arsiv ZIP bulundu — once arsiv yukleniyor...
  python arsiv_import.py
) else (
  python arsiv_import.py 2>nul
)

python tweet_tara.py --purge-en --jsonl-only 2>nul

python tweet_tara.py --attach-port 9222 --require-cdp --max-scroll 500 --pause 3500 --skip-hafiza

python analiz_devam.py

python rapor_durum.py

pause

