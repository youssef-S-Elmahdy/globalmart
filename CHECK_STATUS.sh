#!/bin/bash
# Quick status check for GlobalMart platform (no sudo required)

echo "========================================="
echo "GlobalMart Platform - Status Check"
echo "========================================="
echo ""

# Check Python services
echo "Python Services:"
echo "----------------"

if pgrep -f "data-generator/producer.py" > /dev/null; then
    echo "  ✅ Producer:          RUNNING"
else
    echo "  ❌ Producer:          STOPPED"
fi

if pgrep -f "metrics_collector.py" > /dev/null; then
    echo "  ✅ Metrics Collector: RUNNING"
else
    echo "  ❌ Metrics Collector: STOPPED"
fi

if pgrep -f "notification_service.py" > /dev/null; then
    echo "  ✅ Notifications:     RUNNING"
else
    echo "  ❌ Notifications:     STOPPED"
fi

if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "  ✅ FastAPI:           RUNNING"
else
    echo "  ❌ FastAPI:           STOPPED"
fi

if pgrep -f "streamlit run" > /dev/null; then
    echo "  ✅ Streamlit:         RUNNING"
else
    echo "  ❌ Streamlit:         STOPPED"
fi

echo ""
echo "Docker Containers:"
echo "------------------"
echo "  ℹ️  Run 'sudo docker ps' to check Docker containers"

echo ""
echo "Network Ports:"
echo "--------------"

check_port() {
    if ss -tuln 2>/dev/null | grep -q ":$1 "; then
        echo "  ✅ Port $1: $2"
    else
        echo "  ❌ Port $1: $2 (not listening)"
    fi
}

check_port 8000 "FastAPI"
check_port 8501 "Streamlit"
check_port 3001 "Grafana"
check_port 8080 "Spark UI"
check_port 8081 "MongoDB Express"
check_port 5432 "PostgreSQL"
check_port 27017 "MongoDB"
check_port 9092 "Kafka"

echo ""
echo "Recent Log Activity:"
echo "--------------------"

if [ -f /tmp/producer.log ]; then
    PRODUCER_TIME=$(stat -c %y /tmp/producer.log 2>/dev/null | cut -d'.' -f1)
    echo "  📄 Producer log:     $PRODUCER_TIME"
else
    echo "  ❌ Producer log:     Not found"
fi

if [ -f /tmp/metrics_collector.log ]; then
    METRICS_TIME=$(stat -c %y /tmp/metrics_collector.log 2>/dev/null | cut -d'.' -f1)
    echo "  📄 Metrics log:      $METRICS_TIME"
else
    echo "  ❌ Metrics log:      Not found"
fi

if [ -f /tmp/fastapi.log ]; then
    FASTAPI_TIME=$(stat -c %y /tmp/fastapi.log 2>/dev/null | cut -d'.' -f1)
    echo "  📄 FastAPI log:      $FASTAPI_TIME"
else
    echo "  ❌ FastAPI log:      Not found"
fi

echo ""
echo "========================================="
echo "Quick Actions:"
echo "========================================="
echo ""
echo "  Start all:    ./START_ALL_SERVICES.sh"
echo "  Stop all:     ./STOP_ALL_SERVICES.sh"
echo "  Check logs:   tail -f /tmp/producer.log"
echo ""
