@echo off
chcp 65001 > nul
title Schedule Generator Browser

echo ========================================
echo    SCHEDULE GENERATOR BROWSER
echo ========================================
echo.

REM Ждем запуска сервера
echo Waiting for server to start...
echo Checking if server is ready...

set max_attempts=30
set attempt=1

:check_server
echo Attempt %attempt%/%max_attempts%...
timeout /t 2 /nobreak > nul

REM Проверяем доступность сервера
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2; if ($response.StatusCode -eq 200) { exit 0 } } catch { exit 1 }"
if %errorlevel% equ 0 (
    echo Server is ready!
    goto open_browser
)

set /a attempt+=1
if %attempt% gtr %max_attempts% (
    echo ERROR: Server not responding after %max_attempts% attempts
    echo Please check server window for errors
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b 1
)

goto check_server

:open_browser
echo.
echo Opening browser...
start "" "http://127.0.0.1:8000"

echo.
echo Browser opened! Server is running at http://127.0.0.1:8000
echo You can minimize this window.
echo.
echo Press any key to close this window...
pause > nul
exit