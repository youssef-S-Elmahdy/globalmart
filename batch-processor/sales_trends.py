"""
Sales Trends Analysis
Analyzes sales trends over time (daily, weekly, monthly)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import config

def create_spark_session():
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName("GlobalMart Sales Trends") \
        .config("spark.jars.packages",
                "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .config("spark.mongodb.read.connection.uri", config.MONGODB_URI) \
        .config("spark.mongodb.write.connection.uri", config.MONGODB_URI) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark

def analyze_daily_trends(spark):
    """Analyze daily sales trends"""
    print("Analyzing daily sales trends...")

    # Read fact_sales from MongoDB
    fact_sales = spark.read \
        .format("mongodb") \
        .option("database", config.MONGODB_DB) \
        .option("collection", config.DW_COLLECTIONS['fact_sales']) \
        .load()

    if fact_sales.count() == 0:
        print("WARNING: No sales data found! Run ETL pipeline first.")
        return None

    # Aggregate by date
    daily_trends = fact_sales.groupBy(
        date_format("date_time", "yyyy-MM-dd").alias("date")
    ).agg(
        sum("total_amount").alias("daily_revenue"),
        sum("transaction_count").alias("daily_transactions"),
        avg("avg_transaction_value").alias("avg_order_value")
    ).orderBy("date")

    # Calculate growth rates
    windowSpec = Window.orderBy("date")

    daily_trends = daily_trends.withColumn(
        "prev_revenue",
        lag("daily_revenue", 1).over(windowSpec)
    ).withColumn(
        "revenue_growth_rate",
        when(col("prev_revenue").isNotNull(),
             ((col("daily_revenue") - col("prev_revenue")) / col("prev_revenue") * 100))
        .otherwise(0)
    ).withColumn("trend_type", lit("daily"))

    print(f"Calculated trends for {daily_trends.count()} days")
    return daily_trends

def analyze_weekly_trends(spark):
    """Analyze weekly sales trends"""
    print("Analyzing weekly sales trends...")

    fact_sales = spark.read \
        .format("mongodb") \
        .option("database", config.MONGODB_DB) \
        .option("collection", config.DW_COLLECTIONS['fact_sales']) \
        .load()

    if fact_sales.count() == 0:
        return None

    # Aggregate by week
    weekly_trends = fact_sales.groupBy(
        year("date_time").alias("year"),
        weekofyear("date_time").alias("week")
    ).agg(
        sum("total_amount").alias("weekly_revenue"),
        sum("transaction_count").alias("weekly_transactions"),
        avg("avg_transaction_value").alias("avg_order_value")
    ).orderBy("year", "week")

    # Calculate growth rates
    windowSpec = Window.orderBy("year", "week")

    weekly_trends = weekly_trends.withColumn(
        "prev_revenue",
        lag("weekly_revenue", 1).over(windowSpec)
    ).withColumn(
        "revenue_growth_rate",
        when(col("prev_revenue").isNotNull(),
             ((col("weekly_revenue") - col("prev_revenue")) / col("prev_revenue") * 100))
        .otherwise(0)
    ).withColumn("trend_type", lit("weekly"))

    print(f"Calculated trends for {weekly_trends.count()} weeks")
    return weekly_trends

def analyze_monthly_trends(spark):
    """Analyze monthly sales trends"""
    print("Analyzing monthly sales trends...")

    fact_sales = spark.read \
        .format("mongodb") \
        .option("database", config.MONGODB_DB) \
        .option("collection", config.DW_COLLECTIONS['fact_sales']) \
        .load()

    if fact_sales.count() == 0:
        return None

    # Aggregate by month
    monthly_trends = fact_sales.groupBy(
        year("date_time").alias("year"),
        month("date_time").alias("month")
    ).agg(
        sum("total_amount").alias("monthly_revenue"),
        sum("transaction_count").alias("monthly_transactions"),
        avg("avg_transaction_value").alias("avg_order_value")
    ).orderBy("year", "month")

    # Calculate growth rates
    windowSpec = Window.orderBy("year", "month")

    monthly_trends = monthly_trends.withColumn(
        "prev_revenue",
        lag("monthly_revenue", 1).over(windowSpec)
    ).withColumn(
        "revenue_growth_rate",
        when(col("prev_revenue").isNotNull(),
             ((col("monthly_revenue") - col("prev_revenue")) / col("prev_revenue") * 100))
        .otherwise(0)
    ).withColumn("trend_type", lit("monthly"))

    print(f"Calculated trends for {monthly_trends.count()} months")
    return monthly_trends

def analyze_country_trends(spark):
    """Analyze sales trends by country"""
    print("Analyzing country-wise trends...")

    fact_sales = spark.read \
        .format("mongodb") \
        .option("database", config.MONGODB_DB) \
        .option("collection", config.DW_COLLECTIONS['fact_sales']) \
        .load()

    if fact_sales.count() == 0:
        return None

    # Aggregate by country and date
    country_trends = fact_sales.groupBy(
        "country",
        date_format("date_time", "yyyy-MM-dd").alias("date")
    ).agg(
        sum("total_amount").alias("daily_revenue"),
        sum("transaction_count").alias("daily_transactions")
    ).orderBy("country", "date")

    print(f"Calculated country trends for {country_trends.count()} records")
    return country_trends

def combine_trends(daily, weekly, monthly):
    """Combine all trends into a unified collection"""
    print("Combining all trends...")

    # Normalize schemas for combined storage
    if daily and weekly and monthly:
        combined = daily.select(
            lit("daily").alias("period_type"),
            col("date").alias("period"),
            col("daily_revenue").alias("revenue"),
            col("daily_transactions").alias("transactions"),
            col("revenue_growth_rate")
        ).union(
            weekly.select(
                lit("weekly").alias("period_type"),
                concat(col("year"), lit("-W"), col("week")).alias("period"),
                col("weekly_revenue").alias("revenue"),
                col("weekly_transactions").alias("transactions"),
                col("revenue_growth_rate")
            )
        ).union(
            monthly.select(
                lit("monthly").alias("period_type"),
                concat(col("year"), lit("-"), col("month")).alias("period"),
                col("monthly_revenue").alias("revenue"),
                col("monthly_transactions").alias("transactions"),
                col("revenue_growth_rate")
            )
        )

        return combined.withColumn("analysis_date", lit(datetime.now()))

    return None

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

def run_sales_trends_analysis():
    """Main sales trends analysis process"""
    print("=" * 60)
    print("Starting Sales Trends Analysis")
    print("=" * 60)

    spark = create_spark_session()

    try:
        # Run trend analyses
        daily_trends = analyze_daily_trends(spark)
        weekly_trends = analyze_weekly_trends(spark)
        monthly_trends = analyze_monthly_trends(spark)
        country_trends = analyze_country_trends(spark)

        if daily_trends is None:
            print("Skipping analysis due to no data")
            return

        # Show results
        print("\nDaily Trends (Last 7 days):")
        daily_trends.orderBy(col("date").desc()).limit(7).show()

        print("\nWeekly Trends:")
        if weekly_trends:
            weekly_trends.show()

        print("\nMonthly Trends:")
        if monthly_trends:
            monthly_trends.show()

        # Combine all trends
        combined_trends = combine_trends(daily_trends, weekly_trends, monthly_trends)

        # Save to MongoDB
        save_to_mongodb(combined_trends, config.DW_COLLECTIONS['sales_trends'])

        print("=" * 60)
        print("Sales Trends Analysis completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR in Sales Trends Analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

if __name__ == "__main__":
    run_sales_trends_analysis()
