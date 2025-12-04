@echo off
chcp 65001 > nul
title Schedule Generator Server

echo Starting Schedule Generator Server...
echo.

REM Переходим в корневую директорию проекта
cd /d "%~dp0"

REM Проверяем существование Python
if not exist "python\python.exe" (
    echo ERROR: Python not found!
    echo Expected path: %~dp0python\python.exe
    echo.
    echo Please download Python portable and extract to "python\" folder
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Проверяем существование основного файла приложения
if not exist "app\main.py" (
    echo ERROR: Main application file not found!
    echo Expected path: %~dp0app\main.py
    echo.
    echo Current directory: %CD%
    echo Files in app directory:
    dir app /b
    pause
    exit /b 1
)

echo Python path: %~dp0python\python.exe
echo App path: %~dp0app\main.py
echo.

REM Запускаем сервер через portable python
REM Используем рабочий каталог корень проекта, а app как модуль
cd /d "%~dp0"
python\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info --reload

echo.
echo Server stopped.
pause