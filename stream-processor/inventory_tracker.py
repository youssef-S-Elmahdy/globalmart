"""
Real-time inventory tracking and low-stock alerts
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import psycopg2

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
# Tune thresholds low enough to trigger alerts quickly in short runs
LOW_STOCK_THRESHOLD = 65
INITIAL_STOCK_LEVEL = 80  # Lower start so alerts fire sooner

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

def initialize_inventory_if_needed():
    """Initialize inventory_status table with products if empty"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    cur = conn.cursor()

    # Check if inventory_status is empty
    cur.execute("SELECT COUNT(*) FROM inventory_status")
    count = cur.fetchone()[0]

    if count == 0:
        print("Initializing inventory_status table...")
        # Get unique products from recent transactions
        cur.execute("""
            INSERT INTO inventory_status (product_id, product_name, category, current_stock, reserved_stock, available_stock)
            SELECT DISTINCT
                unnest(ARRAY['PROD001', 'PROD002', 'PROD003', 'PROD004', 'PROD005',
                             'PROD006', 'PROD007', 'PROD008', 'PROD009', 'PROD010']) as product_id,
                'Product ' || unnest(ARRAY['PROD001', 'PROD002', 'PROD003', 'PROD004', 'PROD005',
                                           'PROD006', 'PROD007', 'PROD008', 'PROD009', 'PROD010']) as product_name,
                CASE
                    WHEN random() < 0.3 THEN 'Electronics'
                    WHEN random() < 0.6 THEN 'Clothing'
                    ELSE 'Home & Garden'
                END as category,
                %s as current_stock,
                0 as reserved_stock,
                %s as available_stock
            ON CONFLICT (product_id) DO NOTHING
        """, (INITIAL_STOCK_LEVEL, INITIAL_STOCK_LEVEL))

        conn.commit()
        print(f"Initialized inventory with {INITIAL_STOCK_LEVEL} units per product")

    # Seed initial low-stock alerts for any products already below threshold
    cur.execute("""
        INSERT INTO low_stock_alerts (product_id, product_name, category, current_stock, threshold, status)
        SELECT product_id, product_name, category, available_stock, %s, 'active'
        FROM inventory_status
        WHERE available_stock < %s
          AND NOT EXISTS (
              SELECT 1 FROM low_stock_alerts l WHERE l.product_id = inventory_status.product_id
          )
    """, (LOW_STOCK_THRESHOLD, LOW_STOCK_THRESHOLD))
    conn.commit()

    cur.close()
    conn.close()

def track_inventory(spark):
    """Track inventory changes from transactions"""

    # Initialize inventory if needed
    initialize_inventory_if_needed()

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

    # Aggregate inventory changes by product
    inventory_summary = inventory_updates \
        .withWatermark("timestamp", "1 minute") \
        .groupBy(
            window(col("timestamp"), "1 minute"),
            col("product_id")
        ) \
        .agg(
            sum("quantity").alias("sold_quantity"),
            count("*").alias("transaction_count")
        )

    def update_inventory_and_alerts(batch_df, batch_id):
        """Update inventory and generate alerts"""
        if batch_df.count() == 0:
            return

        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        # Process each product's inventory change
        for row in batch_df.collect():
            product_id = row['product_id']
            sold_qty = row['sold_quantity']

            # Update inventory_status
            cur.execute("""
                UPDATE inventory_status
                SET current_stock = GREATEST(current_stock - %s, 0),
                    available_stock = GREATEST(current_stock - %s - reserved_stock, 0),
                    last_updated = NOW()
                WHERE product_id = %s
                RETURNING product_id, product_name, category, available_stock
            """, (sold_qty, sold_qty, product_id))

            result = cur.fetchone()
            if result:
                prod_id, prod_name, category, available = result

                # Check if we need to generate low stock alert
                if available < LOW_STOCK_THRESHOLD:
                    cur.execute("""
                        INSERT INTO low_stock_alerts
                        (product_id, product_name, category, current_stock, threshold, status)
                        VALUES (%s, %s, %s, %s, %s, 'active')
                    """, (prod_id, prod_name, category, available, LOW_STOCK_THRESHOLD))

                    print(f"Batch {batch_id}: LOW STOCK ALERT - {prod_name} ({prod_id}): {available} units remaining")
            else:
                # Product not in inventory_status, add it
                cur.execute("""
                    INSERT INTO inventory_status
                    (product_id, product_name, category, current_stock, reserved_stock, available_stock)
                    VALUES (%s, %s, %s, %s, 0, %s)
                    ON CONFLICT (product_id) DO NOTHING
                """, (product_id, f"Product {product_id}", "General",
                      INITIAL_STOCK_LEVEL - sold_qty, INITIAL_STOCK_LEVEL - sold_qty))

        conn.commit()
        cur.close()
        conn.close()

        print(f"Batch {batch_id}: Updated inventory for {batch_df.count()} products")

    # Write stream
    query = inventory_summary \
        .writeStream \
        .foreachBatch(update_inventory_and_alerts) \
        .outputMode("update") \
        .start()

    # Console output for monitoring
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
