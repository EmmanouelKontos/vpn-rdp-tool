#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting build process for UniversalVPNTool..."

# Dynamically determine the project root (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "📁 Project root detected: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Set virtual environment path
VENV_DIR="$PROJECT_ROOT/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"

# Create virtual environment if it doesn't exist
if [ ! -f "$VENV_PYTHON" ]; then
    echo "🐍 Virtual environment not found. Creating one at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# Upgrade pip and install dependencies
echo "📦 Installing dependencies..."
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt pyinstaller

# Clean previous build artifacts
echo "🧹 Cleaning previous build artifacts..."
rm -rf build dist *.spec

# Detect OS
OS_TYPE=$(uname -s)

# Build executable
if [ "$OS_TYPE" == "Darwin" ]; then
    echo "🍏 Detected macOS. Building executable..."
    "$VENV_DIR/bin/pyinstaller" --onefile --name UniversalVPNTool main.py
    echo "✅ macOS executable built successfully in $PROJECT_ROOT/dist/"
elif [ "$OS_TYPE" == "Linux" ]; then
    echo "🐧 Detected Linux. Building executable..."
    "$VENV_DIR/bin/pyinstaller" --onefile --name UniversalVPNTool main.py
    echo "✅ Linux executable built successfully in $PROJECT_ROOT/dist/"
else
    echo "❌ Unsupported OS: $OS_TYPE"
    exit 1
fi

echo "🎉 Build complete!"
echo "📦 Your executable is in: $PROJECT_ROOT/dist/"
