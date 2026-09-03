@echo off
title Ultron Hands-Free Voice Assistant
color 0A
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo        ULTRON HANDS-FREE VOICE MODE (ACTIVE)
echo ========================================================
echo Just say "Hey Ultron", "Ultron", or "Wake up" to speak!
echo.
python main.py --voice
pause
