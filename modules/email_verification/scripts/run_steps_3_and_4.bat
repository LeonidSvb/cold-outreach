@echo off
REM Auto-run Step 3 and Step 4 after verification completes

echo ======================================================================
echo RUNNING REMAINING STEPS (3 and 4)
echo ======================================================================
echo.

cd /d "%~dp0"

echo Step 3: Generating icebreakers...
py step3_generate_icebreakers.py
if errorlevel 1 (
    echo ERROR in Step 3!
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo.

echo Step 4: Creating final output files...
py step4_create_final_outputs.py
if errorlevel 1 (
    echo ERROR in Step 4!
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo ALL STEPS COMPLETE!
echo ======================================================================
echo.
echo Results saved to:
echo %~dp0..\results\
echo.
echo Check README_RESULTS.md for file descriptions
echo.
pause
