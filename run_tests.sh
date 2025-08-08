#!/bin/bash

# AlitaOS Test Runner Script
# This script sets up the virtual environment and runs tests within it

set -e  # Exit on any error

echo "🧪 AlitaOS Test Runner"
echo "======================"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📍 Working directory: $SCRIPT_DIR"

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

# Run tests within the virtual environment
echo "🧪 Running AlitaOS functionality tests..."
echo "=========================================="

# Activate virtual environment and run the Python test script
source .venv/bin/activate
cd app
python ../test_alitaos_internal.py

echo "🏁 Test run complete!"
