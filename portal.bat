@echo off
title Ultron Cybernetic Web HUD
color 0C
chcp 65001 >nul
cd /d "%~dp0"
echo Starting Ultron Web Control HUD...
python portal_server.py
pause
