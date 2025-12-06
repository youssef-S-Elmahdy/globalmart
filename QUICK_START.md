# GlobalMart Platform - Quick Start Guide

## 🚀 Fastest Way to Start Everything

```bash
cd /home/g7/Desktop/BigData
./START_ALL_SERVICES.sh
```

## 📦 Docker-Only Quick Start

### Start Docker Infrastructure
```bash
cd /home/g7/Desktop/BigData/globalmart/docker
./START_DOCKER.sh

# OR manually with all compose files:
for f in docker-compose.*.yml; do docker-compose -f "$f" up -d; done
```

### Stop Docker Infrastructure
```bash
cd /home/g7/Desktop/BigData/globalmart/docker
./STOP_DOCKER.sh

# OR manually stop all containers:
docker stop $(docker ps -q --filter "name=globalmart")
```

## 🎯 Essential Commands

### 1. Start Stream Processors (After Docker is Running)

```bash
# Transaction Monitor
docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  transaction_monitor.py

# Session Analyzer
docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  session_analyzer.py

# Inventory Tracker
docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  inventory_tracker.py
```

### 2. Start Data Producer

```bash
cd /home/g7/Desktop/BigData/globalmart/data-generator

# Foreground (see output)
/home/g7/Desktop/BigData/.venv/bin/python producer.py

# Background
nohup /home/g7/Desktop/BigData/.venv/bin/python producer.py > /tmp/producer.log 2>&1 &

# Monitor
tail -f /tmp/producer.log
```

### 3. Start Web Explorer

```bash
cd /home/g7/Desktop/BigData/globalmart/api
/home/g7/Desktop/BigData/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Access: http://localhost:8000/explorer
```

## ✅ Verify Everything is Running

```bash
# Check Docker containers
docker ps --format "table {{.Names}}\t{{.Status}}" | grep globalmart

# Check stream processors
docker exec globalmart-spark-master ps aux | grep -E "transaction_monitor|session_analyzer|inventory_tracker"

# Check producer
ps aux | grep producer.py | grep -v grep

# Check database
/home/g7/Desktop/BigData/.venv/bin/python /tmp/check_tables.py
```

## 🛑 Stop Everything

```bash
cd /home/g7/Desktop/BigData
./STOP_ALL_SERVICES.sh
```

## 🌐 Access URLs

| Service | URL |
|---------|-----|
| Web Explorer | http://localhost:8000/explorer |
| API Docs | http://localhost:8000/docs |
| Grafana | http://localhost:3000 |
| Streamlit | http://localhost:8501 |
| Spark UI | http://localhost:8080 |

## 📊 Expected Performance

- **Producer:** 516+ events/second ✓
- **Stream Latency:** ~1 second
- **Tables Populated:** 6/7 (cart_abandonment needs manual restart)

## 🔧 Troubleshooting

### Producer not starting?
```bash
# Check dependencies
/home/g7/Desktop/BigData/.venv/bin/pip install kafka-python-ng faker python-snappy

# Check Kafka is accessible
docker exec globalmart-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Stream processors not running?
```bash
# Check Spark is up
docker logs globalmart-spark-master

# Restart a processor
docker exec globalmart-spark-master pkill -f session_analyzer.py
# Then start it again with spark-submit command above
```

### Web interface not loading?
```bash
# Check FastAPI is running
ps aux | grep uvicorn

# Check port 8000 is free
lsof -ti:8000

# Check API dependencies
/home/g7/Desktop/BigData/.venv/bin/pip install fastapi uvicorn
```

---

**For complete documentation, see:**
- [COMMAND_REFERENCE.md](/home/g7/Desktop/BigData/COMMAND_REFERENCE.md) - All commands
- [PROJECT_COMPLETION_SUMMARY.md](/tmp/PROJECT_COMPLETION_SUMMARY.md) - Full summary
- [ARCHITECTURE.md](/home/g7/Desktop/BigData/ARCHITECTURE.md) - System design
