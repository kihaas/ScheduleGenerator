@echo off
chcp 65001 > nul
title Schedule Generator - Installation

echo ========================================
echo       SCHEDULE GENERATOR v3.0
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python installation...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo.
    if exist "python-installer.exe" (
        echo Running Python installer...
        start /wait python-installer.exe
        echo Please restart this script!
    )
    pause
    exit /b 1
)

python --version
echo.

echo Step 1: Creating virtual environment...
if exist "venv" rmdir /s /q venv 2>nul
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment!
    pause
    exit /b 1
)

echo.
echo Step 2: Installing dependencies...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
python -m pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 aiosqlite==0.21.0 openpyxl==3.1.5 pydantic==2.12.5 jinja2==3.1.6 python-multipart==0.0.20 typing-extensions>=4.14.1

echo.
echo Step 3: Checking installation...
python -c "import fastapi; print('✓ fastapi installed')"
python -c "import pydantic; print('✓ pydantic installed')"
python -c "import aiosqlite; print('✓ aiosqlite installed')"
python -c "import openpyxl; print('✓ openpyxl installed')"

echo.
echo Step 4: Creating requirements.txt...
(
echo fastapi==0.104.1
echo uvicorn[standard]==0.24.0
echo aiosqlite==0.21.0
echo openpyxl==3.1.5
echo pydantic==2.12.5
echo jinja2==3.1.6
echo python-multipart==0.0.20
echo typing-extensions>=4.14.1
) > requirements.txt

echo.
echo ========================================
echo ✅ INSTALLATION COMPLETE!
echo.
echo Now run: start.bat
echo ========================================
echo.
pause