@echo off
REM Quick launcher for Instantly CSV upload script

echo ========================================
echo INSTANTLY CSV UPLOADER
echo ========================================
echo.

cd /d "%~dp0..\..\..\"

echo Running upload script...
echo.

python modules\instantly\scripts\upload_csv_to_campaign.py

echo.
echo ========================================
echo.
pause
