$chrome = "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) { $chrome = "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe" }
$sess = "$env:LOCALAPPDATA\ekonomikocu_x_session"
if (-not (Test-Path $sess)) { New-Item -ItemType Directory -Path $sess -Force | Out-Null }
Start-Process -FilePath $chrome -ArgumentList @(
  "--remote-debugging-port=9222",
  "--user-data-dir=$sess",
  "--lang=tr-TR",
  "https://x.com/ekonomikocu"
)
Write-Host "Chrome acildi (port 9222). x.com/ekonomikocu yuklensin."
