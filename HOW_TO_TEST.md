# 🚀 How to Test Part 3 - Simple Guide

## The 3-Terminal Method (Recommended)

You need **3 separate terminal windows** running simultaneously.

---

## 📍 Terminal 1: Data Generator

```bash
# Navigate to project
cd /Users/s7s/Desktop/Uni/Fall\ 25/Big\ Data/Project/globalmart/data-generator

# Activate virtual environment
source ../../venv/bin/activate

# Start producing events to Kafka
python producer.py
```

**Keep this running!** You should see:
```
=== Statistics (after 10.0s) ===
Transactions: 1000 (100.0/s)
Product Views: 3000 (300.0/s)
Cart Events: 1000 (100.0/s)
```

---

## 📍 Terminal 2: Stream Processors

```bash
# Navigate to stream processor
cd /Users/s7s/Desktop/Uni/Fall\ 25/Big\ Data/Project/globalmart/stream-processor

# Copy files to Spark container (first time only)
cd ..
docker cp stream-processor/ globalmart-spark-master:/app/
cd stream-processor

# Start all 3 stream processors
./run_all.sh
```

**Keep this running!** You should see:
```
Started transaction monitor
Started inventory tracker
Started session analyzer
```

---

## 📍 Terminal 3: Batch Processing (YOUR PART)

**Wait 5 minutes** after starting terminals 1 and 2, then:

```bash
# Navigate to batch processor
cd /Users/s7s/Desktop/Uni/Fall\ 25/Big\ Data/Project/globalmart/batch-processor

# Run all batch jobs (runs inside Docker)
./run_batch_jobs.sh
```

This script will:
1. Copy your batch processor files to Spark container
2. Execute all jobs inside the Spark container using spark-submit
3. Jobs will use Docker network hostnames (globalmart-postgres, globalmart-mongodb)

You should see each job complete:
```
✓ ETL Pipeline completed successfully
✓ RFM Analysis completed successfully
✓ Product Performance Analysis completed successfully
✓ Sales Trends Analysis completed successfully
```

---

## ✅ Verify It Worked

### Method 1: Web UI (Easiest)
1. Open http://localhost:8082
2. Login: `admin` / `admin123`
3. Click `globalmart_dw` database
4. You should see 6 collections with data

### Method 2: Command Line
```bash
docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123

use globalmart_dw
db.getCollectionNames()
db.fact_sales.countDocuments()
db.customer_segments.find().pretty()
exit
```

---

## 🎯 Quick Visual Check

Open these URLs to see everything working:

| What | URL | What to Check |
|------|-----|---------------|
| **Kafka Topics** | http://localhost:8080 | Should see messages flowing in 3 topics |
| **Spark Jobs** | http://localhost:8081 | Should see 3 running applications |
| **MongoDB Data** | http://localhost:8082 | Should see 6 collections with data |

---

## ⚡ Fastest Test Method

If you want to automate most of it:

```bash
cd /Users/s7s/Desktop/Uni/Fall\ 25/Big\ Data/Project/globalmart

# This will guide you through step by step
./scripts/quick_test.sh
```

---

## 🐛 Common Issues

### "No data in PostgreSQL"
- Make sure Terminal 1 (data generator) is running
- Make sure Terminal 2 (stream processors) is running
- **Wait at least 5 minutes** for data to accumulate

### "Can't connect to Spark"
```bash
# Check Spark is running
docker ps | grep spark

# Restart if needed
docker-compose -f docker/docker-compose.spark.yml restart
```

### "MongoDB connection failed"
```bash
# Check MongoDB
docker ps | grep mongodb

# Restart if needed
docker-compose -f docker/docker-compose.mongodb.yml restart
```

---

## 📊 What Each Component Does

```
Terminal 1 (Data Generator)
    ↓ sends events to
Kafka Topics
    ↓ consumed by
Terminal 2 (Stream Processors)
    ↓ writes real-time metrics to
PostgreSQL
    ↓ batch processed by
Terminal 3 (Batch Jobs) ← YOUR WORK
    ↓ loads data warehouse to
MongoDB
```

---

## 🎬 Demo Sequence

1. Show all 3 terminals running side-by-side
2. Open Kafka UI - show messages flowing
3. Show PostgreSQL data: `SELECT COUNT(*) FROM sales_metrics;`
4. Run batch jobs in Terminal 3
5. Open Mongo Express - show collections with data
6. Run sample queries to show insights

---

## 📝 Sample Queries to Impress

After batch jobs complete, run these in MongoDB:

```javascript
// Top products by revenue
db.product_performance.find().sort({rank: 1}).limit(5)

// Customer segments
db.customer_segments.find({}, {segment_name: 1, monetary: 1})

// Recent trends
db.sales_trends.find({period_type: "daily"}).sort({period: -1}).limit(7)

// Total revenue by country
db.fact_sales.aggregate([
  {$group: {_id: "$country", total: {$sum: "$total_amount"}}},
  {$sort: {total: -1}}
])
```

---

**That's it! Follow these 3 terminals and you're done.** 🎉

For more details, see [TESTING_GUIDE.md](TESTING_GUIDE.md)
