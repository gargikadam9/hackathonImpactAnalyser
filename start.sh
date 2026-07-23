#!/bin/bash
# ============================================
# AI Change Impact Analyzer - Start Script
# ============================================

set -e

echo "========================================"
echo "  AI Change Impact Analyzer"
echo "  Starting all services..."
echo "========================================"

# Check for .env file
if [ ! -f .env ]; then
    echo "[INFO] No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "[INFO] Using default mock mode (no API keys needed)."
fi

# Source environment
set -a
source .env
set +a

# Create necessary directories
mkdir -p ai-service/data/runbooks

# Build and start services
echo "[STEP 1/3] Building and starting services with Docker Compose..."
docker-compose up --build -d

echo "[STEP 2/3] Waiting for services to be healthy..."
sleep 10

echo "[STEP 3/3] Checking service health..."
# Check AI Service
if curl -s http://localhost:${AI_SERVICE_PORT:-8000}/health > /dev/null 2>&1; then
    echo "  ✅ AI Service: http://localhost:${AI_SERVICE_PORT:-8000}/health"
else
    echo "  ⚠️  AI Service not yet ready. Check logs: docker-compose logs ai-service"
fi

# Check Backend
if curl -s http://localhost:${BACKEND_PORT:-8081}/actuator/health > /dev/null 2>&1; then
    echo "  ✅ Backend: http://localhost:${BACKEND_PORT:-8081}/actuator/health"
else
    echo "  ⚠️  Backend may not be ready. Check logs: docker-compose logs backend"
fi

echo ""
echo "========================================"
echo "  🚀 Services Available At:"
echo "  Frontend:     http://localhost:3000"
echo "  Backend:      http://localhost:${BACKEND_PORT:-8081}"
echo "  AI Service:   http://localhost:${AI_SERVICE_PORT:-8000}"
echo "========================================"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop:      ./stop.sh"

