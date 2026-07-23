#!/bin/bash
# ============================================
# AI Change Impact Analyzer - Stop Script
# ============================================

set -e

echo "Stopping all services..."

# Source environment for port info
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Stop with Docker Compose
docker-compose down

echo ""
echo "✅ All services stopped."
echo ""
echo "To restart: ./start.sh"

