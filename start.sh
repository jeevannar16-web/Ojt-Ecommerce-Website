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

# Load seed data only on fresh database
SEED_FLAG="venv/.seed_loaded"
if [ ! -f "$SEED_FLAG" ]; then
  echo "  Loading seed data..."
  python manage.py loaddata fixtures/seed_data.json > /tmp/seed_load.log 2>&1
  if [ $? -eq 0 ]; then
    touch "$SEED_FLAG"
    echo "  ✅ Seed data loaded"
  else
    echo "  ⚠️  Seed data load failed:"
    tail -3 /tmp/seed_load.log
    echo "  (Delete venv/.seed_loaded and re-run to retry)"
  fi
else
  echo "  Seed data already loaded, skipping."
fi

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
