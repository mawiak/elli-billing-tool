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

REM Read and check credentials
findstr /C:"your.email@example.com" "%SETTINGS%" >nul
if %ERRORLEVEL% EQU 0 (
    echo Please configure your Elli account credentials first!
    echo.
    echo Edit %SETTINGS% and set:
    echo   - ELLI_EMAIL ^(your Elli account email^)
    echo   - ELLI_PASSWORD ^(your Elli account password^)
    echo.
    pause
    exit /b 1
)

findstr /C:"your_password" "%SETTINGS%" >nul
if %ERRORLEVEL% EQU 0 (
    echo Please configure your Elli account credentials first!
    echo.
    echo Edit %SETTINGS% and set:
    echo   - ELLI_EMAIL ^(your Elli account email^)
    echo   - ELLI_PASSWORD ^(your Elli account password^)
    echo.
    pause
    exit /b 1
)

REM Check if Station ID or RFID Card ID are empty
findstr /C:"""ELLI_STATION_ID"": """"" "%SETTINGS%" >nul
if %ERRORLEVEL% EQU 0 (
    goto :run_list
)

findstr /C:"""ELLI_RFID_CARD_ID"": """"" "%SETTINGS%" >nul
if %ERRORLEVEL% EQU 0 (
    goto :run_list
)

REM All settings look good, run generate
echo Configuration looks good, generating report...
echo.
"%BINARY%" generate %*
echo.
pause
exit /b 0

:run_list
echo Station ID or RFID Card ID not configured.
echo.
echo Running 'list' command to show your available IDs...
echo.
"%BINARY%" list
echo.
echo Please copy the IDs above into your %SETTINGS% file:
echo   - ELLI_STATION_ID
echo   - ELLI_RFID_CARD_ID
echo.
pause
exit /b 0
