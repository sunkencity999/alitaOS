#!/bin/bash

# AlitaOS Installer (macOS/Linux)
set -e

echo "🚀 Installing AlitaOS (Streamlit)"

# Move to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📍 Working directory: $SCRIPT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
  echo "❌ Python3 not found. Please install Python 3.10+"
  exit 1
fi

# Create venv named alitaOS if missing
if [ ! -d "alitaOS" ]; then
  echo "🔧 Creating virtual environment: alitaOS"
  python3 -m venv alitaOS
fi

# Activate and install deps
source alitaOS/bin/activate
python -m pip install --upgrade pip

if [ -f "requirements.txt" ]; then
  echo "📦 Installing dependencies from requirements.txt"
  pip install -r requirements.txt
else
  echo "❌ requirements.txt not found. Aborting."
  exit 1
fi

# Ensure .env exists
if [ ! -f ".env" ]; then
  echo "🔐 Creating .env template"
  cat > .env <<EOF
OPENAI_API_KEY=
EOF
  echo "➡️  Please edit .env and set OPENAI_API_KEY."
fi

echo "✅ Installation complete. To launch:"
echo "   bash ./launch_streamlit.sh"
