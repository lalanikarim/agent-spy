#!/bin/bash
# Start Agent Spy with Docker Compose

set -e

echo "🚀 Starting Agent Spy with Docker Compose..."

# Check if .env file exists, if not copy from template
if [ ! -f .env ]; then
    if [ -f env.example ]; then
        echo "📝 Creating .env file from template..."
        cp env.example .env
        echo "✅ .env file created. Please review and customize the settings."
    else
        echo "⚠️  No .env file found and no template available."
        echo "Please create a .env file with your configuration."
        exit 1
    fi
fi

# Start services
echo "🐳 Starting containers..."
docker compose -f docker/docker-compose.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."
docker compose -f docker/docker-compose.yml ps

echo "✅ Agent Spy is starting up!"
echo ""
echo "🌐 Frontend: http://localhost:$(grep FRONTEND_PORT .env | cut -d'=' -f2 || echo '80')"
echo "🔧 Backend API: http://localhost:$(grep BACKEND_PORT .env | cut -d'=' -f2 || echo '8000')"
echo "📚 API Documentation: http://localhost:$(grep BACKEND_PORT .env | cut -d'=' -f2 || echo '8000')/docs"
echo ""
echo "📊 To view logs: docker compose -f docker/docker-compose.yml logs -f"
echo "🛑 To stop: docker compose -f docker/docker-compose.yml down"
