@echo off

chcp 65001 >nul

cd /d "%~dp0"

echo.

echo === X ARSIV (tam tweet listesi) ===

echo ZIP = X'in e-postayla gonderdigi tweet dosya paketi.

echo @ekonomikocu hesabiyla giris yapilmis CHROME_X gerekir.

echo.

echo 1) CHROME_X.bat calistir (acik kalsin)

echo 2) Enter - indirme sayfasi acilir

echo.

pause

call CHROME_X.bat

timeout /t 8 /nobreak >nul

python arsiv_istek.py

echo.

echo ZIP gelince ARSIV_YUKLE.bat calistir.

pause

