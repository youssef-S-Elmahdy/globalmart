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

SESSION_TIMEOUT_MINUTES = 2  # shorter window so metrics emit quickly
CART_ABANDONMENT_THRESHOLD_MINUTES = 1  # 1 minute - detect carts with items but no purchase

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

    # Write session metrics with upsert to handle duplicates
    def write_sessions(batch_df, batch_id):
        if batch_df.count() == 0:
            return

        # Drop duplicate session ids in the micro-batch
        unique_batch = batch_df.dropDuplicates(["session_id"])

        # Use a temp table and upsert to avoid duplicate key errors
        temp_table = f"temp_sessions_{batch_id}"

        # Write to temp table
        unique_batch.write \
            .jdbc(
                url=POSTGRES_URL,
                table=temp_table,
                mode="overwrite",
                properties=POSTGRES_PROPERTIES
            )

        # Upsert from temp table to main table
        import psycopg2
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        cur.execute(f"""
            INSERT INTO session_metrics
            SELECT * FROM {temp_table}
            ON CONFLICT (session_id) DO UPDATE SET
                end_time = EXCLUDED.end_time,
                duration_seconds = EXCLUDED.duration_seconds,
                page_views = EXCLUDED.page_views,
                cart_adds = EXCLUDED.cart_adds,
                cart_removes = EXCLUDED.cart_removes
        """)

        # Write cart abandonment records for sessions that qualify
        cur.execute(f"""
            INSERT INTO cart_abandonment (session_id, user_id, products_in_cart, cart_value, abandonment_time, time_in_cart_minutes)
            SELECT
                session_id,
                user_id,
                cart_adds,
                0,
                end_time,
                duration_seconds / 60
            FROM {temp_table}
            WHERE cart_adds > 0 AND duration_seconds > {CART_ABANDONMENT_THRESHOLD_MINUTES * 60}
            ON CONFLICT DO NOTHING
        """)

        cur.execute(f"DROP TABLE {temp_table}")
        conn.commit()
        cur.close()
        conn.close()

    session_query = session_metrics \
        .writeStream \
        .foreachBatch(write_sessions) \
        .outputMode("update") \
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
