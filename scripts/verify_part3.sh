#!/bin/bash

# Verification script for Part 3: Batch Processing
# Checks if all components are properly set up

echo "========================================="
echo "Part 3 Verification Script"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check status
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        return 1
    fi
}

# 1. Check Docker containers
echo "1. Checking Docker containers..."
docker ps | grep -q globalmart-mongodb
check_status "MongoDB is running"

docker ps | grep -q globalmart-postgres
check_status "PostgreSQL is running"

docker ps | grep -q globalmart-spark-master
check_status "Spark Master is running"

docker ps | grep -q globalmart-kafka
check_status "Kafka is running"
echo ""

# 2. Check batch-processor files
echo "2. Checking batch-processor files..."
[ -f "batch-processor/config.py" ]
check_status "config.py exists"

[ -f "batch-processor/etl_pipeline.py" ]
check_status "etl_pipeline.py exists"

[ -f "batch-processor/rfm_analysis.py" ]
check_status "rfm_analysis.py exists"

[ -f "batch-processor/product_performance.py" ]
check_status "product_performance.py exists"

[ -f "batch-processor/sales_trends.py" ]
check_status "sales_trends.py exists"

[ -f "batch-processor/scheduler.py" ]
check_status "scheduler.py exists"
echo ""

# 3. Check MongoDB connectivity
echo "3. Checking MongoDB connectivity..."
docker exec globalmart-mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1
check_status "MongoDB is accessible"
echo ""

# 4. Check PostgreSQL connectivity
echo "4. Checking PostgreSQL connectivity..."
docker exec globalmart-postgres psql -U globalmart -d globalmart -c "SELECT 1;" > /dev/null 2>&1
check_status "PostgreSQL is accessible"
echo ""

# 5. Check if data exists in PostgreSQL
echo "5. Checking data in PostgreSQL..."
SALES_COUNT=$(docker exec globalmart-postgres psql -U globalmart -d globalmart -t -c "SELECT COUNT(*) FROM sales_metrics;" 2>/dev/null | tr -d ' ')

if [ -z "$SALES_COUNT" ]; then
    echo -e "${YELLOW}⚠${NC} Could not check sales_metrics table"
elif [ "$SALES_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Found $SALES_COUNT records in sales_metrics"
else
    echo -e "${YELLOW}⚠${NC} No data in sales_metrics (run data generator + stream processors first)"
fi
echo ""

# 6. Check Python dependencies
echo "6. Checking Python dependencies..."
python3 -c "import pyspark" 2>/dev/null
check_status "PySpark is installed"

python3 -c "import pymongo" 2>/dev/null
check_status "PyMongo is installed"

python3 -c "import schedule" 2>/dev/null
check_status "Schedule is installed"
echo ""

# 7. Check documentation
echo "7. Checking documentation..."
[ -f "config/data_warehouse_schema.md" ]
check_status "Data warehouse schema documented"

[ -f "batch-processor/README.md" ]
check_status "Batch processor README exists"

[ -f "PART3_SUMMARY.md" ]
check_status "Part 3 summary exists"
echo ""

# Summary
echo "========================================="
echo "Verification Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. If PostgreSQL has no data, start:"
echo "   cd data-generator && python producer.py"
echo "   cd stream-processor && ./run_all.sh"
echo ""
echo "2. Wait 5-10 minutes for data to accumulate"
echo ""
echo "3. Run batch jobs:"
echo "   cd batch-processor && ./run_all_jobs.sh"
echo ""
echo "4. Check MongoDB data:"
echo "   Open http://localhost:8082 (admin/admin123)"
echo ""
