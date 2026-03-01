@echo off
echo Setting up AutoPrint Pro silent autostart...
echo.

REM Delete old task if exists
schtasks /delete /tn "AutoPrintPro" /f >nul 2>&1

REM Create silent VBS launcher
echo Set objShell = CreateObject("WScript.Shell") > "C:\autoprint_pro\start_silent.vbs"
echo objShell.Run "cmd /c cd C:\autoprint_pro && python main.py", 0, False >> "C:\autoprint_pro\start_silent.vbs"

REM Create scheduled task - runs silently on login
schtasks /create /tn "AutoPrintPro" /tr "wscript.exe C:\autoprint_pro\start_silent.vbs" /sc onlogon /ru "%USERNAME%" /delay 0000:30 /f

echo.
REM Kill existing and restart silently
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 >nul
wscript.exe "C:\autoprint_pro\start_silent.vbs"

echo ✅ Done! AutoPrint Pro is running silently in background.
echo ✅ Will start automatically every time Windows starts.
echo.
echo To verify: Open Task Manager - Details tab - look for python.exe
echo.
pause
