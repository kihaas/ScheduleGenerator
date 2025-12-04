@echo off
chcp 65001 > nul
title Schedule Generator Server

echo ========================================
echo       SCHEDULE GENERATOR SERVER
echo ========================================
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
python -c "import fastapi, uvicorn, jinja2, sqlalchemy, aiosqlite, pydantic" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Dependencies missing!
    echo Please run install.bat first
    pause
    exit /b 1
)

echo.
echo Starting server in PRODUCTION mode...
echo Server will run at: http://127.0.0.1:8000
echo Press Ctrl+C to stop
echo.

REM Запускаем сервер без autoreload
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info

echo.
echo Server stopped.
pause