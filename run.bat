@echo off
REM Elli Billing Tool Launcher for Windows
REM This script intelligently decides whether to run 'list' or 'generate'

cd /d "%~dp0"

set BINARY=elli-billing-tool.exe
set SETTINGS=settings.json

echo ==========================================
echo Elli Billing Tool
echo ==========================================
echo.

REM Check if settings.json exists
if not exist "%SETTINGS%" (
    echo Error: %SETTINGS% not found!
    echo.
    pause
    exit /b 1
)

if "%~1"=="login" goto :direct
if "%~1"=="logout" goto :direct
if "%~1"=="status" goto :direct
if "%~1"=="oauth-callback" goto :direct

REM Check if Station ID is empty (RFID Card ID is optional)
findstr /R "\"ELLI_STATION_ID\".*:.*\"\"" "%SETTINGS%" >nul
if %ERRORLEVEL% EQU 0 (
    goto :run_list
)

REM All settings look good, run generate
echo Configuration looks good, generating report...
echo.
if "%~1"=="" (
    "%BINARY%" generate
) else (
    "%BINARY%" %*
)
echo.
pause
exit /b 0

:direct
"%BINARY%" %*
exit /b %ERRORLEVEL%

:run_list
echo Station ID not configured.
echo.
echo Running 'list' command to show your available IDs...
echo.
"%BINARY%" list
echo.
echo Please copy the Station ID into your %SETTINGS% file:
echo   - ELLI_STATION_ID ^(required^)
echo   - ELLI_RFID_CARD_ID ^(optional - leave empty to include all sessions^)
echo.
pause
exit /b 0
