# Agent Spy - Development Guide

## Overview

This guide provides comprehensive information for developers working on Agent Spy, including local development setup, architecture understanding, testing strategies, and contribution guidelines.

## 🚀 Development Setup

### Prerequisites

- **Python 3.13+** (required for modern async features)
- **uv** package manager (recommended for fast dependency management)
- **Node.js 18+** (for frontend development)
- **Git** for version control
- **Docker** (optional, for containerized development)

### Local Development Environment

1. **Clone the repository**

   ```bash
   git clone https://github.com/lalanikarim/agent-spy.git
   cd agent-spy
   ```

2. **Install Python dependencies**

   ```bash
   uv sync
   ```

3. **Install frontend dependencies**

   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Set up environment variables**

   ```bash
   cp env.example .env
   # Edit .env with your preferred settings
   ```

5. **Start the backend server**

   ```bash
   PYTHONPATH=. uv run python src/main.py
   ```

6. **Start the frontend development server** (in a new terminal)
   ```bash
   cd frontend
   npm run dev
   ```

### Development URLs

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

## 🏗️ Architecture Overview

### Backend Architecture

```
src/
├── main.py              # FastAPI application entry point
├── api/                 # API route handlers
│   ├── health.py        # Health check endpoints
│   └── runs.py          # Trace/run management endpoints
├── core/                # Core infrastructure
│   ├── config.py        # Configuration management
│   ├── database.py      # Database connection and session management
│   └── logging.py       # Logging configuration
├── models/              # SQLAlchemy database models
│   ├── base.py          # Base model classes and mixins
│   ├── runs.py          # Run/trace database model
│   └── feedback.py      # Feedback database model
├── repositories/        # Data access layer
│   ├── runs.py          # Run repository with business logic
│   └── feedback.py      # Feedback repository
├── schemas/             # Pydantic models for API
│   ├── runs.py          # Run-related schemas
│   ├── dashboard.py     # Dashboard-specific schemas
│   └── feedback.py      # Feedback schemas
└── services/            # Business logic layer (planned)
```

### Frontend Architecture

```
frontend/src/
├── App.tsx              # Main application component
├── main.tsx             # Application entry point
├── components/          # React components
│   ├── Dashboard.tsx    # Main dashboard layout
│   ├── TraceTable.tsx   # Root traces table
│   ├── TraceDetail.tsx  # Detailed trace view
│   ├── DashboardStats.tsx # Statistics cards
│   ├── SimpleTimeline.tsx # Basic timeline component
│   └── TraceTimeline.tsx  # Advanced timeline visualization
├── hooks/               # Custom React hooks
│   └── useTraces.ts     # Data fetching hooks
├── api/                 # API client
│   └── client.ts        # Axios configuration
├── types/               # TypeScript definitions
│   └── traces.ts        # Type definitions for traces
├── utils/               # Utility functions
│   └── formatters.ts    # Data formatting utilities
└── assets/              # Static assets
```

## 🔧 Development Workflow

### Code Quality Tools

Agent Spy uses several tools to maintain code quality:

```bash
# Python linting and formatting
uv run ruff check src/
uv run ruff format src/

# Type checking
uv run basedpyright src/

# Security scanning
uv run bandit -r src/

# Frontend linting
cd frontend && npm run lint
```

### Testing Strategy

#### Backend Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test categories
uv run pytest tests/unit/          # Unit tests
uv run pytest tests/e2e/           # End-to-end tests
uv run pytest tests/integration/   # Integration tests

# Run tests in parallel
uv run pytest -n auto
```

#### Frontend Testing

```bash
# Run frontend tests (when implemented)
cd frontend && npm test
```

#### Test Categories

1. **Unit Tests** (`tests/unit/`)

   - Test individual functions and classes
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (`tests/integration/`)

   - Test component interactions
   - Database operations
   - API endpoint behavior

3. **End-to-End Tests** (`tests/e2e/`)
   - Full application workflow
   - Real HTTP requests
   - Complete trace ingestion and retrieval

### Database Management

#### Development Database

The development environment uses SQLite for simplicity:

```bash
# Database file location
./agentspy.db

# View database directly
sqlite3 agentspy.db

# Common queries
sqlite3 agentspy.db "SELECT COUNT(*) FROM runs;"
sqlite3 agentspy.db "SELECT * FROM runs ORDER BY created_at DESC LIMIT 10;"
```

#### Database Migrations

Currently, Agent Spy uses SQLAlchemy's create_all() for schema management. Future versions will include Alembic for proper migrations.

### Environment Configuration

Key environment variables for development:

```bash
# Development settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database settings
DATABASE_URL=sqlite+aiosqlite:///./agentspy.db
DATABASE_ECHO=true  # Log SQL queries

# API settings
API_PREFIX=/api/v1
REQUIRE_AUTH=false

# CORS settings
CORS_ORIGINS=http://localhost:3000
CORS_CREDENTIALS=true
```

## 🧪 Testing Examples

### Running the Example Scripts

Agent Spy includes comprehensive examples for testing:

```bash
# Basic LangChain integration
uv run python examples/test_langchain_app.py

# LangGraph agent with tools
uv run python examples/test_langgraph_agent.py

# Complex multi-step workflow
uv run python examples/test_complex_langgraph_workflow.py

# Dual chain agent
uv run python examples/test_dual_chain_agent.py
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get service info
curl http://localhost:8000/api/v1/info

# Get root traces
curl http://localhost:8000/api/v1/dashboard/runs/roots

# Get statistics
curl http://localhost:8000/api/v1/dashboard/stats/summary
```

## 🔍 Debugging

### Backend Debugging

#### Logging

Agent Spy uses structured logging with different levels:

```python
import logging
from src.core.logging import get_logger

logger = get_logger(__name__)

# Different log levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

#### Debug Mode

Enable debug mode for detailed logging:

```bash
DEBUG=true uv run python src/main.py
```

#### Database Debugging

Enable SQL query logging:

```bash
DATABASE_ECHO=true uv run python src/main.py
```

### Frontend Debugging

#### React Developer Tools

Install React Developer Tools browser extension for component inspection.

#### Network Debugging

Use browser DevTools to inspect API requests and responses.

#### Console Logging

```typescript
// Debug API calls
console.log("API Response:", data);

// Debug component state
console.log("Component State:", state);
```

## 📊 Performance Monitoring

### Backend Performance

#### Response Time Monitoring

```bash
# Test API response times
time curl http://localhost:8000/api/v1/dashboard/runs/roots

# Monitor with detailed timing
curl -w "@curl-format.txt" http://localhost:8000/api/v1/dashboard/runs/roots
```

#### Database Performance

```sql
-- Check slow queries
SELECT * FROM runs WHERE start_time > datetime('now', '-1 hour');

-- Analyze table sizes
SELECT COUNT(*) as total_runs FROM runs;
SELECT COUNT(*) as completed_runs FROM runs WHERE status = 'completed';
```

### Frontend Performance

#### React Profiler

Use React Profiler to identify performance bottlenecks:

```typescript
import { Profiler } from "react";

function onRenderCallback(id, phase, actualDuration) {
  console.log(`Component ${id} took ${actualDuration}ms to render`);
}
```

#### Bundle Analysis

```bash
# Analyze frontend bundle size
cd frontend && npm run build
npx vite-bundle-analyzer dist
```

## 🚀 Deployment

### Local Production Build

```bash
# Build frontend
cd frontend && npm run build

# Start production server
ENVIRONMENT=production DEBUG=false uv run python src/main.py
```

### Docker Development

```bash
# Development environment
docker compose -f docker/docker-compose.dev.yml up -d

# Production environment
docker compose -f docker/docker-compose.yml up -d
```

## 🤝 Contributing

### Development Workflow

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation

3. **Run quality checks**

   ```bash
   uv run ruff check src/
   uv run basedpyright src/
   uv run pytest
   ```

4. **Commit your changes**

   ```bash
   git add .
   git commit -s -m "feat: add your feature description"
   ```

5. **Push and create a pull request**

### Code Standards

#### Python Code Style

- Follow PEP 8 guidelines
- Use type hints for all public APIs
- Write docstrings for all functions and classes
- Use meaningful variable and function names

#### TypeScript Code Style

- Use TypeScript strict mode
- Prefer functional components with hooks
- Use proper error handling
- Follow React best practices

#### Testing Standards

- Maintain >90% test coverage (currently 51%)
- Write both unit and integration tests
- Use descriptive test names
- Mock external dependencies appropriately

### Documentation Standards

- Update README.md for user-facing changes
- Update API documentation for endpoint changes
- Add inline code comments for complex logic
- Create examples for new features

## 🐛 Common Issues

### Backend Issues

#### Database Connection Errors

```bash
# Check database file permissions
ls -la agentspy.db

# Recreate database if corrupted
rm agentspy.db
uv run python -c "from src.core.database import init_database; import asyncio; asyncio.run(init_database())"
```

#### Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=.

# Check virtual environment
uv run python -c "import sys; print(sys.path)"
```

### Frontend Issues

#### Build Errors

```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### API Connection Issues

```bash
# Check API base URL configuration
cat frontend/src/api/client.ts

# Verify backend is running
curl http://localhost:8000/health
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Ant Design Documentation](https://ant.design/)

## 🆘 Getting Help

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Check the docs/ directory for detailed guides
- **Examples**: Review the examples/ directory for usage patterns
