#!/bin/bash

# Wrapper script to run batch jobs inside Spark Docker container
# Run this from your LOCAL machine

echo "========================================="
echo "Running Batch Jobs in Docker"
echo "========================================="
echo ""

# Step 1: Copy latest files to Spark container
echo "📦 Copying batch processor files to Spark container..."
cd /Users/s7s/Desktop/Uni/Fall\ 25/Big\ Data/Project/globalmart
docker cp batch-processor/ globalmart-spark-master:/app/
echo "✓ Files copied"
echo ""

# Step 2: Make script executable inside container
echo "🔧 Setting permissions..."
docker exec globalmart-spark-master chmod +x /app/batch-processor/run_all_jobs_docker.sh
echo "✓ Permissions set"
echo ""

# Step 3: Execute batch jobs inside container
echo "🚀 Starting batch jobs inside Spark container..."
echo ""
docker exec -w /app/batch-processor globalmart-spark-master ./run_all_jobs_docker.sh

echo ""
echo "========================================="
echo "Done!"
echo "========================================="
