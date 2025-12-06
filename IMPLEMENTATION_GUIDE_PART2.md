# GlobalMart Implementation Guide - Part 2

## Component 3: Batch Processing and Data Warehouse

**Points:** 25 | **Estimated Time:** Week 3

### 3.1 Understanding Requirements

**Batch Processing Tasks:**
1. **Customer Segmentation** - RFM (Recency, Frequency, Monetary) Analysis
2. **Product Performance Analysis** - Best/worst performers by category
3. **Sales Trend Analysis** - Daily, weekly, monthly trends
4. **Data Warehouse** - Star schema design for analytical queries

### 3.2 MongoDB Setup for Data Warehouse

Create `docker/docker-compose.mongodb.yml`:

```yaml
version: '3.8'

services:
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
      - mongodb-config:/data/configdb
    networks:
      - globalmart-network
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

volumes:
  mongodb-data:
  mongodb-config:

networks:
  globalmart-network:
    external: true
```

**Start MongoDB:**
```bash
docker-compose -f docker/docker-compose.mongodb.yml up -d

# Verify MongoDB is running
docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123 --authenticationDatabase admin

# Access Mongo Express at http://localhost:8082
```

### 3.3 Data Warehouse Schema Design

Create `config/data_warehouse_schema.md`:

```markdown
# GlobalMart Data Warehouse - Star Schema Design

## Fact Tables

### fact_sales
- sale_id (PK)
- date_key (FK -> dim_date)
- product_key (FK -> dim_product)
- customer_key (FK -> dim_customer)
- location_key (FK -> dim_location)
- quantity
- unit_price
- discount_amount
- total_amount
- payment_method

### fact_customer_sessions
- session_id (PK)
- customer_key (FK -> dim_customer)
- date_key (FK -> dim_date)
- session_start_time
- session_end_time
- duration_minutes
- page_views
- products_viewed
- cart_adds
- cart_removes
- purchase_completed
- cart_abandoned

## Dimension Tables

### dim_date
- date_key (PK)
- full_date
- day
- month
- year
- quarter
- week_of_year
- day_of_week
- is_weekend
- is_holiday

### dim_product
- product_key (PK)
- product_id (NK)
- product_name
- category
- subcategory
- price
- cost
- supplier
- brand

### dim_customer
- customer_key (PK)
- customer_id (NK)
- email
- age_group
- country
- registration_date
- customer_segment (RFM)
- lifetime_value

### dim_location
- location_key (PK)
- country
- region
- city
- timezone

### dim_time
- time_key (PK)
- hour
- minute
- time_of_day (morning/afternoon/evening/night)
- business_hour (yes/no)
```

Create `batch-processor/warehouse_schema.py`:

```python
"""
Data warehouse schema definitions for MongoDB
"""

# MongoDB collections structure

COLLECTIONS = {
    "fact_sales": {
        "indexes": [
            {"keys": [("date_key", 1)], "name": "idx_date"},
            {"keys": [("product_key", 1)], "name": "idx_product"},
            {"keys": [("customer_key", 1)], "name": "idx_customer"},
            {"keys": [("location_key", 1)], "name": "idx_location"},
            {"keys": [("date_key", 1), ("product_key", 1)], "name": "idx_date_product"}
        ],
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["sale_id", "date_key", "product_key", "customer_key", "total_amount"],
                "properties": {
                    "sale_id": {"bsonType": "string"},
                    "date_key": {"bsonType": "int"},
                    "product_key": {"bsonType": "int"},
                    "customer_key": {"bsonType": "int"},
                    "location_key": {"bsonType": "int"},
                    "quantity": {"bsonType": "int", "minimum": 1},
                    "unit_price": {"bsonType": "double", "minimum": 0},
                    "total_amount": {"bsonType": "double", "minimum": 0}
                }
            }
        }
    },

    "fact_customer_sessions": {
        "indexes": [
            {"keys": [("customer_key", 1)], "name": "idx_customer"},
            {"keys": [("date_key", 1)], "name": "idx_date"},
            {"keys": [("cart_abandoned", 1)], "name": "idx_abandoned"}
        ]
    },

    "dim_product": {
        "indexes": [
            {"keys": [("product_id", 1)], "name": "idx_product_id", "unique": True},
            {"keys": [("category", 1)], "name": "idx_category"}
        ]
    },

    "dim_customer": {
        "indexes": [
            {"keys": [("customer_id", 1)], "name": "idx_customer_id", "unique": True},
            {"keys": [("customer_segment", 1)], "name": "idx_segment"}
        ]
    },

    "dim_date": {
        "indexes": [
            {"keys": [("full_date", 1)], "name": "idx_date", "unique": True}
        ]
    },

    "dim_location": {
        "indexes": [
            {"keys": [("country", 1)], "name": "idx_country"}
        ]
    }
}

# Analytics collections
ANALYTICS_COLLECTIONS = {
    "customer_rfm_analysis": {
        "indexes": [
            {"keys": [("customer_id", 1)], "name": "idx_customer"},
            {"keys": [("rfm_segment", 1)], "name": "idx_segment"}
        ]
    },

    "product_performance": {
        "indexes": [
            {"keys": [("product_id", 1)], "name": "idx_product"},
            {"keys": [("category", 1)], "name": "idx_category"},
            {"keys": [("total_revenue", -1)], "name": "idx_revenue"}
        ]
    },

    "sales_trends": {
        "indexes": [
            {"keys": [("date", 1)], "name": "idx_date"},
            {"keys": [("trend_type", 1), ("date", 1)], "name": "idx_trend_date"}
        ]
    }
}
```

### 3.4 ETL Pipeline Implementation

Create `batch-processor/config.py`:

```python
"""
Batch processing configuration
"""

# Spark Configuration
SPARK_APP_NAME = "GlobalMart Batch Processor"
SPARK_MASTER = "spark://spark-master:7077"

# Data Sources
RAW_DATA_PATH = "/data/raw"
PROCESSED_DATA_PATH = "/data/processed"
WAREHOUSE_DATA_PATH = "/data/warehouse"

# PostgreSQL (source for operational data)
POSTGRES_HOST = "postgres"
POSTGRES_PORT = 5432
POSTGRES_DB = "globalmart"
POSTGRES_USER = "globalmart"
POSTGRES_PASSWORD = "globalmart123"
POSTGRES_URL = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# MongoDB (data warehouse)
MONGODB_HOST = "mongodb"
MONGODB_PORT = 27017
MONGODB_DATABASE = "globalmart_dw"
MONGODB_USER = "globalmart"
MONGODB_PASSWORD = "globalmart123"
MONGODB_URI = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin"

# Kafka (for reading historical data)
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"

# Batch Processing Schedule
BATCH_SCHEDULE = {
    'customer_segmentation': 'daily',  # Run daily at 2 AM
    'product_performance': 'daily',    # Run daily at 3 AM
    'sales_trends': 'hourly'           # Run every hour
}

# RFM Analysis Configuration
RFM_CONFIG = {
    'recency_bins': [1, 30, 90, 180, 365],  # Days
    'frequency_bins': [1, 5, 10, 20, 50],   # Number of transactions
    'monetary_bins': [0, 100, 500, 1000, 5000]  # Total spend
}

# Customer Segments
CUSTOMER_SEGMENTS = {
    'Champions': {'R': [4, 5], 'F': [4, 5], 'M': [4, 5]},
    'Loyal Customers': {'R': [3, 4, 5], 'F': [3, 4, 5], 'M': [3, 4, 5]},
    'Potential Loyalists': {'R': [3, 4, 5], 'F': [1, 2, 3], 'M': [1, 2, 3]},
    'New Customers': {'R': [4, 5], 'F': [1], 'M': [1]},
    'At Risk': {'R': [1, 2], 'F': [3, 4, 5], 'M': [3, 4, 5]},
    'Cannot Lose Them': {'R': [1, 2], 'F': [4, 5], 'M': [4, 5]},
    'Hibernating': {'R': [1, 2], 'F': [1, 2], 'M': [1, 2, 3]},
    'Lost': {'R': [1], 'F': [1, 2], 'M': [1, 2]}
}
```

Create `batch-processor/etl_pipeline.py`:

```python
"""
ETL Pipeline for GlobalMart Data Warehouse
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import config

class ETLPipeline:
    def __init__(self):
        self.spark = self._create_spark_session()

    def _create_spark_session(self):
        """Create Spark session with required connectors"""
        spark = SparkSession.builder \
            .appName(config.SPARK_APP_NAME) \
            .config("spark.jars.packages",
                    "org.postgresql:postgresql:42.6.0,"
                    "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
            .config("spark.mongodb.read.connection.uri", config.MONGODB_URI) \
            .config("spark.mongodb.write.connection.uri", config.MONGODB_URI) \
            .getOrCreate()

        spark.sparkContext.setLogLevel("WARN")
        return spark

    def extract_transactions(self, start_date=None, end_date=None):
        """Extract transactions from PostgreSQL"""
        print("Extracting transaction data...")

        # Read from PostgreSQL
        query = """
            (SELECT
                t.transaction_id,
                t.user_id,
                t.timestamp,
                t.total_amount,
                t.payment_method
             FROM transactions t
        """

        if start_date and end_date:
            query += f" WHERE t.timestamp >= '{start_date}' AND t.timestamp < '{end_date}'"

        query += ") as transactions"

        df = self.spark.read \
            .format("jdbc") \
            .option("url", config.POSTGRES_URL) \
            .option("dbtable", query) \
            .option("user", config.POSTGRES_USER) \
            .option("password", config.POSTGRES_PASSWORD) \
            .option("driver", "org.postgresql.Driver") \
            .load()

        print(f"Extracted {df.count()} transactions")
        return df

    def build_dim_date(self, start_date, end_date):
        """Build date dimension table"""
        print("Building date dimension...")

        # Generate date range
        dates = []
        current = start_date
        while current <= end_date:
            dates.append({
                'date_key': int(current.strftime('%Y%m%d')),
                'full_date': current,
                'day': current.day,
                'month': current.month,
                'year': current.year,
                'quarter': (current.month - 1) // 3 + 1,
                'week_of_year': current.isocalendar()[1],
                'day_of_week': current.weekday(),
                'is_weekend': current.weekday() >= 5,
                'is_holiday': False  # Would need holiday calendar
            })
            current += timedelta(days=1)

        dim_date = self.spark.createDataFrame(dates)

        # Write to MongoDB
        dim_date.write \
            .format("mongodb") \
            .mode("overwrite") \
            .option("database", config.MONGODB_DATABASE) \
            .option("collection", "dim_date") \
            .save()

        print(f"Built date dimension with {dim_date.count()} rows")
        return dim_date

    def build_dim_product(self):
        """Build product dimension from product catalog"""
        print("Building product dimension...")

        # In real scenario, read from product catalog
        # For now, create from transaction data

        # This would typically come from a product master table
        # Simplified version here

        dim_product = self.spark.read \
            .format("mongodb") \
            .option("database", config.MONGODB_DATABASE) \
            .option("collection", "dim_product") \
            .load()

        return dim_product

    def build_fact_sales(self, transactions_df):
        """Build sales fact table"""
        print("Building sales fact table...")

        # Transform transactions to fact table format
        fact_sales = transactions_df \
            .withColumn("date_key",
                       regexp_replace(
                           date_format(col("timestamp"), "yyyyMMdd"),
                           "-", ""
                       ).cast("int")) \
            .withColumn("sale_id", col("transaction_id")) \
            .select(
                col("sale_id"),
                col("date_key"),
                lit(0).alias("product_key"),  # Would join with dim_product
                lit(0).alias("customer_key"), # Would join with dim_customer
                lit(0).alias("location_key"), # Would join with dim_location
                lit(1).alias("quantity"),
                col("total_amount").alias("unit_price"),
                lit(0).alias("discount_amount"),
                col("total_amount"),
                col("payment_method")
            )

        # Write to MongoDB
        fact_sales.write \
            .format("mongodb") \
            .mode("append") \
            .option("database", config.MONGODB_DATABASE) \
            .option("collection", "fact_sales") \
            .save()

        print(f"Built sales fact table with {fact_sales.count()} rows")
        return fact_sales

    def run_daily_etl(self):
        """Run daily ETL process"""
        print("=== Starting Daily ETL Process ===")
        start_time = datetime.now()

        # Define date range (yesterday's data)
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=1)

        print(f"Processing data from {start_date} to {end_date}")

        # Extract
        transactions = self.extract_transactions(start_date, end_date)

        # Build dimensions if needed
        self.build_dim_date(start_date, end_date)

        # Build facts
        self.build_fact_sales(transactions)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"=== ETL Completed in {elapsed:.2f} seconds ===")

if __name__ == "__main__":
    etl = ETLPipeline()
    etl.run_daily_etl()
```

### 3.5 Customer Segmentation (RFM Analysis)

Create `batch-processor/rfm_analysis.py`:

```python
"""
RFM (Recency, Frequency, Monetary) Analysis for Customer Segmentation
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
from datetime import datetime
import config

class RFMAnalysis:
    def __init__(self):
        self.spark = self._create_spark_session()

    def _create_spark_session(self):
        """Create Spark session"""
        spark = SparkSession.builder \
            .appName("RFM Analysis") \
            .config("spark.jars.packages",
                    "org.postgresql:postgresql:42.6.0,"
                    "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
            .config("spark.mongodb.write.connection.uri", config.MONGODB_URI) \
            .getOrCreate()

        spark.sparkContext.setLogLevel("WARN")
        return spark

    def calculate_rfm_scores(self):
        """Calculate RFM scores for all customers"""
        print("Calculating RFM scores...")

        # Read transaction data
        transactions = self.spark.read \
            .format("jdbc") \
            .option("url", config.POSTGRES_URL) \
            .option("dbtable", "(SELECT user_id, timestamp, total_amount FROM transactions) as t") \
            .option("user", config.POSTGRES_USER) \
            .option("password", config.POSTGRES_PASSWORD) \
            .load()

        # Current date for recency calculation
        analysis_date = datetime.now()

        # Calculate RFM metrics
        rfm = transactions \
            .groupBy("user_id") \
            .agg(
                # Recency: days since last purchase
                datediff(lit(analysis_date), max("timestamp")).alias("recency"),
                # Frequency: number of transactions
                count("*").alias("frequency"),
                # Monetary: total amount spent
                sum("total_amount").alias("monetary")
            )

        # Calculate RFM scores (1-5 scale)
        # Using ntile to divide into 5 equal groups
        windowSpec = Window.orderBy(col("recency").desc())
        rfm = rfm.withColumn("r_score", ntile(5).over(windowSpec))

        windowSpec = Window.orderBy(col("frequency"))
        rfm = rfm.withColumn("f_score", ntile(5).over(windowSpec))

        windowSpec = Window.orderBy(col("monetary"))
        rfm = rfm.withColumn("m_score", ntile(5).over(windowSpec))

        # Create RFM segment
        rfm = rfm.withColumn(
            "rfm_score",
            concat(col("r_score"), col("f_score"), col("m_score"))
        )

        # Assign customer segments
        rfm = self._assign_segments(rfm)

        # Add analysis metadata
        rfm = rfm.withColumn("analysis_date", lit(analysis_date))
        rfm = rfm.withColumn("created_at", current_timestamp())

        print(f"Calculated RFM for {rfm.count()} customers")

        # Show sample
        print("\nSample RFM Analysis:")
        rfm.show(10, truncate=False)

        # Show segment distribution
        print("\nCustomer Segment Distribution:")
        rfm.groupBy("rfm_segment").count().orderBy(desc("count")).show()

        return rfm

    def _assign_segments(self, rfm_df):
        """Assign customer segments based on RFM scores"""

        def get_segment(r, f, m):
            """Determine segment based on RFM scores"""
            if r >= 4 and f >= 4 and m >= 4:
                return "Champions"
            elif r >= 3 and f >= 3 and m >= 3:
                return "Loyal Customers"
            elif r >= 3 and f <= 3 and m <= 3:
                return "Potential Loyalists"
            elif r >= 4 and f == 1:
                return "New Customers"
            elif r <= 2 and f >= 3 and m >= 3:
                return "At Risk"
            elif r <= 2 and f >= 4 and m >= 4:
                return "Cannot Lose Them"
            elif r <= 2 and f <= 2:
                return "Hibernating"
            else:
                return "Lost"

        segment_udf = udf(get_segment, StringType())

        return rfm_df.withColumn(
            "rfm_segment",
            segment_udf(col("r_score"), col("f_score"), col("m_score"))
        )

    def save_results(self, rfm_df):
        """Save RFM analysis results to data warehouse"""
        print("Saving RFM results to data warehouse...")

        # Write to MongoDB
        rfm_df.write \
            .format("mongodb") \
            .mode("overwrite") \
            .option("database", config.MONGODB_DATABASE) \
            .option("collection", "customer_rfm_analysis") \
            .save()

        print("RFM results saved successfully")

    def run_analysis(self):
        """Run complete RFM analysis"""
        print("=== Starting RFM Analysis ===")
        start_time = datetime.now()

        rfm_scores = self.calculate_rfm_scores()
        self.save_results(rfm_scores)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"=== RFM Analysis Completed in {elapsed:.2f} seconds ===")

if __name__ == "__main__":
    rfm = RFMAnalysis()
    rfm.run_analysis()
```

### 3.6 Product Performance Analysis

Create `batch-processor/product_performance.py`:

```python
"""
Product Performance Analysis
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import config

class ProductPerformanceAnalyzer:
    def __init__(self):
        self.spark = self._create_spark_session()

    def _create_spark_session(self):
        """Create Spark session"""
        spark = SparkSession.builder \
            .appName("Product Performance Analysis") \
            .config("spark.jars.packages",
                    "org.postgresql:postgresql:42.6.0,"
                    "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
            .config("spark.mongodb.write.connection.uri", config.MONGODB_URI) \
            .getOrCreate()

        spark.sparkContext.setLogLevel("WARN")
        return spark

    def analyze_product_performance(self, days=30):
        """Analyze product performance over specified period"""
        print(f"Analyzing product performance for last {days} days...")

        # Date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Read transaction data
        # Note: In real implementation, would join with product catalog
        query = f"""
            (SELECT
                'sample_product' as product_id,
                'Sample Product' as product_name,
                'Electronics' as category,
                total_amount,
                timestamp
             FROM transactions
             WHERE timestamp >= '{start_date}'
               AND timestamp < '{end_date}'
            ) as product_sales
        """

        sales = self.spark.read \
            .format("jdbc") \
            .option("url", config.POSTGRES_URL) \
            .option("dbtable", query) \
            .option("user", config.POSTGRES_USER) \
            .option("password", config.POSTGRES_PASSWORD) \
            .load()

        # Calculate performance metrics by product
        performance = sales \
            .groupBy("product_id", "product_name", "category") \
            .agg(
                count("*").alias("units_sold"),
                sum("total_amount").alias("total_revenue"),
                avg("total_amount").alias("avg_price"),
                countDistinct(date_format("timestamp", "yyyy-MM-dd")).alias("days_sold")
            ) \
            .withColumn("revenue_per_day", col("total_revenue") / col("days_sold"))

        # Rank products by revenue
        windowSpec = Window.partitionBy("category").orderBy(desc("total_revenue"))
        performance = performance.withColumn("rank_in_category", row_number().over(windowSpec))

        # Add performance indicators
        performance = performance \
            .withColumn("performance_score",
                       (col("total_revenue") / 1000 + col("units_sold") / 10)) \
            .withColumn("analysis_period_days", lit(days)) \
            .withColumn("analysis_date", lit(datetime.now())) \
            .withColumn("created_at", current_timestamp())

        print(f"Analyzed {performance.count()} products")

        # Show top performers
        print("\nTop 10 Products by Revenue:")
        performance.orderBy(desc("total_revenue")).show(10, truncate=False)

        return performance

    def identify_trends(self, performance_df):
        """Identify trending products"""
        # Products with high sales velocity
        trending = performance_df \
            .filter(col("revenue_per_day") > 1000) \
            .withColumn("trend_type", lit("rising_star")) \
            .select("product_id", "product_name", "category",
                   "total_revenue", "revenue_per_day", "trend_type")

        return trending

    def save_results(self, performance_df):
        """Save analysis results"""
        print("Saving product performance results...")

        performance_df.write \
            .format("mongodb") \
            .mode("overwrite") \
            .option("database", config.MONGODB_DATABASE) \
            .option("collection", "product_performance") \
            .save()

        print("Results saved successfully")

    def run_analysis(self):
        """Run complete product performance analysis"""
        print("=== Starting Product Performance Analysis ===")
        start_time = datetime.now()

        performance = self.analyze_product_performance(days=30)
        trends = self.identify_trends(performance)
        self.save_results(performance)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"=== Analysis Completed in {elapsed:.2f} seconds ===")

if __name__ == "__main__":
    analyzer = ProductPerformanceAnalyzer()
    analyzer.run_analysis()
```

### 3.7 Sales Trend Analysis

Create `batch-processor/sales_trends.py`:

```python
"""
Sales Trend Analysis - Daily, Weekly, Monthly
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import config

class SalesTrendAnalyzer:
    def __init__(self):
        self.spark = self._create_spark_session()

    def _create_spark_session(self):
        spark = SparkSession.builder \
            .appName("Sales Trend Analysis") \
            .config("spark.jars.packages",
                    "org.postgresql:postgresql:42.6.0,"
                    "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
            .config("spark.mongodb.write.connection.uri", config.MONGODB_URI) \
            .getOrCreate()

        spark.sparkContext.setLogLevel("WARN")
        return spark

    def analyze_daily_trends(self, days=90):
        """Analyze daily sales trends"""
        print(f"Analyzing daily trends for last {days} days...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Read sales data
        sales = self.spark.read \
            .format("jdbc") \
            .option("url", config.POSTGRES_URL) \
            .option("dbtable",
                   f"""(SELECT timestamp, total_amount
                        FROM transactions
                        WHERE timestamp >= '{start_date}'
                          AND timestamp < '{end_date}') as daily_sales""") \
            .option("user", config.POSTGRES_USER) \
            .option("password", config.POSTGRES_PASSWORD) \
            .load()

        # Aggregate by day
        daily = sales \
            .withColumn("date", date_format("timestamp", "yyyy-MM-dd")) \
            .groupBy("date") \
            .agg(
                count("*").alias("transaction_count"),
                sum("total_amount").alias("total_revenue"),
                avg("total_amount").alias("avg_transaction_value")
            ) \
            .orderBy("date")

        # Calculate moving averages (7-day)
        windowSpec = Window.orderBy("date").rowsBetween(-6, 0)
        daily = daily \
            .withColumn("revenue_7day_ma",
                       avg("total_revenue").over(windowSpec)) \
            .withColumn("transactions_7day_ma",
                       avg("transaction_count").over(windowSpec))

        # Calculate day-over-day growth
        windowSpec = Window.orderBy("date")
        daily = daily \
            .withColumn("prev_day_revenue",
                       lag("total_revenue", 1).over(windowSpec)) \
            .withColumn("revenue_growth_pct",
                       ((col("total_revenue") - col("prev_day_revenue")) /
                        col("prev_day_revenue") * 100))

        daily = daily.withColumn("trend_type", lit("daily"))

        return daily

    def analyze_weekly_trends(self, weeks=12):
        """Analyze weekly sales trends"""
        print(f"Analyzing weekly trends for last {weeks} weeks...")

        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)

        sales = self.spark.read \
            .format("jdbc") \
            .option("url", config.POSTGRES_URL) \
            .option("dbtable",
                   f"""(SELECT timestamp, total_amount
                        FROM transactions
                        WHERE timestamp >= '{start_date}'
                          AND timestamp < '{end_date}') as weekly_sales""") \
            .option("user", config.POSTGRES_USER) \
            .option("password", config.POSTGRES_PASSWORD) \
            .load()

        # Aggregate by week
        weekly = sales \
            .withColumn("year", year("timestamp")) \
            .withColumn("week", weekofyear("timestamp")) \
            .groupBy("year", "week") \
            .agg(
                count("*").alias("transaction_count"),
                sum("total_amount").alias("total_revenue"),
                avg("total_amount").alias("avg_transaction_value")
            ) \
            .orderBy("year", "week")

        weekly = weekly.withColumn("trend_type", lit("weekly"))

        return weekly

    def analyze_monthly_trends(self, months=12):
        """Analyze monthly sales trends"""
        print(f"Analyzing monthly trends for last {months} months...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)

        sales = self.spark.read \
            .format("jdbc") \
            .option("url", config.POSTGRES_URL) \
            .option("dbtable",
                   f"""(SELECT timestamp, total_amount
                        FROM transactions
                        WHERE timestamp >= '{start_date}'
                          AND timestamp < '{end_date}') as monthly_sales""") \
            .option("user", config.POSTGRES_USER) \
            .option("password", config.POSTGRES_PASSWORD) \
            .load()

        # Aggregate by month
        monthly = sales \
            .withColumn("year", year("timestamp")) \
            .withColumn("month", month("timestamp")) \
            .groupBy("year", "month") \
            .agg(
                count("*").alias("transaction_count"),
                sum("total_amount").alias("total_revenue"),
                avg("total_amount").alias("avg_transaction_value")
            ) \
            .orderBy("year", "month")

        monthly = monthly.withColumn("trend_type", lit("monthly"))

        return monthly

    def save_results(self, trends_df):
        """Save trend analysis results"""
        print("Saving trend analysis results...")

        trends_df.write \
            .format("mongodb") \
            .mode("append") \
            .option("database", config.MONGODB_DATABASE) \
            .option("collection", "sales_trends") \
            .save()

        print("Results saved successfully")

    def run_analysis(self):
        """Run complete trend analysis"""
        print("=== Starting Sales Trend Analysis ===")
        start_time = datetime.now()

        # Analyze all trend types
        daily = self.analyze_daily_trends(90)
        weekly = self.analyze_weekly_trends(12)
        monthly = self.analyze_monthly_trends(12)

        # Save results
        self.save_results(daily)
        self.save_results(weekly)
        self.save_results(monthly)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"=== Trend Analysis Completed in {elapsed:.2f} seconds ===")

if __name__ == "__main__":
    analyzer = SalesTrendAnalyzer()
    analyzer.run_analysis()
```

### 3.8 Scheduled Batch Jobs

Create `batch-processor/scheduler.py`:

```python
"""
Job scheduler for batch processing
"""

import schedule
import time
from datetime import datetime
from etl_pipeline import ETLPipeline
from rfm_analysis import RFMAnalysis
from product_performance import ProductPerformanceAnalyzer
from sales_trends import SalesTrendAnalyzer

def run_daily_etl():
    """Run daily ETL job"""
    print(f"\n{'='*60}")
    print(f"Starting Daily ETL Job at {datetime.now()}")
    print('='*60)

    try:
        etl = ETLPipeline()
        etl.run_daily_etl()
        print("✓ Daily ETL completed successfully")
    except Exception as e:
        print(f"✗ Daily ETL failed: {e}")

def run_customer_segmentation():
    """Run customer segmentation job"""
    print(f"\n{'='*60}")
    print(f"Starting Customer Segmentation Job at {datetime.now()}")
    print('='*60)

    try:
        rfm = RFMAnalysis()
        rfm.run_analysis()
        print("✓ Customer segmentation completed successfully")
    except Exception as e:
        print(f"✗ Customer segmentation failed: {e}")

def run_product_analysis():
    """Run product performance analysis job"""
    print(f"\n{'='*60}")
    print(f"Starting Product Analysis Job at {datetime.now()}")
    print('='*60)

    try:
        analyzer = ProductPerformanceAnalyzer()
        analyzer.run_analysis()
        print("✓ Product analysis completed successfully")
    except Exception as e:
        print(f"✗ Product analysis failed: {e}")

def run_sales_trends():
    """Run sales trend analysis job"""
    print(f"\n{'='*60}")
    print(f"Starting Sales Trend Analysis Job at {datetime.now()}")
    print('='*60)

    try:
        analyzer = SalesTrendAnalyzer()
        analyzer.run_analysis()
        print("✓ Sales trend analysis completed successfully")
    except Exception as e:
        print(f"✗ Sales trend analysis failed: {e}")

# Schedule jobs
schedule.every().day.at("02:00").do(run_daily_etl)
schedule.every().day.at("03:00").do(run_customer_segmentation)
schedule.every().day.at("04:00").do(run_product_analysis)
schedule.every().hour.do(run_sales_trends)

if __name__ == "__main__":
    print("Batch Job Scheduler Started")
    print("Scheduled Jobs:")
    print("  - Daily ETL: 02:00 AM")
    print("  - Customer Segmentation: 03:00 AM")
    print("  - Product Analysis: 04:00 AM")
    print("  - Sales Trends: Every hour")
    print("\nPress Ctrl+C to stop\n")

    # Run initial jobs
    print("Running initial batch jobs...")
    run_daily_etl()
    run_customer_segmentation()
    run_product_analysis()
    run_sales_trends()

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)
```

### 3.9 Deliverables Checklist

- [ ] MongoDB data warehouse running
- [ ] Star schema design documented
- [ ] ETL pipeline implemented
- [ ] Customer segmentation (RFM analysis) running daily
- [ ] Product performance analysis running daily
- [ ] Sales trend analysis (daily, weekly, monthly)
- [ ] Scheduled batch job scripts
- [ ] Data warehouse accessible via Mongo Express (localhost:8082)

**Testing Commands:**
```bash
# Start MongoDB
docker-compose -f docker/docker-compose.mongodb.yml up -d

# Run ETL pipeline
docker exec globalmart-spark-master spark-submit \
    --master spark://spark-master:7077 \
    --packages org.postgresql:postgresql:42.6.0,org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
    /app/etl_pipeline.py

# Run RFM analysis
docker exec globalmart-spark-master spark-submit \
    --master spark://spark-master:7077 \
    --packages org.postgresql:postgresql:42.6.0,org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
    /app/rfm_analysis.py

# View data warehouse
open http://localhost:8082
```

---

**Continue to [IMPLEMENTATION_GUIDE_PART3.md](IMPLEMENTATION_GUIDE_PART3.md) for:**
- Component 4: Visualization and API Layer
- Component 5: Infrastructure and Deployment
- Testing & Validation
- Troubleshooting
