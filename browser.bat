@echo off
chcp 65001 > nul
title Schedule Generator Browser

echo Waiting for server to start...
timeout /t 5 /nobreak > nul

echo Opening browser...
start "" "http://127.0.0.1:8000"

echo Browser opened! You can close this window.
timeout /t 3 /nobreak > nul
exit