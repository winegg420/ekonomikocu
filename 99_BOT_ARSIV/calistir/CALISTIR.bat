@echo off

chcp 65001 >nul

set PYTHONUNBUFFERED=1

cd /d "%~dp0"

if not exist "x_arsiv" mkdir "x_arsiv"



echo [1/4] Chrome kontrol...

curl.exe -s -m 2 http://127.0.0.1:9222/json/version >nul 2>&1

if errorlevel 1 (

  echo Chrome aciliyor...

  start "" cmd /c "CHROME_X.bat"

  timeout /t 12 /nobreak >nul

)



echo [2/4] Arsiv ZIP varsa yukle...

python arsiv_import.py 2>nul



echo [3/4] Profil tarama...

python tweet_tara.py --attach-port 9222 --require-cdp --max-scroll 500 --pause 2500 --skip-hafiza

if errorlevel 1 (

  echo Tarama kismi hata - mevcut veri korunuyor.

)



echo [4/4] Analiz...

python analiz_devam.py 2>nul

python rapor_durum.py



echo.

echo Bitti. Dosya: cekilen_tweetler.jsonl

pause

