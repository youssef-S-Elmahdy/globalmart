"""
Stream processing configuration
"""

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = "globalmart-kafka:9092"
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