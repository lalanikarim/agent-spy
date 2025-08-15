#!/bin/bash
# Test script to verify Docker setup is working

set -e

echo "🧪 Testing Agent Spy Docker Setup..."

# Check if required files exist
echo "📂 Checking required files..."
if [ ! -f "docker/docker-compose.yml" ]; then
    echo "❌ docker/docker-compose.yml not found"
    exit 1
fi

if [ ! -f "docker/docker-compose.dev.yml" ]; then
    echo "❌ docker/docker-compose.dev.yml not found"
    exit 1
fi

if [ ! -f "docker/backend/Dockerfile" ]; then
    echo "❌ docker/backend/Dockerfile not found"
    exit 1
fi

if [ ! -f "docker/frontend/Dockerfile" ]; then
    echo "❌ docker/frontend/Dockerfile not found"
    exit 1
fi

echo "✅ All required files found"

# Check if docker compose is available
echo "🐳 Checking docker compose..."
if ! command -v docker &> /dev/null; then
    echo "❌ docker not found. Please install Docker."
    exit 1
fi

echo "✅ docker compose found: $(docker compose version)"

# Test compose file syntax
echo "📋 Validating compose files..."
docker compose -f docker/docker-compose.yml config > /dev/null
echo "✅ Production compose file is valid"

docker compose -f docker/docker-compose.dev.yml config > /dev/null
echo "✅ Development compose file is valid"

# Check environment file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, creating from template..."
    cp env.example .env
    echo "✅ .env file created from template"
else
    echo "✅ .env file found"
fi

echo ""
echo "🎉 Docker setup test completed successfully!"
echo ""
echo "🚀 You can now start Agent Spy with:"
echo "   Production:  bash scripts/docker-start.sh"
echo "   Development: bash scripts/docker-dev.sh"
echo ""
echo "📚 Or manually with:"
echo "   Production:  docker compose -f docker/docker-compose.yml up -d"
echo "   Development: docker compose -f docker/docker-compose.dev.yml up -d"
