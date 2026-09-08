@echo off
chcp 65001 > nul
title Jobpol Reserve Notifier

cd /d "%~dp0"

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python was not found in PATH.
    pause
    exit /b 1
)

if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Checking dependencies...
pip install -r requirements.txt > nul 2>&1

echo Checking Chromium...
playwright install chromium > nul 2>&1

if not exist ".env" (
    echo Missing .env configuration.
    copy .env.example .env > nul
    echo Please fill your settings in .env.
    notepad .env
    pause
    exit /b 0
)

echo Starting notifier...
python main.py --watch

pause
