#!/bin/bash

# Run all batch processing jobs
# Usage: ./run_all_jobs.sh

echo "========================================="
echo "GlobalMart Batch Processing Jobs"
echo "========================================="
echo ""

# Check if in correct directory
if [ ! -f "etl_pipeline.py" ]; then
    echo "ERROR: Must be run from batch-processor directory"
    exit 1
fi

# Function to run job with error handling
run_job() {
    local job_name=$1
    local script=$2

    echo "-----------------------------------"
    echo "Running: $job_name"
    echo "-----------------------------------"

    python $script

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
