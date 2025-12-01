# GlobalMart: Real-Time E-Commerce Analytics Platform

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Kafka](https://img.shields.io/badge/Kafka-3.5-orange)](https://kafka.apache.org/)
[![Spark](https://img.shields.io/badge/Spark-3.5-red)](https://spark.apache.org/)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://www.python.org/)

A complete real-time analytics platform for e-commerce data processing, built with Apache Kafka, Apache Spark, FastAPI, and Grafana. Optimized for **MacBook M1** with Docker.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Components](#components)
- [API Reference](#api-reference)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Team Members](#team-members)

---

## 🎯 Project Overview

**GlobalMart** is a comprehensive big data analytics platform designed for a large-scale e-commerce business with:
- 10 million active users
- 250,000 products across 100 categories
- Operations in 5 countries
- 100,000 daily transactions

### Key Features

✅ **Real-time Stream Processing**
- Transaction monitoring with anomaly detection
- Inventory tracking with low-stock alerts
- Shopping cart abandonment detection
- Real-time sales metrics aggregation

✅ **Batch Processing & Analytics**
- Customer segmentation (RFM Analysis)
- Product performance analysis
- Sales trend analysis (daily, weekly, monthly)
- Star schema data warehouse

✅ **API & Visualization**
- RESTful API for data access
- Executive dashboards with Grafana
- Geographic sales visualization
- Real-time metrics display

✅ **Docker-Based Infrastructure**
- Complete containerized deployment
- Easy scaling and maintenance
- Health monitoring and logging

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Sources                             │
│                  (Data Generator - 500 events/sec)              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │   Apache Kafka         │
         │   - transactions       │
         │   - product_views      │
         │   - cart_events        │
         └──┬─────────────────┬───┘
            │                 │
            │                 │
    ┌───────▼──────┐   ┌──────▼──────────┐
    │ Spark Stream │   │  Data Lake      │
    │  Processing  │   │  (Raw Data)     │
    │              │   │                 │
    │ - Anomalies  │   └────────┬────────┘
    │ - Inventory  │            │
    │ - Sessions   │            │
    └──────┬───────┘            │
           │                    │
           ▼                    ▼
    ┌─────────────┐    ┌───────────────┐
    │ PostgreSQL  │    │ Spark Batch   │
    │ (Metrics)   │    │  Processing   │
    └──────┬──────┘    │               │
           │           │ - RFM         │
           │           │ - Trends      │
           │           │ - Performance │
           │           └───────┬───────┘
           │                   │
           │                   ▼
           │           ┌───────────────┐
           │           │   MongoDB     │
           │           │ (Data Warehouse)
           │           └───────┬───────┘
           │                   │
           └───────┬───────────┘
                   │
                   ▼
           ┌───────────────┐
           │   FastAPI     │
           │  (REST API)   │
           └───────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │   Grafana     │
           │  (Dashboards) │
           └───────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Message Queue** | Apache Kafka 3.5 | Real-time data streaming |
| **Stream Processing** | Apache Spark Streaming | Real-time analytics |
| **Batch Processing** | Apache Spark | ETL and batch analytics |
| **Operational DB** | PostgreSQL 16 | Real-time metrics storage |
| **Data Warehouse** | MongoDB 7 | Analytical data storage |
| **Caching** | Redis 7 | API response caching |
| **API** | FastAPI | RESTful API layer |
| **Visualization** | Grafana | Interactive dashboards |
| **Orchestration** | Docker Compose | Container management |

---

## 📦 Prerequisites

### Required Software

1. **Docker Desktop** (already installed on your Mac)
   ```bash
   docker --version  # Should show: Docker version 28.4.0
   docker-compose --version  # Should show: v2.39.4
   ```

2. **Python 3.11+**
   ```bash
   python3 --version
   ```

3. **Git**
   ```bash
   git --version
   ```

### System Requirements

- **MacBook M1** (ARM64 architecture)
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Disk Space**: 20GB free space
- **Docker Desktop**: Running with at least 6GB memory allocated

### Configure Docker Desktop

1. Open Docker Desktop
2. Go to Preferences → Resources
3. Set Memory to at least 6GB
4. Set CPUs to at least 4
5. Click "Apply & Restart"

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd "/Users/youssef/Desktop/UNI/Semester 9/Big Data/Project"

# Make scripts executable
chmod +x scripts/*.sh
```

### 2. Start Docker Desktop

```bash
# Start Docker Desktop
open -a Docker

# Wait for Docker to be ready
sleep 10

# Verify Docker is running
docker ps
```

### 3. Deploy All Services

```bash
# Run deployment script
./scripts/deploy.sh

# This will:
# - Create Docker network
# - Start all containers
# - Initialize databases
# - Create Kafka topics
# - Set up monitoring
```

**Wait ~2 minutes for all services to start**

### 4. Verify Deployment

```bash
# Check service health
./scripts/health_check.sh

# Should show all services as ✓ Healthy
```

### 5. Start Data Generation

```bash
# In a new terminal
cd data-generator

# Install dependencies
pip install -r requirements.txt

# Start producing events (500/sec)
python producer.py
```

### 6. Start Stream Processing

```bash
# In another terminal
cd stream-processor

# Start all stream processing jobs
./run_all.sh
```

### 7. Access Dashboards

Open the following URLs in your browser:

- **Grafana Dashboard**: http://localhost:8083 (admin/admin123)
- **API Documentation**: http://localhost:8000/docs
- **Kafka UI**: http://localhost:8080
- **Spark UI**: http://localhost:8081
- **Mongo Express**: http://localhost:8082 (admin/admin123)

---

## 📁 Project Structure

```
globalmart/
├── README.md                          # This file
├── IMPLEMENTATION_GUIDE.md            # Part 1: Setup & Data Generation
├── IMPLEMENTATION_GUIDE_PART2.md      # Part 2: Stream & Batch Processing
├── IMPLEMENTATION_GUIDE_PART3.md      # Part 3: API, Visualization & Deployment
│
├── docker-compose.yml                 # Main Docker orchestration
│
├── data-generator/                    # Component 1 (20 points)
│   ├── config.py                      # Configuration
│   ├── generators.py                  # Data generation logic
│   ├── producer.py                    # Kafka producer
│   ├── requirements.txt               # Python dependencies
│   └── test_producer.py               # Tests
│
├── stream-processor/                  # Component 2 (30 points)
│   ├── config.py                      # Stream processing config
│   ├── transaction_monitor.py         # Anomaly detection
│   ├── inventory_tracker.py           # Inventory monitoring
│   ├── session_analyzer.py            # Session analysis
│   ├── requirements.txt               # Dependencies
│   └── run_all.sh                     # Start all jobs
│
├── batch-processor/                   # Component 3 (25 points)
│   ├── config.py                      # Batch processing config
│   ├── etl_pipeline.py                # ETL jobs
│   ├── rfm_analysis.py                # Customer segmentation
│   ├── product_performance.py         # Product analytics
│   ├── sales_trends.py                # Trend analysis
│   ├── scheduler.py                   # Job scheduler
│   └── requirements.txt               # Dependencies
│
├── api/                               # Component 4 (15 points)
│   ├── main.py                        # FastAPI application
│   ├── config.py                      # API configuration
│   ├── database.py                    # Database connections
│   ├── models.py                      # Pydantic models
│   ├── Dockerfile                     # API container
│   └── requirements.txt               # Dependencies
│
├── config/                            # Configuration files
│   ├── postgres/
│   │   └── init.sql                   # Database schema
│   ├── grafana/
│   │   ├── dashboards/                # Dashboard configs
│   │   └── datasources/               # Data source configs
│   └── data_warehouse_schema.md       # DW schema documentation
│
├── scripts/                           # Utility scripts
│   ├── deploy.sh                      # Deployment script
│   ├── shutdown.sh                    # Stop all services
│   ├── create_topics.sh               # Create Kafka topics
│   ├── monitor.sh                     # System monitoring
│   ├── health_check.sh                # Health checks
│   ├── logs.sh                        # View logs
│   └── test_e2e.sh                    # End-to-end tests
│
├── data/                              # Data storage
│   ├── raw/                           # Raw event data
│   ├── processed/                     # Processed data
│   └── warehouse/                     # Warehouse data
│
└── logs/                              # Application logs
    ├── kafka/
    ├── spark/
    └── api/
```

---

## 🔧 Components

### Component 1: Data Generation (20 points)

**Features:**
- Realistic e-commerce event generation
- 500 events/second throughput
- Three event types: transactions, product views, cart events
- Data quality validation
- Kafka producers

**Files:**
- [data-generator/producer.py](data-generator/producer.py)
- [data-generator/generators.py](data-generator/generators.py)

**Testing:**
```bash
cd data-generator
python test_producer.py
```

### Component 2: Stream Processing (30 points)

**Features:**
- Real-time transaction monitoring
- Anomaly detection (high value, unusual quantity)
- Inventory tracking with alerts
- Session analysis
- Cart abandonment detection
- Real-time metrics aggregation

**Files:**
- [stream-processor/transaction_monitor.py](stream-processor/transaction_monitor.py)
- [stream-processor/inventory_tracker.py](stream-processor/inventory_tracker.py)
- [stream-processor/session_analyzer.py](stream-processor/session_analyzer.py)

**Monitoring:**
- Spark UI: http://localhost:8081

### Component 3: Batch Processing (25 points)

**Features:**
- ETL pipeline
- RFM customer segmentation
- Product performance analysis
- Sales trend analysis (daily, weekly, monthly)
- Star schema data warehouse

**Files:**
- [batch-processor/etl_pipeline.py](batch-processor/etl_pipeline.py)
- [batch-processor/rfm_analysis.py](batch-processor/rfm_analysis.py)
- [batch-processor/product_performance.py](batch-processor/product_performance.py)

**Running:**
```bash
# Run ETL
docker exec globalmart-spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages org.postgresql:postgresql:42.6.0,org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  /app/batch-processor/etl_pipeline.py

# Run RFM Analysis
docker exec globalmart-spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages org.postgresql:postgresql:42.6.0,org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  /app/batch-processor/rfm_analysis.py
```

### Component 4: Visualization & API (15 points)

**API Endpoints:**
- `GET /api/v1/sales/metrics` - Sales metrics
- `GET /api/v1/sales/summary` - Sales summary
- `GET /api/v1/customers/segments` - Customer segments
- `GET /api/v1/products/performance` - Product performance
- `GET /api/v1/monitoring/anomalies` - Recent anomalies
- `GET /api/v1/monitoring/dashboard` - Dashboard metrics

**API Testing:**
```bash
# Get dashboard metrics
curl -H "X-API-Key: globalmart-api-key-2024" \
  http://localhost:8000/api/v1/monitoring/dashboard
```

**Dashboards:**
- Executive Dashboard
- Sales Metrics
- Customer Segmentation
- Product Performance
- Real-time Monitoring

### Component 5: Infrastructure (10 points)

**Features:**
- Docker-based deployment
- System monitoring
- Health checks
- Automated deployment scripts
- Service orchestration

**Commands:**
```bash
# Deploy all services
./scripts/deploy.sh

# Monitor system
./scripts/monitor.sh

# Check health
./scripts/health_check.sh

# View logs
./scripts/logs.sh [service-name]

# Shutdown
./scripts/shutdown.sh
```

---

## 📊 API Reference

### Authentication

All API endpoints require an API key:

```bash
X-API-Key: globalmart-api-key-2024
```

### Example Requests

**Get Sales Metrics:**
```bash
curl -H "X-API-Key: globalmart-api-key-2024" \
  "http://localhost:8000/api/v1/sales/metrics?limit=10"
```

**Get Customer Segments:**
```bash
curl -H "X-API-Key: globalmart-api-key-2024" \
  "http://localhost:8000/api/v1/customers/segments?segment=Champions"
```

**Get Product Performance:**
```bash
curl -H "X-API-Key: globalmart-api-key-2024" \
  "http://localhost:8000/api/v1/products/performance?category=Electronics&sort_by=total_revenue"
```

**Full API Documentation:**
http://localhost:8000/docs

---

## 📈 Monitoring

### System Health

```bash
# Quick health check
./scripts/health_check.sh

# Real-time monitoring
./scripts/monitor.sh
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:8083 | admin / admin123 |
| API Docs | http://localhost:8000/docs | API Key required |
| Kafka UI | http://localhost:8080 | None |
| Spark UI | http://localhost:8081 | None |
| Mongo Express | http://localhost:8082 | admin / admin123 |

### Key Metrics

**Data Generation:**
- Events per second: 500
- Transactions: 100/sec
- Product views: 300/sec
- Cart events: 100/sec

**Stream Processing:**
- Processing latency: < 1 second
- Anomaly detection rate: Real-time
- Alerts: Low-stock, anomalies

**Batch Processing:**
- ETL frequency: Daily
- RFM analysis: Daily
- Trend analysis: Hourly

---

## 🔍 Troubleshooting

### Docker Issues

**Docker not running:**
```bash
open -a Docker
sleep 10
docker ps
```

**Port conflicts:**
```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

**Container won't start:**
```bash
# Check logs
docker logs <container-name>

# Restart container
docker-compose restart <service-name>

# Full reset
docker-compose down -v
./scripts/deploy.sh
```

### Kafka Issues

**Topics not created:**
```bash
./scripts/create_topics.sh
```

**No messages in topics:**
```bash
# Check producer is running
ps aux | grep producer.py

# View Kafka UI
open http://localhost:8080
```

### Spark Issues

**Jobs not running:**
```bash
# Check Spark master
docker logs globalmart-spark-master

# Check workers
docker logs globalmart-spark-worker-1

# Restart Spark
docker-compose restart spark-master spark-worker-1 spark-worker-2
```

### Database Issues

**PostgreSQL connection failed:**
```bash
# Test connection
docker exec -it globalmart-postgres psql -U globalmart -d globalmart

# Check tables
\dt

# Restart
docker-compose restart postgres
```

**MongoDB connection failed:**
```bash
# Test connection
docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123

# Check databases
show dbs

# Restart
docker-compose restart mongodb
```

### Common Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f kafka

# Restart all services
docker-compose restart

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Check container resource usage
docker stats

# Execute command in container
docker exec -it <container-name> bash
```

---

## 📝 Development Workflow

### Daily Development

1. **Start services:**
   ```bash
   docker-compose up -d
   ```

2. **Start data generation:**
   ```bash
   cd data-generator && python producer.py
   ```

3. **Monitor:**
   ```bash
   ./scripts/monitor.sh
   ```

4. **Make changes and test**

5. **Shutdown:**
   ```bash
   docker-compose down
   ```

### Testing

```bash
# End-to-end test
./scripts/test_e2e.sh

# Test individual components
cd data-generator && python test_producer.py
cd api && pytest
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# View real-time logs
docker-compose logs -f <service>

# Interactive shell
docker exec -it <container> bash
```

---

## 📚 Documentation

- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Part 1: Setup & Data Generation
- **[IMPLEMENTATION_GUIDE_PART2.md](IMPLEMENTATION_GUIDE_PART2.md)** - Part 2: Stream & Batch Processing
- **[IMPLEMENTATION_GUIDE_PART3.md](IMPLEMENTATION_GUIDE_PART3.md)** - Part 3: API, Visualization & Deployment
- **[config/data_warehouse_schema.md](config/data_warehouse_schema.md)** - Data Warehouse Schema

---

## 👥 Team Members

- **Student 1:** [Name] - [Responsibilities]
- **Student 2:** [Name] - [Responsibilities]
- **Student 3:** [Name] - [Responsibilities]

---

## 📄 License

This project is for educational purposes as part of CSCE4501 Big Data course.

---

## 🎓 Course Information

- **Course:** CSCE4501 - Big Data
- **Semester:** Semester 9
- **Duration:** 4-5 weeks
- **Points:** 100 (20% of final grade)

---

## 🙏 Acknowledgments

- Apache Kafka, Spark, and other open-source technologies
- Course instructors and TAs
- Martin Kleppmann's "Designing Data-Intensive Applications"

---

**Built with ❤️ for Big Data Analytics**
