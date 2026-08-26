@echo off
chcp 65001 >nul
REM === SESSIZ CHROME (ekran disinda, onunu kapatmaz) ===
REM Ayni profil + ayni port (9222) — sadece pencere ekran disinda acilir.
REM Boylece bot tararken Chrome senin onune gelmez, aramalari gormezsin.
set "SESS=%LOCALAPPDATA%\ekonomikocu_x_session"
if not exist "%SESS%" mkdir "%SESS%"

set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
if not defined CHROME (
  echo chrome.exe bulunamadi.
  exit /b 1
)

echo Sessiz Chrome aciliyor (ekran disinda, kismasiz)...
REM Anti-throttle: ekran disindaki pencerede X feed'i yine de yuklensin diye
REM arka plan/occluded kisma kapatildi.
start "Chrome Ekonomikocu Sessiz" "%CHROME%" --remote-debugging-port=9222 --user-data-dir="%SESS%" --lang=tr-TR --disable-features=Translate,TranslateUI,CalculateNativeWinOcclusion --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --window-position=-32000,-32000 --window-size=1400,1000 about:blank https://x.com/ekonomikocu
exit /b 0
