@echo off
setlocal

echo Starting YouMe for mobile on local Wi-Fi...
echo.

set HOST=0.0.0.0
set PORT=5000
set OPEN_BROWSER=0
python app.py

endlocal
