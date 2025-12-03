"""
Configuration for running batch processing from LOCAL machine
Use localhost instead of container hostnames
"""

# Spark Configuration
SPARK_APP_NAME = "GlobalMart Batch Processor"
SPARK_MASTER = "local[*]"  # Run locally instead of cluster

# PostgreSQL Configuration (LOCAL - use localhost)
POSTGRES_HOST = "localhost"
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

# MongoDB Configuration (LOCAL - use localhost)
MONGODB_HOST = "localhost"
MONGODB_PORT = 27017
MONGODB_USER = "globalmart"
MONGODB_PASSWORD = "globalmart123"
MONGODB_DB = "globalmart_dw"
MONGODB_URI = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}?authSource=admin"

# Data Warehouse Collections
DW_COLLECTIONS = {
    'fact_sales': 'fact_sales',
    'fact_sessions': 'fact_sessions',
    'dim_customers': 'dim_customers',
    'dim_products': 'dim_products',
    'dim_time': 'dim_time',
    'customer_segments': 'customer_segments',
    'product_performance': 'product_performance',
    'sales_trends': 'sales_trends'
}

# RFM Analysis Parameters
RFM_QUANTILES = 5

# Batch Job Schedule
BATCH_SCHEDULE = {
    'etl': '0 */6 * * *',
    'rfm': '0 2 * * *',
    'product_perf': '0 3 * * *',
    'sales_trends': '0 4 * * *'
}

# Data Lake / Raw Data Storage
DATA_LAKE_PATH = "/data/raw"
PROCESSED_DATA_PATH = "/data/processed"
