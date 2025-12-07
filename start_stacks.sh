#!/usr/bin/env bash
# Start all GlobalMart stacks: Kafka, Postgres, MongoDB, API/Grafana, Spark, Producer.
# Also starts the metrics collector if available.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="${PROJECT_DIR}/docker"
VENV_PYTHON="${PROJECT_DIR}/.venv/bin/python"

cd "$DOCKER_DIR"

echo "Starting all stacks (project: globalmart)..."
sudo docker compose -p globalmart \
  -f docker-compose.kafka.yml \
  -f docker-compose.postgres.yml \
  -f docker-compose.mongodb.yml \
  -f docker-compose.api.yml \
  -f docker-compose.spark.yml \
  -f docker-compose.producer.yml up -d --remove-orphans

# Start metrics collector on host if available and not running
METRICS_COLLECTOR="${PROJECT_DIR}/scripts/metrics_collector.py"
if [ -f "$METRICS_COLLECTOR" ]; then
  if pgrep -f "metrics_collector.py" >/dev/null 2>&1; then
    echo "Metrics collector already running."
  else
    if [ -x "$VENV_PYTHON" ]; then
      echo "Starting metrics collector..."
      METRICS_INTERVAL=5 nohup "$VENV_PYTHON" "$METRICS_COLLECTOR" > /tmp/metrics_collector.log 2>&1 &
    else
      echo "Python venv not found; skip starting metrics collector."
    fi
  fi
fi

echo "All stacks started."
