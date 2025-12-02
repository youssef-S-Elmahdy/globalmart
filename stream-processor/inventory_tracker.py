"""
Real-time inventory tracking and low-stock alerts
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
LOW_STOCK_THRESHOLD = 10

def create_spark_session():
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName("Inventory Tracker") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.postgresql:postgresql:42.6.0") \
        .config("spark.jars.excludes",
                "org.apache.hadoop:hadoop-client-api,"
                "org.apache.hadoop:hadoop-client-runtime") \
        .config("spark.sql.streaming.checkpointLocation",
                f"{CHECKPOINT_LOCATION}/inventory") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark

def track_inventory(spark):
    """Track inventory changes from transactions"""

    # Transaction schema
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

    # Read transactions from Kafka
    transactions = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPICS['transactions']) \
        .option("startingOffsets", "latest") \
        .load()

    # Parse and explode products
    inventory_updates = transactions \
        .select(from_json(col("value").cast("string"), transaction_schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", to_timestamp(col("timestamp"))) \
        .select(
            col("transaction_id"),
            col("timestamp"),
            explode(col("products")).alias("product")
        ) \
        .select(
            col("transaction_id"),
            col("timestamp"),
            col("product.product_id"),
            col("product.quantity")
        )

    # Aggregate inventory changes
    inventory_summary = inventory_updates \
        .withWatermark("timestamp", "1 minute") \
        .groupBy(
            window(col("timestamp"), "1 minute"),
            col("product_id")
        ) \
        .agg(
            sum("quantity").alias("sold_quantity")
        )

    # Detect low stock
    def check_low_stock(batch_df, batch_id):
        """Check for low stock and write alerts"""
        # This is simplified - in production, you'd join with actual inventory data
        low_stock = batch_df.filter(col("sold_quantity") > 50)  # Example threshold

        if not low_stock.isEmpty():
            # Write to low_stock_alerts table
            low_stock.select(
                col("product_id"),
                lit("Product Name").alias("product_name"),  # Would join with product catalog
                lit("Category").alias("category"),
                (lit(100) - col("sold_quantity")).alias("current_stock"),
                lit(LOW_STOCK_THRESHOLD).alias("threshold")
            ).write \
                .jdbc(
                    url=POSTGRES_URL,
                    table="low_stock_alerts",
                    mode="append",
                    properties=POSTGRES_PROPERTIES
                )

    # Write stream
    query = inventory_summary \
        .writeStream \
        .foreachBatch(check_low_stock) \
        .outputMode("append") \
        .start()

    # Console output
    console_query = inventory_updates \
        .writeStream \
        .format("console") \
        .outputMode("append") \
        .option("truncate", False) \
        .start()

    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    spark = create_spark_session()
    track_inventory(spark)