# GlobalMart - Complete Docker Setup

**Last Updated:** December 6, 2025

---

## Overview

All GlobalMart services now run inside Docker containers for better isolation, networking, and deployment consistency.

---

## Docker Architecture

### Network
All containers run on the **globalmart-network** Docker network for internal communication.

### Containers

| Container | Service | Internal Port | External Port | Hostname |
|-----------|---------|---------------|---------------|----------|
| globalmart-kafka | Message Broker | 9092 | 9093 | globalmart-kafka |
| globalmart-zookeeper | Kafka Coordinator | 2181 | 2181 | globalmart-zookeeper |
| globalmart-postgres | Real-time DB | 5432 | 5432 | globalmart-postgres |
| globalmart-mongodb | Data Warehouse | 27017 | 27017 | globalmart-mongodb |
| globalmart-redis | Cache | 6379 | 6379 | globalmart-redis |
| globalmart-spark-master | Spark Master | 7077, 8080 | 8080 | globalmart-spark-master |
| globalmart-spark-worker-1 | Spark Worker | - | 8081 | globalmart-spark-worker-1 |
| globalmart-spark-worker-2 | Spark Worker | - | 8082 | globalmart-spark-worker-2 |
| globalmart-producer | Data Generator | - | - | globalmart-producer |
| globalmart-api | FastAPI Server | 8000 | 8000 | globalmart-api |
| globalmart-grafana | Monitoring | 3000 | 3001 | globalmart-grafana |
| globalmart-mongo-express | MongoDB UI | 8081 | 8081 | globalmart-mongo-express |
| globalmart-kafka-ui | Kafka UI | 8080 | 8082 | globalmart-kafka-ui |

---

## Docker Compose Files

Located in `/home/g7/Desktop/BigData/globalmart/docker/`:

1. **docker-compose.kafka.yml** - Kafka, Zookeeper, Kafka UI
2. **docker-compose.postgres.yml** - PostgreSQL database
3. **docker-compose.mongodb.yml** - MongoDB + Mongo Express
4. **docker-compose.spark.yml** - Spark cluster (master + 2 workers)
5. **docker-compose.api.yml** - Redis, FastAPI, Grafana
6. **docker-compose.producer.yml** - Data Producer (new)

---

## Configuration Changes

### Producer Configuration
**File:** `/home/g7/Desktop/BigData/globalmart/data-generator/config.py`

```python
# Now uses environment variable with Docker default
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'globalmart-kafka:9092')
```

**Dockerfile:** `/home/g7/Desktop/BigData/globalmart/data-generator/Dockerfile`
- Based on `python:3.10-slim`
- Installs: kafka-python-ng, faker, python-snappy
- Auto-starts producer.py

### API Configuration
**File:** `/home/g7/Desktop/BigData/globalmart/api/Dockerfile`
- Connects to databases via Docker network hostnames
- Environment variables configured in docker-compose.api.yml

---

## How to Start Everything

### Option 1: Automated Build & Start (Recommended)
```bash
cd /home/g7/Desktop/BigData/globalmart/docker
./BUILD_AND_START.sh
```

This script:
1. Builds producer and API Docker images
2. Starts all docker-compose services
3. Waits for services to initialize
4. Displays status and access URLs

### Option 2: Manual Start
```bash
cd /home/g7/Desktop/BigData/globalmart/docker

# Start each service
for f in docker-compose.*.yml; do sudo docker-compose -f "$f" up -d; done

# Wait for initialization
sleep 30

# Check status
sudo docker ps | grep globalmart
```

### Option 3: Start Stream Processors
Stream processors run inside the Spark master container:

```bash
# Transaction Monitor
sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  transaction_monitor.py

# Session Analyzer
sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  session_analyzer.py

# Inventory Tracker
sudo docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit --master spark://spark-master:7077 \
  --executor-cores 1 --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  inventory_tracker.py
```

---

## Monitoring & Logs

### View Container Logs
```bash
# Producer logs (real-time event generation)
sudo docker logs -f globalmart-producer

# API logs
sudo docker logs -f globalmart-api

# Kafka logs
sudo docker logs -f globalmart-kafka

# Spark logs
sudo docker logs -f globalmart-spark-master

# Stream processor logs (inside Spark container)
sudo docker exec globalmart-spark-master tail -f /app/logs/transaction_monitor.log
sudo docker exec globalmart-spark-master tail -f /app/logs/session_analyzer.log
sudo docker exec globalmart-spark-master tail -f /app/logs/inventory_tracker.log
```

### Container Statistics
```bash
# Resource usage
sudo docker stats

# Specific container
sudo docker stats globalmart-producer globalmart-api
```

---

## Access Services

### Web Interfaces
- **Grafana:** http://localhost:3001 (admin/admin123)
- **Web Explorer:** http://localhost:8000/explorer
- **API Docs:** http://localhost:8000/docs
- **Spark UI:** http://localhost:8080
- **MongoDB Express:** http://localhost:8081 (admin/pass)
- **Kafka UI:** http://localhost:8082

### Database Connections

#### PostgreSQL (from host)
```bash
psql -h localhost -p 5432 -U globalmart -d globalmart
# Password: globalmart123
```

#### MongoDB (from host)
```bash
mongosh "mongodb://globalmart:globalmart123@localhost:27017/globalmart_dw"
```

#### From inside Docker network
Containers use internal hostnames:
- PostgreSQL: `globalmart-postgres:5432`
- MongoDB: `globalmart-mongodb:27017`
- Kafka: `globalmart-kafka:9092`
- Redis: `globalmart-redis:6379`

---

## Stopping Services

### Stop all containers
```bash
cd /home/g7/Desktop/BigData
./STOP_ALL_SERVICES.sh
```

Or manually:
```bash
# Stop all globalmart containers
sudo docker stop $(sudo docker ps -q --filter "name=globalmart")

# Stop and remove
sudo docker stop $(sudo docker ps -q --filter "name=globalmart")
sudo docker rm $(sudo docker ps -aq --filter "name=globalmart")
```

### Stop specific service
```bash
# Stop producer only
sudo docker-compose -f docker-compose.producer.yml down

# Stop with volume cleanup
sudo docker-compose -f docker-compose.producer.yml down -v
```

---

## Rebuilding Services

### Rebuild producer after code changes
```bash
cd /home/g7/Desktop/BigData/globalmart/docker

# Stop old container
sudo docker-compose -f docker-compose.producer.yml down

# Rebuild and restart
sudo docker-compose -f docker-compose.producer.yml build --no-cache
sudo docker-compose -f docker-compose.producer.yml up -d

# Check logs
sudo docker logs -f globalmart-producer
```

### Rebuild API
```bash
cd /home/g7/Desktop/BigData/globalmart/docker

sudo docker-compose -f docker-compose.api.yml down
sudo docker-compose -f docker-compose.api.yml build --no-cache
sudo docker-compose -f docker-compose.api.yml up -d
```

---

## Troubleshooting

### Producer not generating events
```bash
# Check logs
sudo docker logs globalmart-producer

# Check if Kafka is accessible
sudo docker exec globalmart-producer ping -c 3 globalmart-kafka

# Restart producer
sudo docker restart globalmart-producer
```

### API container not starting
```bash
# Check logs
sudo docker logs globalmart-api

# Check build logs
sudo docker-compose -f docker-compose.api.yml build

# Check port conflicts
lsof -ti:8000
```

### Network issues
```bash
# Recreate network
sudo docker network rm globalmart-network
sudo docker network create globalmart-network

# Restart all services
./BUILD_AND_START.sh
```

### Database connection errors
```bash
# Check database is running
sudo docker ps | grep -E "postgres|mongodb"

# Test connection from API container
sudo docker exec globalmart-api ping globalmart-postgres
sudo docker exec globalmart-api ping globalmart-mongodb
```

---

## Performance Tuning

### Producer Throughput
Adjust in `config.py`:
```python
TARGET_THROUGHPUT = 500  # events/second
```

Then rebuild:
```bash
sudo docker-compose -f docker-compose.producer.yml up -d --build
```

### Resource Limits
Edit `docker-compose.producer.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
```

---

## Benefits of Docker Setup

1. **Network Isolation** - All services communicate via internal Docker network
2. **Port Management** - Clear mapping of internal/external ports
3. **Reproducibility** - Same environment everywhere
4. **Easy Scaling** - Add more workers/producers easily
5. **Resource Control** - CPU/memory limits per container
6. **Log Management** - Centralized logging via Docker
7. **Health Checks** - Automatic service monitoring
8. **Quick Restart** - Restart individual services without affecting others

---

**Created:** December 6, 2025
**Path:** /home/g7/Desktop/BigData/DOCKER_SETUP.md
