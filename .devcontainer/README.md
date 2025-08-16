# Dev Container Setup

This directory contains a minimal, working dev container configuration for the Agent Spy project. The setup has been tested and verified to work with Podman (aliased as `docker`) on macOS.

## Overview

The dev container setup provides a complete development environment with:
- **Backend**: Python 3.13 with FastAPI, SQLAlchemy, pytest, and other dependencies
- **Frontend**: Node.js 20 with React, TypeScript, Vite, and development tools
- **Security**: Non-root user (`vscode`) with bash shell
- **VS Code Integration**: Extensions, settings, and port forwarding

## Files Structure

```
.devcontainer/
├── devcontainer.json              # Main dev container configuration
├── docker-compose.minimal.yml     # Multi-service container setup
├── backend.simple.Dockerfile      # Python backend container
├── frontend.simple.Dockerfile     # Node.js frontend container
└── README.md                      # This documentation
```

## Key Features

### 🔒 Security
- Containers run as non-root `vscode` user (UID/GID 1000)
- Bash shell configured as default
- Sudo privileges for development tasks

### 🐍 Backend Environment
- Python 3.13.5
- `uv` package manager for fast dependency management
- Pre-installed Python dependencies (FastAPI, SQLAlchemy, pytest, ruff, etc.)
- Virtual environment automatically created and managed

### 🌐 Frontend Environment  
- Node.js 20.x in dedicated frontend container
- npm dependency management
- Dependencies installed on container startup
- Full TypeScript and React development stack
- Frontend tasks execute in the frontend container via Docker CLI

### 🛠 Development Tools
- Git, curl, vim, nano, procps pre-installed
- VS Code extensions for Python and TypeScript development
- Automatic code formatting and linting
- Port forwarding for backend (8000) and frontend (3000, 5173)

## Usage

### Starting the Dev Container

1. Open the project in VS Code
2. Press `Cmd+Shift+P` (macOS) and select "Dev Containers: Reopen in Container"
3. VS Code will build and start the containers automatically
4. Wait for the setup to complete

### Quick Start

Once the dev container is running:

1. **Start both servers**: Press `Cmd+Shift+P` → "Tasks: Run Task" → "Start Both Servers"
2. **Access the application**:
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Frontend: http://localhost:3000 (or http://localhost:5173 for Vite)
3. **Debug backend**: Press `F5` → Select "Python: Debug Agent Spy Backend"

### Working with Python (Backend)

The Python environment uses `uv` for package management. To run Python commands:

```bash
# Use uv run to execute in the virtual environment
uv run python -c "import fastapi; print('FastAPI available')"
uv run python src/main.py

# Or activate the virtual environment manually
source .venv/bin/activate
python src/main.py
```

### Working with Node.js (Frontend)

Node.js dependencies are automatically installed on container startup:

```bash
# Navigate to frontend directory
cd frontend/

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

### Port Access

The following ports are forwarded and accessible from your host machine:

- **8000**: Backend API server
- **3000**: Frontend development server  
- **5173**: Vite development server

## Architecture Decisions

### Why Minimal Setup?

This configuration evolved from a complex setup that had compatibility issues with Podman. The minimal approach:

1. **Uses official base images** (`python:3.13-slim`, `node:20-slim`)
2. **Avoids dev container features** that caused conflicts with Podman
3. **Installs dependencies at build time** for faster startup
4. **Handles npm install at runtime** to access mounted package.json

### Why Two Containers?

- **Separation of concerns**: Backend and frontend have different runtime requirements
- **Independent scaling**: Each service can be developed and tested independently  
- **Cleaner dependencies**: No mixing of Python and Node.js in the same container

### Why Non-Root User?

- **Security best practice**: Containers should not run as root
- **File permissions**: Matches host user permissions (UID 1000)
- **VS Code compatibility**: Works seamlessly with VS Code dev containers

## Troubleshooting

### Container Build Issues

If containers fail to build:

```bash
# Clean rebuild
cd .devcontainer
docker compose -f docker-compose.minimal.yml down
docker compose -f docker-compose.minimal.yml build --no-cache
```

### Python Dependencies Not Found

If Python modules are missing:

```bash
# Check virtual environment
ls -la .venv/

# Reinstall dependencies
uv sync --dev

# Use uv run for commands
uv run python -c "import fastapi"
```

### Frontend Dependencies Issues

If npm modules are missing:

```bash
cd frontend/
npm install
```

### Permission Issues

If you encounter permission errors:

```bash
# Check current user
whoami  # Should show: vscode

# Fix ownership if needed
sudo chown -R vscode:vscode /workspace
```

## Development Workflow

1. **Start dev container** in VS Code
2. **Launch servers**: Use VS Code tasks to start backend and/or frontend servers
3. **Backend development**: Use `uv run` for Python commands or launch configurations for debugging
4. **Frontend development**: Work in `frontend/` directory with npm or use tasks
5. **Testing**: Run tests using tasks or launch configurations
6. **Commit changes**: Use git normally from within the container

### VS Code Tasks

Access tasks via `Cmd+Shift+P` → "Tasks: Run Task":

**Note**: Backend tasks run in the current (Python) container. Frontend tasks use `docker exec` to run commands in the dedicated frontend container, keeping containers clean and focused.

- **Start Both Servers**: Launches backend and frontend simultaneously (default build task)
- **Start Backend Server**: Runs FastAPI server with uvicorn (backend container)
- **Start Frontend Dev Server**: Runs Vite development server (frontend container)
- **Install Backend Dependencies**: Runs `uv sync --dev` (backend container)
- **Install Frontend Dependencies**: Runs `npm install` (frontend container)
- **Run Backend Tests**: Executes pytest (backend container)
- **Lint Backend Code**: Runs ruff linting (backend container)
- **Format Backend Code**: Runs ruff formatting (backend container)
- **Build Frontend**: Production build with Vite (frontend container)
- **Lint Frontend Code**: Runs ESLint (frontend container)

### Debug Configurations

Access via `F5` or Debug panel:

- **Python: Debug Agent Spy Backend**: Debug the FastAPI application
- **Python: Run with uv**: Run backend with uvicorn and auto-reload
- **Python: Run Tests**: Debug pytest execution

## Compatibility

✅ **Tested with:**
- macOS (Apple Silicon)
- Podman 5.x (aliased as `docker`)
- podman-compose 1.5.0
- VS Code Dev Containers extension

❓ **Should work with:**
- Docker Desktop
- Linux systems
- Windows with WSL2

## Migration from Complex Setup

This minimal setup replaces the previous complex configuration that used:
- Custom dev container features (caused Podman conflicts)
- Complex user management
- Multiple Dockerfile variations

The new setup is simpler, more reliable, and easier to maintain while providing the same development capabilities.