@echo off
echo ===================================================
echo Web Dakoku Tool - Library Installation
echo ===================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found.
    echo Please install Python and try again.
    echo Download from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Check Python version
python --version
echo.

echo Installing required libraries...
echo This may take a few minutes.
echo.

REM Update pip to the latest version
python -m pip install --upgrade pip

REM Install libraries from requirements.txt
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install libraries.
    echo Try running as administrator or install individually.
    echo.
    echo Individual installation command:
    echo python -m pip install pillow pystray selenium cryptography
    echo.
) else (
    echo.
    echo ===================================================
    echo Installation completed successfully!
    echo To use Web Dakoku Tool, double-click start_dakoku.bat
    echo ===================================================
    echo.
)

pause 