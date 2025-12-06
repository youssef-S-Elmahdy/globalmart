#!/bin/bash

# Run all batch processing jobs INSIDE Spark Docker container
# Usage: ./run_all_jobs_docker.sh

SPARK_MASTER="spark://spark-master:7077"

echo "========================================="
echo "GlobalMart Batch Processing Jobs"
echo "Running inside Spark container"
echo "========================================="
echo ""

# Function to run job with spark-submit
run_job() {
    local job_name=$1
    local script=$2

    echo "-----------------------------------"
    echo "Running: $job_name"
    echo "-----------------------------------"

    /opt/spark/bin/spark-submit \
        --master $SPARK_MASTER \
        --packages org.postgresql:postgresql:42.6.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
        $script

    if [ $? -eq 0 ]; then
        echo "✓ $job_name completed successfully"
    else
        echo "✗ $job_name failed!"
        return 1
    fi
    echo ""
}

# Run all jobs in sequence
run_job "ETL Pipeline" "etl_pipeline.py"
run_job "RFM Analysis" "rfm_analysis.py"
run_job "Product Performance Analysis" "product_performance.py"
run_job "Sales Trends Analysis" "sales_trends.py"

echo "========================================="
echo "All batch jobs completed!"
echo "========================================="
