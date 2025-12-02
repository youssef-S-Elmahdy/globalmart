"""
Real-time transaction monitoring with anomaly detection
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Configuration
KAFKA_BOOTSTRAP_SERVERS = "globalmart-kafka:9092"
KAFKA_TOPICS = {
    'transactions': 'transactions',
    'product_views': 'product_views',
    'cart_events': 'cart_events'
}
CHECKPOINT_LOCATION = "/data/checkpoints"
POSTGRES_URL = "jdbc:postgresql://globalmart-postgres:5432/globalmart"
POSTGRES_PROPERTIES = {
    "user": "globalmart",
    "password": "globalmart123",
    "driver": "org.postgresql.Driver"
}
WINDOW_DURATION = "1 minute"
SLIDING_DURATION = "30 seconds"
ANOMALY_THRESHOLDS = {
    'high_value_transaction': 5000.00,
    'unusual_quantity': 10,
    'rapid_transactions': 5
}

def create_spark_session():
    """Create Spark session with Kafka integration"""
    spark = SparkSession.builder \
        .appName("Transaction Monitor") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.postgresql:postgresql:42.6.0") \
        .config("spark.jars.excludes",
                "org.apache.hadoop:hadoop-client-api,"
                "org.apache.hadoop:hadoop-client-runtime") \
        .config("spark.sql.streaming.checkpointLocation",
                f"{CHECKPOINT_LOCATION}/transactions") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark

def detect_anomalies(df):
    """Detect anomalies in transactions"""

    # High value transactions
    high_value = df.filter(col("total_amount") > ANOMALY_THRESHOLDS['high_value_transaction']) \
        .withColumn("anomaly_type", lit("high_value")) \
        .withColumn("anomaly_score", col("total_amount") / ANOMALY_THRESHOLDS['high_value_transaction']) \
        .withColumn("description", concat(lit("High value transaction: $"), col("total_amount"))) \
        .select(
            col("transaction_id"),
            col("user_id"),
            col("total_amount").alias("amount"),
            col("anomaly_score"),
            col("anomaly_type"),
            col("timestamp").alias("detected_at"),
            col("description")
        )

    # Unusual quantity per product
    unusual_quantity = df \
        .select(
            col("transaction_id"),
            col("user_id"),
            col("timestamp"),
            col("total_amount"),
            explode(col("products")).alias("product")
        ) \
        .filter(col("product.quantity") > ANOMALY_THRESHOLDS['unusual_quantity']) \
        .withColumn("anomaly_type", lit("unusual_quantity")) \
        .withColumn("anomaly_score", col("product.quantity") / ANOMALY_THRESHOLDS['unusual_quantity']) \
        .withColumn("description",
                   concat(lit("Unusual quantity: "), col("product.quantity"), lit(" items"))) \
        .select(
            col("transaction_id"),
            col("user_id"),
            col("total_amount").alias("amount"),
            col("anomaly_score"),
            col("anomaly_type"),
            col("timestamp").alias("detected_at"),
            col("description")
        )

    # Combine anomalies
    anomalies = high_value.unionAll(unusual_quantity)

    return anomalies

def write_to_postgres(batch_df, batch_id):
    """Write batch to PostgreSQL"""
    batch_df.write \
        .jdbc(
            url=POSTGRES_URL,
            table="transaction_anomalies",
            mode="append",
            properties=POSTGRES_PROPERTIES
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
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPICS['transactions']) \
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
            window(col("timestamp"), WINDOW_DURATION, SLIDING_DURATION),
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
            # Cast category to string to avoid JDBC "void" type issues
            lit("").cast(StringType()).alias("category"),
            col("country"),
            col("total_amount"),
            col("transaction_count"),
            col("avg_transaction_value")
        )

    # Write metrics to PostgreSQL
    def write_metrics(batch_df, batch_id):
        batch_df.write \
            .jdbc(
                url=POSTGRES_URL,
                table="sales_metrics",
                mode="append",
                properties=POSTGRES_PROPERTIES
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
