#!/bin/bash
# start.sh — one-command setup & start
# Usage: ./start.sh          (port 8000)
#        ./start.sh 8080     (custom port)

set -e
PORT=${1:-8000}

# Auto-create venv if missing
if [ ! -d venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

# Auto-install if missing
if [ ! -f venv/installed ]; then
  echo "Installing dependencies..."
  pip install -r requirements.txt --quiet
  touch venv/installed
fi

# Kill stale process
if command -v lsof &>/dev/null; then
  PID=$(lsof -ti:$PORT)
  [ -n "$PID" ] && kill -9 $PID 2>/dev/null
fi

echo "Starting on http://0.0.0.0:$PORT ..."
python manage.py runserver 0.0.0.0:$PORT
