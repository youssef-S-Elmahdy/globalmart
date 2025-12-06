# GlobalMart Platform - Complete Command Reference

## Quick Start (Automated)

### Start Everything
```bash
cd /home/g7/Desktop/BigData
chmod +x START_ALL_SERVICES.sh STOP_ALL_SERVICES.sh
./START_ALL_SERVICES.sh
```

### Stop Everything
```bash
cd /home/g7/Desktop/BigData
./STOP_ALL_SERVICES.sh
```

---

## Manual Step-by-Step Commands

### 1. Start Docker Infrastructure

```bash
cd /home/g7/Desktop/BigData/globalmart/docker

# Start all compose files
for f in docker-compose.*.yml; do sudo docker-compose -f "$f" up -d; done

# Verify containers
sudo docker ps --format "table {{.Names}}\t{{.Status}}"

# Wait for services (30 seconds)
sleep 30
```

**Expected containers:**
- globalmart-kafka
- globalmart-zookeeper
- globalmart-postgres
- globalmart-mongodb
- globalmart-spark-master
- globalmart-spark-worker
- globalmart-grafana
- globalmart-mongo-express

---

### 2. Start Stream Processors (Spark)

#### Transaction Monitor
```bash
sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  transaction_monitor.py
```

#### Session Analyzer (Cart Abandonment)
```bash
sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  session_analyzer.py
```

#### Inventory Tracker
```bash
sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  inventory_tracker.py
```

**Verify processors running:**
```bash
sudo docker exec globalmart-spark-master ps aux | grep -E "transaction_monitor|session_analyzer|inventory_tracker"
```

---

### 3. Start Data Producer

```bash
cd /home/g7/Desktop/BigData/globalmart/data-generator

# Install dependencies (if needed)
/home/g7/Desktop/BigData/.venv/bin/pip install kafka-python-ng faker python-snappy

# Start producer (foreground - to see output)
/home/g7/Desktop/BigData/.venv/bin/python producer.py

# OR start in background
nohup /home/g7/Desktop/BigData/.venv/bin/python producer.py > /tmp/producer.log 2>&1 &

# Monitor throughput
tail -f /tmp/producer.log | grep "Statistics"
```

**Expected output:**
```
=== Statistics (t=9s, rate=552.7/s) ===
Total Events:    5000 (552.7/s)
Target:        500.0/s ✓ ACHIEVED
```

---

### 4. Start Monitoring Services

#### Metrics Collector
```bash
cd /home/g7/Desktop/BigData/globalmart/scripts

# Install dependencies
/home/g7/Desktop/BigData/.venv/bin/pip install psutil

# Start in background
nohup /home/g7/Desktop/BigData/.venv/bin/python metrics_collector.py > /tmp/metrics_collector.log 2>&1 &

# Check it's running
ps aux | grep metrics_collector
```

#### Notification Service
```bash
cd /home/g7/Desktop/BigData/globalmart/scripts

# Configure SMTP first (edit notification_config.py)
nano notification_config.py

# Start service
nohup /home/g7/Desktop/BigData/.venv/bin/python notification_service.py > /tmp/notifications.log 2>&1 &

# OR use startup script
./START_NOTIFICATION_SERVICE.sh
```

---

### 5. Start Web Interfaces

#### FastAPI (Web Explorer + REST API)
```bash
cd /home/g7/Desktop/BigData/globalmart/api

# Install dependencies
/home/g7/Desktop/BigData/.venv/bin/pip install fastapi uvicorn python-multipart

# Start server
/home/g7/Desktop/BigData/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000

# OR in background
nohup /home/g7/Desktop/BigData/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &

# Access:
# - Web Explorer:  http://localhost:8000/explorer
# - API Docs:      http://localhost:8000/docs
# - Health Check:  http://localhost:8000/health
```

#### Streamlit Executive Dashboard
```bash
cd /home/g7/Desktop/BigData/globalmart/visualizations

# Install dependencies
/home/g7/Desktop/BigData/.venv/bin/pip install streamlit plotly

# Start dashboard
/home/g7/Desktop/BigData/.venv/bin/streamlit run executive_dashboard.py

# OR in background
nohup /home/g7/Desktop/BigData/.venv/bin/streamlit run executive_dashboard.py --server.port 8501 --server.headless true > /tmp/streamlit.log 2>&1 &

# Access: http://localhost:8501
```

---

## Verification Commands

### Check All Services Status

```bash
# Docker containers
sudo docker ps --format "table {{.Names}}\t{{.Status}}"

# Stream processors (inside Docker)
sudo docker exec globalmart-spark-master ps aux | grep -E "transaction_monitor|session_analyzer|inventory_tracker" | grep -v grep

# Producer
ps aux | grep "producer.py" | grep -v grep

# Monitoring services
ps aux | grep -E "metrics_collector|notification_service" | grep -v grep

# Web services
ps aux | grep -E "uvicorn|streamlit" | grep -v grep
```

### Check Database Tables

```bash
# PostgreSQL tables
/home/g7/Desktop/BigData/.venv/bin/python /tmp/check_tables.py

# OR manual query
sudo docker exec -it globalmart-postgres psql -U globalmart -d globalmart -c "
SELECT
    'sales_metrics' as table_name, COUNT(*) FROM sales_metrics
UNION ALL
SELECT 'transaction_anomalies', COUNT(*) FROM transaction_anomalies
UNION ALL
SELECT 'inventory_status', COUNT(*) FROM inventory_status
UNION ALL
SELECT 'cart_abandonment', COUNT(*) FROM cart_abandonment;
"
```

### Check Producer Throughput

```bash
tail -f /tmp/producer.log | grep "Total Events"
```

### Check Kafka Topics

```bash
sudo docker exec globalmart-kafka kafka-topics --list --bootstrap-server localhost:9092

# Check topic messages
sudo docker exec globalmart-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic transactions \
  --max-messages 5
```

---

## Stopping Services

### Stop Specific Services

```bash
# Stop producer
pkill -f "producer.py"

# Stop metrics collector
pkill -f "metrics_collector.py"

# Stop notification service
pkill -f "notification_service.py"

# Stop FastAPI
pkill -f "uvicorn main:app"

# Stop Streamlit
pkill -f "streamlit run"

# Stop stream processors
sudo docker exec globalmart-spark-master pkill -f "transaction_monitor.py"
sudo docker exec globalmart-spark-master pkill -f "session_analyzer.py"
sudo docker exec globalmart-spark-master pkill -f "inventory_tracker.py"
```

### Stop Docker Containers

```bash
# Stop all globalmart containers
sudo docker stop $(sudo docker ps -q --filter "name=globalmart")

# Stop and remove all globalmart containers
sudo docker stop $(sudo docker ps -q --filter "name=globalmart")
sudo docker rm $(sudo docker ps -aq --filter "name=globalmart")
```

---

## Monitoring & Logs

### View Logs

```bash
# Producer throughput
tail -f /tmp/producer.log

# Metrics collector
tail -f /tmp/metrics_collector.log

# Notification service
tail -f /tmp/notifications.log

# FastAPI
tail -f /tmp/fastapi.log

# Streamlit
tail -f /tmp/streamlit.log

# Stream processors (inside Docker)
sudo docker exec globalmart-spark-master tail -f /app/logs/transaction_monitor.log
sudo docker exec globalmart-spark-master tail -f /app/logs/session_analyzer.log
sudo docker exec globalmart-spark-master tail -f /app/logs/inventory_tracker.log
```

### Monitor Resource Usage

```bash
# Docker container stats
sudo docker stats

# System resources
htop

# Database connections
sudo docker exec globalmart-postgres psql -U globalmart -d globalmart -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Troubleshooting

### Restart Stream Processors (if cart_abandonment empty)

```bash
# Stop old processors
docker exec globalmart-spark-master pkill -f "session_analyzer.py"
docker exec globalmart-spark-master pkill -f "inventory_tracker.py"

# Wait
sleep 5

# Start with new code
docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  session_analyzer.py

docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  inventory_tracker.py
```

### Producer Not Achieving 500 events/sec

```bash
# Check if running
ps aux | grep producer.py

# Check logs for errors
tail -50 /tmp/producer.log

# Restart producer
pkill -f producer.py
cd /home/g7/Desktop/BigData/globalmart/data-generator
/home/g7/Desktop/BigData/.venv/bin/python producer.py
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -ti:8000

# Kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
/home/g7/Desktop/BigData/.venv/bin/python -m uvicorn main:app --port 8001
```

---

## Access URLs Summary

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin/admin |
| **Web Explorer** | http://localhost:8000/explorer | None |
| **API Documentation** | http://localhost:8000/docs | None |
| **Streamlit Dashboard** | http://localhost:8501 | None |
| **Spark Master UI** | http://localhost:8080 | None |
| **MongoDB Express** | http://localhost:8081 | admin/pass |

---

## Batch Jobs (Optional - Run Daily)

```bash
cd /home/g7/Desktop/BigData/globalmart/batch-processor

# ETL Pipeline (PostgreSQL → MongoDB)
docker exec -w /app/batch-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0,org.postgresql:postgresql:42.6.0 \
  etl_pipeline.py

# RFM Analysis
docker exec -w /app/batch-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  rfm_analysis.py

# Product Performance
docker exec -w /app/batch-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  product_performance.py

# Sales Trends
docker exec -w /app/batch-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  sales_trends.py
```

---

## Quick Reference Card

```bash
# ONE COMMAND TO START EVERYTHING:
/home/g7/Desktop/BigData/START_ALL_SERVICES.sh

# ONE COMMAND TO STOP EVERYTHING:
/home/g7/Desktop/BigData/STOP_ALL_SERVICES.sh

# CHECK STATUS:
docker ps && ps aux | grep -E "producer|metrics|notification|uvicorn|streamlit" | grep -v grep
```

---

**Created:** December 6, 2025
**Path:** /home/g7/Desktop/BigData/COMMAND_REFERENCE.md
