# Agent Spy 🕵️

A powerful, self-hosted observability platform for AI agents and multi-step workflows. Agent Spy provides comprehensive tracing, monitoring, and debugging capabilities for complex agent interactions.

## 🌟 Features

### 🔍 **Comprehensive Agent Tracing**
- **Real-time Monitoring**: Track agent executions as they happen
- **Hierarchical Traces**: Visualize complex agent workflows with parent-child relationships
- **Multi-step Analysis**: Follow agent reasoning through tools, LLMs, and decision points
- **Smart Completion Detection**: Universal pattern-based detection for accurate run status across all trace types
- **Performance Metrics**: Monitor execution times, token usage, and resource consumption

### 📊 **Advanced Analytics**
- **Dashboard Interface**: Clean, intuitive web interface for trace exploration
- **Coordinated Refresh**: Synchronized updates across trace table and detail views
- **Filtering & Search**: Find specific traces by project, status, time range, or content
- **Statistics & Insights**: Understand agent behavior patterns and performance trends
- **Export Capabilities**: Export trace data for further analysis

### 🏗️ **Production Ready**
- **High Performance**: Optimized for handling thousands of concurrent traces
- **Scalable Storage**: SQLite for development, PostgreSQL for production
- **API-First Design**: RESTful API for integration with any agent framework
- **Comprehensive Testing**: Unit, integration, and end-to-end test coverage

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lalanikarim/agent-spy.git
   cd agent-spy
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Start the server**
   ```bash
   PYTHONPATH=. uv run python src/main.py
   ```

4. **Verify installation**
   ```bash
   curl http://localhost:8000/health
   ```

The server will be running at `http://localhost:8000` with the API documentation available at `http://localhost:8000/docs`.

5. **Try the examples** (optional)
   ```bash
   # Test with a LangGraph agent that uses tools
   uv run python examples/test_langgraph_agent.py

   # Test with a complex multi-chain workflow
   uv run python examples/test_dual_chain_agent.py
   ```

   These examples demonstrate the smart completion detection for tool calls, conditional nodes, and complex agent workflows.

## 🐳 Docker Compose Setup

For production deployments or if you prefer containerized environments, Agent Spy provides comprehensive Docker Compose configurations.

### Prerequisites
- [Docker](https://docker.com/) and [Docker Compose](https://docs.docker.com/compose/)

### Quick Start with Docker Compose

1. **Clone the repository**
   ```bash
   git clone https://github.com/lalanikarim/agent-spy.git
   cd agent-spy
   ```

2. **Configure environment**
   ```bash
   # Copy the environment template
   cp env.example .env

   # Edit the .env file with your preferred settings
   nano .env
   ```

3. **Start Agent Spy (Production)**
   ```bash
   # Using the convenience script
   bash scripts/docker-start.sh

   # Or manually with docker compose
   docker compose -f docker/docker-compose.yml up -d
   ```

4. **Start Agent Spy (Development)**
   ```bash
   # Using the convenience script
   bash scripts/docker-dev.sh

   # Or manually with docker compose
   docker compose -f docker/docker-compose.dev.yml up -d
   ```

### Services Overview

The Docker Compose setup includes:

- **Frontend**: React-based web dashboard (Port 80/3000)
- **Backend**: FastAPI server with Agent Spy API (Port 8000/8001)
- **Database**: SQLite with persistent volume storage

### Environment Configuration

Key environment variables in `.env`:

```bash
# Database settings
DATABASE_ECHO=false

# Application ports
FRONTEND_PORT=80
BACKEND_PORT=8000

# Security settings
REQUIRE_AUTH=false
API_KEYS=your-api-key-1,your-api-key-2

# CORS configuration
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Docker Commands

```bash
# View running services
docker compose -f docker/docker-compose.yml ps

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop services
docker compose -f docker/docker-compose.yml down

# Rebuild and restart
docker compose -f docker/docker-compose.yml up -d --build

# Clean up (removes volumes)
docker compose -f docker/docker-compose.yml down -v
```

### Accessing the Application

After starting the containers:

- **Web Dashboard**: http://localhost (or your configured FRONTEND_PORT)
- **API Documentation**: http://localhost:8000/docs (or your configured BACKEND_PORT)
- **Health Check**: http://localhost:8000/health

## 📖 Usage

### Agent Integration

To send traces from your agents to Agent Spy, configure these environment variables in your agent application:

```bash
# Enable tracing
LANGSMITH_TRACING=true

# Point to Agent Spy instead of LangSmith
LANGSMITH_ENDPOINT=http://localhost:8000/api/v1

# API key (can be any value for now, authentication is optional)
LANGSMITH_API_KEY=your-api-key

# Project name for organizing traces
LANGSMITH_PROJECT=your-project-name
```

### Basic Trace Ingestion

Agent Spy accepts traces through a LangSmith-compatible REST API:

```python
import requests
import json
from datetime import datetime
from uuid import uuid4

# Create a trace
trace_data = {
    "id": str(uuid4()),
    "name": "Agent Planning Session",
    "run_type": "chain",
    "start_time": datetime.now().isoformat(),
    "inputs": {"query": "Analyze market trends"},
    "project_name": "market-analysis"
}

# Send to Agent Spy
response = requests.post(
    "http://localhost:8000/api/v1/runs/batch",
    json={"post": [trace_data], "patch": []}
)
```

### Dashboard Access

1. **View Root Traces**: `GET /api/v1/dashboard/runs/roots`
2. **Explore Hierarchy**: `GET /api/v1/dashboard/runs/{trace_id}/hierarchy`
3. **Check Statistics**: `GET /api/v1/dashboard/stats/summary`

### Environment Configuration

Configure Agent Spy behavior using environment variables:

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
ENVIRONMENT=production

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./agentspy.db
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/agentspy
DATABASE_POOL_SIZE=20
DATABASE_ECHO=false

# API Configuration
API_PREFIX=/api/v1
REQUIRE_AUTH=false
API_KEYS=key1,key2,key3

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
CORS_CREDENTIALS=true

# Performance Settings
MAX_TRACE_SIZE_MB=10
REQUEST_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/agentspy.log
```

## 📱 Dashboard Screenshots

### Main Dashboard
The dashboard provides a comprehensive view of all your agent traces with filtering and search capabilities:

![Dashboard](img/Dashboard.png)

### Trace Details View
Detailed trace exploration with hierarchical visualization and execution timeline:

![Details View](img/DetailsView.png)

## 🏛️ Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │   REST API      │    │   Database      │
│                 │    │                 │    │                 │
│ • Master Table  │◄──►│ • Trace Ingest  │◄──►│ • SQLite/Postgres│
│ • Detail View   │    │ • Query Endpoints│    │ • Trace Storage │
│ • Timeline      │    │ • Statistics    │    │ • Relationships │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Model

**Traces (Runs)**
- Hierarchical structure with parent-child relationships
- Rich metadata: inputs, outputs, timing, status
- Project organization and tagging
- Error tracking and debugging information

**Supported Trace Types**
- `chain`: Multi-step agent workflows
- `llm`: Language model interactions
- `tool`: External tool usage (with automatic completion detection)
- `retrieval`: Knowledge base queries
- `prompt`: Template processing operations
- `parser`: Output parsing operations
- `embedding`: Vector embedding operations
- `custom`: User-defined trace types

**Advanced Completion Detection**
Agent Spy uses intelligent pattern-based detection to automatically mark runs as completed when they have both `end_time` and `outputs`, ensuring accurate status tracking across all trace types without manual configuration.

## 🆕 Recent Improvements

### Smart Completion Detection
- **Universal Pattern Recognition**: Automatically detects completion across all run types (tools, chains, prompts, parsers, etc.)
- **Intelligent Status Management**: Marks runs as `completed` when they have both `end_time` and `outputs`
- **Error Handling**: Properly handles failed runs with `end_time` and `error` fields
- **No Configuration Required**: Works out-of-the-box without manual run type whitelisting

### Coordinated Dashboard Refresh
- **Synchronized Updates**: Refresh button updates both root traces table and selected trace details
- **Real-time Status**: Ensures all components show the latest completion status
- **Improved UX**: Single refresh action updates the entire dashboard view
- **Efficient Coordination**: Centralized refresh trigger mechanism prevents inconsistent states

## 🔧 API Reference

### Trace Ingestion

#### Batch Ingest
```http
POST /api/v1/runs/batch
Content-Type: application/json

{
  "post": [/* new traces */],
  "patch": [/* trace updates */]
}
```

#### Individual Operations
```http
POST /api/v1/runs              # Create trace
PATCH /api/v1/runs/{id}        # Update trace
GET /api/v1/runs/{id}          # Get trace details
```

### Dashboard API

#### Root Traces
```http
GET /api/v1/dashboard/runs/roots?project=&status=&search=&limit=50&offset=0
```

#### Trace Hierarchy
```http
GET /api/v1/dashboard/runs/{trace_id}/hierarchy
```

#### Statistics
```http
GET /api/v1/dashboard/stats/summary
```

### Health & Monitoring

```http
GET /health              # Basic health check
GET /health/ready        # Readiness probe
GET /health/live         # Liveness probe
```

## 🧪 Testing

Agent Spy includes a comprehensive test suite:

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/          # Unit tests
uv run pytest tests/e2e/           # End-to-end tests

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Test Categories

- **Unit Tests**: Repository methods, schemas, data validation
- **End-to-End Tests**: Full API integration with real server
- **Performance Tests**: Load testing and response time validation

## 🔒 Security

### Authentication (Planned)
- API key authentication
- Role-based access control
- Project-level permissions

### Data Protection
- Input/output sanitization
- SQL injection prevention
- CORS configuration for web dashboard

## 📈 Performance

### Benchmarks
Performance benchmarks are planned and need to be measured. Key metrics to evaluate:
- **Trace Ingestion Rate**: Traces processed per second
- **Query Response Time**: Dashboard and API response times
- **Storage Efficiency**: Database size vs trace count
- **Memory Usage**: Runtime memory consumption under load

### Optimization Features
- Database connection pooling
- Async request handling
- Efficient SQL queries with proper indexing
- Response caching for dashboard endpoints

## 🛠️ Development

### Project Structure

```
agent-spy/
├── src/
│   ├── api/           # FastAPI route handlers
│   ├── core/          # Database, config, logging
│   ├── models/        # SQLAlchemy models
│   ├── repositories/  # Data access layer
│   └── schemas/       # Pydantic models
├── tests/
│   ├── unit/          # Unit tests
│   ├── e2e/           # End-to-end tests
│   └── integration/   # Integration tests
├── examples/          # Usage examples
└── docs/              # Documentation
```

### Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and add tests**
4. **Run the test suite**: `uv run pytest`
5. **Commit with conventional commits**: `git commit -m "feat: add amazing feature"`
6. **Push and create a pull request**

### Code Style

- **Python**: Follow PEP 8, use `ruff` for linting
- **Type Hints**: Required for all public APIs
- **Testing**: Maintain >90% test coverage
- **Documentation**: Update README and API docs for new features

## 🗺️ Roadmap

### Phase 1: Core Platform ✅
- [x] Basic trace ingestion and storage
- [x] REST API with comprehensive endpoints
- [x] SQLite support for development
- [x] Health monitoring and logging

### Phase 2: Dashboard Interface ✅
- [x] React-based web dashboard
- [x] Master-detail trace exploration
- [x] Real-time updates and filtering
- [x] Coordinated refresh functionality
- [x] Smart completion status detection
- [ ] Timeline visualization

### Phase 3: Advanced Features
- [ ] PostgreSQL production support
- [ ] Authentication and authorization
- [ ] Advanced analytics and insights
- [ ] Alert system for anomalies

### Phase 4: Integrations
- [ ] Popular agent framework integrations
- [ ] Prometheus metrics export
- [ ] Grafana dashboard templates
- [ ] Webhook notifications

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Documentation**: [Full documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/lalanikarim/agent-spy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/lalanikarim/agent-spy/discussions)

## 🙏 Acknowledgments

Built with modern Python tools and best practices:
- **FastAPI** - High-performance web framework
- **SQLAlchemy** - Powerful ORM with async support
- **Pydantic** - Data validation and serialization
- **Pytest** - Comprehensive testing framework
- **uv** - Fast Python package manager

---

**Agent Spy** - Illuminate your AI agents' behavior with comprehensive observability 🔍✨
