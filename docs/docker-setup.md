# Docker Compose Setup Guide

This guide provides detailed instructions for deploying Agent Spy using Docker Compose.

## Overview

Agent Spy provides two Docker Compose configurations:

- `docker-compose.yml`: Production deployment
- `docker-compose.dev.yml`: Development environment with hot reloading

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React/Nginx) │◄──►│   (FastAPI)     │◄──►│   (SQLite)      │
│   Port 80/3000  │    │   Port 8000/8001│    │   Volume Mount  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

### Docker Installation
```bash
# Install Docker and Docker Compose
# Follow instructions at https://docs.docker.com/get-docker/

# Verify installation
docker --version
docker compose version
```

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/lalanikarim/agent-spy.git
cd agent-spy

# Copy environment template
cp env.example .env

# Edit configuration (see Configuration section below)
nano .env
```

### 2. Production Deployment

```bash
# Using convenience script
bash scripts/docker-start.sh

# Or manually
docker compose -f docker/docker-compose.yml up -d
```

### 3. Development Environment

```bash
# Using convenience script
bash scripts/docker-dev.sh

# Or manually
docker compose -f docker/docker-compose.dev.yml up -d
```

## Configuration

### Environment Variables

Edit the `.env` file to customize your deployment:

#### Application Settings
```bash
ENVIRONMENT=production          # development, staging, production
DEBUG=false                    # Enable debug mode
```

#### Database Configuration
```bash
DATABASE_ECHO=false          # Enable SQL query logging for debugging
```

#### Service Ports
```bash
FRONTEND_PORT=80             # Web dashboard port
BACKEND_PORT=8000           # API server port
```

#### Security Settings
```bash
REQUIRE_AUTH=false                    # Enable API authentication
API_KEYS=key1,key2,key3              # Valid API keys (if auth enabled)
CORS_ORIGINS=http://localhost:3000   # Allowed CORS origins
```

#### Performance Tuning
```bash
MAX_TRACE_SIZE_MB=10        # Maximum trace size
REQUEST_TIMEOUT=30          # Request timeout in seconds
LOG_LEVEL=INFO             # Logging level
```

## Service Details

### Frontend Service
- **Technology**: React with Vite, served by Nginx
- **Port**: 80 (production) / 3000 (development)
- **Features**:
  - Gzip compression
  - Security headers
  - API proxy configuration
  - Static asset caching

### Backend Service
- **Technology**: FastAPI with uvicorn
- **Port**: 8000 (production) / 8001 (development)
- **Features**:
  - Async request handling
  - Health checks
  - Request ID tracking
  - CORS middleware

### Database Service
- **Technology**: SQLite with aiosqlite driver
- **Storage**: Persistent Docker volume
- **Features**:
  - File-based database
  - Zero configuration
  - ACID compliance
  - Lightweight and fast

## Management Commands

### Service Management
```bash
# Start services
docker compose -f docker/docker-compose.yml up -d

# Stop services
docker compose -f docker/docker-compose.yml down

# Restart services
docker compose -f docker/docker-compose.yml restart

# View service status
docker compose -f docker/docker-compose.yml ps

# View service logs
docker compose -f docker/docker-compose.yml logs -f

# View logs for specific service
docker compose -f docker/docker-compose.yml logs -f backend
```

### Development Commands
```bash
# Start development environment
docker compose -f docker/docker-compose.dev.yml up -d

# View development logs
docker compose -f docker/docker-compose.dev.yml logs -f

# Stop development environment
docker compose -f docker/docker-compose.dev.yml down
```

### Maintenance
```bash
# Rebuild services
docker compose -f docker/docker-compose.yml up -d --build

# Pull latest images
docker compose -f docker/docker-compose.yml pull

# Clean up (removes containers, networks, volumes)
docker compose -f docker/docker-compose.yml down -v

# View resource usage
docker stats
```

## Accessing Services

### Production URLs
- **Web Dashboard**: http://localhost:80
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

### Development URLs
- **Web Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8001/docs
- **API Health Check**: http://localhost:8001/health
- **Database**: SQLite file in persistent volume

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using a port
lsof -i :8000

# Change ports in .env file
BACKEND_PORT=8080
FRONTEND_PORT=8080
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# SELinux context (if applicable)
sudo setsebool -P container_manage_cgroup on
```

#### Database Issues
```bash
# Check backend logs for database errors
docker compose -f docker/docker-compose.yml logs backend

# Reset database (removes all data)
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

### Health Checks

All services include health checks:

```bash
# Check service health
docker compose -f docker/docker-compose.yml ps

# Manual health check
curl http://localhost:8000/health
```

### Log Analysis

```bash
# View all logs
docker compose -f docker/docker-compose.yml logs

# Follow logs in real-time
docker compose -f docker/docker-compose.yml logs -f

# Filter by service
docker compose -f docker/docker-compose.yml logs backend | grep ERROR

# Export logs
docker compose -f docker/docker-compose.yml logs > agentspy-logs.txt
```

## Production Considerations

### Security
1. **Enable authentication** by setting `REQUIRE_AUTH=true`
2. **Configure CORS origins** appropriately
3. **Use HTTPS** in production (add reverse proxy)
4. **Regular security updates** for base images
5. **Secure database volume** with appropriate file permissions

### Performance
1. **Resource limits**: Add resource constraints to compose file
2. **Monitoring**: Integrate with monitoring solutions
3. **Backups**: Implement SQLite database backup strategy
4. **Volume optimization**: Use SSD storage for database volume

### Scaling
1. **Horizontal scaling**: Use Docker Swarm or Kubernetes
2. **Load balancing**: Add load balancer for multiple instances
3. **Database scaling**: Consider migrating to PostgreSQL for high-load scenarios
4. **Caching**: Add Redis for session/query caching

## Database Backup and Migration

### Backup SQLite Database

```bash
# Create backup of production database
docker compose -f docker/docker-compose.yml exec backend cp /app/data/agentspy.db /app/data/agentspy_backup_$(date +%Y%m%d_%H%M%S).db

# Copy backup to host
docker cp agentspy-backend:/app/data/agentspy_backup_*.db ./
```

### Migration to PostgreSQL (Future)

If you need to migrate to PostgreSQL for production scaling:

1. **Backup existing SQLite data**
2. **Update docker-compose.yml** to include PostgreSQL service
3. **Update environment variables** to use PostgreSQL connection string
4. **Implement data migration script**
5. **Test thoroughly** before production deployment

The application will automatically create the required database schema on first startup.
