#!/bin/bash

# Post-start script for Agent Spy dev container
# This script runs every time the container starts

set -e

echo "🔄 Running post-start setup for Agent Spy..."

# Ensure development directories exist
mkdir -p /workspace/dev-data

# Check if database exists and is accessible
echo "🗄️  Checking database status..."
if [ -f "/workspace/dev-data/agentspy_dev.db" ]; then
    echo "✅ Development database found"
else
    echo "📝 Development database will be created on first run"
fi

# Check Python environment
echo "🐍 Checking Python environment..."
cd /workspace
if uv run python --version > /dev/null 2>&1; then
    echo "✅ Python environment ready"
    echo "   Python version: $(uv run python --version)"
else
    echo "⚠️  Python environment needs setup"
fi

# Check Node.js environment
echo "📦 Checking Node.js environment..."
cd /workspace/frontend
if npm --version > /dev/null 2>&1; then
    echo "✅ Node.js environment ready"
    echo "   Node version: $(node --version)"
    echo "   NPM version: $(npm --version)"
else
    echo "⚠️  Node.js environment needs setup"
fi

# Display helpful information
echo ""
echo "🎯 Agent Spy Development Environment Ready!"
echo "=========================================="
echo ""
echo "🌐 Service URLs:"
echo "   Backend API:    http://localhost:8000"
echo "   API Docs:       http://localhost:8000/docs"
echo "   Frontend:       http://localhost:3000"
echo "   Health Check:   http://localhost:8000/health"
echo ""
echo "🔧 Quick Start Commands:"
echo "   Start Backend:  agentspy-backend"
echo "   Start Frontend: agentspy-frontend"
echo "   Run Tests:      agentspy-test"
echo "   Format Code:    agentspy-format"
echo "   Lint Code:      agentspy-lint"
echo ""
echo "📚 Documentation:"
echo "   Project docs are in /workspace/docs/"
echo "   API docs available at http://localhost:8000/docs when backend is running"
echo ""
echo "🗄️  Database:"
echo "   SQLite DB: /workspace/dev-data/agentspy_dev.db"
echo "   DB CLI:    agentspy-db"
echo ""
echo "Type 'agentspy-info' anytime to see this information again."
echo ""

# Check for any pending git changes
cd /workspace
if [ -d ".git" ]; then
    if [ -n "$(git status --porcelain)" ]; then
        echo "📝 You have uncommitted changes in your workspace."
    fi
fi

echo "✅ Post-start setup completed!"