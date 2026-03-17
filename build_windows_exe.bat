@echo off
echo ============================================
echo   School Bell Scheduler - Build Script
echo ============================================
echo.

echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Building executable...
pyinstaller --onefile --noconsole --name SchoolBell ^
    --add-data "assets;assets" ^
    --add-data "locales;locales" ^
    --add-data "data;data" ^
    --icon "assets/icon.ico" ^
    app/main.py

if errorlevel 1 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build complete!
echo   Output: dist\SchoolBell.exe
echo ============================================
echo.
pause
