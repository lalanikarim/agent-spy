#!/bin/bash

# Post-create script for Agent Spy dev container
# This script runs after the container is created

set -e

echo "🚀 Running post-create setup for Agent Spy..."

# Create necessary directories
echo "📁 Creating development directories..."
mkdir -p /workspace/dev-data
mkdir -p /workspace/.cursor/rules
mkdir -p /workspace/.cursor/artifacts
mkdir -p /workspace/docs/plans

# Set up Git configuration if not already set
echo "⚙️  Setting up Git configuration..."
if [ -z "$(git config --global user.name)" ]; then
    git config --global user.name "Dev Container User"
fi
if [ -z "$(git config --global user.email)" ]; then
    git config --global user.email "dev@example.com"
fi

# Configure Git to be safe with the workspace directory
git config --global --add safe.directory /workspace

# Install Python dependencies if not already installed
echo "🐍 Setting up Python environment..."
cd /workspace
if [ -f "pyproject.toml" ]; then
    echo "Installing Python dependencies with uv..."
    uv sync --dev
fi

# Install frontend dependencies if not already installed
echo "📦 Setting up Node.js environment..."
cd /workspace/frontend
if [ -f "package.json" ] && [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm ci --include=dev
fi

# Initialize database
echo "🗄️  Initializing development database..."
cd /workspace
if [ ! -f "dev-data/agentspy_dev.db" ]; then
    echo "Creating development database..."
    # The database will be created automatically when the application starts
    # but we can create the directory structure
    touch dev-data/.gitkeep
fi

# Set up pre-commit hooks if available
echo "🔧 Setting up development tools..."
cd /workspace
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Installing pre-commit hooks..."
    uv run pre-commit install || echo "Pre-commit not available, skipping..."
fi

# Create development environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📋 Creating development environment file..."
    cp env.example .env || echo "No env.example found, skipping .env creation"
fi

# Set proper permissions
echo "🔐 Setting file permissions..."
chmod +x /workspace/.devcontainer/post-start.sh
chmod +x /workspace/scripts/*.sh

# Create useful aliases for development
echo "💡 Setting up development aliases..."
cat >> /home/vscode/.bashrc << 'EOF'

# Agent Spy Development Aliases
alias agentspy-backend="cd /workspace && uv run python src/main.py"
alias agentspy-frontend="cd /workspace/frontend && npm run dev"
alias agentspy-test="cd /workspace && uv run pytest"
alias agentspy-lint="cd /workspace && uv run ruff check ."
alias agentspy-format="cd /workspace && uv run ruff format ."
alias agentspy-db="sqlite3 /workspace/dev-data/agentspy_dev.db"
alias ll="ls -la"
alias la="ls -la"

# Useful functions
agentspy-logs() {
    if [ "$1" = "backend" ]; then
        docker logs -f agentspy-dev-backend
    elif [ "$1" = "frontend" ]; then
        docker logs -f agentspy-dev-frontend
    else
        echo "Usage: agentspy-logs [backend|frontend]"
    fi
}

agentspy-shell() {
    if [ "$1" = "backend" ]; then
        docker exec -it agentspy-dev-backend bash
    elif [ "$1" = "frontend" ]; then
        docker exec -it agentspy-dev-frontend bash
    else
        echo "Usage: agentspy-shell [backend|frontend]"
    fi
}

# Show development information
agentspy-info() {
    echo "🕵️  Agent Spy Development Environment"
    echo "======================================"
    echo "Backend API: http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo "API Docs: http://localhost:8000/docs"
    echo "SQLite Web: http://localhost:8080 (if enabled)"
    echo ""
    echo "Useful commands:"
    echo "  agentspy-backend   - Start backend server"
    echo "  agentspy-frontend  - Start frontend dev server"
    echo "  agentspy-test      - Run tests"
    echo "  agentspy-lint      - Run linting"
    echo "  agentspy-format    - Format code"
    echo "  agentspy-db        - Open SQLite CLI"
}
EOF

echo "✅ Post-create setup completed successfully!"
echo ""
echo "🎉 Welcome to Agent Spy development environment!"
echo "   Run 'agentspy-info' to see available commands and URLs."