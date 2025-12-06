#!/bin/bash
# Build and start all GlobalMart Docker services

set -e

echo "========================================="
echo "Building GlobalMart Docker Services"
echo "========================================="
echo ""

cd "$(dirname "$0")"

# Build producer image
echo "[1/2] Building producer image..."
sudo docker-compose -f docker-compose.producer.yml build --no-cache

# Build API image
echo "[2/2] Building API image..."
sudo docker-compose -f docker-compose.api.yml build --no-cache

echo ""
echo "✓ All images built successfully"
echo ""

# Start all services
echo "========================================="
echo "Starting All Services"
echo "========================================="
echo ""

# Start infrastructure
for compose_file in docker-compose.*.yml; do
    if [ -f "$compose_file" ]; then
        echo "Starting $compose_file..."
        sudo docker-compose -f "$compose_file" up -d
    fi
done

echo ""
echo "Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "Container Status:"
sudo docker ps --format "table {{.Names}}\t{{.Status}}" | grep globalmart

echo ""
echo "========================================="
echo "✓ All Services Started"
echo "========================================="
echo ""
echo "Access Points:"
echo "  - Grafana:         http://localhost:3001 (admin/admin123)"
echo "  - Web Explorer:    http://localhost:8000/explorer"
echo "  - API Docs:        http://localhost:8000/docs"
echo "  - Spark Master UI: http://localhost:8080"
echo "  - MongoDB Express: http://localhost:8081"
echo ""
echo "Check logs:"
echo "  sudo docker logs -f globalmart-producer"
echo "  sudo docker logs -f globalmart-api"
echo ""
