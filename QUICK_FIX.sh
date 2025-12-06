#!/bin/bash
# Quick fix for common GlobalMart issues

echo "========================================="
echo "GlobalMart Quick Fix Script"
echo "========================================="
echo ""

# Fix 1: Install missing Python dependencies
echo "[1/3] Installing missing Python dependencies..."
/home/g7/Desktop/BigData/.venv/bin/pip install -q redis psycopg2-binary pymongo fastapi uvicorn python-multipart 2>&1 | grep -v "already satisfied" || echo "  ✓ All dependencies installed"
echo ""

# Fix 2: Kill old FastAPI running as root
echo "[2/3] Stopping old FastAPI processes..."
sudo pkill -9 -f "uvicorn main:app" 2>/dev/null && echo "  ✓ Old FastAPI stopped" || echo "  - No old FastAPI running"
sleep 2
echo ""

# Fix 3: Start FastAPI from correct directory
echo "[3/3] Starting FastAPI from correct directory..."
cd /home/g7/Desktop/BigData/globalmart/api
nohup /home/g7/Desktop/BigData/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
FASTAPI_PID=$!
sleep 3

if ps -p $FASTAPI_PID > /dev/null 2>&1; then
    echo "  ✓ FastAPI started (PID: $FASTAPI_PID)"
else
    echo "  ✗ FastAPI failed to start. Check logs:"
    tail -20 /tmp/fastapi.log
    exit 1
fi

echo ""
echo "========================================="
echo "Testing Services..."
echo "========================================="
echo ""

# Test FastAPI
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ FastAPI:           http://localhost:8000/explorer"
else
    echo "  ❌ FastAPI:           Not responding (HTTP $HTTP_CODE)"
fi

# Test Streamlit
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ Streamlit:         http://localhost:8501"
else
    echo "  ⚠️  Streamlit:         Not running (start with START_ALL_SERVICES.sh)"
fi

# Test Grafana
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 2>&1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "  ✅ Grafana:           http://localhost:3001"
else
    echo "  ⚠️  Grafana:           Docker container not running"
    echo "                        Run: cd /home/g7/Desktop/BigData/globalmart/docker && sudo docker-compose -f docker-compose.monitoring.yml up -d"
fi

# Test MongoDB Express
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081 2>&1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "  ✅ MongoDB Express:   http://localhost:8081"
else
    echo "  ⚠️  MongoDB Express:   Not running"
fi

# Test Spark UI
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ Spark Master UI:   http://localhost:8080"
else
    echo "  ⚠️  Spark UI:          Not running"
fi

echo ""
echo "========================================="
echo "✓ Quick Fix Complete"
echo "========================================="
echo ""
echo "Main Access Point:"
echo "  🌐 http://localhost:8000/explorer"
echo ""
echo "If Grafana is not running, start Docker containers:"
echo "  cd /home/g7/Desktop/BigData"
echo "  ./START_ALL_SERVICES.sh"
echo ""
