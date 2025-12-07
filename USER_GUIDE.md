# GlobalMart Analytics Platform - User Guide

**Version:** 1.0
**Last Updated:** December 2025

## Table of Contents

1. [Overview](#overview)
2. [Setup and Installation](#setup-and-installation)
3. [Configuration Guide](#configuration-guide)
4. [Usage Instructions](#usage-instructions)
5. [Troubleshooting](#troubleshooting)
6. [API Documentation](#api-documentation)
7. [Architecture Reference](#architecture-reference)

---

## Overview

GlobalMart Analytics Platform is a real-time e-commerce analytics system that processes streaming transaction data, performs customer segmentation using RFM analysis, and provides interactive dashboards for business intelligence.

### Key Features

- **Real-time transaction processing** with Apache Spark Structured Streaming
- **Customer segmentation** using RFM (Recency, Frequency, Monetary) analysis
- **Anomaly detection** for fraud prevention
- **Interactive dashboards** with Streamlit and Grafana
- **Scalable architecture** with Kafka, Spark, PostgreSQL, and MongoDB

### System Components

- **Data Generator**: Synthetic transaction data generator (Kafka producer)
- **Stream Processor**: Real-time transaction monitoring with Spark Streaming
- **Batch Processor**: ETL pipeline, RFM analysis, and sales trends analysis
- **Visualizations**: Streamlit executive dashboard and Grafana real-time metrics
- **Data Stores**: PostgreSQL (operational), MongoDB (data warehouse)

---

## Setup and Installation

### Prerequisites

- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 1.29+
- **Python**: Version 3.8+ (for local development)
- **Minimum Resources**: 8GB RAM, 20GB disk space

### Step 1: Clone the Repository

```bash
cd ~/Desktop/BigData
ls -la globalmart/
```

### Step 2: Start Infrastructure Services

Start all Docker containers (Kafka, Spark, PostgreSQL, MongoDB, Grafana):

```bash
cd globalmart
docker-compose up -d
```

Verify all services are running:

```bash
docker ps
```

You should see containers for:
- `globalmart-kafka`
- `globalmart-zookeeper`
- `globalmart-spark-master`
- `globalmart-spark-worker`
- `globalmart-postgres`
- `globalmart-mongodb`
- `globalmart-grafana`

### Step 3: Initialize Databases

Create PostgreSQL tables:

```bash
docker exec -it globalmart-postgres psql -U globalmart -d globalmart -f /docker-entrypoint-initdb.d/init.sql
```

Verify MongoDB connection:

```bash
docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123 --authenticationDatabase admin globalmart_dw --eval "db.stats()"
```

### Step 4: Start Data Generation

Start the transaction data generator:

```bash
docker exec -d globalmart-spark-master python3 /app/data-generator/main.py
```

Check generator logs:

```bash
docker logs -f globalmart-spark-master | grep "Generated"
```

### Step 5: Start Stream Processing

Launch the transaction monitor (Spark Structured Streaming):

```bash
docker exec -d -w /app/stream-processor globalmart-spark-master \
  /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --executor-cores 1 \
  --total-executor-cores 1 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
  transaction_monitor.py
```

### Step 6: Run Batch Processing Jobs

Wait 2-3 minutes for transactions to accumulate, then run:

**ETL Pipeline** (loads fact tables to MongoDB):

```bash
docker exec globalmart-spark-master /opt/spark/bin/spark-submit \
  --master local[*] \
  --packages org.postgresql:postgresql:42.6.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  /app/batch-processor/etl_pipeline.py
```

**RFM Analysis** (customer segmentation):

```bash
docker exec globalmart-spark-master /opt/spark/bin/spark-submit \
  --master local[*] \
  --packages org.postgresql:postgresql:42.6.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  /app/batch-processor/rfm_analysis.py
```

**Sales Trends Analysis**:

```bash
docker exec globalmart-spark-master /opt/spark/bin/spark-submit \
  --master local[*] \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  /app/batch-processor/sales_trends.py
```

### Step 7: Access Dashboards

**Streamlit Executive Dashboard**:

```bash
# Create Python virtual environment (if not exists)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install streamlit pandas plotly pymongo

# Run dashboard
streamlit run visualizations/executive_dashboard.py
```

Access at: [http://localhost:8501](http://localhost:8501)

**Grafana Real-time Metrics**:

Access at: [http://localhost:3000](http://localhost:3000)
- Username: `admin`
- Password: `admin`

**Spark Master UI**:

Access at: [http://localhost:8080](http://localhost:8080)

---

## Configuration Guide

### Data Generator Configuration

File: `data-generator/config.py`

```python
# Business Configuration
NUM_USERS = 100_000         # Total number of simulated users
NUM_PRODUCTS = 250_000      # Total number of products
NUM_CATEGORIES = 100        # Total number of categories
COUNTRIES = ['USA', 'UK', 'Canada', 'Germany', 'France']

# Event Generation Rates (events per second)
TRANSACTION_RATE = 200      # Transactions per second
PRODUCT_VIEW_RATE = 300     # Product views per second
CART_EVENT_RATE = 100       # Cart events per second

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'globalmart-kafka:9092'
KAFKA_TOPICS = {
    'transactions': 'transactions',
    'product_views': 'product_views',
    'cart_events': 'cart_events',
    'system_metrics': 'system_metrics'
}
```

### Batch Processor Configuration

File: `batch-processor/config.py`

```python
# PostgreSQL Configuration
POSTGRES_URL = "jdbc:postgresql://globalmart-postgres:5432/globalmart"
POSTGRES_PROPERTIES = {
    "user": "globalmart",
    "password": "globalmart123",
    "driver": "org.postgresql.Driver"
}

# MongoDB Configuration
MONGODB_URI = "mongodb://globalmart:globalmart123@globalmart-mongodb:27017/globalmart_dw?authSource=admin"
MONGODB_DB = "globalmart_dw"

# RFM Configuration
RFM_QUANTILES = 5  # Number of quantiles for RFM scoring (1-5)

# Data Warehouse Collections
DW_COLLECTIONS = {
    'fact_sales': 'fact_sales',
    'fact_sessions': 'fact_sessions',
    'customer_segments': 'customer_segments',
    'sales_trends': 'sales_trends',
    'product_performance': 'product_performance'
}
```

### Stream Processor Configuration

File: `stream-processor/transaction_monitor.py`

```python
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = "globalmart-kafka:9092"
KAFKA_TOPICS = {
    'transactions': 'transactions',
    'product_views': 'product_views',
    'cart_events': 'cart_events'
}

# Streaming Window Configuration
WINDOW_DURATION = "1 minute"      # Aggregation window size
SLIDING_DURATION = "30 seconds"   # Window slide interval

# Anomaly Detection Thresholds
ANOMALY_THRESHOLDS = {
    'high_value_transaction': 5000.00,   # Transactions over $5000
    'unusual_quantity': 10,              # Orders with 10+ items
    'rapid_transactions': 5              # More than 5 transactions/minute
}

# PostgreSQL Configuration
POSTGRES_URL = "jdbc:postgresql://globalmart-postgres:5432/globalmart"
POSTGRES_PROPERTIES = {
    "user": "globalmart",
    "password": "globalmart123",
    "driver": "org.postgresql.Driver"
}
```

### Docker Compose Configuration

File: `docker-compose.yml`

Key service ports:
- **Kafka**: 9092 (internal), 29092 (external)
- **Zookeeper**: 2181
- **Spark Master**: 7077 (cluster), 8080 (web UI)
- **PostgreSQL**: 5432
- **MongoDB**: 27017
- **Grafana**: 3000

Environment variables can be customized in the `docker-compose.yml` file.

---

## Usage Instructions

### Starting the System

1. **Start infrastructure**:
   ```bash
   docker-compose up -d
   ```

2. **Start data generator**:
   ```bash
   docker exec -d globalmart-spark-master python3 /app/data-generator/main.py
   ```

3. **Start stream processor**:
   ```bash
   docker exec -d -w /app/stream-processor globalmart-spark-master \
     /opt/spark/bin/spark-submit \
     --master spark://spark-master:7077 \
     --executor-cores 1 \
     --total-executor-cores 1 \
     --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
     transaction_monitor.py
   ```

4. **Wait 2-3 minutes** for data to accumulate

5. **Run batch jobs** (in order):
   - ETL Pipeline
   - RFM Analysis
   - Sales Trends Analysis

6. **Launch dashboards**:
   - Streamlit: `streamlit run visualizations/executive_dashboard.py`
   - Grafana: Navigate to [http://localhost:3000](http://localhost:3000)

### Stopping the System

1. **Stop data generator**:
   ```bash
   docker exec globalmart-spark-master pkill -f "python3.*main.py"
   ```

2. **Stop stream processor**:
   ```bash
   docker exec globalmart-spark-master bash -c "ps aux | grep transaction_monitor.py | grep -v grep | awk '{print \$2}' | xargs kill -9"
   ```

3. **Stop infrastructure**:
   ```bash
   docker-compose down
   ```

### Monitoring System Health

**Check running processes**:
```bash
docker ps
```

**View Spark jobs**:
```bash
# Navigate to Spark Master UI
http://localhost:8080
```

**Check Kafka topics**:
```bash
docker exec globalmart-kafka kafka-topics --list --bootstrap-server localhost:9092
```

**Monitor transaction count**:
```bash
docker exec -it globalmart-postgres psql -U globalmart -d globalmart -c "SELECT COUNT(*) FROM transactions;"
```

**Check MongoDB collections**:
```bash
docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123 --authenticationDatabase admin globalmart_dw --eval "db.getCollectionNames()"
```

### Running Batch Jobs Manually

Batch jobs should be run periodically (e.g., daily) to update the data warehouse:

```bash
# Run all batch jobs in sequence
docker exec globalmart-spark-master bash -c "
  /opt/spark/bin/spark-submit --master local[*] \
    --packages org.postgresql:postgresql:42.6.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
    /app/batch-processor/etl_pipeline.py && \
  /opt/spark/bin/spark-submit --master local[*] \
    --packages org.postgresql:postgresql:42.6.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
    /app/batch-processor/rfm_analysis.py && \
  /opt/spark/bin/spark-submit --master local[*] \
    --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
    /app/batch-processor/sales_trends.py
"
```

---

## Troubleshooting

### Common Issues

#### 1. Containers Not Starting

**Symptom**: `docker-compose up -d` fails or containers exit immediately

**Solutions**:
- Check Docker daemon is running: `sudo systemctl status docker`
- Check available resources: `docker system df`
- View container logs: `docker logs <container-name>`
- Restart Docker: `sudo systemctl restart docker`

#### 2. Kafka Connection Errors

**Symptom**: `Failed to connect to Kafka broker` or `Connection refused`

**Solutions**:
- Verify Kafka is running: `docker ps | grep kafka`
- Check Kafka logs: `docker logs globalmart-kafka`
- Wait for Kafka to fully start (can take 30-60 seconds)
- Test connection: `docker exec globalmart-kafka kafka-topics --list --bootstrap-server localhost:9092`

#### 3. PostgreSQL Connection Issues

**Symptom**: `psycopg2.OperationalError` or `Connection refused`

**Solutions**:
- Check PostgreSQL is running: `docker ps | grep postgres`
- Verify credentials in config files
- Test connection:
  ```bash
  docker exec -it globalmart-postgres psql -U globalmart -d globalmart -c "SELECT 1"
  ```

#### 4. MongoDB Authentication Failures

**Symptom**: `Authentication failed` or `MongoServerError`

**Solutions**:
- Check MongoDB is running: `docker ps | grep mongodb`
- Verify connection URI format:
  ```
  mongodb://globalmart:globalmart123@localhost:27017/globalmart_dw?authSource=admin
  ```
- Test connection:
  ```bash
  docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123 --authenticationDatabase admin
  ```

#### 5. Spark Jobs Failing

**Symptom**: Spark submit returns errors or jobs hang

**Solutions**:
- Check Spark Master UI: [http://localhost:8080](http://localhost:8080)
- View Spark logs: `docker logs globalmart-spark-master`
- Verify package versions match Spark version (3.5.0)
- Increase executor memory if OOM errors occur
- Check if ports 7077 and 8080 are available

#### 6. No Data in Transactions Table

**Symptom**: `SELECT COUNT(*) FROM transactions` returns 0

**Solutions**:
- Verify data generator is running:
  ```bash
  docker exec globalmart-spark-master ps aux | grep "python3.*main.py"
  ```
- Verify stream processor is running:
  ```bash
  docker exec globalmart-spark-master ps aux | grep transaction_monitor
  ```
- Check Kafka topic has messages:
  ```bash
  docker exec globalmart-kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic transactions \
    --from-beginning \
    --max-messages 1
  ```
- Restart transaction monitor (see [Usage Instructions](#usage-instructions))

#### 7. NULL Values in total_amount Column

**Symptom**: Revenue shows as $0 or NULL in queries

**Solutions**:
- Verify transaction_monitor.py has decimal casting (line 196):
  ```python
  col("total_amount").cast("decimal(12,2)").alias("total_amount")
  ```
- Clear and restart:
  ```bash
  # Stop transaction monitor
  docker exec globalmart-spark-master bash -c "ps aux | grep transaction_monitor.py | grep -v grep | awk '{print \$2}' | xargs kill -9"

  # Clear transactions table
  docker exec -it globalmart-postgres psql -U globalmart -d globalmart -c "TRUNCATE TABLE transactions"

  # Restart transaction monitor
  docker exec -d -w /app/stream-processor globalmart-spark-master \
    /opt/spark/bin/spark-submit \
    --master spark://spark-master:7077 \
    --executor-cores 1 \
    --total-executor-cores 1 \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    transaction_monitor.py
  ```

#### 8. Grafana Dashboards Show No Data

**Symptom**: Grafana panels display "No data"

**Solutions**:
- Verify PostgreSQL datasource is configured correctly in Grafana
- Check `sales_metrics` table has data:
  ```bash
  docker exec -it globalmart-postgres psql -U globalmart -d globalmart -c "SELECT COUNT(*) FROM sales_metrics"
  ```
- Verify time range in Grafana matches data timestamps
- Check panel queries for syntax errors

#### 9. Streamlit Dashboard Errors

**Symptom**: `Decimal128` type errors or `No module named` errors

**Solutions**:
- Install required packages:
  ```bash
  pip install streamlit pandas plotly pymongo
  ```
- Clear Streamlit cache: Press 'C' in browser or restart Streamlit
- Verify MongoDB has data:
  ```bash
  docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123 --authenticationDatabase admin globalmart_dw --eval "db.customer_segments.count()"
  ```

#### 10. Country Filter Not Working

**Symptom**: Selecting a country in the dashboard doesn't change data

**Solutions**:
- Refresh the Streamlit page (press 'R' in browser)
- Clear cache and rerun: Press 'C' in Streamlit UI
- Verify the dashboard code includes country filtering on all pages

### Performance Tuning

**Slow Spark Jobs**:
- Increase executor memory in docker-compose.yml
- Reduce data generator rates in `config.py`
- Add more Spark workers

**High Memory Usage**:
- Limit data generator throughput
- Reduce batch sizes in ETL jobs
- Increase Docker memory limits

**Slow Dashboard Loading**:
- Add indexes to MongoDB collections
- Reduce cache TTL in Streamlit
- Limit data loaded (use `.limit()` in MongoDB queries)

---

## API Documentation

### REST API Endpoints

The FastAPI service provides REST endpoints for programmatic access to analytics data.

**Base URL**: `http://localhost:8000`

#### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-07T04:32:00Z"
}
```

#### Get Sales Metrics

```http
GET /api/v1/sales/metrics
```

**Query Parameters**:
- `start_date` (optional): ISO 8601 date string
- `end_date` (optional): ISO 8601 date string
- `country` (optional): Country code

**Response**:
```json
{
  "total_revenue": 17096943.98,
  "total_transactions": 24800,
  "avg_order_value": 689.39,
  "period": {
    "start": "2025-12-01",
    "end": "2025-12-07"
  }
}
```

#### Get Customer Segments

```http
GET /api/v1/customers/segments
```

**Query Parameters**:
- `country` (optional): Filter by country

**Response**:
```json
{
  "segments": [
    {
      "segment_name": "Champions",
      "customer_count": 8934,
      "avg_monetary": 1245.67,
      "avg_frequency": 12.3,
      "total_value": 11123456.78
    },
    ...
  ]
}
```

#### Get Product Performance

```http
GET /api/v1/products/performance
```

**Query Parameters**:
- `category` (optional): Filter by category
- `limit` (optional): Number of results (default: 100)

**Response**:
```json
{
  "products": [
    {
      "category": "Electronics",
      "revenue": 3456789.12,
      "transaction_count": 4532,
      "avg_transaction_value": 762.45
    },
    ...
  ]
}
```

#### Get Anomalies

```http
GET /api/v1/anomalies
```

**Query Parameters**:
- `anomaly_type` (optional): Filter by type (`high_value`, `unusual_quantity`)
- `start_date` (optional): ISO 8601 date string
- `limit` (optional): Number of results (default: 100)

**Response**:
```json
{
  "anomalies": [
    {
      "transaction_id": "abc123",
      "user_id": "user456",
      "anomaly_type": "high_value",
      "anomaly_score": 1.8,
      "amount": 9000.00,
      "detected_at": "2025-12-07T04:30:00Z",
      "description": "High value transaction: $9000.00"
    },
    ...
  ]
}
```

### Database Schemas

#### PostgreSQL Tables

**transactions**:
```sql
CREATE TABLE transactions (
    transaction_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    category VARCHAR(100),
    country VARCHAR(50),
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_time ON transactions(timestamp);
CREATE INDEX idx_transactions_country ON transactions(country);
```

**sales_metrics**:
```sql
CREATE TABLE sales_metrics (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    category VARCHAR(100),
    country VARCHAR(50),
    total_amount DECIMAL(15, 2),
    transaction_count INTEGER,
    avg_transaction_value DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_metrics_time ON sales_metrics(window_start, window_end);
CREATE INDEX idx_sales_metrics_country ON sales_metrics(country);
```

**transaction_anomalies**:
```sql
CREATE TABLE transaction_anomalies (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100),
    user_id VARCHAR(100),
    amount DECIMAL(12, 2),
    anomaly_score DECIMAL(10, 4),
    anomaly_type VARCHAR(50),
    detected_at TIMESTAMP,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_anomalies_type ON transaction_anomalies(anomaly_type);
CREATE INDEX idx_anomalies_time ON transaction_anomalies(detected_at);
```

#### MongoDB Collections

**customer_segments**:
```json
{
  "user_id": "string",
  "country": "string",
  "recency": "integer",
  "frequency": "integer",
  "monetary": "decimal128",
  "r_score": "integer",
  "f_score": "integer",
  "m_score": "integer",
  "rfm_segment": "string",
  "segment_name": "string",
  "analysis_date": "datetime"
}
```

**fact_sales**:
```json
{
  "date_time": "datetime",
  "country": "string",
  "category": "string",
  "total_amount": "decimal128",
  "transaction_count": "integer",
  "avg_transaction_value": "decimal128"
}
```

**sales_trends**:
```json
{
  "period_type": "string",  // "daily", "weekly", "monthly"
  "period": "string",
  "revenue": "decimal128",
  "transactions": "integer",
  "revenue_growth_rate": "decimal128",
  "analysis_date": "datetime"
}
```

### Python Client Example

```python
import requests
from datetime import datetime, timedelta

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Get sales metrics for last 7 days
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

response = requests.get(
    f"{BASE_URL}/sales/metrics",
    params={
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "country": "USA"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Total Revenue: ${data['total_revenue']:,.2f}")
    print(f"Total Transactions: {data['total_transactions']:,}")
else:
    print(f"Error: {response.status_code}")
```

---

## Architecture Reference

### System Architecture

```
┌─────────────────┐
│  Data Generator │
│   (Kafka Prod)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Apache Kafka   │
│  (Event Stream) │
└────┬────────────┘
     │
     ├──────────────────────┐
     │                      │
     ▼                      ▼
┌─────────────┐    ┌──────────────┐
│   Spark     │    │    Spark     │
│  Streaming  │    │    Batch     │
│  (Monitor)  │    │ (ETL/RFM)    │
└──────┬──────┘    └──────┬───────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌─────────────┐
│  PostgreSQL  │   │   MongoDB   │
│ (Operational)│   │(Data Warehouse)
└──────┬───────┘   └──────┬──────┘
       │                  │
       └────────┬─────────┘
                │
         ┌──────┴──────┐
         │             │
         ▼             ▼
    ┌─────────┐  ┌──────────┐
    │ Grafana │  │Streamlit │
    │Dashboard│  │Dashboard │
    └─────────┘  └──────────┘
```

### Data Flow

1. **Data Generation**: Synthetic transactions generated at 200/sec
2. **Streaming**: Kafka distributes events to consumers
3. **Real-time Processing**: Spark Streaming processes transactions, detects anomalies, aggregates metrics
4. **Storage**: PostgreSQL stores operational data, MongoDB stores analytics
5. **Batch Processing**: Daily ETL jobs update data warehouse
6. **Visualization**: Dashboards query databases for interactive analytics

### Technology Stack

- **Message Queue**: Apache Kafka 3.5.0
- **Stream Processing**: Apache Spark 3.5.0 (Structured Streaming)
- **Batch Processing**: Apache Spark 3.5.0 (SQL/DataFrames)
- **Operational Database**: PostgreSQL 14
- **Data Warehouse**: MongoDB 6.0
- **Dashboards**: Streamlit 1.28+, Grafana 10.0
- **Orchestration**: Docker Compose
- **Language**: Python 3.8+

---

## Support and Contribution

### Getting Help

- Check this user guide first
- Review troubleshooting section
- Check Docker/Spark/Kafka logs
- Consult official documentation for components

### Best Practices

1. **Monitor resource usage** regularly
2. **Run batch jobs daily** to keep data warehouse current
3. **Set up alerts** in Grafana for anomaly thresholds
4. **Backup databases** regularly
5. **Scale Spark workers** based on load
6. **Tune Kafka** for higher throughput if needed

### Maintenance Tasks

**Daily**:
- Run batch ETL jobs
- Check system health
- Review anomaly alerts

**Weekly**:
- Clean up old Kafka logs
- Vacuum PostgreSQL tables
- Compact MongoDB collections

**Monthly**:
- Review and optimize indexes
- Archive old data
- Update dependencies

---

**End of User Guide**