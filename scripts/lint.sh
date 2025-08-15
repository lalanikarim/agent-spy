#!/bin/bash
# Linting and formatting script for Agent Spy

set -e

echo "🔍 Running pre-commit hooks..."

# Run ruff check with fix
echo "📝 Running ruff check (with --fix)..."
uv run ruff check --fix src/

# Run ruff format
echo "🎨 Running ruff format..."
uv run ruff format src/

# Run basedpyright type checking
echo "🔍 Running basedpyright type check..."
uv run basedpyright src/

# Run bandit security check
echo "🔒 Running bandit security check..."
uv run bandit -c pyproject.toml -r src/

echo "✅ All linting checks completed!"
