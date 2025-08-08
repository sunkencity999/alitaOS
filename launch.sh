#!/bin/bash

# AlitaOS Launch Script
# This script sets up the virtual environment and launches the AlitaOS web GUI

set -e  # Exit on any error

echo "🚀 Starting AlitaOS Launch Sequence..."
echo "=================================="

# Get the script directory (works even if script is called from elsewhere)
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

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv package manager not found!"
    echo "Please install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "✅ uv package manager found"

# Create/sync virtual environment
echo "🔧 Setting up virtual environment..."
uv sync

echo "✅ Virtual environment ready"

# Check if chainlit is available
if ! .venv/bin/python -c "import chainlit" 2>/dev/null; then
    echo "❌ Error: Chainlit not properly installed"
    echo "Trying to reinstall dependencies..."
    uv sync --reinstall
fi

echo "✅ Dependencies verified"

# Launch AlitaOS
echo "🎙️ Launching AlitaOS..."
echo "=================================="
echo "🌐 AlitaOS will be available at: http://localhost:8000"
echo "🔑 Make sure your OPENAI_API_KEY is valid"
echo "🎤 Click 'Enable Microphone' when prompted for voice features"
echo "=================================="

# Activate virtual environment and run chainlit
source .venv/bin/activate
cd app
chainlit run alita.py --host 0.0.0.0 --port 8000

echo "👋 AlitaOS session ended. Goodbye!"
