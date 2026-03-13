@echo off
echo ============================================
echo      YouMe - YouTube Downloader
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

:: Install dependencies silently if not present
echo [1/2] Checking dependencies...
pip install -r requirements.txt -q

:: Check ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] ffmpeg not found. Merging video+audio may not work.
    echo To install: winget install Gyan.FFmpeg  OR  choco install ffmpeg
    echo.
)

echo [2/2] Starting server...
echo.
echo  Open your browser at: http://127.0.0.1:5000
echo  Press Ctrl+C to stop.
echo.
python app.py
pause
