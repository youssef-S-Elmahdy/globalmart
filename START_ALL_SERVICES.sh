#!/bin/bash
# GlobalMart Complete Service Startup Script
# This script starts all components of the GlobalMart platform

set -e  # Exit on error

echo "========================================="
echo "GlobalMart Platform - Complete Startup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base paths
PROJECT_DIR="/home/g7/Desktop/BigData"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
VENV_PIP="$PROJECT_DIR/.venv/bin/pip"

# =========================================
# STEP 1: Verify Prerequisites
# =========================================
echo -e "${GREEN}[1/7] Verifying Prerequisites...${NC}"

# Check virtual environment
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Virtual environment not found at $VENV_PYTHON"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker first."
    exit 1
fi

echo "✓ Virtual environment found"
echo "✓ Docker installed"
echo ""

# =========================================
# STEP 2: Start Docker Infrastructure
# =========================================
echo -e "${GREEN}[2/7] Starting Docker Infrastructure...${NC}"

cd "$PROJECT_DIR/globalmart/docker" || exit 1

echo "Starting Docker containers from compose files..."

# Free port 8000 if a host uvicorn is running (avoid clash with api container)
if pgrep -f "uvicorn main:app" >/dev/null; then
    echo "Host FastAPI detected on port 8000; stopping to free the port..."
    pkill -f "uvicorn main:app" || true
    sleep 2
fi

# Start core stacks explicitly to ensure all services are up
COMPOSE_FILES=(
  docker-compose.kafka.yml
  docker-compose.postgres.yml
  docker-compose.mongodb.yml
  docker-compose.api.yml
  docker-compose.spark.yml
  docker-compose.producer.yml
)

for compose_file in "${COMPOSE_FILES[@]}"; do
    if [ -f "$compose_file" ]; then
        # If API stack and port 8000 busy, skip to prevent failure
        if [[ "$compose_file" == "docker-compose.api.yml" ]]; then
            if sudo lsof -i :8000 >/dev/null 2>&1; then
                echo -e "${YELLOW}Port 8000 in use; skipping API stack. Stop the process using 8000 and rerun if needed.${NC}"
                continue
            fi
        fi
        echo "  Starting $compose_file..."
        sudo docker compose -f "$compose_file" up -d
    fi
done

# Wait for services to be ready
echo "Waiting for services to start (30 seconds)..."
sleep 30

# Verify containers
echo ""
echo "Container Status:"
sudo docker ps --format "table {{.Names}}\t{{.Status}}" | grep globalmart || echo "No containers running!"

echo ""
echo "✓ Docker infrastructure started"
echo ""

# =========================================
# STEP 3: Start Stream Processors
# =========================================
echo -e "${GREEN}[3/7] Starting Stream Processors...${NC}"

cd "$PROJECT_DIR/globalmart/docker" || exit 1

# Ensure Spark stack is running before submitting jobs
if ! sudo docker ps --format "{{.Names}}" | grep -q "^globalmart-spark-master$"; then
    echo "Spark master not running. Starting Spark stack..."
    sudo docker compose -f docker-compose.spark.yml up -d
    # Give Spark a moment to come up
    sleep 5
fi

# Re-check Spark master presence; if missing, abort early with guidance
if ! sudo docker ps --format "{{.Names}}" | grep -q "^globalmart-spark-master$"; then
    echo "ERROR: Spark master container not found. Please start it manually:"
    echo "  cd \"$PROJECT_DIR/globalmart/docker\" && sudo docker compose -f docker-compose.spark.yml up -d"
    echo "Exiting because stream processors cannot run without Spark."
    exit 1
fi

# Ensure Python dependencies are installed inside Spark master (once)
STREAM_DEPS_MARKER="/tmp/stream_deps_installed"
if ! sudo docker exec globalmart-spark-master test -f "$STREAM_DEPS_MARKER"; then
    echo "Installing stream processor Python dependencies inside Spark master..."
    sudo docker exec -u root globalmart-spark-master env HOME=/root \
        pip install --no-cache-dir -r /app/stream-processor/requirements.txt && \
        sudo docker exec globalmart-spark-master touch "$STREAM_DEPS_MARKER"
else
    echo "Stream processor dependencies already installed inside Spark master (marker found)."
fi

# Kill any existing processors
echo "Stopping any existing stream processors..."
sudo docker exec globalmart-spark-master pkill -f "transaction_monitor.py" 2>/dev/null || true
sudo docker exec globalmart-spark-master pkill -f "session_analyzer.py" 2>/dev/null || true
sudo docker exec globalmart-spark-master pkill -f "inventory_tracker.py" 2>/dev/null || true
sleep 2

# Start transaction_monitor
echo "Starting transaction_monitor.py..."
sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  transaction_monitor.py

sleep 3

# Start session_analyzer
echo "Starting session_analyzer.py..."
sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  session_analyzer.py

sleep 3

# Start inventory_tracker
echo "Starting inventory_tracker.py..."
sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  inventory_tracker.py

echo ""
echo "✓ Stream processors started"
echo ""

# =========================================
# STEP 4: Start Data Producer (Docker)
# =========================================
echo -e "${GREEN}[4/7] Starting Data Producer (Docker)...${NC}"

cd "$PROJECT_DIR/globalmart/docker" || exit 1

# Ensure producer container is fresh and using the internal Kafka endpoint
echo "Starting/refreshing producer container..."
# Remove only the producer container if it exists (avoid tearing down other stacks)
sudo docker rm -f globalmart-producer >/dev/null 2>&1 || true
sudo docker compose -f docker-compose.producer.yml up -d --build

sleep 5

# Check container status
PRODUCER_STATUS=$(sudo docker ps --filter "name=globalmart-producer" --format "{{.Status}}")
if [[ -n "$PRODUCER_STATUS" ]]; then
    echo "✓ Producer container running ($PRODUCER_STATUS)"
    echo "  View logs: sudo docker logs -f globalmart-producer"
else
    echo "ERROR: Producer container not running. Inspect with:"
    echo "  sudo docker-compose -f docker-compose.producer.yml logs -f"
fi

echo ""

# =========================================
# STEP 5: Start Monitoring Services
# =========================================
echo -e "${GREEN}[5/7] Starting Monitoring Services...${NC}"

cd "$PROJECT_DIR/globalmart/scripts" || exit 1

# Check if metrics collector already running
if pgrep -f "metrics_collector.py" > /dev/null; then
    echo "✓ Metrics collector already running"
else
    # Install dependencies
    if ! $VENV_PYTHON -c "import psutil" 2>/dev/null; then
        echo "Installing monitoring dependencies..."
        $VENV_PIP install -q psutil
    fi

    echo "Starting metrics collector..."
    nohup $VENV_PYTHON metrics_collector.py > /tmp/metrics_collector.log 2>&1 &
    METRICS_PID=$!
    echo "✓ Metrics collector started (PID: $METRICS_PID)"
fi

# Start notification service (optional)
read -p "Start notification service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if pgrep -f "notification_service.py" > /dev/null; then
        echo "✓ Notification service already running"
    else
        echo "Starting notification service..."
        nohup $VENV_PYTHON notification_service.py > /tmp/notifications.log 2>&1 &
        NOTIF_PID=$!
        echo "✓ Notification service started (PID: $NOTIF_PID)"
        echo "  Note: Configure SMTP in notification_config.py for real emails"
    fi
fi

echo ""

# =========================================
# STEP 6: Start Web Interfaces
# =========================================
echo -e "${GREEN}[6/7] Starting Web Interfaces...${NC}"

cd "$PROJECT_DIR/globalmart/api" || exit 1

# Install FastAPI dependencies
if ! $VENV_PYTHON -c "import fastapi" 2>/dev/null; then
    echo "Installing API dependencies..."
    $VENV_PIP install -q fastapi uvicorn python-multipart
fi

# Start FastAPI (Web Explorer + API)
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✓ FastAPI already running"
else
    echo "Starting FastAPI (Web Explorer + REST API)..."
    nohup $VENV_PYTHON -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
    FASTAPI_PID=$!
    sleep 3
    if ps -p $FASTAPI_PID > /dev/null; then
        echo "✓ FastAPI started (PID: $FASTAPI_PID)"
    fi
fi

# Start Streamlit Dashboard (optional)
read -p "Start Streamlit executive dashboard? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$PROJECT_DIR/globalmart/visualizations" || exit 1

    if ! $VENV_PYTHON -c "import streamlit" 2>/dev/null; then
        echo "Installing Streamlit dependencies..."
        $VENV_PIP install -q streamlit plotly
    fi

    if pgrep -f "streamlit run" > /dev/null; then
        echo "✓ Streamlit already running"
    else
        echo "Starting Streamlit dashboard..."
        nohup $VENV_PYTHON -m streamlit run executive_dashboard.py --server.port 8501 --server.headless true > /tmp/streamlit.log 2>&1 &
        STREAMLIT_PID=$!
        echo "✓ Streamlit started (PID: $STREAMLIT_PID)"
    fi
fi

echo ""

# =========================================
# STEP 7: Verification & Summary
# =========================================
echo -e "${GREEN}[7/7] Verifying Services...${NC}"
echo ""

# Check stream processors
echo "Stream Processors:"
PROCESSORS=$(sudo docker exec globalmart-spark-master ps aux 2>/dev/null | grep -E "transaction_monitor|session_analyzer|inventory_tracker" | grep -v grep | wc -l)
if [ "$PROCESSORS" -lt 3 ]; then
    echo "  ⚠ Only $PROCESSORS/3 processors running; attempting restart..."
    # Retry starting the processors
    sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
      /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
      --executor-cores 1 --total-executor-cores 1 \
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
      transaction_monitor.py

    sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
      /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
      --executor-cores 1 --total-executor-cores 1 \
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
      session_analyzer.py

    sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
      /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
      --executor-cores 1 --total-executor-cores 1 \
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
      inventory_tracker.py

    sleep 5
    PROCESSORS=$(sudo docker exec globalmart-spark-master ps aux | grep -E "transaction_monitor|session_analyzer|inventory_tracker" | grep -v grep | wc -l)
    if [ "$PROCESSORS" -eq 3 ]; then
        echo "  ✓ All 3 processors running after restart"
    else
        echo "  ⚠ Still $PROCESSORS/3 processors running. Check spark logs inside globalmart-spark-master."
    fi
else
    echo "  ✓ All 3 processors running"
fi

# Check producer container
if sudo docker ps --filter "name=globalmart-producer" --format "{{.Names}}" | grep -q globalmart-producer; then
    echo "  ✓ Data producer container running"
else
    echo "  ✗ Data producer container NOT running"
fi

# Check monitoring
if pgrep -f "metrics_collector.py" > /dev/null; then
    echo "  ✓ Metrics collector running"
fi

# Check web services
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "  ✓ FastAPI running"
fi

if pgrep -f "streamlit run" > /dev/null; then
    echo "  ✓ Streamlit running"
fi

echo ""
echo "========================================="
echo "✓ GlobalMart Platform Started!"
echo "========================================="
echo ""
echo "Access Points:"
echo "  • Grafana:           http://localhost:3001 (admin/admin123)"
echo "  • Web Explorer:      http://localhost:8000/explorer"
echo "  • API Docs:          http://localhost:8000/docs"
echo "  • Streamlit:         http://localhost:8501"
echo "  • Spark Master UI:   http://localhost:8080"
echo "  • MongoDB Express:   http://localhost:8081"
echo ""
echo "Logs:"
echo "  • Producer:          tail -f /tmp/producer.log"
echo "  • Metrics:           tail -f /tmp/metrics_collector.log"
echo "  • Notifications:     tail -f /tmp/notifications.log"
echo "  • FastAPI:           tail -f /tmp/fastapi.log"
echo "  • Streamlit:         tail -f /tmp/streamlit.log"
echo ""
echo "Process IDs saved to: /tmp/globalmart_pids.txt"
echo ""
echo "To stop all services, run:"
echo "  bash $PROJECT_DIR/STOP_ALL_SERVICES.sh"
echo ""
echo "========================================="

# Save PIDs
cat > /tmp/globalmart_pids.txt << EOF
# GlobalMart Service PIDs
# Generated: $(date)

PRODUCER_PID=${PRODUCER_PID:-N/A}
METRICS_PID=${METRICS_PID:-N/A}
NOTIF_PID=${NOTIF_PID:-N/A}
FASTAPI_PID=${FASTAPI_PID:-N/A}
STREAMLIT_PID=${STREAMLIT_PID:-N/A}

# Stream processors run inside Docker (use docker exec to check)
EOF

# Wait for user to see the output
sleep 2
