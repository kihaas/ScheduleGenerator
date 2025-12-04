@echo off
chcp 65001 > nul
title Schedule Generator

echo ========================================
echo       SCHEDULE GENERATOR
echo ========================================
echo.

REM Устанавливаем зависимости
echo Installing dependencies...
pip install fastapi uvicorn jinja2 sqlalchemy aiosqlite pydantic

echo.
echo Starting application...
echo.

REM Запускаем сервер
start "Schedule Server" cmd /k "cd /d %~dp0 && uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM Ждем 5 секунд и открываем браузер
timeout /t 5 /nobreak > nul

echo Opening browser...
start "" http://127.0.0.1:8000

echo.
echo Application started!
echo Server: http://127.0.0.1:8000
echo Press Ctrl+C in server window to stop
pause