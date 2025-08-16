FROM node:20-slim

# Install basic development tools and sudo
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    nano \
    procps \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with bash as default shell (handle case where UID/GID might already exist)
ARG USER_UID=1000
ARG USER_GID=1000
RUN if id -u $USER_UID >/dev/null 2>&1; then \
        EXISTING_USER=$(id -nu $USER_UID) && \
        usermod -l vscode $EXISTING_USER && \
        groupmod -n vscode $(id -gn $USER_UID) && \
        usermod -d /home/vscode -m -s /bin/bash vscode; \
    else \
        (groupadd --gid $USER_GID vscode || true) && \
        useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash vscode; \
    fi \
    && echo vscode ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

# Set working directory
WORKDIR /workspace/frontend

# Copy supervisor script
COPY .devcontainer/frontend-supervisor.sh /usr/local/bin/frontend-supervisor.sh
RUN chmod +x /usr/local/bin/frontend-supervisor.sh

# Change ownership of workspace to vscode user
RUN chown -R vscode:vscode /workspace

# Switch to non-root user
USER vscode

# Default command
CMD ["sleep", "infinity"]
