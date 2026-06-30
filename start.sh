#!/bin/bash
# start.sh — one-command setup & start
# Usage: ./start.sh          (port 8000)
#        ./start.sh 8080     (custom port)

PORT=${1:-8000}

# Auto-create venv if missing
if [ ! -d venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate 2>/dev/null || . venv/bin/activate

# Auto-install if missing
if [ ! -f venv/installed ]; then
  echo "Installing dependencies..."
  pip install -r requirements.txt --quiet
  touch venv/installed
fi

# Kill stale process on the same port
if command -v lsof &>/dev/null; then
  PID=$(lsof -ti:$PORT)
  [ -n "$PID" ] && kill -9 $PID 2>/dev/null
fi

echo ""
echo "  Applying migrations..."
python manage.py migrate --run-syncdb 2>&1 | tail -2
echo ""
echo "  Collecting static files..."
python manage.py collectstatic --noinput 2>&1 | tail -2
echo ""
echo "  Starting server..."
echo ""

python manage.py runserver 127.0.0.1:$PORT &
sleep 2

echo ""
echo "  ✅ Server is ready!"
echo ""
echo "  Open http://127.0.0.1:$PORT or http://localhost:$PORT in your browser"
echo ""
echo "  To stop: ./stop.sh"
echo ""

wait
