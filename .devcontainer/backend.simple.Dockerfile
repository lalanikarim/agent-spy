FROM python:3.13-slim

# Install basic development tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    nano \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /workspace

# Copy Python dependency files (for layer caching)
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN uv sync --dev

# Default command
CMD ["sleep", "infinity"]
