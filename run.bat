@echo off
title Ultron Desktop AI Assistant
color 0C
cd /d "%~dp0"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [Ultron exited or encountered an error]
    pause
)
