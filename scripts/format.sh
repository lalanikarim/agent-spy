#!/bin/bash
# Format Python code with Ruff
# Run this before committing to ensure consistent formatting

set -e

echo "🎨 Formatting Python code with Ruff..."

# Format all Python files in src/ and tests/
uv run ruff format src/ tests/

echo "✅ Formatting complete!"
echo ""
echo "💡 Tip: You can also format specific files:"
echo "   uv run ruff format path/to/file.py"
