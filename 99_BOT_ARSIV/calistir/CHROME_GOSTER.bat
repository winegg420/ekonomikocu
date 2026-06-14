@echo off
chcp 65001 >nul
REM === SESSIZ CHROME'U EKRANA GETIR ===
REM Eger sessiz Chrome'da bir sey gormen gerekirse (giris/Retry) bunu calistir:
REM acik olan Chrome penceresini ekranin ortasina tasir.
powershell -NoProfile -Command ^
  "Add-Type -Namespace W -Name U -MemberDefinition '[DllImport(\"user32.dll\")] public static extern bool SetWindowPos(IntPtr h,IntPtr a,int x,int y,int cx,int cy,uint f); [DllImport(\"user32.dll\")] public static extern bool ShowWindow(IntPtr h,int n);'; Get-Process chrome -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | ForEach-Object { [W.U]::SetWindowPos($_.MainWindowHandle,[IntPtr]::Zero,200,120,1400,1000,0x40) | Out-Null; [W.U]::ShowWindow($_.MainWindowHandle,5) | Out-Null }"
echo Sessiz Chrome ekrana getirildi (varsa).
pause
