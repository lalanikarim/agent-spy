# Agent Spy 🕵️

A powerful, self-hosted observability platform for AI agents and multi-step workflows. Agent Spy provides comprehensive tracing, monitoring, and debugging capabilities for complex agent interactions.

## 🌟 Features

### 🔍 **Comprehensive Agent Tracing**
- **Real-time Monitoring**: Track agent executions as they happen
- **Hierarchical Traces**: Visualize complex agent workflows with parent-child relationships
- **Multi-step Analysis**: Follow agent reasoning through tools, LLMs, and decision points
- **Performance Metrics**: Monitor execution times, token usage, and resource consumption

### 📊 **Advanced Analytics**
- **Dashboard Interface**: Clean, intuitive web interface for trace exploration
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

## 📖 Usage

### Agent Integration

To send traces from your agents to Agent Spy, configure these environment variables in your agent application:

```bash
# Enable tracing
LANGCHAIN_TRACING_V2=true

# Point to Agent Spy instead of LangSmith
LANGCHAIN_ENDPOINT=http://localhost:8000/api/v1

# API key (can be any value for now, authentication is optional)
LANGCHAIN_API_KEY=your-api-key

# Project name for organizing traces
LANGCHAIN_PROJECT=your-project-name
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
- `tool`: External tool usage
- `retrieval`: Knowledge base queries
- `custom`: User-defined trace types

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

### Phase 2: Dashboard Interface (In Progress)
- [ ] React-based web dashboard
- [ ] Master-detail trace exploration
- [ ] Real-time updates and filtering
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