FROM node:20

# Install basic development tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    nano \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port for development server
EXPOSE 3000

# Default command to run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
