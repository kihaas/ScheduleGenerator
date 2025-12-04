@echo off
chcp 65001 > nul
title Schedule Generator - Development Mode

echo ========================================
echo       SCHEDULE GENERATOR
echo ========================================
echo.
echo Starting in DEVELOPMENT mode...
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Проверяем зависимости
if not exist "requirements.txt" (
    echo WARNING: requirements.txt not found!
    echo Running installation...
    call install.bat
)

echo Checking dependencies...
python -c "import fastapi, uvicorn, jinja2, sqlalchemy, aiosqlite, pydantic" >nul 2>&1
if errorlevel 1 (
    echo Some dependencies missing. Installing...
    call install.bat
)

echo.
echo Starting server...
echo.

REM Запускаем сервер в новом окне с autoreload
start "Schedule Generator Server" cmd /k "cd /d %~dp0 && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Waiting 3 seconds for server to start...
timeout /t 3 /nobreak > nul

REM Проверяем запустился ли сервер
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2 -ErrorAction Stop; if ($response.StatusCode -eq 200) { exit 0 } } catch { exit 1 }"
if %errorlevel% equ 0 (
    echo Server started successfully!
    echo.
    echo Opening browser...
    start "" "http://127.0.0.1:8000"

    echo.
    echo ========================================
    echo     APPLICATION IS RUNNING!
    echo ========================================
    echo.
    echo Server:  http://127.0.0.1:8000
    echo Health:  http://127.0.0.1:8000/health
    echo.
    echo Press Ctrl+C in server window to stop
) else (
    echo ERROR: Server failed to start!
    echo Check the server window for errors
)

echo.
echo Press any key to close this window...
pause > nul