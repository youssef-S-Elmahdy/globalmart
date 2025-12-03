"""
ETL Pipeline for GlobalMart Data Warehouse
Extracts data from PostgreSQL and loads into MongoDB in star schema format
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import config

def create_spark_session():
    """Create Spark session with PostgreSQL and MongoDB connectors"""
    spark = SparkSession.builder \
        .appName("GlobalMart ETL Pipeline") \
        .config("spark.jars.packages",
                "org.postgresql:postgresql:42.6.0,"
                "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .config("spark.mongodb.write.connection.uri", config.MONGODB_URI) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark

def extract_sales_metrics(spark):
    """Extract sales data from PostgreSQL"""
    print("Extracting sales metrics from PostgreSQL...")

    sales_df = spark.read \
        .jdbc(
            url=config.POSTGRES_URL,
            table="sales_metrics",
            properties=config.POSTGRES_PROPERTIES
        )

    print(f"Extracted {sales_df.count()} sales metric records")
    return sales_df

def extract_transaction_anomalies(spark):
    """Extract anomaly data"""
    print("Extracting transaction anomalies...")

    anomalies_df = spark.read \
        .jdbc(
            url=config.POSTGRES_URL,
            table="transaction_anomalies",
            properties=config.POSTGRES_PROPERTIES
        )

    print(f"Extracted {anomalies_df.count()} anomaly records")
    return anomalies_df

def extract_session_metrics(spark):
    """Extract session data"""
    print("Extracting session metrics...")

    sessions_df = spark.read \
        .jdbc(
            url=config.POSTGRES_URL,
            table="session_metrics",
            properties=config.POSTGRES_PROPERTIES
        )

    print(f"Extracted {sessions_df.count()} session records")
    return sessions_df

def transform_to_fact_sales(sales_df):
    """Transform sales metrics to fact table format"""
    print("Transforming to fact_sales...")

    fact_sales = sales_df.select(
        col("window_start").alias("date_time"),
        date_format(col("window_start"), "yyyyMMdd").cast("int").alias("date_id"),
        col("category"),
        col("country"),
        col("total_amount"),
        col("transaction_count"),
        col("avg_transaction_value"),
        current_timestamp().alias("loaded_at")
    )

    return fact_sales

def transform_to_fact_sessions(sessions_df):
    """Transform session metrics to fact table"""
    print("Transforming to fact_sessions...")

    fact_sessions = sessions_df.select(
        col("session_id"),
        col("user_id"),
        col("start_time"),
        col("end_time"),
        col("duration_seconds"),
        col("page_views"),
        col("cart_adds"),
        col("cart_removes"),
        col("purchase_completed"),
        col("abandoned"),
        col("total_amount"),
        date_format(col("start_time"), "yyyyMMdd").cast("int").alias("date_id"),
        current_timestamp().alias("loaded_at")
    )

    return fact_sessions

def create_dim_time(spark, start_date, end_date):
    """Create time dimension table"""
    print("Creating time dimension...")

    # Generate date range
    from datetime import datetime, timedelta

    dates = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current <= end:
        dates.append({
            'date_id': int(current.strftime("%Y%m%d")),
            'date': current.strftime("%Y-%m-%d"),
            'year': current.year,
            'quarter': (current.month - 1) // 3 + 1,
            'month': current.month,
            'month_name': current.strftime("%B"),
            'week': current.isocalendar()[1],
            'day': current.day,
            'day_of_week': current.weekday() + 1,
            'day_name': current.strftime("%A"),
            'is_weekend': current.weekday() >= 5
        })
        current += timedelta(days=1)

    dim_time = spark.createDataFrame(dates)
    return dim_time

def load_to_mongodb(df, collection_name):
    """Load DataFrame to MongoDB collection"""
    print(f"Loading {df.count()} records to {collection_name}...")

    df.write \
        .format("mongodb") \
        .mode("append") \
        .option("database", config.MONGODB_DB) \
        .option("collection", collection_name) \
        .save()

    print(f"Successfully loaded to {collection_name}")

def run_etl():
    """Main ETL process"""
    print("=" * 60)
    print("Starting GlobalMart ETL Pipeline")
    print("=" * 60)

    # Create Spark session
    spark = create_spark_session()

    try:
        # Extract data from PostgreSQL
        sales_df = extract_sales_metrics(spark)
        sessions_df = extract_session_metrics(spark)

        if sales_df.count() == 0:
            print("WARNING: No sales data found in PostgreSQL!")
            print("Make sure the data generator and stream processors are running.")

        if sessions_df.count() == 0:
            print("WARNING: No session data found in PostgreSQL!")

        # Transform to fact tables
        fact_sales = transform_to_fact_sales(sales_df)
        fact_sessions = transform_to_fact_sessions(sessions_df)

        # Create dimension tables
        today = datetime.now()
        start_date = (today - timedelta(days=365)).strftime("%Y-%m-%d")  # Last year
        end_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")     # Next month
        dim_time = create_dim_time(spark, start_date, end_date)

        # Load to MongoDB
        load_to_mongodb(fact_sales, config.DW_COLLECTIONS['fact_sales'])
        load_to_mongodb(fact_sessions, config.DW_COLLECTIONS['fact_sessions'])
        load_to_mongodb(dim_time, config.DW_COLLECTIONS['dim_time'])

        print("=" * 60)
        print("ETL Pipeline completed successfully!")
        print("=" * 60)

        # Show summary statistics
        print("\nSummary:")
        print(f"  Fact Sales Records: {fact_sales.count()}")
        print(f"  Fact Session Records: {fact_sessions.count()}")
        print(f"  Dim Time Records: {dim_time.count()}")

    except Exception as e:
        print(f"ERROR in ETL Pipeline: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

if __name__ == "__main__":
    run_etl()
