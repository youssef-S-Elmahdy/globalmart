#!/bin/bash

# Run all stream processing jobs

SPARK_MASTER="spark://spark-master:7077"

echo "Starting stream processing jobs..."

# Run transaction monitor
docker exec -w /app/stream-processor globalmart-spark-master /opt/spark/bin/spark-submit \
    --master $SPARK_MASTER \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    transaction_monitor.py &

echo "Started transaction monitor"

# Run inventory tracker
docker exec -w /app/stream-processor globalmart-spark-master /opt/spark/bin/spark-submit \
    --master $SPARK_MASTER \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    inventory_tracker.py &

echo "Started inventory tracker"

# Run session analyzer
docker exec -w /app/stream-processor globalmart-spark-master /opt/spark/bin/spark-submit \
    --master $SPARK_MASTER \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
    session_analyzer.py &

echo "Started session analyzer"

echo "All stream processing jobs started!"
echo "Monitor at http://localhost:8081"