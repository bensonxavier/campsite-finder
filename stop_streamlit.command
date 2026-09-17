#!/bin/bash
cd /Users/benzhome/Documents/GitHub/campsite-finder || exit 1

# Prefer PID file stop if present
if [ -f .streamlit/streamlit.pid ]; then
  PID=$(cat .streamlit/streamlit.pid 2>/dev/null)
  if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null && rm -f .streamlit/streamlit.pid && echo "Stopped streamlit (PID $PID)" && exit 0
  fi
fi
if [ -f streamlit.pid ]; then
  PID=$(cat streamlit.pid 2>/dev/null)
  if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null && rm -f streamlit.pid && echo "Stopped streamlit (PID $PID)" && exit 0
  fi
fi

# Fallback: kill by process name
pkill -f "venv/bin/streamlit" 2>/dev/null && echo "Stopped streamlit (venv)" && exit 0
pkill -f "streamlit" 2>/dev/null && echo "Stopped streamlit" && exit 0

echo "No streamlit process found"
