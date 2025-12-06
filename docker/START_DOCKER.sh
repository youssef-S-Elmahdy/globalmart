#!/bin/bash
# Start all GlobalMart Docker services

echo "Starting GlobalMart Docker Infrastructure..."
echo ""

cd "$(dirname "$0")"

# Start all compose files
for compose_file in docker-compose.*.yml; do
    if [ -f "$compose_file" ]; then
        echo "Starting $compose_file..."
        sudo docker-compose -f "$compose_file" up -d
    fi
done

echo ""
echo "Waiting for services to initialize (30 seconds)..."
sleep 30

echo ""
echo "Container Status:"
sudo docker ps --format "table {{.Names}}\t{{.Status}}" | grep globalmart

echo ""
echo "✓ Docker infrastructure started"
echo ""
echo "Access points:"
echo "  - Grafana:         http://localhost:3001 (admin/admin123)"
echo "  - Spark Master UI: http://localhost:8080"
echo "  - MongoDB Express: http://localhost:8081"
