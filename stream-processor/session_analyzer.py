"""
Session analysis and cart abandonment detection
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.functions import approx_count_distinct
from pyspark.sql.types import *
from pyspark.sql.window import Window

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
SESSION_TIMEOUT_MINUTES = 2  # shorter window so metrics emit quickly
CART_ABANDONMENT_THRESHOLD_MINUTES = 15

def create_spark_session():
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName("Session Analyzer") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.postgresql:postgresql:42.6.0") \
        .config("spark.jars.excludes",
                "org.apache.hadoop:hadoop-client-api,"
                "org.apache.hadoop:hadoop-client-runtime") \
        .config("spark.sql.streaming.checkpointLocation",
                f"{CHECKPOINT_LOCATION}/sessions") \
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
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPICS['cart_events']) \
        .option("startingOffsets", "latest") \
        .load()

    # Parse cart events
    cart_df = cart_events \
        .select(from_json(col("value").cast("string"), cart_schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", to_timestamp(col("timestamp")))

    # Aggregate session metrics
    session_metrics = cart_df \
        .withWatermark("timestamp", "5 minutes") \
        .groupBy(
            col("session_id"),
            col("user_id"),
            window(col("timestamp"), f"{SESSION_TIMEOUT_MINUTES} minutes")
        ) \
        .agg(
            min("timestamp").alias("start_time"),
            max("timestamp").alias("end_time"),
            count("*").alias("total_events"),
            sum(when(col("action") == "add", 1).otherwise(0)).alias("cart_adds"),
            sum(when(col("action") == "remove", 1).otherwise(0)).alias("cart_removes"),
            approx_count_distinct("product_id").alias("unique_products")
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
            (col("duration_seconds") > CART_ABANDONMENT_THRESHOLD_MINUTES * 60)
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
        # Drop duplicate session ids in the micro-batch to avoid PK conflicts on replays
        batch_df.dropDuplicates(["session_id"]).write \
            .jdbc(
                url=POSTGRES_URL,
                table="session_metrics",
                mode="append",
                properties=POSTGRES_PROPERTIES
            )

    session_query = session_metrics \
        .writeStream \
        .foreachBatch(write_sessions) \
        .outputMode("update") \
        .start()

    # Write abandonment events
    def write_abandonment(batch_df, batch_id):
        batch_df.write \
            .jdbc(
                url=POSTGRES_URL,
                table="cart_abandonment",
                mode="append",
                properties=POSTGRES_PROPERTIES
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
