#!/bin/bash
cd /Users/benzhome/Documents/GitHub/campsite-finder || exit 1

# Activate virtualenv if present
if [ -f venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

PORT=8501
ADDR=0.0.0.0

# prefer venv-installed streamlit when available
if [ -x venv/bin/streamlit ]; then
  STREAMLIT_BIN="$(pwd)/venv/bin/streamlit"
else
  STREAMLIT_BIN="$(command -v streamlit 2>/dev/null)"
  if [ -z "$STREAMLIT_BIN" ]; then
    echo "streamlit not found in venv or PATH; please install dependencies first" >&2
    exit 2
  fi
fi

if [ "$1" = "bg" ]; then
  nohup "$STREAMLIT_BIN" run app.py --server.address "$ADDR" --server.port "$PORT" --server.headless true > /tmp/streamlit_nohup.log 2>&1 &
  PID=$!
  mkdir -p .streamlit
  echo "$PID" > .streamlit/streamlit.pid
  echo "Started streamlit in background (PID $PID). Logs: /tmp/streamlit_nohup.log"
else
  exec "$STREAMLIT_BIN" run app.py --server.address "$ADDR" --server.port "$PORT"
fi
