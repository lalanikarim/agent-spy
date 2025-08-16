# Development Dockerfile for Agent Spy Backend
# Optimized for dev containers with development tools and hot reloading

FROM python:3.13-slim

# Build arguments
ARG USER_UID=1000
ARG USER_GID=1000

# Environment variables for development
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONPATH=/workspace \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including development tools
RUN apt-get update && apt-get install -y \
    # Basic utilities
    curl \
    wget \
    git \
    vim \
    nano \
    # Build tools
    build-essential \
    # SQLite tools for database management
    sqlite3 \
    # Network tools for debugging
    netcat-traditional \
    telnet \
    # Process tools
    procps \
    htop \
    # Development tools
    make \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create vscode user with matching UID/GID
RUN groupadd --gid $USER_GID vscode \
    && useradd --uid $USER_UID --gid $USER_GID -m vscode \
    && apt-get update \
    && apt-get install -y sudo \
    && echo vscode ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directory
RUN mkdir -p /workspace && chown vscode:vscode /workspace

# Switch to vscode user
USER vscode

# Create cache directories
RUN mkdir -p /home/vscode/.cache/uv \
    && mkdir -p /home/vscode/.cache/pip \
    && mkdir -p /home/vscode/.local/bin

# Add local bin to PATH
ENV PATH="/home/vscode/.local/bin:$PATH"

# Set working directory
WORKDIR /workspace

# Copy dependency files (these change less frequently)
COPY --chown=vscode:vscode pyproject.toml uv.lock ./

# Install Python dependencies in development mode
RUN uv sync --dev

# Create dev-data directory for SQLite database
RUN mkdir -p /workspace/dev-data

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command for development (overridden by devcontainer)
CMD ["sleep", "infinity"]