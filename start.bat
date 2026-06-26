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

echo Starting on http://0.0.0.0:%PORT% ...
python manage.py runserver 0.0.0.0:%PORT%
