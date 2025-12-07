#!/usr/bin/env bash
# Stop all GlobalMart stacks and background collectors.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="${PROJECT_DIR}/docker"

# Stop metrics collector if running
if pgrep -f "metrics_collector.py" >/dev/null 2>&1; then
  echo "Stopping metrics collector..."
  pkill -f "metrics_collector.py" || true
fi

cd "$DOCKER_DIR"

echo "Stopping all stacks (project: globalmart)..."
sudo docker compose -p globalmart \
  -f docker-compose.kafka.yml \
  -f docker-compose.postgres.yml \
  -f docker-compose.mongodb.yml \
  -f docker-compose.api.yml \
  -f docker-compose.spark.yml \
  -f docker-compose.producer.yml down --remove-orphans

echo "All stacks stopped."
