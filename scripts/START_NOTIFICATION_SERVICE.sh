#!/bin/bash
# Start GlobalMart Notification Service

echo "========================================="
echo "GlobalMart Alert Notification Service"
echo "========================================="

cd "$(dirname "$0")" || exit 1

# Check if virtual environment exists
VENV_PYTHON="/home/g7/Desktop/BigData/.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found"
    exit 1
fi

echo ""
echo "Starting notification service..."
echo "Monitoring for:"
echo "  - Low stock alerts (< 10 units)"
echo "  - Transaction anomalies (score >= 0.8)"
echo "  - Cart abandonment spikes"
echo ""
echo "Check interval: 5 minutes"
echo "Log file: /tmp/globalmart_notifications.log"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================="
echo ""

# Start the service
$VENV_PYTHON notification_service.py
