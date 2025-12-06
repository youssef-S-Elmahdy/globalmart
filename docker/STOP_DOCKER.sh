#!/bin/bash
# Stop all GlobalMart Docker services

echo "Stopping GlobalMart Docker Infrastructure..."
echo ""

# Find and stop all globalmart containers
CONTAINERS=$(sudo docker ps -a --filter "name=globalmart" --format "{{.Names}}" | tr '\n' ' ')

if [ -n "$CONTAINERS" ]; then
    echo "Stopping containers: $CONTAINERS"
    sudo docker stop $CONTAINERS

    read -p "Remove containers? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo docker rm $CONTAINERS
        echo "✓ Containers removed"
    fi
else
    echo "No GlobalMart containers found"
fi

echo ""
echo "✓ Docker infrastructure stopped"
