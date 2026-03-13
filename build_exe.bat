@echo off
setlocal

echo ============================================
echo      Building YouMe Portable EXE
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found in PATH.
  pause
  exit /b 1
)

if not exist "ffmpeg.exe" (
  echo [WARNING] ffmpeg.exe not found in project root.
  echo          The exe will still build, but merge/audio conversion may fail.
  echo.
  set "FFMPEG_ARG="
) else (
  set "FFMPEG_ARG=--add-data ffmpeg.exe;."
)

echo [1/4] Installing build tools...
python -m pip install --upgrade pip >nul
python -m pip install pyinstaller flask yt-dlp
if errorlevel 1 (
  echo [ERROR] Failed to install build dependencies.
  pause
  exit /b 1
)

echo [2/4] Cleaning previous build output...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "YouMeDownloader.spec" del /q "YouMeDownloader.spec"

echo [3/4] Building portable exe...
pyinstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --name "YouMeDownloader" ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  %FFMPEG_ARG% ^
  app.py

if errorlevel 1 (
  echo [ERROR] Build failed.
  pause
  exit /b 1
)

echo [4/4] Build complete.
echo Output: dist\YouMeDownloader.exe
echo.
echo Copy `YouMeDownloader.exe` anywhere and run it.
echo It will start a local server at http://127.0.0.1:5000
echo.
pause
endlocal
