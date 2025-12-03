#!/bin/bash

# Wrapper to start stream processors in Docker from LOCAL machine
# Run this from your local terminal

echo "========================================="
echo "Starting Stream Processors in Docker"
echo "========================================="
echo ""

# Step 1: Copy files to container
echo "📦 Copying stream processor files to Spark container..."
cd /Users/s7s/Desktop/Uni/Fall\ 25/Big\ Data/Project/globalmart
docker cp stream-processor/ globalmart-spark-master:/app/
echo "✓ Files copied"
echo ""

# Step 2: Make scripts executable
echo "🔧 Setting permissions..."
docker exec globalmart-spark-master chmod +x /app/stream-processor/run_all_docker.sh
echo "✓ Permissions set"
echo ""

# Step 3: Execute inside container
echo "🚀 Starting stream processors..."
echo ""
docker exec -w /app/stream-processor globalmart-spark-master ./run_all_docker.sh

echo ""
echo "========================================="
echo "Stream processors started!"
echo "========================================="
echo ""
echo "Monitor progress:"
echo "  Spark UI: http://localhost:8081"
echo "  Kafka UI: http://localhost:8080"
echo ""
echo "Check logs:"
echo "  docker exec globalmart-spark-master tail -f /tmp/transaction_monitor.log"
echo ""
echo "Wait 2-3 minutes, then check PostgreSQL:"
echo "  docker exec globalmart-postgres psql -U globalmart -d globalmart -c \"SELECT COUNT(*) FROM sales_metrics;\""
echo ""
