"""
Simple test to verify Kafka streaming works
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Create Spark session
spark = SparkSession.builder \
    .appName("Test Streaming") \
    .master("local[2]") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
            "org.postgresql:postgresql:42.6.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=" * 60)
print("Testing Kafka Connection")
print("=" * 60)

# Define transaction schema
transaction_schema = StructType([
    StructField("transaction_id", StringType()),
    StructField("user_id", StringType()),
    StructField("timestamp", TimestampType()),
    StructField("total_amount", DoubleType()),
    StructField("payment_method", StringType()),
    StructField("products", ArrayType(StructType([
        StructField("product_id", StringType()),
        StructField("name", StringType()),
        StructField("category", StringType()),
        StructField("price", DoubleType()),
        StructField("quantity", IntegerType())
    ])))
])

# Read from Kafka
try:
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "globalmart-kafka:9092") \
        .option("subscribe", "transactions") \
        .option("startingOffsets", "latest") \
        .load()

    print("✓ Connected to Kafka successfully")

    # Parse JSON
    transactions = kafka_df.select(
        from_json(col("value").cast("string"), transaction_schema).alias("data")
    ).select("data.*")

    # Simple aggregation by category
    sales_by_category = transactions \
        .select(
            col("timestamp"),
            explode("products").alias("product")
        ) \
        .select(
            col("timestamp"),
            col("product.category").alias("category"),
            (col("product.price") * col("product.quantity")).alias("amount")
        ) \
        .withWatermark("timestamp", "1 minute") \
        .groupBy(
            window("timestamp", "1 minute"),
            "category"
        ) \
        .agg(
            sum("amount").alias("total_amount"),
            count("*").alias("transaction_count")
        )

    print("✓ Created aggregation query")

    # Write to PostgreSQL
    def write_to_postgres(batch_df, batch_id):
        if batch_df.count() > 0:
            print(f"\n--- Batch {batch_id} ---")
            print(f"Records: {batch_df.count()}")
            batch_df.show(truncate=False)

            batch_df.select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("category"),
                lit("Unknown").alias("country"),  # Placeholder
                col("total_amount"),
                col("transaction_count"),
                (col("total_amount") / col("transaction_count")).alias("avg_transaction_value"),
                current_timestamp().alias("created_at")
            ).write \
                .format("jdbc") \
                .option("url", "jdbc:postgresql://globalmart-postgres:5432/globalmart") \
                .option("dbtable", "sales_metrics") \
                .option("user", "globalmart") \
                .option("password", "globalmart123") \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()

            print(f"✓ Batch {batch_id} written to PostgreSQL")

    print("\nStarting stream processing...")
    print("Waiting for data from Kafka...")
    print("(Press Ctrl+C to stop)")
    print("=" * 60)

    # Start streaming
    query = sales_by_category.writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("update") \
        .option("checkpointLocation", "/data/checkpoints/test") \
        .start()

    query.awaitTermination()

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    spark.stop()
