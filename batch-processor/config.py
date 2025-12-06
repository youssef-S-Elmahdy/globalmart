"""
Configuration for GlobalMart Batch Processing
"""

# Spark Configuration
SPARK_APP_NAME = "GlobalMart Batch Processor"
SPARK_MASTER = "spark://spark-master:7077"

# PostgreSQL Configuration (Source for real-time data)
POSTGRES_HOST = "globalmart-postgres"
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

# MongoDB Configuration (Data Warehouse)
MONGODB_HOST = "globalmart-mongodb"
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
RFM_QUANTILES = 5  # Divide customers into 5 segments per metric
RFM_SEGMENTS = {
    '555': 'Champions',
    '554': 'Champions',
    '545': 'Champions',
    '544': 'Champions',
    '455': 'Loyal Customers',
    '454': 'Loyal Customers',
    '445': 'Loyal Customers',
    '444': 'Loyal Customers',
    '355': 'Potential Loyalists',
    '354': 'Potential Loyalists',
    '345': 'Potential Loyalists',
    '344': 'Potential Loyalists',
    '255': 'New Customers',
    '254': 'New Customers',
    '245': 'New Customers',
    '244': 'New Customers',
    '155': 'Promising',
    '154': 'Promising',
    '145': 'Promising',
    '144': 'Promising',
    '555': 'Champions',
    '454': 'Loyal Customers',
    '344': 'Potential Loyalists',
    '244': 'New Customers',
    '144': 'Promising',
    '543': 'Recent Customers',
    '533': 'Recent Customers',
    '443': 'Need Attention',
    '434': 'Need Attention',
    '343': 'About to Sleep',
    '334': 'About to Sleep',
    '244': 'At Risk',
    '234': 'At Risk',
    '143': 'Cannot Lose Them',
    '134': 'Cannot Lose Them',
    '133': 'Hibernating',
    '132': 'Hibernating',
    '131': 'Hibernating',
    '123': 'Lost',
    '122': 'Lost',
    '121': 'Lost',
    '111': 'Lost'
}

# Batch Job Schedule
BATCH_SCHEDULE = {
    'etl': '0 */6 * * *',      # Every 6 hours
    'rfm': '0 2 * * *',         # Daily at 2 AM
    'product_perf': '0 3 * * *', # Daily at 3 AM
    'sales_trends': '0 4 * * *'  # Daily at 4 AM
}

# Data Lake / Raw Data Storage
DATA_LAKE_PATH = "/data/raw"
PROCESSED_DATA_PATH = "/data/processed"
