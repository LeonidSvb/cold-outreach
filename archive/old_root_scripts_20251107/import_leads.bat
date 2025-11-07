@echo off
REM Import leads to Supabase
REM Usage: import_leads.bat path\to\file.csv source_name

if "%1"=="" (
    echo Usage: import_leads.bat path\to\file.csv [source_name]
    echo.
    echo Examples:
    echo   import_leads.bat data.csv apollo
    echo   import_leads.bat "C:\Downloads\leads.csv" instantly
    exit /b 1
)

set CSV_FILE=%1
set SOURCE=%2

if "%SOURCE%"=="" (
    set SOURCE=manual
)

echo ========================================
echo IMPORTING LEADS TO SUPABASE
echo ========================================
echo File: %CSV_FILE%
echo Source: %SOURCE%
echo ========================================
echo.

py scripts\data_import\import_leads_to_supabase.py "%CSV_FILE%" %SOURCE%

pause
