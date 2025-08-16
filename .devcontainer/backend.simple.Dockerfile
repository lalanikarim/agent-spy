FROM python:3.13-slim

# Install basic development tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    nano \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Default command
CMD ["sleep", "infinity"]
