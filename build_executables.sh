#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting build process for UniversalVPNTool..."

# Define project root (assuming script is run from project root or a subdirectory)
PROJECT_ROOT="/Users/emmanouilkontos/Documents/GitHub/vpn-rdp-tool"

# Navigate to the project root
echo "Navigating to project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Clean up previous builds
echo "Cleaning up previous build artifacts..."
rm -rf build dist *.spec

# Install dependencies
echo "Installing Python dependencies and PyInstaller..."
VENV_PYTHON="/Users/emmanouilkontos/Documents/GitHub/vpn-rdp-tool/venv/bin/python3"

"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt pyinstaller

# Determine current OS
OS_TYPE=$(uname -s)

if [ "$OS_TYPE" == "Darwin" ]; then
    echo "Detected macOS. Building macOS executable..."
    # Build for macOS
    "$PROJECT_ROOT/venv/bin/pyinstaller" --onefile --name UniversalVPNTool main.py
    echo "macOS executable built successfully in $PROJECT_ROOT/dist/"
elif [ "$OS_TYPE" == "Linux" ]; then
    echo "Detected Linux. Building Linux executable..."
    # Build for Linux
    "$PROJECT_ROOT/venv/bin/pyinstaller" --onefile --name UniversalVPNTool main.py
    echo "Linux executable built successfully in $PROJECT_ROOT/dist/"
else
    echo "Unsupported operating system: $OS_TYPE. This script only supports macOS and Linux."
    exit 1
fi

echo "Build process completed."
echo "Executables can be found in the 'dist' directory: $PROJECT_ROOT/dist"