# Development Dockerfile for Agent Spy Frontend
# Optimized for dev containers with development tools and hot reloading

FROM node:20-slim

# Build arguments
ARG USER_UID=1000
ARG USER_GID=1000

# Environment variables for development
ENV NODE_ENV=development \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including development tools
RUN apt-get update && apt-get install -y \
    # Basic utilities
    curl \
    wget \
    git \
    vim \
    nano \
    # Process tools
    procps \
    htop \
    # Network tools for debugging
    netcat-traditional \
    telnet \
    # Development tools
    make \
    # Python for some node packages that need it
    python3 \
    python3-pip \
    build-essential \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Create vscode user with matching UID/GID
RUN groupadd --gid $USER_GID vscode \
    && useradd --uid $USER_UID --gid $USER_GID -m vscode \
    && apt-get update \
    && apt-get install -y sudo \
    && echo vscode ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directory
RUN mkdir -p /workspace/frontend && chown -R vscode:vscode /workspace

# Switch to vscode user
USER vscode

# Create cache directories
RUN mkdir -p /home/vscode/.npm \
    && mkdir -p /home/vscode/.cache

# Configure npm for development
RUN npm config set cache /home/vscode/.npm \
    && npm config set fund false \
    && npm config set audit false

# Set working directory
WORKDIR /workspace/frontend

# Copy package files (these change less frequently)
COPY --chown=vscode:vscode package*.json ./

# Install dependencies
RUN npm ci --include=dev

# Install global development tools
RUN npm install -g \
    @vscode/vsce \
    typescript \
    eslint \
    prettier \
    @types/node

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || curl -f http://localhost:5173/ || exit 1

# Default command for development (overridden by devcontainer)
CMD ["sleep", "infinity"]
