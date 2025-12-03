"""
Product Performance Analysis
Analyzes product sales, trends, and performance metrics
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import config

def create_spark_session():
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName("GlobalMart Product Performance") \
        .config("spark.jars.packages",
                "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .config("spark.mongodb.read.connection.uri", config.MONGODB_URI) \
        .config("spark.mongodb.write.connection.uri", config.MONGODB_URI) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark

def analyze_product_performance(spark):
    """Analyze product performance metrics"""
    print("Analyzing product performance...")

    # Read fact_sales from MongoDB
    fact_sales = spark.read \
        .format("mongodb") \
        .option("database", config.MONGODB_DB) \
        .option("collection", config.DW_COLLECTIONS['fact_sales']) \
        .load()

    if fact_sales.count() == 0:
        print("WARNING: No sales data found! Run ETL pipeline first.")
        return None

    # Aggregate by category
    product_perf = fact_sales.groupBy("category").agg(
        sum("total_amount").alias("total_revenue"),
        sum("transaction_count").alias("total_transactions"),
        avg("avg_transaction_value").alias("avg_order_value"),
        count("*").alias("data_points")
    )

    # Calculate performance metrics
    total_revenue = product_perf.agg(sum("total_revenue")).collect()[0][0]

    product_perf = product_perf.withColumn(
        "revenue_share",
        (col("total_revenue") / lit(total_revenue) * 100)
    )

    # Add performance rating
    product_perf = product_perf.withColumn(
        "performance_rating",
        when(col("revenue_share") >= 20, "Excellent")
        .when(col("revenue_share") >= 10, "Good")
        .when(col("revenue_share") >= 5, "Average")
        .otherwise("Below Average")
    )

    # Add ranking
    windowSpec = Window.orderBy(col("total_revenue").desc())
    product_perf = product_perf.withColumn("rank", row_number().over(windowSpec))

    # Add metadata
    product_perf = product_perf.withColumn("analysis_date", lit(datetime.now()))

    print(f"Analyzed performance for {product_perf.count()} product categories")
    return product_perf.orderBy("rank")

def analyze_top_products(spark):
    """Identify top performing products"""
    print("Identifying top products...")

    fact_sales = spark.read \
        .format("mongodb") \
        .option("database", config.MONGODB_DB) \
        .option("collection", config.DW_COLLECTIONS['fact_sales']) \
        .load()

    if fact_sales.count() == 0:
        return None

    # Get top 10 categories by revenue
    top_categories = fact_sales.groupBy("category").agg(
        sum("total_amount").alias("revenue")
    ).orderBy(col("revenue").desc()).limit(10)

    return top_categories

def analyze_underperforming_products(spark):
    """Identify underperforming products that need attention"""
    print("Identifying underperforming products...")

    fact_sales = spark.read \
        .format("mongodb") \
        .option("database", config.MONGODB_DB) \
        .option("collection", config.DW_COLLECTIONS['fact_sales']) \
        .load()

    if fact_sales.count() == 0:
        return None

    # Get bottom 10 categories by revenue
    low_performers = fact_sales.groupBy("category").agg(
        sum("total_amount").alias("revenue"),
        sum("transaction_count").alias("transactions")
    ).orderBy(col("revenue")).limit(10)

    return low_performers

def save_to_mongodb(df, collection_name):
    """Save DataFrame to MongoDB"""
    if df is None:
        print("No data to save")
        return

    print(f"Saving to MongoDB collection: {collection_name}...")

    df.write \
        .format("mongodb") \
        .mode("overwrite") \
        .option("database", config.MONGODB_DB) \
        .option("collection", collection_name) \
        .save()

    print(f"Successfully saved {df.count()} records")

def run_product_performance_analysis():
    """Main product performance analysis process"""
    print("=" * 60)
    print("Starting Product Performance Analysis")
    print("=" * 60)

    spark = create_spark_session()

    try:
        # Run analyses
        product_performance = analyze_product_performance(spark)

        if product_performance is None:
            print("Skipping analysis due to no data")
            return

        top_products = analyze_top_products(spark)
        underperforming = analyze_underperforming_products(spark)

        # Show results
        print("\nProduct Performance Summary:")
        product_performance.show(truncate=False)

        print("\nTop 10 Products:")
        if top_products:
            top_products.show()

        print("\nUnderperforming Products:")
        if underperforming:
            underperforming.show()

        # Save to MongoDB
        save_to_mongodb(product_performance, config.DW_COLLECTIONS['product_performance'])

        print("=" * 60)
        print("Product Performance Analysis completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR in Product Performance Analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

if __name__ == "__main__":
    run_product_performance_analysis()
