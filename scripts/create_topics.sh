#!/bin/bash

# Create Kafka topics for GlobalMart

KAFKA_CONTAINER="globalmart-kafka"

echo "Creating Kafka topics..."

# Transaction events topic
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic transactions \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000

# Product view events topic
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic product_views \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000

# Cart events topic
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic cart_events \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000

# System metrics topic
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic system_metrics \
  --partitions 1 \
  --replication-factor 1 \
  --config retention.ms=86400000

echo "Listing all topics:"
docker exec $KAFKA_CONTAINER kafka-topics --list --bootstrap-server localhost:9092

echo "Topics created successfully!"
