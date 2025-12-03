#!/bin/bash

# Run all stream processing jobs INSIDE the Spark container
# This script should be executed INSIDE the container

SPARK_MASTER="spark://spark-master:7077"

echo "Starting stream processing jobs..."
echo "Running inside Spark container"

# Run transaction monitor in background
/opt/spark/bin/spark-submit \
    --master $SPARK_MASTER \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    transaction_monitor.py > /tmp/transaction_monitor.log 2>&1 &

echo "Started transaction monitor (PID: $!)"

# Run inventory tracker in background
/opt/spark/bin/spark-submit \
    --master $SPARK_MASTER \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    inventory_tracker.py > /tmp/inventory_tracker.log 2>&1 &

echo "Started inventory tracker (PID: $!)"

# Run session analyzer in background
/opt/spark/bin/spark-submit \
    --master $SPARK_MASTER \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    session_analyzer.py > /tmp/session_analyzer.log 2>&1 &

echo "Started session analyzer (PID: $!)"

echo ""
echo "All stream processing jobs started!"
echo "Monitor at http://localhost:8081"
echo ""
echo "View logs:"
echo "  docker exec globalmart-spark-master tail -f /tmp/transaction_monitor.log"
echo "  docker exec globalmart-spark-master tail -f /tmp/inventory_tracker.log"
echo "  docker exec globalmart-spark-master tail -f /tmp/session_analyzer.log"
