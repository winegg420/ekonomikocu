@echo off

chcp 65001 >nul

set PYTHONUNBUFFERED=1

cd /d "%~dp0"



echo.

echo === ALINTI TAMAMLA ===

echo Dogru dosyadasin: ALINTI_TAMAMLA

echo.

echo 1) CHROME_X dosyasina cift tikla — Chrome acik kalsin

echo 2) x.com yuklensin

echo 3) Bu dosyaya (ALINTI_TAMAMLA) tekrar cift tikla

echo.



netstat -an | findstr ":9222" | findstr "LISTENING" >nul

if errorlevel 1 (

  echo Chrome acilmadi — CHROME_X calistiriliyor...

  call "%~dp0CHROME_X.bat"

  timeout /t 15 /nobreak >nul

)



python alinti_dogrula.py

if errorlevel 1 (

  echo Alintilar dolduruluyor...

  python alinti_tamamla.py

  python alinti_dogrula.py

) else (

  echo Alintilar zaten tamam.

)



echo.

pause

