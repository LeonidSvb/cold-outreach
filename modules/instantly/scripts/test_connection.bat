@echo off
REM Test Instantly API connection

echo ========================================
echo INSTANTLY API CONNECTION TEST
echo ========================================
echo.

cd /d "%~dp0..\..\..\"

echo Testing API connection...
echo.

python modules\instantly\scripts\test_instantly_connection.py

echo.
echo ========================================
echo.
pause
