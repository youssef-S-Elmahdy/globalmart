#!/bin/bash

# Monitor Kafka topics for GlobalMart

KAFKA_CONTAINER="globalmart-kafka"

echo "Monitoring Kafka topics..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=== GlobalMart Kafka Monitoring ==="
    echo "Time: $(date)"
    echo ""

    # Get message counts for each topic
    echo "Topic: transactions"
    docker exec $KAFKA_CONTAINER kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 \
        --topic transactions \
        --time -1 | awk -F ":" '{sum += $3} END {print "  Messages: " sum}'

    echo ""
    echo "Topic: product_views"
    docker exec $KAFKA_CONTAINER kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 \
        --topic product_views \
        --time -1 | awk -F ":" '{sum += $3} END {print "  Messages: " sum}'

    echo ""
    echo "Topic: cart_events"
    docker exec $KAFKA_CONTAINER kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 \
        --topic cart_events \
        --time -1 | awk -F ":" '{sum += $3} END {print "  Messages: " sum}'

    echo ""
    echo "Consumer Groups:"
    docker exec $KAFKA_CONTAINER kafka-consumer-groups \
        --bootstrap-server localhost:9092 \
        --list

    sleep 5
done