# GlobalMart: Real-Time E-Commerce Analytics Platform
## Complete Implementation Guide for Linux with Docker

**Duration:** 4-5 weeks | **Team Size:** 3 students | **Total Points:** 100 (20% of final grade)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Prerequisites & Setup](#prerequisites--setup)
4. [Component 1: Data Generation and Ingestion (20 points)](#component-1-data-generation-and-ingestion)
5. [Component 2: Stream Processing Pipeline (30 points)](#component-2-stream-processing-pipeline)
6. [Component 3: Batch Processing and Data Warehouse (25 points)](#component-3-batch-processing-and-data-warehouse)
7. [Component 4: Visualization and API Layer (15 points)](#component-4-visualization-and-api-layer)
8. [Component 5: Infrastructure and Deployment (10 points)](#component-5-infrastructure-and-deployment)
9. [Testing & Validation](#testing--validation)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

### Business Scenario: GlobalMart
- **10 million** active users
- **250,000** products across **100** categories
- Operations in **5** countries
- **100,000** daily transactions
- Real-time monitoring and business intelligence requirements

### Technology Stack (Docker-Based)
```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Environment                       │
├─────────────────────────────────────────────────────────────┤
│ Storage:          HDFS / MinIO (S3-compatible)              │
│ Message Queue:    Apache Kafka + Zookeeper                  │
│ Stream Processing: Apache Spark Streaming                   │
│ Batch Processing:  Apache Spark                             │
│ Databases:         PostgreSQL + MongoDB                     │
│ Visualization:     Grafana                                  │
│ API:              FastAPI / Flask                           │
│ Monitoring:       Prometheus (optional)                     │
│ Caching:          Redis (optional)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## System Architecture

### High-Level Architecture Diagram
```
┌─────────────────┐
│  Data Generator │
│   (Python)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Kafka Topics   │────▶│ Spark Streaming  │────▶│ PostgreSQL  │
│  - transactions │     │  - Anomaly Det.  │     │  - Metrics  │
│  - product_views│     │  - Inventory     │     └─────────────┘
│  - cart_events  │     │  - Sessions      │
└─────────────────┘     └──────────────────┘
         │
         │
         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Data Lake      │────▶│  Spark Batch     │────▶│  MongoDB    │
│  (MinIO/HDFS)   │     │  - RFM Analysis  │     │  - Analytics│
└─────────────────┘     │  - Aggregations  │     └─────────────┘
                        └──────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │   REST API       │
                        │   (FastAPI)      │
                        └──────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │    Grafana       │
                        │   Dashboards     │
                        └──────────────────┘
```

---

## Prerequisites & Setup

### Step 1: Verify Docker Installation

**Start Docker Desktop:**
```bash
# Check if Docker Desktop is running
docker ps

# If not running, start Docker Desktop from Applications
open -a Docker

# Wait for Docker to start, then verify
docker --version
docker-compose --version
```

**Expected Output:**
```
Docker version 28.4.0, build d8eb465
Docker Compose version v2.39.4-desktop.1
```

### Step 2: Create Project Structure

```bash
# Create project directory structure
mkdir -p globalmart/{data-generator,stream-processor,batch-processor,api,dashboards,docker,scripts,data,logs,config}

cd globalmart

# Create subdirectories
mkdir -p data/{raw,processed,warehouse}
mkdir -p logs/{kafka,spark,api}
mkdir -p config/{kafka,spark,postgres,mongodb,grafana}
mkdir -p docker/{kafka,spark,postgres,mongodb,api,grafana}
```

**Final Directory Structure:**
```
globalmart/
├── data-generator/          # Python scripts for data generation
├── stream-processor/        # Spark Streaming applications
├── batch-processor/         # Spark Batch jobs
├── api/                     # FastAPI REST API
├── dashboards/              # Grafana dashboard configs
├── docker/                  # Dockerfiles for each service
├── scripts/                 # Utility scripts
├── data/                    # Data storage
│   ├── raw/                 # Raw event data
│   ├── processed/           # Processed data
│   └── warehouse/           # Data warehouse
├── logs/                    # Application logs
├── config/                  # Configuration files
└── docker-compose.yml       # Docker orchestration
```

### Step 3: Install Python Dependencies Locally (for development)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install kafka-python faker pandas numpy pyspark fastapi uvicorn psycopg2-binary pymongo redis requests
```

---

## Component 1: Data Generation and Ingestion

**Points:** 20 | **Estimated Time:** Week 1

### 1.1 Understanding the Requirements

**Generate three types of events:**
1. **Transaction Events** - Completed purchases
2. **Product View Events** - User browsing activity
3. **Cart Events** - Add to cart, remove from cart

**Performance Target:** 500 events/second

### 1.2 Data Schemas

Create `config/schemas.py`:

```python
from datetime import datetime
import uuid

# User Profile Schema
USER_SCHEMA = {
    "user_id": "string (UUID)",
    "email": "string",
    "age": "integer (18-80)",
    "country": "string (USA, UK, Canada, Germany, France)",
    "registration_date": "timestamp",
    "preferences": ["array of categories"]
}

# Transaction Event Schema
TRANSACTION_SCHEMA = {
    "transaction_id": "string (UUID)",
    "user_id": "string (UUID)",
    "timestamp": "timestamp (ISO 8601)",
    "products": [{
        "product_id": "string (UUID)",
        "quantity": "integer (1-10)",
        "price": "float (10.00-2000.00)"
    }],
    "total_amount": "float",
    "payment_method": "string (credit_card, paypal, debit_card, apple_pay)"
}

# Product View Event Schema
PRODUCT_VIEW_SCHEMA = {
    "event_id": "string (UUID)",
    "user_id": "string (UUID)",
    "product_id": "string (UUID)",
    "timestamp": "timestamp",
    "session_id": "string (UUID)",
    "duration_seconds": "integer (5-300)"
}

# Cart Event Schema
CART_EVENT_SCHEMA = {
    "event_id": "string (UUID)",
    "user_id": "string (UUID)",
    "product_id": "string (UUID)",
    "timestamp": "timestamp",
    "action": "string (add, remove, update)",
    "quantity": "integer (0-10)",
    "session_id": "string (UUID)"
}

# Product Catalog Schema
PRODUCT_SCHEMA = {
    "product_id": "string (UUID)",
    "name": "string",
    "category": "string (100 categories)",
    "price": "float (10.00-2000.00)",
    "inventory": "integer (0-1000)",
    "ratings": "float (1.0-5.0)"
}
```

### 1.3 Docker Setup for Kafka

Create `docker/docker-compose.kafka.yml`:

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    platform: linux/amd64
    container_name: globalmart-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
      - zookeeper-logs:/var/lib/zookeeper/log
    networks:
      - globalmart-network

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    platform: linux/amd64
    container_name: globalmart-kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
      KAFKA_LOG_RETENTION_HOURS: 168
    volumes:
      - kafka-data:/var/lib/kafka/data
    networks:
      - globalmart-network

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    platform: linux/amd64
    container_name: globalmart-kafka-ui
    depends_on:
      - kafka
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: globalmart
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181
    networks:
      - globalmart-network

volumes:
  zookeeper-data:
  zookeeper-logs:
  kafka-data:

networks:
  globalmart-network:
    driver: bridge
```

**Start Kafka:**
```bash
cd globalmart
docker-compose -f docker/docker-compose.kafka.yml up -d

# Verify Kafka is running
docker ps
docker logs globalmart-kafka

# Access Kafka UI at http://localhost:8080
```

### 1.4 Create Kafka Topics

Create `scripts/create_topics.sh`:

```bash
#!/bin/bash

# Create Kafka topics for GlobalMart

KAFKA_CONTAINER="globalmart-kafka"

echo "Creating Kafka topics..."

# Transaction events topic
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic transactions \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000

# Product view events topic
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic product_views \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000

# Cart events topic
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic cart_events \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000

# System metrics topic
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic system_metrics \
  --partitions 1 \
  --replication-factor 1 \
  --config retention.ms=86400000

echo "Listing all topics:"
docker exec $KAFKA_CONTAINER kafka-topics --list --bootstrap-server localhost:9092

echo "Topics created successfully!"
```

**Run the script:**
```bash
chmod +x scripts/create_topics.sh
./scripts/create_topics.sh
```

### 1.5 Data Generator Implementation

Create `data-generator/config.py`:

```python
"""
Configuration for GlobalMart Data Generator
"""

# Business Configuration
NUM_USERS = 10_000_000  # 10 million active users
NUM_PRODUCTS = 250_000  # 250k products
NUM_CATEGORIES = 100    # 100 categories
COUNTRIES = ['USA', 'UK', 'Canada', 'Germany', 'France']
DAILY_TRANSACTIONS = 100_000

# Event Generation Rates (events per second)
TARGET_THROUGHPUT = 500  # Total events per second
TRANSACTION_RATE = 100   # ~20% of throughput
PRODUCT_VIEW_RATE = 300  # ~60% of throughput
CART_EVENT_RATE = 100    # ~20% of throughput

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9093'
KAFKA_TOPICS = {
    'transactions': 'transactions',
    'product_views': 'product_views',
    'cart_events': 'cart_events',
    'system_metrics': 'system_metrics'
}

# Data Generation Parameters
PRODUCT_CATEGORIES = [
    'Electronics', 'Clothing', 'Home & Garden', 'Books', 'Sports',
    'Toys', 'Food & Beverages', 'Beauty', 'Automotive', 'Health',
    # ... add 90 more categories
]

PAYMENT_METHODS = ['credit_card', 'paypal', 'debit_card', 'apple_pay', 'google_pay']

# Price Ranges by Category (min, max)
PRICE_RANGES = {
    'Electronics': (50, 2000),
    'Clothing': (10, 200),
    'Home & Garden': (15, 500),
    'Books': (10, 50),
    'Sports': (20, 300),
    # Default for others
    'default': (10, 200)
}
```

Create `data-generator/generators.py`:

```python
"""
Data generators for GlobalMart events
"""

from faker import Faker
import random
import uuid
from datetime import datetime, timedelta
import json

fake = Faker()

class DataGenerator:
    def __init__(self, config):
        self.config = config
        self.users = []
        self.products = []
        self.active_sessions = {}

    def generate_user_pool(self, num_users=10000):
        """Generate a pool of users for realistic data"""
        print(f"Generating {num_users} users...")
        self.users = []
        for _ in range(num_users):
            user = {
                'user_id': str(uuid.uuid4()),
                'email': fake.email(),
                'age': random.randint(18, 80),
                'country': random.choice(self.config.COUNTRIES),
                'registration_date': fake.date_time_between(
                    start_date='-2y',
                    end_date='now'
                ).isoformat(),
                'preferences': random.sample(
                    self.config.PRODUCT_CATEGORIES,
                    k=random.randint(1, 5)
                )
            }
            self.users.append(user)
        print(f"Generated {len(self.users)} users")
        return self.users

    def generate_product_catalog(self, num_products=10000):
        """Generate product catalog"""
        print(f"Generating {num_products} products...")
        self.products = []
        for _ in range(num_products):
            category = random.choice(self.config.PRODUCT_CATEGORIES)
            price_range = self.config.PRICE_RANGES.get(
                category,
                self.config.PRICE_RANGES['default']
            )

            product = {
                'product_id': str(uuid.uuid4()),
                'name': fake.catch_phrase(),
                'category': category,
                'price': round(random.uniform(*price_range), 2),
                'inventory': random.randint(0, 1000),
                'ratings': round(random.uniform(1.0, 5.0), 1)
            }
            self.products.append(product)
        print(f"Generated {len(self.products)} products")
        return self.products

    def generate_transaction_event(self):
        """Generate a transaction event"""
        user = random.choice(self.users)
        num_items = random.randint(1, 5)
        products = random.sample(self.products, num_items)

        transaction_products = []
        total_amount = 0

        for product in products:
            quantity = random.randint(1, 3)
            item_total = product['price'] * quantity
            total_amount += item_total

            transaction_products.append({
                'product_id': product['product_id'],
                'quantity': quantity,
                'price': product['price']
            })

        event = {
            'transaction_id': str(uuid.uuid4()),
            'user_id': user['user_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'products': transaction_products,
            'total_amount': round(total_amount, 2),
            'payment_method': random.choice(self.config.PAYMENT_METHODS),
            'country': user['country']
        }

        return event

    def generate_product_view_event(self):
        """Generate a product view event"""
        user = random.choice(self.users)
        product = random.choice(self.products)

        # Create or get session ID
        if user['user_id'] not in self.active_sessions or \
           random.random() < 0.1:  # 10% chance of new session
            self.active_sessions[user['user_id']] = str(uuid.uuid4())

        event = {
            'event_id': str(uuid.uuid4()),
            'user_id': user['user_id'],
            'product_id': product['product_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.active_sessions[user['user_id']],
            'duration_seconds': random.randint(5, 300),
            'category': product['category']
        }

        return event

    def generate_cart_event(self):
        """Generate a cart event (add/remove/update)"""
        user = random.choice(self.users)
        product = random.choice(self.products)
        action = random.choice(['add', 'add', 'add', 'remove', 'update'])

        # Create or get session ID
        if user['user_id'] not in self.active_sessions:
            self.active_sessions[user['user_id']] = str(uuid.uuid4())

        event = {
            'event_id': str(uuid.uuid4()),
            'user_id': user['user_id'],
            'product_id': product['product_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'quantity': random.randint(1, 5) if action != 'remove' else 0,
            'session_id': self.active_sessions[user['user_id']]
        }

        return event
```

Create `data-generator/producer.py`:

```python
"""
Kafka Producer for GlobalMart events
"""

from kafka import KafkaProducer
import json
import time
import logging
from datetime import datetime
from generators import DataGenerator
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GlobalMartProducer:
    def __init__(self):
        self.config = config
        self.producer = None
        self.generator = DataGenerator(config)
        self.stats = {
            'transactions': 0,
            'product_views': 0,
            'cart_events': 0,
            'errors': 0
        }

    def connect(self):
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=5
            )
            logger.info("Connected to Kafka successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False

    def send_event(self, topic, event):
        """Send event to Kafka topic"""
        try:
            future = self.producer.send(topic, value=event)
            future.get(timeout=10)  # Wait for confirmation
            return True
        except Exception as e:
            logger.error(f"Error sending to {topic}: {e}")
            self.stats['errors'] += 1
            return False

    def start_streaming(self, duration_seconds=None):
        """Start streaming events"""
        logger.info("Starting event generation...")

        # Generate initial data
        self.generator.generate_user_pool(10000)  # Generate 10k users
        self.generator.generate_product_catalog(10000)  # Generate 10k products

        start_time = time.time()
        iteration = 0

        try:
            while True:
                iteration += 1
                cycle_start = time.time()

                # Generate events based on configured rates
                # Transaction events (100/sec)
                for _ in range(self.config.TRANSACTION_RATE):
                    event = self.generator.generate_transaction_event()
                    if self.send_event(self.config.KAFKA_TOPICS['transactions'], event):
                        self.stats['transactions'] += 1

                # Product view events (300/sec)
                for _ in range(self.config.PRODUCT_VIEW_RATE):
                    event = self.generator.generate_product_view_event()
                    if self.send_event(self.config.KAFKA_TOPICS['product_views'], event):
                        self.stats['product_views'] += 1

                # Cart events (100/sec)
                for _ in range(self.config.CART_EVENT_RATE):
                    event = self.generator.generate_cart_event()
                    if self.send_event(self.config.KAFKA_TOPICS['cart_events'], event):
                        self.stats['cart_events'] += 1

                # Log statistics every 10 seconds
                if iteration % 10 == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"""
                    === Statistics (after {elapsed:.1f}s) ===
                    Transactions: {self.stats['transactions']} ({self.stats['transactions']/elapsed:.1f}/s)
                    Product Views: {self.stats['product_views']} ({self.stats['product_views']/elapsed:.1f}/s)
                    Cart Events: {self.stats['cart_events']} ({self.stats['cart_events']/elapsed:.1f}/s)
                    Errors: {self.stats['errors']}
                    Total Events: {sum([self.stats['transactions'], self.stats['product_views'], self.stats['cart_events']])}
                    """)

                # Check if duration limit reached
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    logger.info(f"Reached duration limit of {duration_seconds} seconds")
                    break

                # Sleep to maintain target rate (1 second per cycle)
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, 1.0 - cycle_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Stopping event generation...")
        finally:
            self.close()

    def close(self):
        """Close producer connection"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Producer closed")

if __name__ == '__main__':
    producer = GlobalMartProducer()
    if producer.connect():
        producer.start_streaming()
```

Create `data-generator/requirements.txt`:

```
kafka-python==2.0.2
faker==20.1.0
```

### 1.6 Testing Data Generation

**Create test script `data-generator/test_producer.py`:**

```python
"""
Test data generator and Kafka producer
"""

from producer import GlobalMartProducer
import logging

logging.basicConfig(level=logging.INFO)

def test_connection():
    """Test Kafka connection"""
    print("Testing Kafka connection...")
    producer = GlobalMartProducer()
    if producer.connect():
        print("✓ Connection successful")
        producer.close()
        return True
    else:
        print("✗ Connection failed")
        return False

def test_event_generation():
    """Test event generation"""
    print("\nTesting event generation...")
    producer = GlobalMartProducer()
    producer.generator.generate_user_pool(100)
    producer.generator.generate_product_catalog(100)

    # Generate sample events
    transaction = producer.generator.generate_transaction_event()
    product_view = producer.generator.generate_product_view_event()
    cart_event = producer.generator.generate_cart_event()

    print("✓ Transaction event:", transaction)
    print("✓ Product view event:", product_view)
    print("✓ Cart event:", cart_event)

def test_producer_run():
    """Test producer for 30 seconds"""
    print("\nTesting producer (30 seconds)...")
    producer = GlobalMartProducer()
    if producer.connect():
        producer.start_streaming(duration_seconds=30)
        print("✓ Producer test completed")
    else:
        print("✗ Producer test failed")

if __name__ == '__main__':
    test_connection()
    test_event_generation()
    test_producer_run()
```

**Run tests:**
```bash
cd data-generator
pip install -r requirements.txt
python test_producer.py
```

### 1.7 Monitoring Dashboard (Basic)

Create `scripts/monitor_kafka.sh`:

```bash
#!/bin/bash

# Monitor Kafka topics for GlobalMart

KAFKA_CONTAINER="globalmart-kafka"

echo "Monitoring Kafka topics..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=== GlobalMart Kafka Monitoring ==="
    echo "Time: $(date)"
    echo ""

    # Get message counts for each topic
    echo "Topic: transactions"
    docker exec $KAFKA_CONTAINER kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 \
        --topic transactions \
        --time -1 | awk -F ":" '{sum += $3} END {print "  Messages: " sum}'

    echo ""
    echo "Topic: product_views"
    docker exec $KAFKA_CONTAINER kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 \
        --topic product_views \
        --time -1 | awk -F ":" '{sum += $3} END {print "  Messages: " sum}'

    echo ""
    echo "Topic: cart_events"
    docker exec $KAFKA_CONTAINER kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 \
        --topic cart_events \
        --time -1 | awk -F ":" '{sum += $3} END {print "  Messages: " sum}'

    echo ""
    echo "Consumer Groups:"
    docker exec $KAFKA_CONTAINER kafka-consumer-groups \
        --bootstrap-server localhost:9092 \
        --list

    sleep 5
done
```

**Run monitoring:**
```bash
chmod +x scripts/monitor_kafka.sh
./scripts/monitor_kafka.sh
```

### 1.8 Deliverables Checklist

- [ ] Kafka cluster running in Docker
- [ ] Three topics created (transactions, product_views, cart_events)
- [ ] Data generator with configurable parameters
- [ ] Kafka producers for all event types
- [ ] Data quality validation (schema validation)
- [ ] Duplicate handling (unique IDs)
- [ ] Target throughput achieved (500 events/sec)
- [ ] Basic monitoring dashboard (Kafka UI at localhost:8080)

**Testing Commands:**
```bash
# Start Kafka
docker-compose -f docker/docker-compose.kafka.yml up -d

# Create topics
./scripts/create_topics.sh

# Run data generator
cd data-generator
python producer.py

# Monitor in separate terminal
./scripts/monitor_kafka.sh

# View Kafka UI
open http://localhost:8080
```

---

## Component 2: Stream Processing Pipeline

**Points:** 30 | **Estimated Time:** Week 2

### 2.1 Understanding Requirements

**Real-time Processing Tasks:**
1. **Transaction Monitoring** - Detect anomalies in real-time
2. **Inventory Tracking** - Monitor stock levels and alert on low inventory
3. **Session Analysis** - Track user sessions and detect cart abandonment
4. **Sales Metrics** - Aggregate sales by hour, category, and region

### 2.2 Setup Spark Streaming with Docker

Create `docker/docker-compose.spark.yml`:

```yaml
version: '3.8'

services:
  spark-master:
    image: bitnami/spark:3.5.0
    platform: linux/amd64
    container_name: globalmart-spark-master
    environment:
      - SPARK_MODE=master
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
      - SPARK_MASTER_WEBUI_PORT=8081
    ports:
      - "8081:8081"
      - "7077:7077"
    volumes:
      - ../stream-processor:/app
      - ../data:/data
      - ../logs:/logs
    networks:
      - globalmart-network

  spark-worker-1:
    image: bitnami/spark:3.5.0
    platform: linux/amd64
    container_name: globalmart-spark-worker-1
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=2G
      - SPARK_WORKER_CORES=2
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    depends_on:
      - spark-master
    volumes:
      - ../stream-processor:/app
      - ../data:/data
      - ../logs:/logs
    networks:
      - globalmart-network

  spark-worker-2:
    image: bitnami/spark:3.5.0
    platform: linux/amd64
    container_name: globalmart-spark-worker-2
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=2G
      - SPARK_WORKER_CORES=2
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    depends_on:
      - spark-master
    volumes:
      - ../stream-processor:/app
      - ../data:/data
      - ../logs:/logs
    networks:
      - globalmart-network

networks:
  globalmart-network:
    external: true
```

**Start Spark:**
```bash
# Create network if not exists
docker network create globalmart-network

# Start Spark cluster
docker-compose -f docker/docker-compose.spark.yml up -d

# Verify Spark is running
docker ps | grep spark

# Access Spark UI at http://localhost:8081
```

### 2.3 PostgreSQL Setup for Metrics Storage

Create `docker/docker-compose.postgres.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    platform: linux/amd64
    container_name: globalmart-postgres
    environment:
      POSTGRES_DB: globalmart
      POSTGRES_USER: globalmart
      POSTGRES_PASSWORD: globalmart123
      POSTGRES_INITDB_ARGS: "-E UTF8"
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ../config/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - globalmart-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U globalmart"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:

networks:
  globalmart-network:
    external: true
```

Create `config/postgres/init.sql`:

```sql
-- GlobalMart Database Schema

-- Real-time sales metrics
CREATE TABLE sales_metrics (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    category VARCHAR(100),
    country VARCHAR(50),
    total_amount DECIMAL(12, 2),
    transaction_count INTEGER,
    avg_transaction_value DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(window_start, category, country)
);

CREATE INDEX idx_sales_metrics_window ON sales_metrics(window_start, window_end);
CREATE INDEX idx_sales_metrics_category ON sales_metrics(category);
CREATE INDEX idx_sales_metrics_country ON sales_metrics(country);

-- Inventory tracking
CREATE TABLE inventory_status (
    product_id VARCHAR(100) PRIMARY KEY,
    product_name VARCHAR(255),
    category VARCHAR(100),
    current_stock INTEGER,
    reserved_stock INTEGER,
    available_stock INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_category ON inventory_status(category);
CREATE INDEX idx_inventory_stock ON inventory_status(available_stock);

-- Low stock alerts
CREATE TABLE low_stock_alerts (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100),
    product_name VARCHAR(255),
    category VARCHAR(100),
    current_stock INTEGER,
    threshold INTEGER DEFAULT 10,
    alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);

CREATE INDEX idx_low_stock_product ON low_stock_alerts(product_id);
CREATE INDEX idx_low_stock_status ON low_stock_alerts(status);

-- Anomaly detection results
CREATE TABLE transaction_anomalies (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) UNIQUE,
    user_id VARCHAR(100),
    amount DECIMAL(12, 2),
    anomaly_score DECIMAL(5, 4),
    anomaly_type VARCHAR(50),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

CREATE INDEX idx_anomalies_user ON transaction_anomalies(user_id);
CREATE INDEX idx_anomalies_time ON transaction_anomalies(detected_at);

-- Session analysis
CREATE TABLE session_metrics (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    page_views INTEGER,
    cart_adds INTEGER,
    cart_removes INTEGER,
    purchase_completed BOOLEAN DEFAULT FALSE,
    abandoned BOOLEAN DEFAULT FALSE,
    total_amount DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_session_user ON session_metrics(user_id);
CREATE INDEX idx_session_abandoned ON session_metrics(abandoned);
CREATE INDEX idx_session_time ON session_metrics(start_time);

-- Cart abandonment tracking
CREATE TABLE cart_abandonment (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    user_id VARCHAR(100),
    products_in_cart INTEGER,
    cart_value DECIMAL(12, 2),
    abandonment_time TIMESTAMP,
    time_in_cart_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_abandonment_user ON cart_abandonment(user_id);
CREATE INDEX idx_abandonment_time ON cart_abandonment(abandonment_time);

-- Real-time dashboard metrics
CREATE TABLE dashboard_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value DECIMAL(15, 2),
    metric_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dashboard_name ON dashboard_metrics(metric_name);
CREATE INDEX idx_dashboard_time ON dashboard_metrics(timestamp);
```

**Start PostgreSQL:**
```bash
docker-compose -f docker/docker-compose.postgres.yml up -d

# Verify database is ready
docker exec globalmart-postgres psql -U globalmart -d globalmart -c "\dt"
```

### 2.4 Stream Processing Applications

Create `stream-processor/requirements.txt`:

```
pyspark==3.5.0
kafka-python==2.0.2
psycopg2-binary==2.9.9
```

Create `stream-processor/config.py`:

```python
"""
Stream processing configuration
"""

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
KAFKA_TOPICS = {
    'transactions': 'transactions',
    'product_views': 'product_views',
    'cart_events': 'cart_events'
}

# Spark Configuration
SPARK_APP_NAME = "GlobalMart Stream Processor"
SPARK_MASTER = "spark://spark-master:7077"
CHECKPOINT_LOCATION = "/data/checkpoints"

# PostgreSQL Configuration
POSTGRES_HOST = "postgres"
POSTGRES_PORT = 5432
POSTGRES_DB = "globalmart"
POSTGRES_USER = "globalmart"
POSTGRES_PASSWORD = "globalmart123"
POSTGRES_URL = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
POSTGRES_PROPERTIES = {
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "driver": "org.postgresql.Driver"
}

# Processing Windows
WINDOW_DURATION = "1 minute"
SLIDING_DURATION = "30 seconds"

# Anomaly Detection Thresholds
ANOMALY_THRESHOLDS = {
    'high_value_transaction': 5000.00,
    'unusual_quantity': 10,
    'rapid_transactions': 5  # transactions per minute
}

# Inventory Alerts
LOW_STOCK_THRESHOLD = 10
CRITICAL_STOCK_THRESHOLD = 5

# Session Configuration
SESSION_TIMEOUT_MINUTES = 30
CART_ABANDONMENT_THRESHOLD_MINUTES = 15
```

Create `stream-processor/transaction_monitor.py`:

```python
"""
Real-time transaction monitoring with anomaly detection
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import config

def create_spark_session():
    """Create Spark session with Kafka integration"""
    spark = SparkSession.builder \
        .appName("Transaction Monitor") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.postgresql:postgresql:42.6.0") \
        .config("spark.sql.streaming.checkpointLocation",
                f"{config.CHECKPOINT_LOCATION}/transactions") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark

def detect_anomalies(df):
    """Detect anomalies in transactions"""

    # High value transactions
    high_value = df.filter(col("total_amount") > config.ANOMALY_THRESHOLDS['high_value_transaction']) \
        .withColumn("anomaly_type", lit("high_value")) \
        .withColumn("anomaly_score", col("total_amount") / config.ANOMALY_THRESHOLDS['high_value_transaction']) \
        .withColumn("description", concat(lit("High value transaction: $"), col("total_amount")))

    # Unusual quantity per product
    unusual_quantity = df \
        .select(
            col("transaction_id"),
            col("user_id"),
            col("timestamp"),
            col("total_amount"),
            explode(col("products")).alias("product")
        ) \
        .filter(col("product.quantity") > config.ANOMALY_THRESHOLDS['unusual_quantity']) \
        .withColumn("anomaly_type", lit("unusual_quantity")) \
        .withColumn("anomaly_score", col("product.quantity") / config.ANOMALY_THRESHOLDS['unusual_quantity']) \
        .withColumn("description",
                   concat(lit("Unusual quantity: "), col("product.quantity"), lit(" items"))) \
        .select("transaction_id", "user_id", "timestamp", "total_amount",
               "anomaly_type", "anomaly_score", "description")

    # Combine anomalies
    anomalies = high_value.unionAll(unusual_quantity)

    return anomalies

def write_to_postgres(batch_df, batch_id):
    """Write batch to PostgreSQL"""
    batch_df.write \
        .jdbc(
            url=config.POSTGRES_URL,
            table="transaction_anomalies",
            mode="append",
            properties=config.POSTGRES_PROPERTIES
        )

def process_transactions():
    """Main transaction processing function"""
    spark = create_spark_session()

    # Define transaction schema
    transaction_schema = StructType([
        StructField("transaction_id", StringType()),
        StructField("user_id", StringType()),
        StructField("timestamp", StringType()),
        StructField("products", ArrayType(StructType([
            StructField("product_id", StringType()),
            StructField("quantity", IntegerType()),
            StructField("price", DoubleType())
        ]))),
        StructField("total_amount", DoubleType()),
        StructField("payment_method", StringType()),
        StructField("country", StringType())
    ])

    # Read from Kafka
    transactions = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", config.KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", config.KAFKA_TOPICS['transactions']) \
        .option("startingOffsets", "latest") \
        .load()

    # Parse JSON
    transactions_df = transactions \
        .select(from_json(col("value").cast("string"), transaction_schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", to_timestamp(col("timestamp")))

    # Detect anomalies
    anomalies = detect_anomalies(transactions_df)

    # Write anomalies to PostgreSQL
    anomaly_query = anomalies \
        .writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("append") \
        .start()

    # Calculate real-time metrics (1-minute windows)
    metrics = transactions_df \
        .withWatermark("timestamp", "1 minute") \
        .groupBy(
            window(col("timestamp"), config.WINDOW_DURATION, config.SLIDING_DURATION),
            col("country")
        ) \
        .agg(
            count("*").alias("transaction_count"),
            sum("total_amount").alias("total_amount"),
            avg("total_amount").alias("avg_transaction_value")
        ) \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            lit(None).alias("category"),
            col("country"),
            col("total_amount"),
            col("transaction_count"),
            col("avg_transaction_value")
        )

    # Write metrics to PostgreSQL
    def write_metrics(batch_df, batch_id):
        batch_df.write \
            .jdbc(
                url=config.POSTGRES_URL,
                table="sales_metrics",
                mode="append",
                properties=config.POSTGRES_PROPERTIES
            )

    metrics_query = metrics \
        .writeStream \
        .foreachBatch(write_metrics) \
        .outputMode("append") \
        .start()

    # Console output for debugging
    console_query = transactions_df \
        .writeStream \
        .format("console") \
        .outputMode("append") \
        .option("truncate", False) \
        .start()

    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    process_transactions()
```

Create `stream-processor/inventory_tracker.py`:

```python
"""
Real-time inventory tracking and low-stock alerts
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import config

def create_spark_session():
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName("Inventory Tracker") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.postgresql:postgresql:42.6.0") \
        .config("spark.sql.streaming.checkpointLocation",
                f"{config.CHECKPOINT_LOCATION}/inventory") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark

def track_inventory(spark):
    """Track inventory changes from transactions"""

    # Transaction schema
    transaction_schema = StructType([
        StructField("transaction_id", StringType()),
        StructField("user_id", StringType()),
        StructField("timestamp", StringType()),
        StructField("products", ArrayType(StructType([
            StructField("product_id", StringType()),
            StructField("quantity", IntegerType()),
            StructField("price", DoubleType())
        ]))),
        StructField("total_amount", DoubleType()),
        StructField("payment_method", StringType()),
        StructField("country", StringType())
    ])

    # Read transactions from Kafka
    transactions = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", config.KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", config.KAFKA_TOPICS['transactions']) \
        .option("startingOffsets", "latest") \
        .load()

    # Parse and explode products
    inventory_updates = transactions \
        .select(from_json(col("value").cast("string"), transaction_schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", to_timestamp(col("timestamp"))) \
        .select(
            col("transaction_id"),
            col("timestamp"),
            explode(col("products")).alias("product")
        ) \
        .select(
            col("transaction_id"),
            col("timestamp"),
            col("product.product_id"),
            col("product.quantity")
        )

    # Aggregate inventory changes
    inventory_summary = inventory_updates \
        .withWatermark("timestamp", "1 minute") \
        .groupBy(
            window(col("timestamp"), "1 minute"),
            col("product_id")
        ) \
        .agg(
            sum("quantity").alias("sold_quantity")
        )

    # Detect low stock
    def check_low_stock(batch_df, batch_id):
        """Check for low stock and write alerts"""
        # This is simplified - in production, you'd join with actual inventory data
        low_stock = batch_df.filter(col("sold_quantity") > 50)  # Example threshold

        if not low_stock.isEmpty():
            # Write to low_stock_alerts table
            low_stock.select(
                col("product_id"),
                lit("Product Name").alias("product_name"),  # Would join with product catalog
                lit("Category").alias("category"),
                (lit(100) - col("sold_quantity")).alias("current_stock"),
                lit(config.LOW_STOCK_THRESHOLD).alias("threshold")
            ).write \
                .jdbc(
                    url=config.POSTGRES_URL,
                    table="low_stock_alerts",
                    mode="append",
                    properties=config.POSTGRES_PROPERTIES
                )

    # Write stream
    query = inventory_summary \
        .writeStream \
        .foreachBatch(check_low_stock) \
        .outputMode("append") \
        .start()

    # Console output
    console_query = inventory_updates \
        .writeStream \
        .format("console") \
        .outputMode("append") \
        .option("truncate", False) \
        .start()

    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    spark = create_spark_session()
    track_inventory(spark)
```

Create `stream-processor/session_analyzer.py`:

```python
"""
Session analysis and cart abandonment detection
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import config

def create_spark_session():
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName("Session Analyzer") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.postgresql:postgresql:42.6.0") \
        .config("spark.sql.streaming.checkpointLocation",
                f"{config.CHECKPOINT_LOCATION}/sessions") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark

def analyze_sessions(spark):
    """Analyze user sessions and detect cart abandonment"""

    # Cart event schema
    cart_schema = StructType([
        StructField("event_id", StringType()),
        StructField("user_id", StringType()),
        StructField("product_id", StringType()),
        StructField("timestamp", StringType()),
        StructField("action", StringType()),
        StructField("quantity", IntegerType()),
        StructField("session_id", StringType())
    ])

    # Read cart events
    cart_events = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", config.KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", config.KAFKA_TOPICS['cart_events']) \
        .option("startingOffsets", "latest") \
        .load()

    # Parse cart events
    cart_df = cart_events \
        .select(from_json(col("value").cast("string"), cart_schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", to_timestamp(col("timestamp")))

    # Aggregate session metrics
    session_metrics = cart_df \
        .withWatermark("timestamp", "30 minutes") \
        .groupBy(
            col("session_id"),
            col("user_id"),
            window(col("timestamp"), f"{config.SESSION_TIMEOUT_MINUTES} minutes")
        ) \
        .agg(
            min("timestamp").alias("start_time"),
            max("timestamp").alias("end_time"),
            count("*").alias("total_events"),
            sum(when(col("action") == "add", 1).otherwise(0)).alias("cart_adds"),
            sum(when(col("action") == "remove", 1).otherwise(0)).alias("cart_removes"),
            countDistinct("product_id").alias("unique_products")
        ) \
        .select(
            col("session_id"),
            col("user_id"),
            col("start_time"),
            col("end_time"),
            ((unix_timestamp("end_time") - unix_timestamp("start_time"))).alias("duration_seconds"),
            col("total_events").alias("page_views"),
            col("cart_adds"),
            col("cart_removes")
        )

    # Detect potential cart abandonment
    abandonment = session_metrics \
        .filter(
            (col("cart_adds") > 0) &
            (col("duration_seconds") > config.CART_ABANDONMENT_THRESHOLD_MINUTES * 60)
        ) \
        .select(
            col("session_id"),
            col("user_id"),
            col("cart_adds").alias("products_in_cart"),
            lit(0).alias("cart_value"),  # Would need product prices
            col("end_time").alias("abandonment_time"),
            (col("duration_seconds") / 60).alias("time_in_cart_minutes")
        )

    # Write session metrics
    def write_sessions(batch_df, batch_id):
        batch_df.write \
            .jdbc(
                url=config.POSTGRES_URL,
                table="session_metrics",
                mode="append",
                properties=config.POSTGRES_PROPERTIES
            )

    session_query = session_metrics \
        .writeStream \
        .foreachBatch(write_sessions) \
        .outputMode("append") \
        .start()

    # Write abandonment events
    def write_abandonment(batch_df, batch_id):
        batch_df.write \
            .jdbc(
                url=config.POSTGRES_URL,
                table="cart_abandonment",
                mode="append",
                properties=config.POSTGRES_PROPERTIES
            )

    abandonment_query = abandonment \
        .writeStream \
        .foreachBatch(write_abandonment) \
        .outputMode("append") \
        .start()

    # Console output
    console_query = session_metrics \
        .writeStream \
        .format("console") \
        .outputMode("append") \
        .option("truncate", False) \
        .start()

    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    spark = create_spark_session()
    analyze_sessions(spark)
```

### 2.5 Running Stream Processing Jobs

Create `stream-processor/run_all.sh`:

```bash
#!/bin/bash

# Run all stream processing jobs

SPARK_MASTER="spark://spark-master:7077"

echo "Starting stream processing jobs..."

# Run transaction monitor
docker exec globalmart-spark-master spark-submit \
    --master $SPARK_MASTER \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    /app/transaction_monitor.py &

echo "Started transaction monitor"

# Run inventory tracker
docker exec globalmart-spark-master spark-submit \
    --master $SPARK_MASTER \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    /app/inventory_tracker.py &

echo "Started inventory tracker"

# Run session analyzer
docker exec globalmart-spark-master spark-submit \
    --master $SPARK_MASTER \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    /app/session_analyzer.py &

echo "Started session analyzer"

echo "All stream processing jobs started!"
echo "Monitor at http://localhost:8081"
```

### 2.6 Deliverables Checklist

- [ ] Spark Streaming cluster running
- [ ] Real-time transaction monitoring with anomaly detection
- [ ] Inventory tracking with low-stock alerts
- [ ] Session analysis and cart abandonment detection
- [ ] Sales metrics aggregation (hourly, by category, by region)
- [ ] Alert notification system (stored in PostgreSQL)
- [ ] Real-time metrics dashboard (Spark UI at localhost:8081)

**Testing Commands:**
```bash
# Start all services
docker-compose -f docker/docker-compose.kafka.yml up -d
docker-compose -f docker/docker-compose.spark.yml up -d
docker-compose -f docker/docker-compose.postgres.yml up -d

# Run stream processors
chmod +x stream-processor/run_all.sh
./stream-processor/run_all.sh

# Monitor Spark jobs
open http://localhost:8081

# Query metrics
docker exec -it globalmart-postgres psql -U globalmart -d globalmart -c "SELECT * FROM sales_metrics ORDER BY window_start DESC LIMIT 10;"
```

---

*This is Part 1 of the guide. Continue to the next sections for:*
- Component 3: Batch Processing and Data Warehouse
- Component 4: Visualization and API Layer
- Component 5: Infrastructure and Deployment
- Testing & Validation
- Troubleshooting

Would you like me to continue with the remaining components?
