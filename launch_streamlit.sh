#!/bin/bash

# AlitaOS Streamlit Launch Script
# Clean, simple UI with Streamlit and OpenAI

set -e  # Exit on any error

echo "🚀 Starting AlitaOS (Streamlit Version)"
echo "======================================"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📍 Working directory: $SCRIPT_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your OPENAI_API_KEY"
    echo "Example:"
    echo "OPENAI_API_KEY=your_openai_api_key_here"
    exit 1
fi

# Check if OPENAI_API_KEY is set in .env
if ! grep -q "OPENAI_API_KEY" .env; then
    echo "❌ Error: OPENAI_API_KEY not found in .env file!"
    echo "Please add your OpenAI API key to the .env file:"
    echo "OPENAI_API_KEY=your_openai_api_key_here"
    exit 1
fi

echo "✅ Environment file found"

# Ensure Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.10+"
    exit 1
fi

# Create virtual environment named 'alitaOS' if it doesn't exist
if [ ! -d "alitaOS" ]; then
    echo "🔧 Creating virtual environment: alitaOS"
    python3 -m venv alitaOS
fi

echo "✅ Virtual environment present"

# Activate venv and install dependencies
source alitaOS/bin/activate
python -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies from requirements.txt"
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found, installing from pyproject.toml via pip may be incomplete."
    echo "   Please keep requirements.txt up to date."
fi

# Default realtime settings
export ALITA_REALTIME_PORT=${ALITA_REALTIME_PORT:-8787}
export OPENAI_REALTIME_MODEL=${OPENAI_REALTIME_MODEL:-gpt-4o-realtime-preview-2024-12-17}

# Launch AlitaOS with Streamlit and start realtime proxy (background)
echo "🎨 Launching AlitaOS (Streamlit)..."
echo "=================================="
echo "🌐 AlitaOS will be available at: http://localhost:8501"
echo "🔑 Make sure your OPENAI_API_KEY is valid"
echo "🎧 Realtime proxy listening on http://localhost:${ALITA_REALTIME_PORT}"
echo "=================================="

# Run realtime proxy
(
  cd app
  echo "▶️  Starting realtime proxy on 127.0.0.1:${ALITA_REALTIME_PORT} (HTTP)"
  python -m uvicorn realtime_proxy:app --host 127.0.0.1 --port ${ALITA_REALTIME_PORT}
) &

# Run Streamlit app (bind to localhost)
cd app
streamlit run alita_streamlit.py --server.port 8501

echo "👋 AlitaOS session ended. Goodbye!"
