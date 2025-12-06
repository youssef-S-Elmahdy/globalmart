#!/bin/bash
# GlobalMart Web Interface Startup Script

echo "========================================="
echo "GlobalMart Data Explorer"
echo "========================================="

# Navigate to API directory
cd "$(dirname "$0")/../api" || exit 1

# Check if virtual environment exists
VENV_PATH="/home/g7/Desktop/BigData/.venv/bin/python"

if [ ! -f "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Check if FastAPI is installed
if ! $VENV_PATH -c "import fastapi" 2>/dev/null; then
    echo "Installing FastAPI and dependencies..."
    /home/g7/Desktop/BigData/.venv/bin/pip install fastapi uvicorn[standard] psycopg2-binary pymongo python-multipart
fi

echo ""
echo "Starting FastAPI server..."
echo ""
echo "Web Interface will be available at:"
echo "  http://localhost:8000/explorer"
echo ""
echo "API Documentation:"
echo "  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================="
echo ""

# Start the server
$VENV_PATH -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
