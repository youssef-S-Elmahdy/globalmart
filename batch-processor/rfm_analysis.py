"""
RFM (Recency, Frequency, Monetary) Analysis for Customer Segmentation
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import config

def create_spark_session():
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName("GlobalMart RFM Analysis") \
        .config("spark.jars.packages",
                "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .config("spark.mongodb.read.connection.uri", config.MONGODB_URI) \
        .config("spark.mongodb.write.connection.uri", config.MONGODB_URI) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark

def calculate_rfm_scores(spark):
    """Calculate RFM scores for each customer"""
    print("Calculating RFM scores...")

    # Read fact_sales from MongoDB
    fact_sales = spark.read \
        .format("mongodb") \
        .option("database", config.MONGODB_DB) \
        .option("collection", config.DW_COLLECTIONS['fact_sales']) \
        .load()

    if fact_sales.count() == 0:
        print("WARNING: No sales data found! Run ETL pipeline first.")
        return None

    # Calculate reference date (today)
    reference_date = datetime.now()

    # Calculate RFM metrics per customer
    # Note: We need to aggregate by a customer identifier
    # Since we don't have customer IDs in sales_metrics, we'll use country as a proxy
    # In a real scenario, you'd join with transaction data that has user_ids

    rfm = fact_sales.groupBy("country").agg(
        # Recency: days since last purchase (we'll use window_start as proxy)
        datediff(lit(reference_date), max("date_time")).alias("recency"),
        # Frequency: number of transactions
        sum("transaction_count").alias("frequency"),
        # Monetary: total amount spent
        sum("total_amount").alias("monetary")
    )

    # Calculate RFM scores using quantiles (1-5, where 5 is best)
    # Lower recency is better (more recent), so we reverse it
    rfm_scored = rfm.withColumn(
        "r_score",
        ntile(config.RFM_QUANTILES).over(Window.orderBy(col("recency").desc()))
    ).withColumn(
        "f_score",
        ntile(config.RFM_QUANTILES).over(Window.orderBy(col("frequency")))
    ).withColumn(
        "m_score",
        ntile(config.RFM_QUANTILES).over(Window.orderBy(col("monetary")))
    )

    # Create RFM segment string (e.g., "555" for Champions)
    rfm_scored = rfm_scored.withColumn(
        "rfm_segment",
        concat(
            col("r_score").cast("string"),
            col("f_score").cast("string"),
            col("m_score").cast("string")
        )
    )

    # Map to segment names
    # Create a UDF for segment mapping
    def get_segment_name(rfm_code):
        # Simplified mapping
        r, f, m = int(rfm_code[0]), int(rfm_code[1]), int(rfm_code[2])

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 4 and f >= 3:
            return "Loyal Customers"
        elif r >= 3 and f >= 1 and m >= 3:
            return "Potential Loyalists"
        elif r >= 4 and f <= 2:
            return "New Customers"
        elif r >= 3 and f <= 2:
            return "Promising"
        elif r <= 2 and f >= 4:
            return "Cannot Lose Them"
        elif r <= 2 and f >= 2:
            return "At Risk"
        elif r <= 2:
            return "Hibernating"
        else:
            return "Need Attention"

    from pyspark.sql.types import StringType
    segment_udf = udf(get_segment_name, StringType())

    rfm_scored = rfm_scored.withColumn(
        "segment_name",
        segment_udf(col("rfm_segment"))
    )

    # Add metadata
    rfm_scored = rfm_scored.withColumn("analysis_date", lit(datetime.now()))

    print(f"Calculated RFM scores for {rfm_scored.count()} customers")
    return rfm_scored

def generate_segment_summary(rfm_df):
    """Generate summary statistics per segment"""
    print("Generating segment summary...")

    segment_summary = rfm_df.groupBy("segment_name").agg(
        count("*").alias("customer_count"),
        avg("recency").alias("avg_recency"),
        avg("frequency").alias("avg_frequency"),
        avg("monetary").alias("avg_monetary"),
        sum("monetary").alias("total_revenue")
    ).orderBy(col("total_revenue").desc())

    return segment_summary

def save_to_mongodb(df, collection_name):
    """Save DataFrame to MongoDB"""
    print(f"Saving to MongoDB collection: {collection_name}...")

    df.write \
        .format("mongodb") \
        .mode("overwrite") \
        .option("database", config.MONGODB_DB) \
        .option("collection", collection_name) \
        .save()

    print(f"Successfully saved {df.count()} records")

def run_rfm_analysis():
    """Main RFM analysis process"""
    print("=" * 60)
    print("Starting RFM Analysis")
    print("=" * 60)

    spark = create_spark_session()

    try:
        # Calculate RFM scores
        rfm_scores = calculate_rfm_scores(spark)

        if rfm_scores is None:
            print("Skipping RFM analysis due to no data")
            return

        # Generate segment summary
        segment_summary = generate_segment_summary(rfm_scores)

        # Show results
        print("\nRFM Scores Sample:")
        rfm_scores.select("country", "recency", "frequency", "monetary",
                          "r_score", "f_score", "m_score", "segment_name").show()

        print("\nSegment Summary:")
        segment_summary.show()

        # Save to MongoDB
        save_to_mongodb(rfm_scores, config.DW_COLLECTIONS['customer_segments'])

        print("=" * 60)
        print("RFM Analysis completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR in RFM Analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

if __name__ == "__main__":
    run_rfm_analysis()
