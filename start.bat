@echo off
chcp 65001 > nul
title Schedule Generator

echo ========================================
echo       SCHEDULE GENERATOR
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Installing dependencies...
python\python.exe -m pip install -r requirements.txt

echo.
echo Step 2: Starting application...
echo.

REM Запускаем браузер в отдельном окне
start "Schedule Browser" browser.bat

REM Запускаем сервер (это окно останется открытым)
server.bat

echo.
echo Application closed.
pause