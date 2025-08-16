# Agent Spy Dev Container

This directory contains the development container configuration for Agent Spy, providing a complete, consistent development environment.

## Quick Start

1. **Prerequisites**: Install Docker Desktop and VS Code with Dev Containers extension
2. **Open Project**: Open the agent-spy folder in VS Code
3. **Start Dev Container**: Click "Reopen in Container" when prompted
4. **Start Development**: Use the provided commands and tasks

## What's Included

### 🐍 Backend Development
- Python 3.13 with uv package manager
- FastAPI with hot reloading
- All Python dependencies pre-installed
- Ruff for linting/formatting
- MyPy for type checking
- Pytest for testing

### 🌐 Frontend Development  
- Node.js 20 with npm
- React 19 with TypeScript
- Vite dev server
- All npm dependencies pre-installed
- ESLint and Prettier configured

### 🔧 Development Tools
- VS Code extensions pre-installed
- Debug configurations ready
- Task runners for common operations
- Git hooks and configuration
- SQLite database tools

## Quick Commands

```bash
# Start backend server
agentspy-backend

# Start frontend dev server
agentspy-frontend

# Run tests
agentspy-test

# Format and lint code
agentspy-format
agentspy-lint

# Open database CLI
agentspy-db

# Show development info
agentspy-info
```

## Service URLs

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs  
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8000/health
- **SQLite Web** (optional): http://localhost:8080

## Files Overview

- `devcontainer.json` - Main configuration
- `docker-compose.dev.yml` - Multi-container setup
- `backend.Dockerfile` - Python development container
- `frontend.Dockerfile` - Node.js development container
- `post-create.sh` - Initial setup script
- `post-start.sh` - Container startup script
- `development.env` - Environment variables
- `launch.json` - VS Code debug configs
- `tasks.json` - VS Code task definitions

## Troubleshooting

### Container won't start
```bash
# Rebuild containers
docker compose -f .devcontainer/docker-compose.dev.yml build --no-cache

# Check logs
docker compose -f .devcontainer/docker-compose.dev.yml logs
```

### Port conflicts
```bash
# Check what's using the port
lsof -i :8000

# Change ports in docker-compose.dev.yml if needed
```

### Permission issues
```bash
# Fix permissions
sudo chown -R $USER:$USER .

# Or rebuild with correct user ID
docker compose build --build-arg USER_UID=$(id -u)
```

## Documentation

See [DEVCONTAINER_SETUP.md](../docs/DEVCONTAINER_SETUP.md) for comprehensive documentation.

## Need Help?

1. Check the troubleshooting section above
2. Review the full documentation
3. Check container logs
4. Open an issue in the repository