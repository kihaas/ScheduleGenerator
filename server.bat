@echo off
chcp 65001 > nul
title Schedule Generator Server

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Run install.bat first!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
cd app
python main.py