#!/usr/bin/env bash
# Launcher for macOS to run the Streamlit app on the local network
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/venv"

echo "Creating virtual environment (if missing)..."
python3 -m venv "$VENV_DIR"

echo "Activating venv and installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements.txt"

# Disable Streamlit telemetry for this run (explicit env var)
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

IP_ADDR="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")"

echo "Starting Streamlit on 0.0.0.0:8501 (accessible as http://$IP_ADDR:8501 on your LAN)"
streamlit run "$ROOT_DIR/app.py" --server.address 0.0.0.0 --server.port 8501
