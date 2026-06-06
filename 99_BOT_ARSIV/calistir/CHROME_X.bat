@echo off
chcp 65001 >nul
set SESS=%LOCALAPPDATA%\ekonomikocu_x_session
if not exist "%SESS%" mkdir "%SESS%"
echo.
echo === ONEMLI ===
echo 1) "Geri yukle" penceresini KAPAT
echo 2) Bu Chrome'da x.com/ekonomikocu acilir — tweetler gorunene kadar Retry
echo 3) Pencereyi KAPATMA — BASLAT_TARA.bat calistir
echo.
for %%P in (
  "%ProgramFiles%\Google\Chrome\Application\chrome.exe"
  "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
  "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
) do if exist "%%P" set CHROME=%%P
if not defined CHROME (
  echo chrome.exe bulunamadi.
  pause
  exit /b 1
)
start "" "%CHROME%" --remote-debugging-port=9222 --user-data-dir="%SESS%" --lang=tr-TR --disable-features=Translate,TranslateUI "https://x.com/ekonomikocu"
