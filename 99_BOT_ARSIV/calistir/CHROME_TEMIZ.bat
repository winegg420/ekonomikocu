@echo off
chcp 65001 >nul
echo.
echo === CHROME TEMIZ BASLAT ===
echo Once tum Chrome pencerelerini kapatin, sonra bir tusa basin.
echo.
pause
taskkill /F /IM chrome.exe /T 2>nul
timeout /t 3 /nobreak >nul
call "%~dp0CHROME_X.bat"
echo.
echo Chrome acildi. x.com/ekonomikocu gorunene kadar bekleyin.
echo Siyah ekran ise F5 veya adres cubuguna: https://x.com/ekonomikocu
pause
