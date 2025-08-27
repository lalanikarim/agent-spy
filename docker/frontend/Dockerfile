# Frontend Dockerfile for Agent Spy
FROM node:20-alpine as builder

# Set work directory
WORKDIR /app

# Accept build arguments
ARG VITE_API_BASE_URL=/api/v1

# Copy package files
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application with environment variables
RUN VITE_API_BASE_URL=$VITE_API_BASE_URL npm run build

# Production stage
FROM nginx:alpine

# Accept build arguments for backend service configuration
ARG BACKEND_SERVICE_NAME=prod-backend
ARG BACKEND_PORT=8000

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration template
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Create nginx configuration with backend service name
RUN sed "s/\${BACKEND_SERVICE_NAME:-prod-backend}/$BACKEND_SERVICE_NAME/g; s/\${BACKEND_PORT:-8000}/$BACKEND_PORT/g" /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
