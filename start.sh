#!/bin/bash

echo "=========================================="
echo "FortiGate Debug Monitor - Startup Script"
echo "=========================================="
echo ""

# Verify Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed"
    echo "Please install Python 3.8 or newer first"
    exit 1
fi

echo "✓ Python3 detected: $(python3 --version)"
echo ""

# Check dependencies
echo "Checking dependencies..."
if python3 -c "import flask" 2>/dev/null; then
    echo "✓ Flask already installed"
else
    echo "⚠ Flask not installed, installing dependencies..."
    pip3 install -r requirements.txt
fi

echo ""
echo "=========================================="
echo "Starting backend server..."
echo "=========================================="
echo ""
echo "Backend API will run at: http://localhost:5000"
echo "Open the frontend page via: index.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Launch Flask application
python3 app.py
