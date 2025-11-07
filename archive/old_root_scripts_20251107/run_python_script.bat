@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
echo Starting icebreaker generator...
echo.

python run_icebreaker.py

if %errorlevel% neq 0 (
    echo.
    echo Error occurred with code: %errorlevel%
) else (
    echo.
    echo Generation completed successfully!
)

pause
