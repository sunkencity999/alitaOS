#!/bin/bash

# AlitaOS Streamlit HTTPS Launch Script
# Generates a self-signed cert on first run and serves Streamlit over HTTPS (localhost)

set -e

echo "🔐 Starting AlitaOS over HTTPS (Streamlit)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check .env
if [ ! -f ".env" ]; then
  echo "❌ .env not found. Please create it with OPENAI_API_KEY=..."
  exit 1
fi

# Ensure Python
if ! command -v python3 &>/dev/null; then
  echo "❌ python3 not found. Install Python 3.10+"
  exit 1
fi

# Venv
if [ ! -d "alitaOS" ]; then
  echo "🔧 Creating virtual environment: alitaOS"
  python3 -m venv alitaOS
fi
source alitaOS/bin/activate
python -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi

# Create certs dir
CERT_DIR=".cert"
mkdir -p "$CERT_DIR"
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"

# Generate self-signed cert if missing
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
  echo "🪪 Generating self-signed TLS certificate (localhost)"
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" -out "$CERT_FILE" \
    -subj "/C=US/ST=CA/L=Local/O=AlitaOS/OU=Dev/CN=localhost"
fi

# Default realtime settings
export ALITA_REALTIME_PORT=${ALITA_REALTIME_PORT:-8787}
export OPENAI_REALTIME_MODEL=${OPENAI_REALTIME_MODEL:-gpt-4o-realtime-preview-2024-12-17}

# Launch Streamlit with HTTPS on localhost and start realtime proxy with TLS
cd app

echo "🌐 Open https://localhost:8501 (accept the browser warning)"

# Start realtime proxy with TLS so browser can call it from HTTPS page
echo "▶️  Starting realtime proxy on 127.0.0.1:${ALITA_REALTIME_PORT} (HTTPS)"
python -m uvicorn realtime_proxy:app \
  --host 127.0.0.1 \
  --port ${ALITA_REALTIME_PORT} \
  --ssl-keyfile ../$KEY_FILE \
  --ssl-certfile ../$CERT_FILE &

streamlit run alita_streamlit.py \
  --server.port 8501 \
  --server.sslCertFile ../$CERT_FILE \
  --server.sslKeyFile ../$KEY_FILE
