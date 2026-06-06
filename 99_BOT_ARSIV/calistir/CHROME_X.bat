@echo off

chcp 65001 >nul

set "SESS=%LOCALAPPDATA%\ekonomikocu_x_session"

if not exist "%SESS%" mkdir "%SESS%"

echo.

echo === ONEMLI ===

echo 1) "Geri yukle" penceresini KAPAT

echo 2) Bu Chrome'da x.com/ekonomikocu acilir — tweetler gorunene kadar Retry

echo 3) Pencereyi KAPATMA — tarama .bat calistir

echo.

set "CHROME="

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (

  set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"

)

if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (

  set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"

)

if not defined CHROME if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (

  set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

)

if not defined CHROME (

  echo chrome.exe bulunamadi.

  pause

  exit /b 1

)

echo Chrome: %CHROME%

start "Chrome Ekonomikocu" "%CHROME%" --remote-debugging-port=9222 --user-data-dir="%SESS%" --lang=tr-TR --disable-features=Translate,TranslateUI https://x.com/ekonomikocu

exit /b 0

