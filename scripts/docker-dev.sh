#!/bin/bash
# Start Agent Spy in development mode with Docker Compose

set -e

echo "🚀 Starting Agent Spy in development mode..."

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

# Start development services
echo "🐳 Starting development containers..."
docker compose -f docker/docker-compose.dev.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."
docker compose -f docker/docker-compose.dev.yml ps

echo "✅ Agent Spy development environment is ready!"
echo ""
echo "🌐 Frontend (dev): http://localhost:3000"
echo "🔧 Backend API (dev): http://localhost:8001"
echo "📚 API Documentation: http://localhost:8001/docs"
echo "🗄️  Database: SQLite (persistent volume)"
echo ""
echo "📊 To view logs: docker compose -f docker/docker-compose.dev.yml logs -f"
echo "🛑 To stop: docker compose -f docker/docker-compose.dev.yml down"
