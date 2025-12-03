#!/bin/bash

# Quick test script for Part 3
# This script will guide you through testing step by step

echo "========================================"
echo "Part 3 Quick Test Script"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Verify setup
echo "Step 1: Verifying setup..."
./scripts/verify_part3.sh | grep -q "✓ MongoDB is running"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Setup verified${NC}"
else
    echo "ERROR: Setup verification failed. Run ./scripts/verify_part3.sh for details"
    exit 1
fi
echo ""

# Step 2: Copy files to Spark container
echo "Step 2: Copying files to Spark container..."
docker cp data-generator/ globalmart-spark-master:/app/ 2>/dev/null
docker cp stream-processor/ globalmart-spark-master:/app/ 2>/dev/null
docker cp batch-processor/ globalmart-spark-master:/app/ 2>/dev/null
echo -e "${GREEN}✓ Files copied to Spark container${NC}"
echo ""

# Step 3: Check if data generator is running
echo "Step 3: Checking data flow..."
echo -e "${YELLOW}You need to start the data generator in a separate terminal:${NC}"
echo "  cd data-generator"
echo "  source ../../venv/bin/activate"
echo "  python producer.py"
echo ""
read -p "Press Enter when data generator is running..."

# Step 4: Check if stream processors are running
echo ""
echo "Step 4: Stream processors..."
echo -e "${YELLOW}You need to start stream processors in another terminal:${NC}"
echo "  cd stream-processor"
echo "  ./run_all.sh"
echo ""
read -p "Press Enter when stream processors are running..."

# Step 5: Wait for data
echo ""
echo "Step 5: Waiting for data to accumulate..."
echo "Checking PostgreSQL for data..."

for i in {1..30}; do
    COUNT=$(docker exec globalmart-postgres psql -U globalmart -d globalmart -t -c "SELECT COUNT(*) FROM sales_metrics;" 2>/dev/null | tr -d ' ')

    if [ ! -z "$COUNT" ] && [ "$COUNT" -gt 10 ]; then
        echo -e "${GREEN}✓ Found $COUNT records in PostgreSQL${NC}"
        break
    fi

    echo "  Waiting... ($i/30) - Found: ${COUNT:-0} records (need >10)"
    sleep 10
done

if [ -z "$COUNT" ] || [ "$COUNT" -lt 10 ]; then
    echo -e "${YELLOW}⚠ Only found ${COUNT:-0} records. Recommend waiting longer, but continuing...${NC}"
fi
echo ""

# Step 6: Run batch jobs
echo "Step 6: Running batch processing jobs..."
echo "This will:"
echo "  1. Extract data from PostgreSQL"
echo "  2. Transform to star schema"
echo "  3. Load to MongoDB"
echo "  4. Run RFM analysis"
echo "  5. Analyze product performance"
echo "  6. Calculate sales trends"
echo ""
read -p "Press Enter to run batch jobs..."

cd batch-processor
./run_all_jobs.sh
cd ..

echo ""
echo "========================================"
echo "Testing Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Verify MongoDB data:"
echo "   Open http://localhost:8082 (admin/admin123)"
echo ""
echo "2. Or query via CLI:"
echo "   docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123"
echo "   use globalmart_dw"
echo "   db.fact_sales.find().limit(5)"
echo ""
echo "3. View full guide:"
echo "   cat TESTING_GUIDE.md"
echo ""
