@echo off
chcp 65001 > nul
title Schedule Generator Server

echo Starting Schedule Generator Server...
echo.

cd /d "%~dp0"

REM Запускаем сервер через portable python
python\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level error

echo.
echo Server stopped.
pause