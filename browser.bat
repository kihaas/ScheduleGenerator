@echo off
chcp 65001 > nul
title Schedule Generator - Open Browser

echo ========================================
echo    SCHEDULE GENERATOR - OPEN BROWSER
echo ========================================
echo.

REM Проверяем доступность сервера
echo Checking if server is running...

set max_attempts=10
set attempt=1

:check_server
echo Attempt %attempt%/%max_attempts%...

powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; if ($response.StatusCode -eq 200) { exit 0 } } catch { exit 1 }"
if %errorlevel% equ 0 (
    echo Server is running!
    goto open_browser
)

echo Server not responding, waiting 2 seconds...
timeout /t 2 /nobreak > nul

set /a attempt+=1
if %attempt% gtr %max_attempts% (
    echo ERROR: Server not found after %max_attempts% attempts
    echo.
    echo Make sure server is running:
    echo 1. Run server.bat (for production)
    echo 2. Or start.bat (for development)
    echo.
    pause
    exit /b 1
)

goto check_server

:open_browser
echo.
echo Opening browser...
start "" "http://127.0.0.1:8000"

echo.
echo Browser opened!
echo You can close this window.
timeout /t 2 /nobreak > nul