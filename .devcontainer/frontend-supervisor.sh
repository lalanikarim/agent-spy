#!/bin/bash

# Frontend Development Supervisor
# Keeps the dev server running and restarts it on failure

echo "🚀 Starting Frontend Development Supervisor"
echo "📁 Working directory: $(pwd)"

# Install dependencies first
echo "📦 Installing dependencies..."
if npm install; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    echo "🔄 Retrying in 10 seconds..."
    sleep 10
    exec "$0"  # Restart the entire script
fi

# Function to start dev server with restart logic
start_dev_server() {
    local attempt=1
    local restart_delay=5

    while true; do
        echo "🌟 Starting dev server (attempt $attempt)..."
        
        # Start the dev server on port 3000
        if npm run dev -- --host 0.0.0.0 --port 3000; then
            echo "✅ Dev server started successfully"
            # If we get here, the server exited normally (unlikely for dev server)
            echo "⚠️  Dev server exited normally"
        else
            local exit_code=$?
            echo "❌ Dev server failed with exit code: $exit_code"
        fi
        
        # Always restart after 5 seconds
        echo "🔄 Restarting in $restart_delay seconds... (attempt $((attempt + 1)))"
        echo "💡 You can connect anytime with: docker exec -it agentspy-minimal-frontend bash"
        sleep $restart_delay
        
        attempt=$((attempt + 1))
    done
}

# Handle signals gracefully
cleanup() {
    echo "🛑 Received shutdown signal"
    echo "👋 Goodbye!"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start the dev server supervisor
start_dev_server
