@echo off
chcp 65001 > nul

echo Opening browser in 5 seconds...
timeout /t 5 /nobreak > nul
start "" "http://127.0.0.1:8000"
exit