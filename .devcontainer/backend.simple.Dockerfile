FROM python:3.13-slim

# Install basic development tools, sudo, and Docker CLI
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    nano \
    procps \
    sudo \
    ca-certificates \
    gnupg \
    lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create non-root user with bash as default shell
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid $USER_GID vscode \
    && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash vscode \
    && echo vscode ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

# Set working directory
WORKDIR /workspace

# Copy Python dependency files (for layer caching)
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN uv sync --dev

# Change ownership of workspace and .venv to vscode user
RUN chown -R vscode:vscode /workspace

# Switch to non-root user
USER vscode

# Default command
CMD ["sleep", "infinity"]
