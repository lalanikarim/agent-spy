#!/bin/bash

# Setup script for Agent Spy Dev Container
# This script helps users set up the development container environment

set -e

echo "🕵️  Agent Spy Dev Container Setup"
echo "=================================="
echo ""

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "   Please install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    echo "   Please start Docker Desktop"
    exit 1
fi

echo "✅ Docker is installed and running"

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    echo "   Please update to a newer version of Docker that includes Docker Compose v2"
    exit 1
fi

echo "✅ Docker Compose is available"

# Check if VS Code is installed
if command -v code &> /dev/null; then
    echo "✅ VS Code is installed"
    
    # Check if Dev Containers extension is installed
    if code --list-extensions | grep -q "ms-vscode-remote.remote-containers"; then
        echo "✅ Dev Containers extension is installed"
    else
        echo "⚠️  Dev Containers extension is not installed"
        echo "   Installing Dev Containers extension..."
        code --install-extension ms-vscode-remote.remote-containers
        echo "✅ Dev Containers extension installed"
    fi
else
    echo "⚠️  VS Code is not installed or not in PATH"
    echo "   You can still use the dev container with other editors that support dev containers"
fi

# Create dev-data directory
echo "📁 Creating development directories..."
mkdir -p dev-data
mkdir -p .cursor/rules
mkdir -p .cursor/artifacts
mkdir -p docs/plans

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x .devcontainer/post-create.sh
chmod +x .devcontainer/post-start.sh
chmod +x scripts/*.sh

# Check if .env exists, if not create from template
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "📋 Creating .env file from template..."
        cp env.example .env
        echo "✅ Created .env file - you may want to customize it for development"
    else
        echo "⚠️  No env.example found - you may need to create a .env file manually"
    fi
else
    echo "✅ .env file already exists"
fi

# Test Docker Compose configuration
echo "🧪 Testing Docker Compose configuration..."
if docker compose -f .devcontainer/docker-compose.dev.yml config &> /dev/null; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    echo "   Please check the .devcontainer/docker-compose.dev.yml file"
    exit 1
fi

echo ""
echo "🎉 Dev Container setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Open this project in VS Code"
echo "2. When prompted, click 'Reopen in Container'"
echo "3. Or use Ctrl+Shift+P and select 'Dev Containers: Reopen in Container'"
echo ""
echo "If you don't see the prompt:"
echo "1. Press Ctrl+Shift+P (or Cmd+Shift+P on macOS)"
echo "2. Type 'Dev Containers: Reopen in Container'"
echo "3. Select the command"
echo ""
echo "The first time will take 5-10 minutes to build the containers."
echo "After that, starting the dev container will be much faster."
echo ""
echo "Once in the container, run 'agentspy-info' to see available commands."
echo ""
echo "Happy coding! 🚀"

