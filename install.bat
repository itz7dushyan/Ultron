@echo off
title Ultron Installer
color 0C
echo ========================================================
echo               ULTRON ASSISTANT INSTALLER
echo ========================================================
echo.
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo Installing required Python libraries...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Some audio optional packages may have had issues.
    echo Ultron will still function with standard voice and terminal mode!
)

if not exist .env (
    echo Creating .env configuration from template...
    copy .env.example .env
    echo.
    echo [IMPORTANT] Please open .env in Notepad and paste your GROQ_API_KEY or OPENAI_API_KEY!
)

echo.
echo ========================================================
echo         ULTRON INSTALLATION COMPLETED SUCCESSFULLY!
echo ========================================================
echo You can now double-click 'run.bat' to start Ultron!
pause
