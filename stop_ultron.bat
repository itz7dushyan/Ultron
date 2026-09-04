@echo off
title Ultron Process Stopper
echo ========================================================
echo               STOPPING ULTRON BACKGROUND ENGINE
echo ========================================================
echo Terminating Ultron processes...
taskkill /F /IM pythonw.exe /T 2>nul
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" 2>nul
echo.
echo [SUCCESS] Ultron has been completely shut down!
echo.
timeout /t 2 >nul
