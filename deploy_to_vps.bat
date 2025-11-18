@echo off
REM ========================================
REM VPS Deployment Script for Cold Outreach
REM ========================================
echo.
echo ======================================
echo VPS Deployment Script
echo ======================================
echo.

REM Check if arguments provided
if "%~1"=="" (
    echo Usage: deploy_to_vps.bat [VPS_IP] [USERNAME]
    echo.
    echo Example: deploy_to_vps.bat 185.123.45.67 root
    echo.
    pause
    exit /b 1
)

set VPS_IP=%~1
set VPS_USER=%~2
set SSH_KEY=C:Users79818.sshhostinger_key
set REMOTE_DIR=/root/cold-outreach

echo VPS IP: %VPS_IP%
echo Username: %VPS_USER%
echo SSH Key: %SSH_KEY%
echo Remote Directory: %REMOTE_DIR%
echo.

REM Test SSH connection
echo [1/6] Testing SSH connection...
ssh -i "%SSH_KEY%" -o StrictHostKeyChecking=no %VPS_USER%@%VPS_IP% "echo 'Connection successful'" 2>nul
if errorlevel 1 (
    echo ERROR: Cannot connect to VPS
    echo Please check:
    echo - IP address is correct
    echo - Username is correct
    echo - SSH key has proper permissions
    pause
    exit /b 1
)
echo ✓ Connection successful
echo.

REM Create directory structure
echo [2/6] Creating directory structure on VPS...
ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "mkdir -p %REMOTE_DIR%/modules/apollo/scripts && mkdir -p %REMOTE_DIR%/modules/apollo/results && mkdir -p %REMOTE_DIR%/modules/instantly/scripts && mkdir -p %REMOTE_DIR%/modules/instantly/results && mkdir -p %REMOTE_DIR%/modules/openai/scripts && mkdir -p %REMOTE_DIR%/modules/openai/results && mkdir -p %REMOTE_DIR%/modules/scraping/scripts && mkdir -p %REMOTE_DIR%/modules/scraping/results && mkdir -p %REMOTE_DIR%/modules/shared && mkdir -p %REMOTE_DIR%/data/raw && mkdir -p %REMOTE_DIR%/data/processed"
echo ✓ Directories created
echo.

REM Upload Python scripts
echo [3/6] Uploading Python scripts...
scp -i "%SSH_KEY%" -r modules/apollo/scripts/*.py %VPS_USER%@%VPS_IP%:%REMOTE_DIR%/modules/apollo/scripts/ 2>nul
scp -i "%SSH_KEY%" -r modules/instantly/scripts/*.py %VPS_USER%@%VPS_IP%:%REMOTE_DIR%/modules/instantly/scripts/ 2>nul
scp -i "%SSH_KEY%" -r modules/openai/scripts/*.py %VPS_USER%@%VPS_IP%:%REMOTE_DIR%/modules/openai/scripts/ 2>nul
scp -i "%SSH_KEY%" -r modules/scraping/scripts/*.py %VPS_USER%@%VPS_IP%:%REMOTE_DIR%/modules/scraping/scripts/ 2>nul
scp -i "%SSH_KEY%" -r modules/shared/*.py %VPS_USER%@%VPS_IP%:%REMOTE_DIR%/modules/shared/ 2>nul
echo ✓ Scripts uploaded
echo.

REM Upload requirements.txt if exists
echo [4/6] Uploading dependencies...
if exist requirements.txt (
    scp -i "%SSH_KEY%" requirements.txt %VPS_USER%@%VPS_IP%:%REMOTE_DIR%/
    echo ✓ requirements.txt uploaded
) else (
    echo ℹ No requirements.txt found, skipping
)
echo.

REM Upload .env file
echo [5/6] Uploading environment variables...
if exist .env (
    scp -i "%SSH_KEY%" .env %VPS_USER%@%VPS_IP%:%REMOTE_DIR%/
    echo ✓ .env uploaded
) else (
    echo ⚠ WARNING: No .env file found!
    echo You'll need to create it manually on VPS
)
echo.

REM Setup Python environment
echo [6/6] Setting up Python environment on VPS...
ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "cd %REMOTE_DIR% && python3 --version && pip3 --version"
if errorlevel 1 (
    echo ERROR: Python3 or pip3 not found on VPS
    echo Please install Python 3.8+ manually
    pause
    exit /b 1
)

ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "cd %REMOTE_DIR% && pip3 install requests pandas python-dotenv beautifulsoup4 openai --quiet"
echo ✓ Dependencies installed
echo.

echo ======================================
echo ✓ Deployment Complete!
echo ======================================
echo.
echo Your scripts are now on VPS at: %REMOTE_DIR%
echo.
echo To run scripts on VPS:
echo   ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP%
echo   cd %REMOTE_DIR%
echo   python3 modules/apollo/scripts/apollo_lead_collector.py
echo.
echo To setup cron jobs (auto-scheduling):
echo   ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP%
echo   crontab -e
echo.
pause
