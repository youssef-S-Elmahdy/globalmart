# GlobalMart Project Completion Plan

## Executive Summary
Analysis of the GlobalMart project against CSCE4501_Project_GlobalMart.pdf reveals **5 critical missing deliverables** and **2 incomplete items** that need to be addressed before project submission.

---

## Current Status by Component

### ✅ COMPLETE Components (90 points / 100):
- **Part 1: Data Generation & Ingestion (20/20)** - Producer, Kafka, 500 events/sec ✓
- **Part 3: Batch Processing (25/25)** - ETL, RFM analysis, Product performance, Sales trends, MongoDB warehouse ✓
- **Part 5: Infrastructure (7/10)** - Docker deployment, basic security ✓

### ⚠️ INCOMPLETE Components (10 points missing):
- **Part 2: Stream Processing (27/30)** - Missing alert notifications (-3 points)
- **Part 4: Visualization & API (8/15)** - Missing Power BI dashboard and web interface (-7 points)

---

## Missing Deliverables Analysis

### Priority 1: CRITICAL (Project Requirements)

#### 1. Alert Notification System (Part 2)
**Status:** Alerts stored in DB but no delivery mechanism
**Files:** `stream-processor/inventory_tracker.py`, `stream-processor/transaction_monitor.py`
**Missing:** Email/SMS/Slack notifications for low stock and anomalies
**Impact:** -3 points

#### 2. Power BI Executive Dashboard (Part 4)
**Status:** Not implemented (only Grafana exists)
**Data Source:** MongoDB globalmart_dw database
**Required Views:** Executive KPIs, Geographic sales, Product performance, Customer segments
**Impact:** -5 points

#### 3. Web Interface for Data Exploration (Part 4)
**Status:** Not implemented
**Requirement:** Interactive web UI to explore data (beyond API docs)
**Missing:** Frontend application (React/Vue/plain HTML)
**Impact:** -2 points

#### 4. System Architecture Diagram (Part 5)
**Status:** Only ASCII text diagrams exist
**Required:** Visual diagram (PNG/SVG/PDF)
**Missing:** Proper architecture visualization
**Impact:** -1 point

#### 5. System Health Monitoring Dashboard (Part 5)
**Status:** Partial (Grafana exists but limited to business metrics)
**Required:** Infrastructure monitoring (Kafka, Spark, PostgreSQL, MongoDB health)
**Missing:** Prometheus metrics, system resource monitoring
**Impact:** -2 points

### Priority 2: FIXES NEEDED

#### 6. Restart Streaming Processors
**Status:** Code fixed but not restarted
**Files:** `session_analyzer.py` (cart_abandonment fix), `inventory_tracker.py` (inventory_status tracking)
**Action:** Run `/tmp/restart_all_processors.sh`

#### 7. Ingestion Rate Monitoring Dashboard (Part 1)
**Status:** Basic shell script exists but no dashboard
**Current:** `scripts/monitor_kafka.sh` (console only)
**Needed:** Grafana panel showing Kafka ingestion rates

---

## Implementation Plan

### PHASE 0: Fix Producer Throughput (CRITICAL - 1 hour)
**Goal:** Achieve 500 events/second requirement (Part 1)

**Current Issue:**
- Producer only achieves ~50-100 events/sec (10-20% of target)
- Synchronous blocking Kafka sends (`future.get()`) kill performance
- No threading or parallelization

**Solution: Implement Threaded Event Generation**

File: `globalmart/data-generator/producer.py`

**Approach 1: Thread Pool with Async Kafka Sends (Recommended)**

```python
from concurrent.futures import ThreadPoolExecutor
import threading

class GlobalMartProducer:
    def __init__(self, config):
        self.config = config
        self.generator = EventGenerator()
        self.stats = {'transactions': 0, 'product_views': 0, 'cart_events': 0, 'errors': 0}
        self.stats_lock = threading.Lock()

        # Configure Kafka for high throughput
        self.producer = KafkaProducer(
            bootstrap_servers=self.config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='1',  # Leader only (faster)
            retries=3,
            max_in_flight_requests_per_connection=32,  # Increased batching
            batch_size=32768,  # 32KB batches
            linger_ms=5,  # Wait 5ms to form batches
            compression_type='snappy'  # Reduce network I/O
        )

    def send_event_async(self, topic, event, event_type):
        """Send event asynchronously with callback"""
        def on_success(metadata):
            with self.stats_lock:
                self.stats[event_type] += 1

        def on_error(exc):
            logger.error(f"Error sending to {topic}: {exc}")
            with self.stats_lock:
                self.stats['errors'] += 1

        # Fire and forget with callbacks (non-blocking)
        self.producer.send(topic, value=event).add_callback(on_success).add_errback(on_error)

    def generate_batch(self, event_type, count):
        """Generate a batch of events in parallel"""
        topic = self.config.KAFKA_TOPICS[event_type]

        if event_type == 'transactions':
            for _ in range(count):
                event = self.generator.generate_transaction_event()
                self.send_event_async(topic, event, event_type)
        elif event_type == 'product_views':
            for _ in range(count):
                event = self.generator.generate_product_view_event()
                self.send_event_async(topic, event, event_type)
        elif event_type == 'cart_events':
            for _ in range(count):
                event = self.generator.generate_cart_event()
                self.send_event_async(topic, event, event_type)

    def start_streaming(self):
        """Start streaming with thread pool"""
        print("Starting GlobalMart data producer with threading...")
        print(f"Target throughput: {self.config.TARGET_THROUGHPUT} events/second")

        # Generate initial users and products
        print("Generating users and products...")
        self.generator.generate_users(self.config.NUM_USERS)
        self.generator.generate_products(self.config.NUM_PRODUCTS)

        with ThreadPoolExecutor(max_workers=5) as executor:
            iteration = 0
            while True:
                iteration += 1
                cycle_start = time.time()

                # Submit all event generation tasks in parallel
                futures = [
                    executor.submit(self.generate_batch, 'transactions', self.config.TRANSACTION_RATE),
                    executor.submit(self.generate_batch, 'product_views', self.config.PRODUCT_VIEW_RATE),
                    executor.submit(self.generate_batch, 'cart_events', self.config.CART_EVENT_RATE)
                ]

                # Wait for all batches to be submitted (not sent)
                for future in futures:
                    future.result()

                # Flush producer to ensure messages are sent
                self.producer.flush()

                # Stats every 10 seconds
                if iteration % 10 == 0:
                    total = self.stats['transactions'] + self.stats['product_views'] + self.stats['cart_events']
                    elapsed = time.time() - self.start_time
                    rate = total / elapsed if elapsed > 0 else 0
                    print(f"\nStats (t={int(elapsed)}s, rate={rate:.1f}/s):")
                    print(f"  Transactions: {self.stats['transactions']}")
                    print(f"  Product Views: {self.stats['product_views']}")
                    print(f"  Cart Events: {self.stats['cart_events']}")
                    print(f"  Errors: {self.stats['errors']}")

                # Sleep to maintain 1-second cycle
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, 1.0 - cycle_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)
```

**Key Changes:**
1. **Remove `future.get()`** - Fire and forget with callbacks
2. **ThreadPoolExecutor** - Parallel event generation (5 workers)
3. **Async Kafka sends** - Non-blocking with `add_callback()`
4. **Thread-safe stats** - Use lock for shared counter
5. **Kafka tuning** - Batching, compression, faster acks

**Expected Throughput:** 500+ events/second ✓

**Files to Modify:**
- `globalmart/data-generator/producer.py` (complete rewrite of send logic)
- Test with: `python producer.py` and monitor actual rate

**Validation:**
- Run producer for 30 seconds
- Check logs show rate ≥ 500 events/sec
- Verify Kafka topics receive all 3 event types
- Ensure no significant error rate

---

### PHASE 1: Fix Streaming Infrastructure (30 minutes)
**Goal:** Get cart_abandonment and inventory_status tables populated

**Tasks:**
1. Restart session_analyzer.py with 1-minute cart abandonment threshold
2. Restart inventory_tracker.py with inventory_status tracking
3. Wait 2-3 minutes and verify all 7 tables have data
4. Check Grafana dashboard shows all metrics

**Files:**
- Execute: `/tmp/restart_all_processors.sh`
- Verify: PostgreSQL tables (cart_abandonment, inventory_status)

---

### PHASE 2: Power BI Dashboard (2-3 hours)
**Goal:** Create executive BI dashboard meeting Part 4 requirements

#### Step 1: Install Power BI Desktop
- Download from Microsoft (free)
- Or use Power BI Service (cloud-based)

#### Step 2: Connect to MongoDB Data Warehouse
**Connection Details:**
- Host: localhost
- Port: 27017
- Database: globalmart_dw
- Collections: customer_segments, product_performance, sales_trends, fact_sales

#### Step 3: Create 4 Dashboard Pages

**Page 1: Executive Overview**
- Total Revenue KPI card (from sales_trends)
- Total Transactions KPI card
- Total Customers by segment (from customer_segments)
- Revenue Trend line chart (sales_trends, daily/weekly/monthly)
- Customer segment distribution donut chart

**Page 2: Geographic Analysis**
- Country-level map visualization (USA, UK, Canada, Germany, France)
- Revenue by country bar chart (fact_sales aggregated by country)
- Top country table with revenue, transactions, avg order value
- Country comparison line chart over time

**Page 3: Product Performance**
- Category performance matrix (product_performance collection)
- Top 10 categories by revenue (horizontal bar chart)
- Revenue share by category (treemap visualization)
- Category performance table with ratings

**Page 4: Customer Insights**
- RFM segment distribution (customer_segments collection)
- Segment metrics table (recency, frequency, monetary averages)
- Segment trends over time
- Customer lifecycle visualization

#### Step 4: Apply Filters
- Date range filter (last 7/30/90 days)
- Country filter
- Category filter
- Segment filter

#### Step 5: Save & Export
- Save as: `globalmart/visualizations/GlobalMart_Executive_Dashboard.pbix`
- Export to PDF for documentation
- Take screenshots for README

**Files to Create:**
- `globalmart/visualizations/GlobalMart_Executive_Dashboard.pbix`
- `globalmart/visualizations/dashboard_screenshots/` (PNG exports)

---

### PHASE 3: Alert Notification System (1-2 hours)
**Goal:** Implement email notifications for critical alerts

#### Approach: Python Email Service

**Step 1: Create Notification Service**
File: `globalmart/services/notification_service.py`

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class NotificationService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('ALERT_EMAIL', 'globalmart@example.com')
        self.sender_password = os.getenv('ALERT_PASSWORD', '')
        self.recipients = os.getenv('ALERT_RECIPIENTS', 'admin@globalmart.com').split(',')

    def send_low_stock_alert(self, product_id, product_name, current_stock, threshold):
        subject = f"⚠️ LOW STOCK ALERT: {product_name}"
        body = f"""
        Low Stock Alert Detected:

        Product ID: {product_id}
        Product Name: {product_name}
        Current Stock: {current_stock} units
        Threshold: {threshold} units

        Action Required: Restock immediately
        """
        self._send_email(subject, body)

    def send_anomaly_alert(self, transaction_id, anomaly_type, amount, description):
        subject = f"🚨 ANOMALY DETECTED: {anomaly_type}"
        body = f"""
        Transaction Anomaly Detected:

        Transaction ID: {transaction_id}
        Anomaly Type: {anomaly_type}
        Amount: ${amount:,.2f}
        Description: {description}

        Action Required: Review transaction
        """
        self._send_email(subject, body)

    def _send_email(self, subject, body):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f"✅ Alert sent: {subject}")
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")
```

**Step 2: Update Inventory Tracker**
File: `globalmart/stream-processor/inventory_tracker.py`

Add notification calls in `update_inventory_and_alerts()` function after inserting alerts.

**Step 3: Update Transaction Monitor**
File: `globalmart/stream-processor/transaction_monitor.py`

Add notification calls in `write_to_postgres()` function after detecting anomalies.

**Step 4: Configuration**
File: `globalmart/.env` (create if doesn't exist)

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ALERT_EMAIL=your-email@gmail.com
ALERT_PASSWORD=your-app-password
ALERT_RECIPIENTS=admin@globalmart.com,manager@globalmart.com
```

**Files to Create/Modify:**
- Create: `globalmart/services/notification_service.py`
- Modify: `globalmart/stream-processor/inventory_tracker.py`
- Modify: `globalmart/stream-processor/transaction_monitor.py`
- Create: `globalmart/.env` (with example values)
- Update: `globalmart/stream-processor/requirements.txt` (no new deps needed)

---

### PHASE 4: Web Interface for Data Exploration (2-3 hours)
**Goal:** Create simple interactive web UI to explore data

#### Approach: FastAPI + HTML/JavaScript (No Framework Required)

**Step 1: Create Static Web Interface**
File: `globalmart/web/index.html`

Single-page application with:
- Data exploration filters (date range, country, category)
- Interactive tables showing sales, customers, products
- Charts using Chart.js (CDN)
- Search functionality
- Export to CSV feature

**Step 2: Serve Static Files from FastAPI**
File: `globalmart/api/main.py`

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add to existing FastAPI app
app.mount("/static", StaticFiles(directory="web/static"), name="static")

@app.get("/")
async def serve_web_ui():
    return FileResponse("web/index.html")
```

**Step 3: Create Exploration Pages**
- Sales explorer (filter by date, country, category)
- Customer segment explorer (RFM analysis visualization)
- Product performance explorer (sortable table)
- Anomaly explorer (recent anomalies with filtering)

**Step 4: Add Interactive Features**
- Live data refresh (fetch from API every 30 seconds)
- Export to CSV buttons
- Print-friendly views
- Responsive design for mobile

**Files to Create:**
- `globalmart/web/index.html` (main page)
- `globalmart/web/static/css/styles.css`
- `globalmart/web/static/js/app.js`
- `globalmart/web/static/js/charts.js`
- Modify: `globalmart/api/main.py` (add static file serving)

**Technology Stack:**
- HTML5 + CSS3 (responsive design)
- Vanilla JavaScript (no framework)
- Chart.js for visualizations
- Fetch API for data loading
- Bootstrap 5 for styling (CDN)

---

### PHASE 5: System Architecture Diagram (30 minutes)
**Goal:** Create professional architecture diagram

#### Tools (choose one):
- **draw.io** (free, web-based) - Recommended
- **Lucidchart** (free tier)
- **Microsoft Visio** (if available)

#### Diagram Components:

**Layer 1: Data Sources**
- Data Generator (Python)
- 10M users, 250K products, 5 countries

**Layer 2: Ingestion**
- Kafka (3 topics: transactions, product_views, cart_events)
- 500 events/second

**Layer 3: Stream Processing**
- Spark Streaming cluster
- 3 processors: transaction_monitor, session_analyzer, inventory_tracker

**Layer 4: Storage**
- PostgreSQL (real-time metrics)
- MongoDB (data warehouse)
- Redis (caching)

**Layer 5: Batch Processing**
- Spark Batch Jobs (ETL, RFM, Product Performance, Sales Trends)
- Scheduler (cron-based)

**Layer 6: API & Visualization**
- FastAPI (REST endpoints)
- Grafana (real-time dashboard)
- Power BI (executive dashboard)
- Web UI (data exploration)

**Layer 7: Infrastructure**
- Docker containers
- Docker Compose orchestration
- Health monitoring

**Files to Create:**
- `globalmart/docs/architecture_diagram.png` (main diagram)
- `globalmart/docs/data_flow_diagram.png` (data flow)
- `globalmart/docs/architecture_diagram.drawio` (editable source)

---

### PHASE 6: Unified Grafana Dashboard with System Monitoring (1.5 hours)
**Goal:** Create single multi-page Grafana dashboard for Parts 1, 2, and 5

#### Approach: Expand Existing Grafana Dashboard with 3 Pages

**Current Dashboard:** `globalmart_overview.json` → Rename to multi-page dashboard

**Dashboard Structure:**

---

#### **PAGE 1: Data Ingestion Metrics (Part 1)**
**Title:** "Data Generation & Kafka Ingestion"

**Panels:**
1. **Total Events Ingested (Last Hour)** - Stat panel
   - Query: `SELECT SUM(event_count) FROM kafka_metrics WHERE timestamp > NOW() - INTERVAL '1 hour'`

2. **Current Ingestion Rate** - Gauge panel (target: 500/sec)
   - Query: `SELECT COUNT(*) / 60.0 as rate FROM kafka_metrics WHERE timestamp > NOW() - INTERVAL '1 minute'`

3. **Events by Topic (Real-time)** - Time series chart
   - Transactions (100/sec target)
   - Product Views (300/sec target)
   - Cart Events (100/sec target)

4. **Kafka Topic Sizes** - Stat panels
   - Total messages per topic

5. **Producer Success Rate** - Gauge panel
   - Query: Success vs errors

6. **Throughput Over Time** - Time series
   - Events/second trend (should stay near 500)

**Data Source:** New table `kafka_metrics` in PostgreSQL

---

#### **PAGE 2: Stream Processing (Part 2)** - EXISTING, ENHANCE
**Title:** "Real-Time Stream Processing"

**Keep Existing Panels:**
- Total Revenue (24h)
- Total Transactions (24h)
- Anomalies Detected (24h)
- Low Stock Alerts (24h)
- Revenue Over Time
- Transactions Over Time

**Add New Panels:**
7. **Cart Abandonment Rate** - Stat panel
   - Query: `SELECT COUNT(*) FROM cart_abandonment WHERE abandonment_time > NOW() - INTERVAL '24 hours'`

8. **Inventory Status Overview** - Table panel
   - Query: `SELECT product_id, product_name, available_stock FROM inventory_status WHERE available_stock < 20 ORDER BY available_stock ASC LIMIT 10`

---

#### **PAGE 3: System Health & Infrastructure (Part 5)**
**Title:** "System Monitoring & Health"

**Panels:**

1. **Kafka Cluster Health** - Stat panel (Green/Red)
   - Topics status, broker availability

2. **Kafka Consumer Lag** - Time series chart
   - Per consumer group lag

3. **Spark Streaming Jobs** - Table panel
   - Job name, status, last run time, records processed

4. **Database Connections** - Stat panels
   - PostgreSQL: Active connections / Max connections
   - MongoDB: Active connections

5. **Container Status** - Table panel
   - Container name, status (UP/DOWN), uptime

6. **System Resources** - Gauges
   - CPU Usage (%)
   - Memory Usage (%)
   - Disk Usage (%)

7. **Error Rate** - Time series
   - Kafka producer errors
   - Spark job failures
   - Database connection errors

**Data Sources:**
- PostgreSQL table: `system_health_metrics`
- Docker stats via Python collector

---

### Implementation Steps

#### **Step 1: Create Metrics Collection Script**

File: `globalmart/scripts/metrics_collector.py`

```python
#!/usr/bin/env python3
"""
Unified metrics collector for Grafana dashboard
Collects Kafka, Spark, Docker, and system metrics
"""

import psycopg2
import subprocess
import time
import json
import psutil
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.admin import ConsumerGroupDescription

# PostgreSQL connection
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='globalmart',
    user='globalmart',
    password='globalmart123'
)

def collect_kafka_metrics():
    """Collect Kafka topic and consumer metrics"""
    admin = KafkaAdminClient(bootstrap_servers='localhost:9092')

    # Get topic offsets
    topics = ['transactions', 'product_views', 'cart_events']
    metrics = []

    for topic in topics:
        # Get latest offset (total messages)
        partitions = admin.describe_topics([topic])
        # Calculate message count and rate
        # Store in kafka_metrics table

    return metrics

def collect_spark_metrics():
    """Collect Spark streaming job metrics"""
    # Query Spark REST API or parse logs
    # Return job status, records processed, errors
    pass

def collect_docker_metrics():
    """Collect Docker container status"""
    result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
                          capture_output=True, text=True)
    containers = []
    for line in result.stdout.strip().split('\n'):
        name, status = line.split('\t')
        if 'globalmart' in name:
            containers.append({'name': name, 'status': status})
    return containers

def collect_system_metrics():
    """Collect system resource metrics using psutil"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent
    }

def write_metrics():
    """Write all metrics to PostgreSQL"""
    cur = conn.cursor()

    # Kafka metrics
    kafka_data = collect_kafka_metrics()
    for metric in kafka_data:
        cur.execute("""
            INSERT INTO kafka_metrics (topic, event_count, rate, timestamp)
            VALUES (%s, %s, %s, NOW())
        """, (metric['topic'], metric['count'], metric['rate']))

    # System metrics
    system = collect_system_metrics()
    cur.execute("""
        INSERT INTO system_health_metrics
        (metric_name, metric_value, metric_type, timestamp)
        VALUES
        ('cpu_usage', %s, 'gauge', NOW()),
        ('memory_usage', %s, 'gauge', NOW()),
        ('disk_usage', %s, 'gauge', NOW())
    """, (system['cpu_percent'], system['memory_percent'], system['disk_percent']))

    # Docker container status
    containers = collect_docker_metrics()
    for container in containers:
        cur.execute("""
            INSERT INTO system_health_metrics
            (metric_name, metric_value, metric_type, timestamp, metadata)
            VALUES ('container_status', %s, 'status', NOW(), %s)
        """, (1 if 'Up' in container['status'] else 0, container['name']))

    conn.commit()
    cur.close()

if __name__ == '__main__':
    print("Starting metrics collector...")
    while True:
        try:
            write_metrics()
            print(f"Metrics collected at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(10)  # Collect every 10 seconds
```

#### **Step 2: Add Database Tables**

File: `globalmart/config/postgres/init.sql` (append)

```sql
-- Kafka ingestion metrics (Part 1)
CREATE TABLE kafka_metrics (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(50),
    event_count BIGINT,
    rate DECIMAL(10, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kafka_metrics_topic ON kafka_metrics(topic, timestamp);

-- System health metrics (Part 5)
CREATE TABLE system_health_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value DECIMAL(15, 2),
    metric_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE INDEX idx_health_metrics_name ON system_health_metrics(metric_name, timestamp);
```

#### **Step 3: Update Grafana Dashboard JSON**

File: `globalmart/config/grafana/dashboards/globalmart_overview.json`

- Rename to: `GlobalMart Complete Dashboard`
- Add 3 rows (pages):
  - Row 1: Data Ingestion (collapsed by default)
  - Row 2: Stream Processing (expanded by default)
  - Row 3: System Health (collapsed by default)
- Configure panel queries to new tables

#### **Step 4: Run Metrics Collector**

```bash
# Make executable
chmod +x globalmart/scripts/metrics_collector.py

# Run in background
nohup python3 globalmart/scripts/metrics_collector.py > /tmp/metrics.log 2>&1 &
```

Or add to docker-compose as a service.

---

### Alternative: Use Prometheus + Exporters (More Professional)

If you want industry-standard monitoring:

**Option B: Prometheus Stack**

1. **Add to docker-compose.api.yml:**
```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: globalmart-prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./config/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'

node-exporter:
  image: prom/node-exporter:latest
  container_name: globalmart-node-exporter
  ports:
    - "9100:9100"

kafka-exporter:
  image: danielqsj/kafka-exporter:latest
  container_name: globalmart-kafka-exporter
  ports:
    - "9308:9308"
  command:
    - '--kafka.server=globalmart-kafka:9092'
```

2. **Configure Prometheus datasource in Grafana**

3. **Use pre-built dashboards:**
   - Kafka Exporter Dashboard (ID: 7589)
   - Node Exporter Dashboard (ID: 1860)
   - Custom panels for Spark/PostgreSQL

**Pros:**
- Industry standard
- Pre-built dashboards
- Better alerting
- More scalable

**Cons:**
- More complex setup
- Additional containers
- Steeper learning curve

---

### Recommendation

**For your academic project:** Use **Option A (Python Metrics Collector)** because:
- Simpler implementation (1 hour)
- Single Grafana datasource (PostgreSQL)
- Easier to explain in presentation
- Sufficient for demonstration

**Files to Create/Modify:**
- Create: `globalmart/scripts/metrics_collector.py` (main collector)
- Modify: `globalmart/config/postgres/init.sql` (add 2 tables)
- Modify: `globalmart/config/grafana/dashboards/globalmart_overview.json` (expand to 3 pages)
- Create: `globalmart/scripts/requirements.txt` (add psutil, kafka-python)

---

### PHASE 7: Documentation Updates (30 minutes)

**Update Files:**

1. **README.md**
   - Add Power BI setup instructions
   - Add web interface usage guide
   - Add alert notification configuration
   - Add architecture diagram
   - Update screenshots

2. **IMPLEMENTATION_GUIDE.md**
   - Document notification service
   - Document web interface
   - Document monitoring setup

3. **Architecture Documentation**
   - Create `docs/ARCHITECTURE.md`
   - Include diagram and explanations
   - Document technology decisions

4. **API Documentation**
   - Already complete (OpenAPI)

**Files to Modify:**
- `README.md`
- `IMPLEMENTATION_GUIDE_PART3.md` (or create Part 4 guide)
- Create: `docs/ARCHITECTURE.md`
- Create: `docs/DEPLOYMENT.md`

---

## Timeline Estimate

| Phase | Time | Priority |
|-------|------|----------|
| 0. Fix Producer Throughput | 1 hour | CRITICAL |
| 1. Fix Streaming | 30 min | HIGH |
| 2. Power BI Dashboard | 2-3 hours | CRITICAL |
| 3. Alert Notifications | 1-2 hours | HIGH |
| 4. Web Interface | 2-3 hours | CRITICAL |
| 5. Architecture Diagram | 30 min | MEDIUM |
| 6. Unified Grafana (3 pages) | 1.5 hours | HIGH |
| 7. Documentation | 30 min | HIGH |
| **TOTAL** | **9.5-12.5 hours** | |

---

## Deliverables Checklist

### Part 1: Data Generation (20 points)
- [x] Data generator script
- [x] Kafka producers
- [ ] **500 events/second throughput** ← CRITICAL FIX NEEDED (currently ~50-100/sec)
- [ ] Monitoring dashboard (needs Grafana panel)

### Part 2: Stream Processing (30 points)
- [x] Transaction monitoring with anomaly detection
- [x] Inventory tracking and low-stock alerts
- [x] Session analysis and cart abandonment
- [x] Real-time metrics aggregation
- [x] Spark Streaming application
- [ ] **Alert notification system** ← MISSING
- [x] Real-time metrics dashboard (Grafana)

### Part 3: Batch Processing (25 points) ✅
- [x] RFM analysis (daily at 2 AM)
- [x] Product performance analysis
- [x] Sales trend analysis
- [x] Star schema warehouse (MongoDB)
- [x] ETL pipeline
- [x] Data warehouse schema docs
- [x] Scheduled batch jobs

### Part 4: Visualization & API (15 points)
- [x] RESTful API endpoints (10 endpoints)
- [x] API documentation (OpenAPI)
- [x] Interactive dashboard (Grafana)
- [x] Product category charts (in Grafana)
- [x] Geographic sales visualization (country-level)
- [ ] **Power BI/Tableau dashboard** ← MISSING
- [ ] **Web interface for exploration** ← MISSING

### Part 5: Infrastructure (10 points)
- [x] Docker deployment
- [x] System health checks (basic)
- [x] Authentication (API key)
- [x] Data validation
- [x] Deployment scripts
- [ ] **System architecture diagram** ← MISSING
- [ ] **Monitoring dashboard for system health** ← MISSING

---

## Geographic Data Constraint

**Important:** Producer generates only country-level data (5 countries: USA, UK, Canada, Germany, France).

**Implications:**
- Power BI maps: Use country-level choropleth (no state/city data)
- Geographic visualizations: Country comparisons, not regional breakdowns
- No need to modify producer for more granular geography

---

## Technology Stack Summary

**Current:**
- Python 3.x, PySpark 3.5.0
- Kafka, PostgreSQL, MongoDB, Redis
- FastAPI, Grafana, Docker

**To Add:**
- Power BI Desktop (for dashboard)
- HTML/CSS/JavaScript (for web interface)
- SMTP for email notifications
- draw.io for diagrams

---

## Recommended Execution Order

1. **Phase 0** (1 hr) - Fix producer throughput to 500 events/sec (Part 1 requirement)
2. **Phase 1** (30 min) - Fix streaming processors (unblock data population)
3. **Phase 6** (1.5 hrs) - Unified Grafana dashboard with 3 pages (Parts 1, 2, 5)
4. **Phase 2** (2-3 hrs) - Power BI dashboard (highest point value, critical)
5. **Phase 4** (2-3 hrs) - Web interface (critical deliverable)
6. **Phase 3** (1-2 hrs) - Alert notifications (completes Part 2)
7. **Phase 5** (30 min) - Architecture diagram (quick win)
8. **Phase 7** (30 min) - Documentation updates

**Total: 9.5-12.5 hours of focused work**

**Why this order:** Phases 0-1-6 complete all infrastructure (ingestion→processing→monitoring), then build visualization layers (Power BI, Web), then add enhancements (alerts, docs).

---

## Success Criteria

✅ **Producer:** 500+ events/second throughput measured
✅ **Database:** All 7 PostgreSQL tables populated with data
✅ **Grafana:** Single dashboard with 3 pages (Ingestion, Processing, System Health)
✅ **Power BI:** Executive dashboard with 4 pages showing MongoDB data
✅ **Web Interface:** Data exploration UI accessible at `http://localhost:8000`
✅ **Alerts:** Email notifications for low stock and anomalies
✅ **Diagrams:** Architecture diagram in `docs/` folder (PNG/SVG)
✅ **Documentation:** README updated with all new features

**Final Score Target: 100/100 points**
