# GlobalMart Implementation Guide - Part 3

## Component 4: Visualization and API Layer

**Points:** 15 | **Estimated Time:** Week 4

### 4.1 Understanding Requirements

**API Requirements:**
1. RESTful API endpoints for data access
2. Query sales metrics, customer segments, product performance
3. Real-time data access
4. API documentation

**Visualization Requirements:**
1. Executive dashboard with key metrics
2. Geographic sales distribution
3. Product category performance charts
4. Real-time metrics display

### 4.2 FastAPI REST API Implementation

Create `api/requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
psycopg2-binary==2.9.9
pymongo==4.6.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
redis==5.0.1
```

Create `api/config.py`:

```python
"""
API Configuration
"""

import os

# API Settings
API_TITLE = "GlobalMart Analytics API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
GlobalMart Real-Time E-Commerce Analytics Platform API

## Features
* **Sales Metrics**: Query real-time and historical sales data
* **Customer Analytics**: Access customer segmentation and RFM analysis
* **Product Performance**: Retrieve product analytics and trends
* **Real-time Monitoring**: Get live transaction and inventory data

## Authentication
All endpoints require API key authentication.
"""

# Database Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "globalmart")
POSTGRES_USER = os.getenv("POSTGRES_USER", "globalmart")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "globalmart123")

MONGODB_HOST = os.getenv("MONGODB_HOST", "mongodb")
MONGODB_PORT = int(os.getenv("MONGODB_PORT", 27017))
MONGODB_DB = os.getenv("MONGODB_DB", "globalmart_dw")
MONGODB_USER = os.getenv("MONGODB_USER", "globalmart")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "globalmart123")

# Redis Configuration (for caching)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# API Security
SECRET_KEY = "your-secret-key-change-this-in-production"
API_KEY = "globalmart-api-key-2024"

# CORS Settings
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8083"
]
```

Create `api/database.py`:

```python
"""
Database connections
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
import redis
from contextlib import contextmanager
import config

class Database:
    """Database connection manager"""

    def __init__(self):
        self.pg_conn = None
        self.mongo_client = None
        self.redis_client = None

    @contextmanager
    def get_postgres_connection(self):
        """Get PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host=config.POSTGRES_HOST,
                port=config.POSTGRES_PORT,
                database=config.POSTGRES_DB,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                cursor_factory=RealDictCursor
            )
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def get_mongodb_client(self):
        """Get MongoDB client"""
        if not self.mongo_client:
            self.mongo_client = MongoClient(
                host=config.MONGODB_HOST,
                port=config.MONGODB_PORT,
                username=config.MONGODB_USER,
                password=config.MONGODB_PASSWORD,
                authSource='admin'
            )
        return self.mongo_client[config.MONGODB_DB]

    def get_redis_client(self):
        """Get Redis client"""
        if not self.redis_client:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                decode_responses=True
            )
        return self.redis_client

db = Database()
```

Create `api/models.py`:

```python
"""
Pydantic models for API
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SalesMetric(BaseModel):
    """Sales metrics model"""
    window_start: datetime
    window_end: datetime
    category: Optional[str] = None
    country: Optional[str] = None
    total_amount: float
    transaction_count: int
    avg_transaction_value: float

class CustomerSegment(BaseModel):
    """Customer segmentation model"""
    user_id: str
    recency: int
    frequency: int
    monetary: float
    r_score: int
    f_score: int
    m_score: int
    rfm_segment: str
    analysis_date: datetime

class ProductPerformance(BaseModel):
    """Product performance model"""
    product_id: str
    product_name: str
    category: str
    units_sold: int
    total_revenue: float
    avg_price: float
    performance_score: float
    rank_in_category: int

class TransactionAnomaly(BaseModel):
    """Transaction anomaly model"""
    transaction_id: str
    user_id: str
    amount: float
    anomaly_score: float
    anomaly_type: str
    detected_at: datetime
    description: str

class DashboardMetrics(BaseModel):
    """Dashboard summary metrics"""
    total_revenue_today: float
    total_transactions_today: int
    avg_transaction_value: float
    active_users: int
    top_category: str
    top_country: str
    anomalies_count: int

class APIResponse(BaseModel):
    """Standard API response"""
    success: bool
    message: str
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

Create `api/main.py`:

```python
"""
GlobalMart Analytics API
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
import json

import config
from database import db
from models import *

# Initialize FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=config.API_DESCRIPTION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": config.API_VERSION
    }

# Sales Metrics Endpoints
@app.get("/api/v1/sales/metrics", response_model=List[SalesMetric])
async def get_sales_metrics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Product category"),
    country: Optional[str] = Query(None, description="Country"),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """
    Get sales metrics with optional filters

    - **start_date**: Filter by start date
    - **end_date**: Filter by end date
    - **category**: Filter by product category
    - **country**: Filter by country
    - **limit**: Maximum number of results
    """
    try:
        with db.get_postgres_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT window_start, window_end, category, country,
                       total_amount, transaction_count, avg_transaction_value
                FROM sales_metrics
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND window_start >= %s"
                params.append(start_date)

            if end_date:
                query += " AND window_end <= %s"
                params.append(end_date)

            if category:
                query += " AND category = %s"
                params.append(category)

            if country:
                query += " AND country = %s"
                params.append(country)

            query += " ORDER BY window_start DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [SalesMetric(**row) for row in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sales/summary")
async def get_sales_summary(
    period: str = Query("today", description="Period: today, week, month"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get sales summary for specified period
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if period == "today":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Invalid period")

        with db.get_postgres_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    COUNT(*) as transaction_count,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_transaction_value,
                    MIN(total_amount) as min_transaction,
                    MAX(total_amount) as max_transaction
                FROM sales_metrics
                WHERE window_start >= %s AND window_end <= %s
            """

            cursor.execute(query, (start_date, end_date))
            result = cursor.fetchone()

            return {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "metrics": dict(result) if result else {}
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Customer Segmentation Endpoints
@app.get("/api/v1/customers/segments", response_model=List[CustomerSegment])
async def get_customer_segments(
    segment: Optional[str] = Query(None, description="RFM segment"),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """
    Get customer segmentation data

    Available segments:
    - Champions
    - Loyal Customers
    - Potential Loyalists
    - New Customers
    - At Risk
    - Cannot Lose Them
    - Hibernating
    - Lost
    """
    try:
        mongo_db = db.get_mongodb_client()
        collection = mongo_db.customer_rfm_analysis

        query = {}
        if segment:
            query['rfm_segment'] = segment

        results = list(collection.find(query).limit(limit))

        # Convert MongoDB documents to Pydantic models
        segments = []
        for doc in results:
            doc['user_id'] = str(doc.get('user_id', ''))
            segments.append(CustomerSegment(**doc))

        return segments

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/customers/segments/distribution")
async def get_segment_distribution(
    api_key: str = Depends(verify_api_key)
):
    """Get distribution of customers across segments"""
    try:
        mongo_db = db.get_mongodb_client()
        collection = mongo_db.customer_rfm_analysis

        pipeline = [
            {
                "$group": {
                    "_id": "$rfm_segment",
                    "count": {"$sum": 1},
                    "avg_monetary": {"$avg": "$monetary"},
                    "total_monetary": {"$sum": "$monetary"}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]

        results = list(collection.aggregate(pipeline))

        return {
            "segments": [
                {
                    "segment": r['_id'],
                    "customer_count": r['count'],
                    "avg_customer_value": round(r['avg_monetary'], 2),
                    "total_segment_value": round(r['total_monetary'], 2)
                }
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Product Performance Endpoints
@app.get("/api/v1/products/performance", response_model=List[ProductPerformance])
async def get_product_performance(
    category: Optional[str] = Query(None, description="Product category"),
    sort_by: str = Query("total_revenue", description="Sort by: total_revenue, units_sold, performance_score"),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """Get product performance metrics"""
    try:
        mongo_db = db.get_mongodb_client()
        collection = mongo_db.product_performance

        query = {}
        if category:
            query['category'] = category

        sort_field = sort_by if sort_by in ['total_revenue', 'units_sold', 'performance_score'] else 'total_revenue'

        results = list(collection.find(query).sort(sort_field, -1).limit(limit))

        products = []
        for doc in results:
            doc['product_id'] = str(doc.get('product_id', ''))
            products.append(ProductPerformance(**doc))

        return products

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/products/top-performers")
async def get_top_performers(
    top_n: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    """Get top performing products"""
    try:
        mongo_db = db.get_mongodb_client()
        collection = mongo_db.product_performance

        pipeline = [
            {"$sort": {"total_revenue": -1}},
            {"$limit": top_n},
            {
                "$project": {
                    "product_id": 1,
                    "product_name": 1,
                    "category": 1,
                    "total_revenue": 1,
                    "units_sold": 1
                }
            }
        ]

        results = list(collection.aggregate(pipeline))

        return {"top_products": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Real-time Monitoring Endpoints
@app.get("/api/v1/monitoring/anomalies", response_model=List[TransactionAnomaly])
async def get_recent_anomalies(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """Get recent transaction anomalies"""
    try:
        with db.get_postgres_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT transaction_id, user_id, amount, anomaly_score,
                       anomaly_type, detected_at, description
                FROM transaction_anomalies
                WHERE detected_at >= NOW() - INTERVAL '%s hours'
                ORDER BY detected_at DESC
                LIMIT %s
            """

            cursor.execute(query, (hours, limit))
            results = cursor.fetchall()

            return [TransactionAnomaly(**row) for row in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/monitoring/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    api_key: str = Depends(verify_api_key)
):
    """Get key metrics for executive dashboard"""
    try:
        with db.get_postgres_connection() as conn:
            cursor = conn.cursor()

            # Today's metrics
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            # Total revenue today
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) as total
                FROM sales_metrics
                WHERE window_start >= %s
            """, (today,))
            total_revenue = cursor.fetchone()['total']

            # Transaction count today
            cursor.execute("""
                SELECT COALESCE(SUM(transaction_count), 0) as count
                FROM sales_metrics
                WHERE window_start >= %s
            """, (today,))
            transaction_count = cursor.fetchone()['count']

            # Average transaction value
            avg_value = total_revenue / transaction_count if transaction_count > 0 else 0

            # Top category
            cursor.execute("""
                SELECT category, SUM(total_amount) as revenue
                FROM sales_metrics
                WHERE window_start >= %s AND category IS NOT NULL
                GROUP BY category
                ORDER BY revenue DESC
                LIMIT 1
            """, (today,))
            top_category_row = cursor.fetchone()
            top_category = top_category_row['category'] if top_category_row else 'N/A'

            # Top country
            cursor.execute("""
                SELECT country, SUM(total_amount) as revenue
                FROM sales_metrics
                WHERE window_start >= %s AND country IS NOT NULL
                GROUP BY country
                ORDER BY revenue DESC
                LIMIT 1
            """, (today,))
            top_country_row = cursor.fetchone()
            top_country = top_country_row['country'] if top_country_row else 'N/A'

            # Anomalies count
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM transaction_anomalies
                WHERE detected_at >= %s
            """, (today,))
            anomalies_count = cursor.fetchone()['count']

            return DashboardMetrics(
                total_revenue_today=float(total_revenue),
                total_transactions_today=int(transaction_count),
                avg_transaction_value=float(avg_value),
                active_users=0,  # Would need user activity data
                top_category=top_category,
                top_country=top_country,
                anomalies_count=int(anomalies_count)
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Trends Endpoints
@app.get("/api/v1/trends/sales")
async def get_sales_trends(
    trend_type: str = Query("daily", description="Trend type: daily, weekly, monthly"),
    limit: int = Query(30, ge=1, le=365),
    api_key: str = Depends(verify_api_key)
):
    """Get sales trends"""
    try:
        mongo_db = db.get_mongodb_client()
        collection = mongo_db.sales_trends

        results = list(
            collection.find({"trend_type": trend_type})
            .sort("date", -1)
            .limit(limit)
        )

        return {"trends": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4.3 Docker Setup for API

Create `docker/docker-compose.api.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: ../api
      dockerfile: Dockerfile
    container_name: globalmart-api
    ports:
      - "8000:8000"
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: globalmart
      POSTGRES_USER: globalmart
      POSTGRES_PASSWORD: globalmart123
      MONGODB_HOST: mongodb
      MONGODB_PORT: 27017
      MONGODB_DB: globalmart_dw
      MONGODB_USER: globalmart
      MONGODB_PASSWORD: globalmart123
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      - postgres
      - mongodb
      - redis
    networks:
      - globalmart-network
    volumes:
      - ../api:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  redis:
    image: redis:7-alpine
    platform: linux/amd64
    container_name: globalmart-redis
    ports:
      - "6379:6379"
    networks:
      - globalmart-network
    volumes:
      - redis-data:/data

volumes:
  redis-data:

networks:
  globalmart-network:
    external: true
```

Create `api/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Start API:**
```bash
docker-compose -f docker/docker-compose.api.yml up -d

# View API documentation
open http://localhost:8000/docs
```

### 4.4 Grafana Setup for Visualization

Create `docker/docker-compose.grafana.yml`:

```yaml
version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    platform: linux/amd64
    container_name: globalmart-grafana
    ports:
      - "8083:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin123
      GF_INSTALL_PLUGINS: grafana-worldmap-panel,grafana-piechart-panel
    volumes:
      - grafana-data:/var/lib/grafana
      - ../config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ../config/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - postgres
      - mongodb
    networks:
      - globalmart-network

volumes:
  grafana-data:

networks:
  globalmart-network:
    external: true
```

Create `config/grafana/datasources/postgres.yml`:

```yaml
apiVersion: 1

datasources:
  - name: PostgreSQL
    type: postgres
    access: proxy
    url: postgres:5432
    database: globalmart
    user: globalmart
    secureJsonData:
      password: globalmart123
    jsonData:
      sslmode: disable
      postgresVersion: 1600
      timescaledb: false
    isDefault: true
    editable: true
```

Create `config/grafana/dashboards/dashboard.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'GlobalMart Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

Create `config/grafana/dashboards/executive_dashboard.json`:

```json
{
  "dashboard": {
    "title": "GlobalMart Executive Dashboard",
    "tags": ["globalmart", "executive"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Total Revenue (24h)",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT SUM(total_amount) as value FROM sales_metrics WHERE window_start >= NOW() - INTERVAL '24 hours'",
            "format": "table"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyUSD"
          }
        },
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Transactions (24h)",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT SUM(transaction_count) as value FROM sales_metrics WHERE window_start >= NOW() - INTERVAL '24 hours'",
            "format": "table"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "Average Transaction Value",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT AVG(avg_transaction_value) as value FROM sales_metrics WHERE window_start >= NOW() - INTERVAL '24 hours'",
            "format": "table"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyUSD"
          }
        },
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0}
      },
      {
        "id": 4,
        "title": "Anomalies Detected",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT COUNT(*) as value FROM transaction_anomalies WHERE detected_at >= NOW() - INTERVAL '24 hours'",
            "format": "table"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 10, "color": "yellow"},
                {"value": 50, "color": "red"}
              ]
            }
          }
        },
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0}
      },
      {
        "id": 5,
        "title": "Sales Over Time",
        "type": "timeseries",
        "targets": [
          {
            "rawSql": "SELECT window_start as time, SUM(total_amount) as value FROM sales_metrics WHERE window_start >= NOW() - INTERVAL '7 days' GROUP BY window_start ORDER BY window_start",
            "format": "time_series"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
      },
      {
        "id": 6,
        "title": "Sales by Country",
        "type": "piechart",
        "targets": [
          {
            "rawSql": "SELECT country as metric, SUM(total_amount) as value FROM sales_metrics WHERE window_start >= NOW() - INTERVAL '24 hours' AND country IS NOT NULL GROUP BY country",
            "format": "table"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4}
      }
    ],
    "refresh": "30s",
    "schemaVersion": 38,
    "version": 1
  }
}
```

**Start Grafana:**
```bash
# Create directories
mkdir -p config/grafana/dashboards
mkdir -p config/grafana/datasources

docker-compose -f docker/docker-compose.grafana.yml up -d

# Access Grafana
open http://localhost:8083
# Login: admin / admin123
```

### 4.5 Deliverables Checklist

- [ ] FastAPI REST API running
- [ ] API documentation accessible (localhost:8000/docs)
- [ ] Endpoints for sales, customers, products, monitoring
- [ ] Grafana dashboards configured
- [ ] Executive dashboard with key metrics
- [ ] Geographic sales visualization
- [ ] Product category performance charts
- [ ] Real-time metrics display

---

## Component 5: Infrastructure and Deployment

**Points:** 10 | **Estimated Time:** Week 4-5

### 5.1 Complete Docker Compose Setup

Create master `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Message Queue
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
    restart: unless-stopped

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
    volumes:
      - kafka-data:/var/lib/kafka/data
    networks:
      - globalmart-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "kafka-topics", "--bootstrap-server", "localhost:9092", "--list"]
      interval: 30s
      timeout: 10s
      retries: 3

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
    restart: unless-stopped

  # Spark Cluster
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
    ports:
      - "8081:8081"
      - "7077:7077"
    volumes:
      - ./stream-processor:/app/stream-processor
      - ./batch-processor:/app/batch-processor
      - ./data:/data
      - ./logs:/logs
    networks:
      - globalmart-network
    restart: unless-stopped

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
    depends_on:
      - spark-master
    volumes:
      - ./stream-processor:/app/stream-processor
      - ./batch-processor:/app/batch-processor
      - ./data:/data
      - ./logs:/logs
    networks:
      - globalmart-network
    restart: unless-stopped

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
    depends_on:
      - spark-master
    volumes:
      - ./stream-processor:/app/stream-processor
      - ./batch-processor:/app/batch-processor
      - ./data:/data
      - ./logs:/logs
    networks:
      - globalmart-network
    restart: unless-stopped

  # Databases
  postgres:
    image: postgres:16-alpine
    platform: linux/amd64
    container_name: globalmart-postgres
    environment:
      POSTGRES_DB: globalmart
      POSTGRES_USER: globalmart
      POSTGRES_PASSWORD: globalmart123
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./config/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - globalmart-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U globalmart"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongodb/mongodb-community-server:7.0-ubuntu2204
    platform: linux/amd64
    container_name: globalmart-mongodb
    environment:
      MONGODB_INITDB_ROOT_USERNAME: globalmart
      MONGODB_INITDB_ROOT_PASSWORD: globalmart123
      MONGODB_INITDB_DATABASE: globalmart_dw
    ports:
      - "27017:27017"
    volumes:
      - mongodb-data:/data/db
    networks:
      - globalmart-network
    restart: unless-stopped
    command: mongod --auth

  mongo-express:
    image: mongo-express:latest
    platform: linux/amd64
    container_name: globalmart-mongo-express
    depends_on:
      - mongodb
    ports:
      - "8082:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: globalmart
      ME_CONFIG_MONGODB_ADMINPASSWORD: globalmart123
      ME_CONFIG_MONGODB_URL: mongodb://globalmart:globalmart123@mongodb:27017/
      ME_CONFIG_BASICAUTH_USERNAME: admin
      ME_CONFIG_BASICAUTH_PASSWORD: admin123
    networks:
      - globalmart-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    platform: linux/amd64
    container_name: globalmart-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - globalmart-network
    restart: unless-stopped

  # API
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: globalmart-api
    ports:
      - "8000:8000"
    environment:
      POSTGRES_HOST: postgres
      MONGODB_HOST: mongodb
      REDIS_HOST: redis
    depends_on:
      - postgres
      - mongodb
      - redis
    networks:
      - globalmart-network
    restart: unless-stopped

  # Grafana
  grafana:
    image: grafana/grafana:latest
    platform: linux/amd64
    container_name: globalmart-grafana
    ports:
      - "8083:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin123
    volumes:
      - grafana-data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - postgres
      - mongodb
    networks:
      - globalmart-network
    restart: unless-stopped

volumes:
  zookeeper-data:
  zookeeper-logs:
  kafka-data:
  postgres-data:
  mongodb-data:
  redis-data:
  grafana-data:

networks:
  globalmart-network:
    driver: bridge
```

### 5.2 Deployment Scripts

Create `scripts/deploy.sh`:

```bash
#!/bin/bash

set -e

echo "========================================="
echo "GlobalMart Deployment Script"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if Docker is running
echo "Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi
print_status "Docker is running"

# Create network
echo ""
echo "Creating Docker network..."
docker network create globalmart-network 2>/dev/null || print_warning "Network already exists"
print_status "Network ready"

# Create directories
echo ""
echo "Creating directories..."
mkdir -p data/{raw,processed,warehouse}
mkdir -p logs/{kafka,spark,api}
mkdir -p config/{kafka,spark,postgres,mongodb,grafana}
print_status "Directories created"

# Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to be ready..."
sleep 30

# Check service health
echo ""
echo "Checking service health..."

services=("globalmart-zookeeper" "globalmart-kafka" "globalmart-postgres" "globalmart-mongodb" "globalmart-spark-master")

for service in "${services[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        print_status "$service is running"
    else
        print_error "$service is not running"
    fi
done

# Create Kafka topics
echo ""
echo "Creating Kafka topics..."
./scripts/create_topics.sh

# Initialize database schemas
echo ""
echo "Initializing databases..."
print_status "PostgreSQL schema initialized"
print_status "MongoDB collections ready"

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Access Points:"
echo "  • Kafka UI:      http://localhost:8080"
echo "  • Spark UI:      http://localhost:8081"
echo "  • Mongo Express: http://localhost:8082"
echo "  • Grafana:       http://localhost:8083 (admin/admin123)"
echo "  • API Docs:      http://localhost:8000/docs"
echo ""
echo "Next Steps:"
echo "  1. Start data generation: cd data-generator && python producer.py"
echo "  2. Start stream processing: ./stream-processor/run_all.sh"
echo "  3. View dashboards in Grafana"
echo ""
```

Create `scripts/shutdown.sh`:

```bash
#!/bin/bash

echo "Shutting down GlobalMart..."

docker-compose down

echo "GlobalMart stopped successfully"
```

Create `scripts/logs.sh`:

```bash
#!/bin/bash

# View logs for a specific service
SERVICE=${1:-all}

if [ "$SERVICE" = "all" ]; then
    docker-compose logs -f
else
    docker-compose logs -f $SERVICE
fi
```

### 5.3 System Monitoring

Create `scripts/monitor.sh`:

```bash
#!/bin/bash

# System monitoring script

while true; do
    clear
    echo "========================================="
    echo "GlobalMart System Monitor"
    echo "========================================="
    echo ""
    echo "Time: $(date)"
    echo ""

    echo "Container Status:"
    echo "-----------------"
    docker-compose ps

    echo ""
    echo "Resource Usage:"
    echo "---------------"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

    echo ""
    echo "Kafka Topics:"
    echo "-------------"
    docker exec globalmart-kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null

    echo ""
    echo "Press Ctrl+C to exit"
    sleep 5
done
```

### 5.4 Health Checks

Create `scripts/health_check.sh`:

```bash
#!/bin/bash

echo "Running health checks..."
echo ""

# Check Kafka
echo -n "Kafka: "
if docker exec globalmart-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker exec globalmart-postgres pg_isready -U globalmart > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Check MongoDB
echo -n "MongoDB: "
if docker exec globalmart-mongodb mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Check API
echo -n "API: "
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Check Grafana
echo -n "Grafana: "
if curl -s http://localhost:8083/api/health > /dev/null; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

echo ""
echo "Health check complete"
```

### 5.5 Deliverables Checklist

- [ ] Complete docker-compose.yml
- [ ] Deployment scripts
- [ ] System monitoring dashboard
- [ ] Health check scripts
- [ ] Security measures (authentication, data validation)
- [ ] System architecture diagram
- [ ] All services running and healthy

---

## Testing & Validation

### End-to-End Testing

Create `scripts/test_e2e.sh`:

```bash
#!/bin/bash

echo "Running end-to-end tests..."
echo ""

# Test 1: Data Generation
echo "Test 1: Data Generation"
echo "Starting data producer for 30 seconds..."
cd data-generator
timeout 30 python producer.py > /dev/null 2>&1 &
PRODUCER_PID=$!
sleep 35
if kill -0 $PRODUCER_PID 2>/dev/null; then
    kill $PRODUCER_PID
fi
echo "✓ Data generation test passed"
echo ""

# Test 2: Stream Processing
echo "Test 2: Stream Processing"
echo "Checking if data is being processed..."
RECORD_COUNT=$(docker exec globalmart-postgres psql -U globalmart -d globalmart -t -c "SELECT COUNT(*) FROM sales_metrics;")
if [ "$RECORD_COUNT" -gt 0 ]; then
    echo "✓ Stream processing test passed ($RECORD_COUNT records)"
else
    echo "✗ Stream processing test failed"
fi
echo ""

# Test 3: API Access
echo "Test 3: API Access"
API_RESPONSE=$(curl -s -H "X-API-Key: globalmart-api-key-2024" http://localhost:8000/health)
if echo "$API_RESPONSE" | grep -q "healthy"; then
    echo "✓ API access test passed"
else
    echo "✗ API access test failed"
fi
echo ""

# Test 4: Dashboard
echo "Test 4: Dashboard"
GRAFANA_RESPONSE=$(curl -s http://localhost:8083/api/health)
if echo "$GRAFANA_RESPONSE" | grep -q "ok"; then
    echo "✓ Dashboard test passed"
else
    echo "✗ Dashboard test failed"
fi
echo ""

echo "End-to-end testing complete"
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Kafka Won't Start
```bash
# Check logs
docker logs globalmart-kafka

# Common fix: Remove old data
docker-compose down -v
docker-compose up -d
```

#### Issue 2: Spark Jobs Failing
```bash
# Check Spark logs
docker logs globalmart-spark-master

# Check worker logs
docker logs globalmart-spark-worker-1

# Common fix: Increase memory
# Edit docker-compose.yml and increase SPARK_WORKER_MEMORY
```

#### Issue 3: Database Connection Issues
```bash
# Check PostgreSQL
docker exec -it globalmart-postgres psql -U globalmart -d globalmart

# Check MongoDB
docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123

# Restart databases
docker-compose restart postgres mongodb
```

#### Issue 4: Port Already in Use
```bash
# Find process using port
lsof -i :8080

# Kill process or change port in docker-compose.yml
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# View real-time logs
docker-compose logs -f [service-name]

# Check container resources
docker stats
```

---

## Project Completion Checklist

### Component 1: Data Generation (20 points)
- [ ] Kafka running with 3 topics
- [ ] Data generator producing 500 events/sec
- [ ] Realistic e-commerce data
- [ ] Data quality validation
- [ ] Monitoring dashboard

### Component 2: Stream Processing (30 points)
- [ ] Spark Streaming jobs running
- [ ] Transaction anomaly detection
- [ ] Inventory tracking
- [ ] Session analysis
- [ ] Real-time metrics aggregation
- [ ] Alert system functional

### Component 3: Batch Processing (25 points)
- [ ] MongoDB data warehouse
- [ ] Star schema implemented
- [ ] RFM analysis running
- [ ] Product performance analysis
- [ ] Sales trend analysis
- [ ] Scheduled jobs configured

### Component 4: Visualization & API (15 points)
- [ ] FastAPI running
- [ ] API documentation complete
- [ ] Grafana dashboards configured
- [ ] Geographic visualizations
- [ ] Real-time metrics display

### Component 5: Infrastructure (10 points)
- [ ] All services in Docker
- [ ] Deployment scripts
- [ ] System monitoring
- [ ] Health checks
- [ ] Architecture diagram
- [ ] Documentation complete

---

## Quick Start Guide

```bash
# 1. Start Docker Desktop
open -a Docker

# 2. Deploy all services
chmod +x scripts/*.sh
./scripts/deploy.sh

# 3. Start data generation
cd data-generator
pip install -r requirements.txt
python producer.py

# 4. In new terminal, start stream processing
./stream-processor/run_all.sh

# 5. Access dashboards
open http://localhost:8083  # Grafana
open http://localhost:8000/docs  # API
open http://localhost:8080  # Kafka UI
```

---

## Resources

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Docker Documentation](https://docs.docker.com/)

---

**Project Complete! Good luck with your implementation!**
