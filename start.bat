@echo off
chcp 65001 > nul
title Schedule Generator

echo ========================================
echo       SCHEDULE GENERATOR v3.0
echo ========================================
echo.

cd /d "%~dp0"

REM Проверяем Python
python --version >nul 2>nul
if errorlevel 1 (
    echo ❌ Python not found!
    echo Install Python 3.8+ from python.org
    echo Check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Проверяем виртуальное окружение
if not exist "venv\Scripts\python.exe" (
    echo ⚠️  Virtual environment not found!
    echo Running install.bat...
    call install.bat
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 🚀 Starting Schedule Generator...
echo.
echo ⚠️  Keep this window open!
echo.
echo 🌐 Opening browser...
start "" "http://127.0.0.1:8000"
echo.
echo ⏹️  Press Ctrl+C to stop
echo ========================================
echo.

REM Запускаем сервер
cd app
python main.py

echo.
echo Application closed.
pause