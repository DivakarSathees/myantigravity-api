#!/bin/bash

# MyAntigravity Server Startup Script
# This script starts the FastAPI server that powers the agent

echo "🚀 Starting MyAntigravity Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install requirements if needed
echo "📦 Checking dependencies..."
pip install -q -r requirement.txt

# Start the server
echo ""
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "🔌 WebSocket endpoint: ws://localhost:8000/ws/logs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 server.py

