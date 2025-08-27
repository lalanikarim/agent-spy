# Agent Spy 🕵️

A powerful, self-hosted observability platform for AI agents and multi-step workflows. Agent Spy provides comprehensive tracing, monitoring, and debugging capabilities for complex agent interactions with **API specification compatible with LangSmith endpoints** for seamless integration.

## ⚖️ Legal Disclaimer

Agent Spy is an independent, open-source project and is not affiliated with, endorsed by, or sponsored by LangChain AI or the LangSmith platform. The use of the term "LangSmith" is for compatibility purposes only and does not imply any association with LangChain AI. All trademarks and registered trademarks are the property of their respective owners.

This project implements an API specification compatible with LangSmith endpoints to enable integration with existing LangChain SDK configurations. The implementation is original work developed independently without access to LangSmith's proprietary source code.

## ⚠️ Disclaimer & Project Status

Agent Spy is an experimental project provided "as is" under the MIT License, without warranty of any kind. It is intended for research, development, and personal use.

This software is not recommended for production environments. Users assume all risks associated with its use, including but not limited to data loss, system instability, and unexpected behavior.

While Agent Spy aims to provide a powerful open-source alternative for AI observability, it is not a replacement for enterprise-grade, commercially supported solutions like LangSmith. For business-critical applications, we recommend using a commercially supported and validated product.

## 🌟 Features

### 🔍 **Comprehensive Agent Tracing**

- **Real-time Monitoring**: Track agent executions as they happen with live WebSocket updates
- **Live Dashboard Updates**: See traces appear instantly without manual refresh
- **Hierarchical Traces**: Visualize complex agent workflows with parent-child relationships
- **Multi-step Analysis**: Follow agent reasoning through tools, LLMs, and decision points
- **Smart Completion Detection**: Universal pattern-based detection for accurate run status across all trace types
- **Performance Metrics**: Monitor execution times, token usage, and resource consumption
- **WebSocket URL Resolution**: Intelligent WebSocket URL inference with browser host fallback
- **Vite WebSocket Proxy**: Development server WebSocket proxying for seamless local development

### 📊 **Advanced Analytics & Dashboard**

- **Interactive Dashboard**: Clean, intuitive web interface for trace exploration
- **Real-time Updates**: Live WebSocket updates with instant trace notifications
- **Live Connection Status**: Visual indicators for WebSocket connection health
- **Coordinated Refresh**: Synchronized updates across trace table and detail views
- **Filtering & Search**: Find specific traces by project, status, time range, or content
- **Statistics & Insights**: Understand agent behavior patterns and performance trends
- **Timeline Visualization**: Advanced timeline component for execution flow analysis
- **Advanced Theming**: Comprehensive theme system with dark/light mode support
- **Responsive Design**: Optimized for desktop and mobile viewing

### 🏗️ **Development & Research Ready**

- **High Performance**: Optimized for handling thousands of concurrent traces
- **Scalable Storage**: SQLite for development; PostgreSQL supported
- **API-First Design**: RESTful API for integration with any agent framework
- **Comprehensive Testing**: Unit, integration, and end-to-end test coverage (51% coverage, 65 tests passing, 2 skipped)
- **Containerized Deployment**: Docker Compose setup for easy deployment with improved service naming
- **OTLP Integration**: 9 comprehensive integration tests for OpenTelemetry Protocol
- **Dev Container Support**: Comprehensive VS Code dev container configuration with PostgreSQL and Jaeger

### 🔌 **Framework Compatibility**

- **LangSmith API Specification Compatible**: Self-hosted alternative for AI agent observability
- **OpenTelemetry Protocol (OTLP) Support**: Native OTLP HTTP and gRPC receivers for industry-standard tracing
- **LangChain Support**: Full compatibility with all LangChain components
- **LangGraph Support**: Multi-node agent workflows with complex hierarchies
- **Custom Agents**: REST API for any framework to send trace data

## 🎉 **Docker Compose Verification - COMPLETED ✅**

**Status**: ✅ **VERIFICATION COMPLETE**
**Success Rate**: **100% (12/12 examples working)**
**Total Traces Created**: **208 traces**
**Completion Date**: August 19, 2025

All Docker Compose verification tasks have been completed successfully. All three categories of examples are now working perfectly:

### ✅ **LangSmith Examples (5/5 Working)**

- `test_simple_tracing.py` - Basic LangSmith tracing
- `test_langchain_app.py` - LangChain application with Ollama
- `test_langgraph_agent.py` - LangGraph agent with Ollama
- `test_complex_langgraph_workflow.py` - Complex LangGraph workflow
- `test_dual_chain_agent.py` - Dual chain agent

### ✅ **OTeL to HTTP Examples (3/3 Working)**

- `ollama_otel_instrumentation.py` - OpenTelemetry with Ollama
- `ollama_direct_http.py` - Direct HTTP with protobuf conversion
- `simple_ollama_test.py` - Simple Ollama connection test

### ✅ **OTeL to gRPC Examples (4/4 Working)**

- `nested_workflow_otlp_grpc.py` - Nested workflow with HTTP
- `nested_workflow_otlp_grpc_real.py` - Real gRPC with single-span sending
- `multi_step_otlp_workflow.py` - Multi-step workflow
- `openai_otel_instrumentation.py` - OpenAI-compatible API with Ollama

### 🔧 **Environment Variables for Testing**

#### **For Ollama Examples:**

```bash
export OLLAMA_HOST="http://192.168.1.200:11434"
```

#### **For OpenAI-Compatible API:**

```bash
export OPENAI_API_KEY="dummy-key"
export OPENAI_API_BASE="http://192.168.1.200:11434/v1"
export OPENAI_MODEL_NAME="qwen2.5:7b"
```

#### **For LangSmith Examples:**

```bash
export LANGSMITH_TRACING="true"
export LANGSMITH_ENDPOINT="http://localhost:8000/api/v1"
export LANGSMITH_API_KEY="test-key"
export LANGSMITH_PROJECT="agent-spy-demo"
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- [Docker](https://docker.com/) (optional, for containerized deployment)

### Local Development

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
   # Set up environment variables for Ollama
   export OLLAMA_HOST="http://192.168.1.200:11434"

   # LangSmith Examples (5 examples)
   uv run python examples/test_simple_tracing.py
   uv run python examples/test_langchain_app.py
   uv run python examples/test_langgraph_agent.py
   uv run python examples/test_complex_langgraph_workflow.py
   uv run python examples/test_dual_chain_agent.py

   # OTeL HTTP Examples (3 examples)
   uv run python examples/ollama_otel_instrumentation.py
   uv run python examples/ollama_direct_http.py
   uv run python examples/simple_ollama_test.py

   # OTeL gRPC Examples (4 examples)
   uv run python examples/nested_workflow_otlp_grpc.py
   uv run python examples/nested_workflow_otlp_grpc_real.py
   uv run python examples/multi_step_otlp_workflow.py

   # OpenAI-compatible API Example
   export OPENAI_API_KEY="dummy-key"
   export OPENAI_API_BASE="http://192.168.1.200:11434/v1"
   export OPENAI_MODEL_NAME="qwen2.5:7b"
   uv run python examples/openai_otel_instrumentation.py
   ```

### Docker Deployment

For development, research, or testing environments using containerized deployment:

1. **Clone and configure**

   ```bash
   git clone https://github.com/lalanikarim/agent-spy.git
   cd agent-spy
   cp env.example .env
   ```

2. **Start Agent Spy (Production)**

   ```bash
   # Using the convenience script
   bash scripts/docker-start.sh

   # Or manually with docker compose
   docker compose -f docker/docker-compose.yml up -d
   ```

3. **Start Agent Spy (Development with Hot Reload)**

   ```bash
   # Using the convenience script
   bash scripts/docker-dev.sh

   # Or manually with docker compose
   docker compose -f docker/docker-compose.dev.yml up -d
   ```

**Access the application:**

- **Web Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **OTLP HTTP Endpoint**: http://localhost:8000/v1/traces/ (shares main API port)
- **OTLP gRPC Endpoint**: localhost:4317 (dedicated port)

## 📖 Usage

### Agent Integration

To send traces from your agents to Agent Spy, configure these environment variables in your agent application:

#### LangSmith API Compatibility

```bash
# Enable tracing (compatible with LangChain SDK)
LANGSMITH_TRACING=true

# Point to Agent Spy (compatible with LangSmith API specification)
LANGSMITH_ENDPOINT=http://localhost:8000/api/v1

# API key (can be any value for now, authentication is optional)
LANGSMITH_API_KEY=your-api-key

# Project name for organizing traces
LANGSMITH_PROJECT=your-project-name
```

#### OpenTelemetry Protocol (OTLP)

```bash
# OTLP HTTP endpoint (shares main API port)
OTLP_ENDPOINT=http://localhost:8000/v1/traces/

# OTLP gRPC endpoint (dedicated port)
OTLP_GRPC_ENDPOINT=localhost:4317

# Service name for OTLP traces
OTEL_SERVICE_NAME=your-agent-service
```

### Basic Trace Ingestion

Agent Spy accepts traces through multiple protocols:

#### LangSmith API Specification (REST)

Agent Spy accepts traces through a REST API compatible with the LangSmith API specification:

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

#### OpenTelemetry Protocol (OTLP)

Agent Spy also supports the OpenTelemetry Protocol for industry-standard tracing:

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:8000/v1/traces/"
)

# Set up tracing
provider = TracerProvider()
processor = SimpleSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Create spans
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("agent-operation") as span:
    span.set_attribute("input.prompt", "Analyze market trends")
    # Your agent logic here
    span.set_attribute("output.response", "Market analysis complete")
```

### Dashboard Access

1. **View Root Traces**: `GET /api/v1/dashboard/runs/roots`
2. **Explore Hierarchy**: `GET /api/v1/dashboard/runs/{trace_id}/hierarchy`
3. **Check Statistics**: `GET /api/v1/dashboard/stats/summary`

## 🏛️ Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Dashboard│    │   FastAPI       │    │   SQLite        │
│   (TypeScript)  │◄──►│   Backend       │◄──►│   Database      │
│                 │    │   (Python 3.13) │    │   (Storage)     │
│ • Trace Table   │    │ • Trace Ingest  │    │ • Runs/Traces   │
│ • Detail View   │    │ • Query API     │    │ • Relationships │
│ • Statistics    │    │ • Dashboard API │    │ • Metadata      │
│ • Timeline      │    │ • Health Checks │    │ • Projects      │
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

### WebSocket Connectivity & Docker Improvements

- **WebSocket URL Resolution**: Intelligent URL inference with browser host fallback for relative API URLs
- **Vite WebSocket Proxy**: Development server WebSocket proxying for seamless local development
- **Docker Service Naming**: Improved service naming to avoid conflicts between dev/prod environments
- **Dev Container Enhancement**: Comprehensive VS Code dev container setup with PostgreSQL and Jaeger
- **Database Configuration**: Fixed SQLite URL handling logic for better compatibility
- **Documentation Updates**: Updated Docker setup guides for PostgreSQL production deployment

### OpenTelemetry Protocol (OTLP) Integration

- **OTLP HTTP Receiver**: Accepts traces via HTTP POST to `/v1/traces/`
- **OTLP gRPC Receiver**: Accepts traces via gRPC Export service
- **Real-time WebSocket Updates**: Live notifications for OTLP trace events
- **Span Conversion**: Automatic conversion from OTLP spans to Agent Spy runs
- **Hierarchical Support**: Full parent-child relationship preservation
- **Status Mapping**: OTLP status codes mapped to Agent Spy status
- **Attribute Preservation**: All OTLP attributes preserved in trace metadata
- **Comprehensive Testing**: 9 integration tests covering all major OTLP scenarios

### WebSocket Real-Time Updates

- **Live Dashboard Updates**: See traces appear instantly without manual refresh
- **Real-time Notifications**: Toast notifications for trace creation, completion, and failures
- **WebSocket Connection Management**: Automatic reconnection and connection status indicators
- **Event-driven Updates**: React Query integration for efficient cache invalidation
- **User Control**: Toggle to enable/disable real-time updates
- **Performance Optimized**: Efficient event filtering and subscription management

### Advanced Theme System

- **Dark/Light Mode**: Comprehensive theme switching with persistent preferences
- **Customizable UI**: Advanced theming system with CSS-in-JS support
- **Responsive Design**: Optimized layouts for desktop and mobile devices
- **Professional Styling**: Modern UI components with consistent design language

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

### Enhanced Examples

- **Complex Multi-Step Workflow**: 7-step linear pipeline with deep trace hierarchies
- **Dual Chain Agent**: Multiple LLM chains with specialized analysis nodes
- **OTLP Integration Examples**: Complete OTLP workflow examples with HTTP and gRPC
- **Comprehensive Testing**: Examples demonstrate various trace patterns and use cases

## 🔧 API Reference

### Trace Ingestion

#### LangSmith API (Batch Ingest)

```http
POST /api/v1/runs/batch
Content-Type: application/json

{
  "post": [/* new traces */],
  "patch": [/* trace updates */]
}
```

#### LangSmith API (Individual Operations)

```http
POST /api/v1/runs              # Create trace
PATCH /api/v1/runs/{id}        # Update trace
GET /api/v1/runs/{id}          # Get trace details
```

#### OpenTelemetry Protocol (OTLP)

```http
POST /v1/traces/
Content-Type: application/x-protobuf

[OTLP protobuf trace data]
```

**OTLP Features:**

- HTTP receiver (shares main API port 8000)
- gRPC receiver (dedicated port 4317)
- Real-time WebSocket notifications
- Automatic span-to-run conversion
- Hierarchical trace support
- Status code mapping
- Attribute preservation
- Configurable paths and ports

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

### Code Quality

```bash
# Linting
uv run ruff check src/

# Type checking
uv run basedpyright src/

# Security scanning
uv run bandit -r src/
```

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

### Current Benchmarks

- **Test Coverage**: 51% (65 tests passing, 2 skipped)
- **Code Quality**: All linting and type checks passing
- **Response Time**: Sub-second API responses for typical queries
- **Memory Usage**: Optimized for concurrent trace processing
- **Frontend Components**: 12+ React components with TypeScript
- **Backend Files**: 25+ Python files with comprehensive API coverage
- **OTLP Integration**: 9 comprehensive integration tests
- **Documentation**: 13 well-organized guides with minimal redundancy

### Optimization Features

- Database connection pooling
- Async request handling
- Efficient SQL queries with proper indexing
- Response caching for dashboard endpoints

## 🛠️ Development

### Project Structure

```
agent-spy/
├── src/                    # Backend source code
│   ├── api/               # FastAPI route handlers
│   ├── core/              # Database, config, logging
│   ├── models/            # SQLAlchemy models
│   ├── repositories/      # Data access layer
│   ├── schemas/           # Pydantic models
│   └── services/          # Business logic layer
├── frontend/              # React dashboard
│   ├── src/               # React components
│   │   ├── components/    # UI components
│   │   ├── contexts/      # React contexts
│   │   ├── hooks/         # Custom hooks
│   │   ├── theme/         # Theme system
│   │   └── api/           # API client
│   ├── public/            # Static assets
│   └── package.json       # Dependencies
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── e2e/               # End-to-end tests
│   └── integration/       # Integration tests
├── examples/              # Usage examples
├── docs/                  # Documentation
├── docker/                # Docker configurations
└── scripts/               # Utility scripts
```

### Technology Stack

**Backend**

- **Python 3.13+** with modern async/await patterns
- **FastAPI** for high-performance API development
- **SQLAlchemy 2.0** with async support for database operations
- **Pydantic** for data validation and serialization
- **uv** for fast dependency management
- **OpenTelemetry** for industry-standard tracing support

**Frontend**

- **React 19** with TypeScript for type safety
- **Vite** for fast development and optimized builds
- **Ant Design** for professional UI components
- **TanStack Query** for efficient data fetching
- **Tailwind CSS 4.1** for utility-first styling
- **Advanced Theming**: CSS-in-JS system with dark/light mode
- **Recharts** for data visualization
- **vis-timeline** for advanced timeline visualization

**Infrastructure**

- **Docker & Docker Compose** for containerization
- **SQLite** for development; **PostgreSQL** supported
- **Nginx** for serving frontend assets
- **Health checks** and monitoring built-in

### Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and add tests**
4. **Run the test suite**: `uv run pytest`
5. **Check code quality**: `uv run ruff check src/ && uv run basedpyright src/`
6. **Commit with conventional commits**: `git commit -m "feat: add amazing feature"`
7. **Push and create a pull request**

### Code Style

- **Python**: Follow PEP 8, use `ruff` for linting
- **Type Hints**: Required for all public APIs
- **Testing**: Maintain >90% test coverage (currently 51%)
- **Documentation**: Update README and API docs for new features

## 🗺️ Roadmap

### Phase 1: Core Platform ✅

- [x] Basic trace ingestion and storage
- [x] REST API with comprehensive endpoints
- [x] SQLite support for development
- [x] Health monitoring and logging
- [x] Smart completion detection
- [x] Coordinated dashboard refresh

### Phase 2: Dashboard Interface ✅

- [x] React-based web dashboard
- [x] Master-detail trace exploration
- [x] Real-time updates and filtering
- [x] Advanced timeline visualization
- [x] Statistics and metrics display
- [x] Advanced theme system with dark/light mode
- [x] Responsive design for mobile and desktop
- [x] Real-time notifications and status updates

### Phase 3: Advanced Features 🚧

- [x] PostgreSQL support
- [x] OpenTelemetry Protocol (OTLP) integration
- [ ] Authentication and authorization

### Phase 4: Integrations 📋

- [ ] Kubernetes deployment manifests

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
- **React** - Modern frontend framework
- **Ant Design** - Professional UI components
- **Tailwind CSS** - Utility-first CSS framework
- **TanStack Query** - Data fetching and caching

**Note**: This project is not affiliated with LangChain AI or the LangSmith platform. The API compatibility is implemented independently based on public API specifications. OpenTelemetry Protocol support provides industry-standard tracing capabilities.

---

**Agent Spy** - Illuminate your AI agents' behavior with comprehensive observability 🔍✨
