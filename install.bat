@echo off
chcp 65001 > nul
title Schedule Generator - Install Dependencies

echo ========================================
echo       SCHEDULE GENERATOR - INSTALL
echo ========================================
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

echo Installing/updating dependencies...
echo.

REM Устанавливаем зависимости
pip install --upgrade pip
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 jinja2==3.1.2 sqlalchemy==2.0.23 aiosqlite==0.19.0 pydantic==2.5.0 pydantic-settings==2.1.0 openpyxl==3.1.2

echo.
echo Creating requirements.txt...
pip freeze > requirements.txt

echo.
echo ========================================
echo     INSTALLATION COMPLETE!
echo ========================================
echo.
echo Dependencies installed successfully!
echo You can now run the application with:
echo    start.bat     - For development with browser auto-open
echo    server.bat    - For server only
echo.
pause