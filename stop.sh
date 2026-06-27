#!/bin/bash
# stop.sh — stop the Django dev server

PORT=${1:-8000}

if command -v lsof &>/dev/null; then
  PID=$(lsof -ti:$PORT)
  if [ -n "$PID" ]; then
    kill -9 $PID 2>/dev/null
    echo "Server on port $PORT stopped."
  else
    echo "No server running on port $PORT."
  fi
else
  pkill -f "manage.py runserver" 2>/dev/null && echo "Server stopped." || echo "No server found."
fi
