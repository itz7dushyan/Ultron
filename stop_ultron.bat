@echo off
title Ultron Process Stopper
echo ========================================================
echo               STOPPING ULTRON BACKGROUND ENGINE
echo ========================================================
taskkill /F /IM pythonw.exe /T 2>nul
echo [OK] Ultron background service terminated cleanly.
echo.
timeout /t 2 >nul
