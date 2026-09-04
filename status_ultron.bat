@echo off
title Ultron Status Checker
echo ========================================================
echo                 ULTRON STATUS CHECKER
echo ========================================================
tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul | find /I /N "pythonw.exe">nul
if "%ERRORLEVEL%"=="0" (
    echo [STATUS: ACTIVE]
    echo Ultron is running silently in the background!
    echo Microphone is armed. Say "Hey Ultron" or "Wake up Ultron" to command.
) else (
    echo [STATUS: INACTIVE]
    echo Ultron is currently stopped.
    echo Double-click 'start_silent.vbs' to launch in the background.
)
echo ========================================================
pause
