# Agent Spy - Troubleshooting Guide

## Overview

This guide provides solutions for common issues you may encounter when using Agent Spy. It covers both development and production environments, with step-by-step solutions and diagnostic commands.

## Quick Diagnostics

### Check System Status

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check if frontend is accessible
curl http://localhost:3000

# Check database connectivity
sqlite3 agentspy.db "SELECT COUNT(*) FROM runs;"

# Check logs
tail -f server.log
```

### Verify Environment

```bash
# Check Python version
python --version  # Should be 3.13+

# Check uv installation
uv --version

# Check Node.js version
node --version  # Should be 18+

# Check Docker (if using containers)
docker --version
docker compose --version
```

## Common Issues

### Backend Issues

#### 1. Import Errors

**Symptoms:**

```
ModuleNotFoundError: No module named 'src'
ImportError: cannot import name 'RunRepository'
```

**Solutions:**

```bash
# Set PYTHONPATH correctly
export PYTHONPATH=.
PYTHONPATH=. uv run python src/main.py

# Or use absolute imports
uv run python -m src.main
```

#### 2. Database Connection Errors

**Symptoms:**

```
sqlite3.OperationalError: unable to open database file
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
```

**Solutions:**

```bash
# Check file permissions
ls -la agentspy.db

# Fix permissions
chmod 644 agentspy.db

# Recreate database if corrupted
rm agentspy.db
uv run python -c "from src.core.database import init_database; import asyncio; asyncio.run(init_database())"

# Check directory permissions
ls -la .
chmod 755 .
```

#### 3. Port Already in Use

**Symptoms:**

```
OSError: [Errno 98] Address already in use
```

**Solutions:**

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
PORT=8001 uv run python src/main.py
```

#### 4. CORS Errors

**Symptoms:**

```
Access to fetch at 'http://localhost:8000/api/v1/dashboard/runs/roots' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solutions:**

```bash
# Check CORS configuration in .env
CORS_ORIGINS=http://localhost:3000
CORS_CREDENTIALS=true

# Or allow all origins for development
CORS_ORIGINS=*
```

#### 5. Memory Issues

**Symptoms:**

```
MemoryError: Unable to allocate memory
```

**Solutions:**

```bash
# Check memory usage
free -h

# Reduce database pool size
DATABASE_POOL_SIZE=5

# Limit trace size
MAX_TRACE_SIZE_MB=5
```

### Frontend Issues

#### 1. Build Errors

**Symptoms:**

```
npm ERR! code ELIFECYCLE
npm ERR! errno 1
npm ERR! build failed
```

**Solutions:**

```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+

# Clear npm cache
npm cache clean --force
```

#### 2. API Connection Issues

**Symptoms:**

```
Failed to fetch: NetworkError when attempting to fetch resource
```

**Solutions:**

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check API base URL in frontend config
cat frontend/src/api/client.ts

# Verify CORS settings
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS http://localhost:8000/api/v1/dashboard/runs/roots
```

#### 3. React Development Server Issues

**Symptoms:**

```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solutions:**

```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use a different port
cd frontend
npm run dev -- --port 3001
```

### Docker Issues

#### 1. Container Won't Start

**Symptoms:**

```
docker: Error response from daemon: failed to create shim task
```

**Solutions:**

```bash
# Check Docker daemon
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Check available disk space
df -h

# Clean up Docker resources
docker system prune -a
```

#### 2. Volume Mount Issues

**Symptoms:**

```
sqlite3.OperationalError: unable to open database file
```

**Solutions:**

```bash
# Check volume permissions
docker compose -f docker/docker-compose.yml exec backend ls -la /app/data

# Fix volume permissions
docker compose -f docker/docker-compose.yml exec backend chown -R 1000:1000 /app/data

# Recreate volumes
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

#### 3. Network Issues

**Symptoms:**

```
Connection refused
```

**Solutions:**

```bash
# Check container network
docker network ls
docker network inspect agentspy_agentspy-network

# Check container logs
docker compose -f docker/docker-compose.yml logs backend
docker compose -f docker/docker-compose.yml logs frontend

# Restart containers
docker compose -f docker/docker-compose.yml restart
```

### Trace Ingestion Issues

#### 1. Traces Not Appearing

**Symptoms:**

```
No traces visible in dashboard
```

**Solutions:**

```bash
# Check if traces are being received
tail -f server.log | grep "Batch ingest"

# Check database directly
sqlite3 agentspy.db "SELECT COUNT(*) FROM runs;"
sqlite3 agentspy.db "SELECT * FROM runs ORDER BY created_at DESC LIMIT 5;"

# Test trace ingestion manually
curl -X POST http://localhost:8000/api/v1/runs/batch \
  -H "Content-Type: application/json" \
  -d '{"post":[{"id":"test-123","name":"Test Run","run_type":"chain","start_time":"2024-01-01T12:00:00Z","project_name":"test"}],"patch":[]}'
```

#### 2. Project Name Issues

**Symptoms:**

```
Traces not grouped by project
```

**Solutions:**

```bash
# Check project name in environment
echo $LANGSMITH_PROJECT

# Check project name in headers
curl -H "X-LangSmith-Project: my-project" \
     http://localhost:8000/api/v1/dashboard/runs/roots

# Check database for project names
sqlite3 agentspy.db "SELECT DISTINCT project_name FROM runs;"
```

#### 3. Completion Status Issues

**Symptoms:**

```
Runs stuck in "running" status
```

**Solutions:**

```bash
# Check completion detection logic
grep -r "completion" src/

# Check run data structure
sqlite3 agentspy.db "SELECT id, name, status, end_time, outputs IS NOT NULL as has_outputs FROM runs WHERE status = 'running';"

# Manually update status
sqlite3 agentspy.db "UPDATE runs SET status = 'completed' WHERE end_time IS NOT NULL AND outputs IS NOT NULL;"
```

## Performance Issues

### Slow Dashboard Loading

**Symptoms:**

```
Dashboard takes a long time to load
```

**Solutions:**

```bash
# Check database performance
sqlite3 agentspy.db "EXPLAIN QUERY PLAN SELECT * FROM runs WHERE parent_run_id IS NULL ORDER BY start_time DESC LIMIT 50;"

# Add database indexes
sqlite3 agentspy.db "CREATE INDEX IF NOT EXISTS idx_runs_parent_start ON runs(parent_run_id, start_time);"
sqlite3 agentspy.db "CREATE INDEX IF NOT EXISTS idx_runs_project_time ON runs(project_name, start_time);"

# Check API response times
time curl http://localhost:8000/api/v1/dashboard/runs/roots

# Monitor memory usage
htop
```

### High Memory Usage

**Symptoms:**

```
Out of memory errors
```

**Solutions:**

```bash
# Check memory usage
free -h
ps aux | grep python

# Reduce database pool size
DATABASE_POOL_SIZE=5

# Limit concurrent requests
REQUEST_TIMEOUT=30

# Monitor with detailed logging
LOG_LEVEL=DEBUG
```

## Debugging Commands

### Database Debugging

```bash
# Check database schema
sqlite3 agentspy.db ".schema"

# Check table sizes
sqlite3 agentspy.db "SELECT name, COUNT(*) as count FROM runs GROUP BY name;"

# Check recent activity
sqlite3 agentspy.db "SELECT * FROM runs ORDER BY created_at DESC LIMIT 10;"

# Check for orphaned runs
sqlite3 agentspy.db "SELECT COUNT(*) FROM runs WHERE parent_run_id IS NOT NULL AND parent_run_id NOT IN (SELECT id FROM runs);"

# Analyze database performance
sqlite3 agentspy.db "ANALYZE;"
```

### API Debugging

```bash
# Test health endpoint
curl -v http://localhost:8000/health

# Test API with verbose output
curl -v -X POST http://localhost:8000/api/v1/runs/batch \
  -H "Content-Type: application/json" \
  -d '{"post":[],"patch":[]}'

# Check API documentation
curl http://localhost:8000/docs

# Test with authentication
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/api/v1/dashboard/runs/roots
```

### Log Analysis

```bash
# Follow logs in real-time
tail -f server.log

# Search for errors
grep -i error server.log

# Search for specific patterns
grep "Batch ingest" server.log
grep "database" server.log

# Check log levels
grep "DEBUG\|INFO\|WARNING\|ERROR" server.log
```

## Environment-Specific Issues

### Development Environment

#### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf .venv
uv sync

# Check Python path
uv run python -c "import sys; print(sys.path)"

# Verify dependencies
uv run pip list
```

#### IDE Issues

```bash
# Configure IDE for uv
# Add to .vscode/settings.json:
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

### Production Environment

#### System Resource Issues

```bash
# Check system resources
htop
df -h
free -h

# Monitor application
ps aux | grep python
netstat -tlnp | grep 8000

# Check system limits
ulimit -a
```

#### Security Issues

```bash
# Check file permissions
ls -la agentspy.db
ls -la .env

# Secure sensitive files
chmod 600 .env
chmod 644 agentspy.db

# Check for open ports
netstat -tlnp
```

## Getting Help

### Before Asking for Help

1. **Check the logs**: Look at `server.log` for error messages
2. **Verify environment**: Ensure all prerequisites are met
3. **Test with examples**: Try the example scripts
4. **Check documentation**: Review relevant documentation

### Providing Information

When reporting issues, include:

```bash
# System information
uname -a
python --version
node --version
docker --version

# Application logs
tail -50 server.log

# Database state
sqlite3 agentspy.db "SELECT COUNT(*) FROM runs;"

# Environment variables (remove sensitive data)
env | grep -E "(AGENT|LANG|DATABASE|API)"

# Error messages
# Include full error traceback
```

### Support Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and community support
- **Documentation**: Check the `docs/` directory
- **Examples**: Review the `examples/` directory

## Prevention

### Best Practices

1. **Regular backups**: Backup your database regularly
2. **Monitor resources**: Keep an eye on system resources
3. **Update dependencies**: Keep dependencies up to date
4. **Test changes**: Test in development before production
5. **Document configuration**: Keep track of environment changes

### Monitoring

```bash
# Set up basic monitoring
# Add to crontab for regular checks
*/5 * * * * curl -f http://localhost:8000/health || echo "Backend down"
*/5 * * * * curl -f http://localhost:3000 || echo "Frontend down"
```

### Maintenance

```bash
# Regular maintenance tasks
# Clean up old logs
find . -name "*.log" -mtime +7 -delete

# Optimize database
sqlite3 agentspy.db "VACUUM;"

# Update dependencies
uv sync
cd frontend && npm update
```
