@echo off
REM start.bat — one-command setup & start
REM Usage: start.bat           (port 8000)
REM        start.bat 8080      (custom port)

set PORT=%1
if "%PORT%"=="" set PORT=8000

REM Auto-create venv if missing
if not exist venv\Scripts\activate (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

REM Auto-install if missing
if not exist venv\installed (
    echo Installing dependencies...
    pip install -r requirements.txt -q
    echo installed > venv\installed
)

echo Starting server...
start /B python manage.py runserver 0.0.0.0:%PORT% > nul 2>&1
timeout /t 2 /nobreak > nul
echo.
echo   Server is ready!
echo   Open http://localhost:%PORT% in your browser
echo.
echo   To stop: taskkill /F /IM python.exe 2^>nul
echo.
