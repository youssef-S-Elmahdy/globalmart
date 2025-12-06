#!/bin/bash
# GlobalMart - Stop All Services Script

echo "========================================="
echo "Stopping GlobalMart Platform Services"
echo "========================================="
echo ""

# Stop Python processes
echo "Stopping Python services..."

pkill -f "data-generator/producer.py" && echo "  ✓ Producer stopped" || echo "  - Producer not running"
pkill -f "metrics_collector.py" && echo "  ✓ Metrics collector stopped" || echo "  - Metrics collector not running"
pkill -f "notification_service.py" && echo "  ✓ Notification service stopped" || echo "  - Notification service not running"
pkill -f "uvicorn main:app" && echo "  ✓ FastAPI stopped" || echo "  - FastAPI not running"
pkill -f "streamlit run" && echo "  ✓ Streamlit stopped" || echo "  - Streamlit not running"

echo ""
echo "Stopping stream processors in Docker..."

# Stop stream processors
sudo docker exec globalmart-spark-master pkill -f "transaction_monitor.py" 2>/dev/null && echo "  ✓ transaction_monitor stopped" || echo "  - transaction_monitor not running"
sudo docker exec globalmart-spark-master pkill -f "session_analyzer.py" 2>/dev/null && echo "  ✓ session_analyzer stopped" || echo "  - session_analyzer not running"
sudo docker exec globalmart-spark-master pkill -f "inventory_tracker.py" 2>/dev/null && echo "  ✓ inventory_tracker stopped" || echo "  - inventory_tracker not running"

echo ""
read -p "Stop Docker containers? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping Docker containers..."

    # Stop containers by name (works regardless of compose file structure)
    CONTAINERS=$(sudo docker ps -a --filter "name=globalmart" --format "{{.Names}}" | tr '\n' ' ')

    if [ -n "$CONTAINERS" ]; then
        echo "Found containers: $CONTAINERS"
        sudo docker stop $CONTAINERS 2>/dev/null
        sudo docker rm $CONTAINERS 2>/dev/null
        echo "  ✓ Docker containers stopped and removed"
    else
        echo "  - No GlobalMart containers found"
    fi
fi

echo ""
echo "========================================="
echo "✓ All services stopped"
echo "========================================="
