# Agent Spy - Project Overview

## What is Agent Spy?

Agent Spy is a powerful, self-hosted observability platform specifically designed for AI agents and multi-step workflows. It provides comprehensive tracing, monitoring, and debugging capabilities for complex agent interactions, making it an essential tool for developers working with LangChain, LangGraph, and other AI agent frameworks.

## Key Value Propositions

### 🔍 **Comprehensive Agent Tracing**

- **Real-time Monitoring**: Track agent executions as they happen
- **Hierarchical Traces**: Visualize complex agent workflows with parent-child relationships
- **Multi-step Analysis**: Follow agent reasoning through tools, LLMs, and decision points
- **Universal Compatibility**: Works with any framework that supports LangSmith-compatible tracing
- **Smart Completion Detection**: Automatic pattern-based detection for accurate run status tracking

### 📊 **Advanced Analytics & Visualization**

- **Interactive Dashboard**: Clean, intuitive web interface for trace exploration
- **Real-time Statistics**: Monitor performance metrics, success rates, and resource consumption
- **Filtering & Search**: Find specific traces by project, status, time range, or content
- **Timeline Visualization**: Advanced timeline component for execution flow analysis
- **Coordinated Refresh**: Synchronized updates across all dashboard components

### 🏗️ **Architecture**

- **High Performance**: Optimized for handling thousands of concurrent traces
- **Scalable Storage**: SQLite for development, PostgreSQL support planned for production
- **API-First Design**: RESTful API for integration with any agent framework
- **Containerized Deployment**: Docker Compose setup for easy deployment
- **Comprehensive Testing**: 51% test coverage with 32 passing tests

## Architecture Overview

Agent Spy follows a modern, three-tier architecture:

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

## Core Components

### 1. Backend API Server (`src/`)

- **FastAPI-based REST API** with async support
- **LangSmith-compatible endpoints** for seamless integration
- **Comprehensive data models** using SQLAlchemy and Pydantic
- **Health monitoring** and logging infrastructure
- **Smart completion detection** for accurate run status tracking
- **Repository pattern** for clean data access layer

### 2. React Frontend Dashboard (`frontend/`)

- **Modern React application** built with TypeScript and Vite
- **Ant Design UI components** for professional appearance
- **React Query** for efficient data fetching and caching
- **Master-detail interface** for trace exploration
- **Real-time statistics** and filtering capabilities
- **Advanced timeline visualization** with vis-timeline

### 3. Docker Infrastructure (`docker/`)

- **Production and development** Docker Compose configurations
- **Multi-stage builds** for optimized container images
- **Volume management** for data persistence
- **Health checks** and container orchestration
- **Environment-based configuration**

## Data Model

### Traces (Runs)

Agent Spy stores all trace data in a hierarchical structure:

- **Root Traces**: Top-level agent executions (parent_run_id = null)
- **Child Runs**: Sub-operations like tool calls, LLM invocations, etc.
- **Rich Metadata**: Inputs, outputs, timing, status, error information
- **Project Organization**: Group traces by project for better organization
- **Relationships**: Parent-child links for hierarchical visualization

### Supported Run Types

- `chain`: Multi-step agent workflows
- `llm`: Language model interactions
- `tool`: External tool usage (with automatic completion detection)
- `retrieval`: Knowledge base queries
- `prompt`: Template processing operations
- `parser`: Output parsing operations
- `embedding`: Vector embedding operations
- `custom`: User-defined trace types

### Smart Completion Detection

Agent Spy uses intelligent pattern-based detection to automatically mark runs as completed when they have both `end_time` and `outputs`, ensuring accurate status tracking across all trace types without manual configuration.

## Integration Patterns

### LangSmith Compatibility

Agent Spy is designed to be a drop-in replacement for LangSmith:

```python
# Standard LangSmith configuration
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "http://localhost:8000/api/v1"
os.environ["LANGSMITH_API_KEY"] = "your-api-key"
os.environ["LANGSMITH_PROJECT"] = "your-project-name"
```

### Framework Support

- **LangChain**: Full compatibility with all LangChain components
- **LangGraph**: Support for complex multi-node agent workflows
- **Custom Agents**: REST API for any framework to send trace data

## Deployment Options

### 1. Development Setup

```bash
# Quick local development
uv sync
PYTHONPATH=. uv run python src/main.py
```

### 2. Container Deployment (Docker Compose)

See `docs/DOCKER_SETUP.md` for container deployment instructions. Podman Compose is also supported; Docker commands are provided for reference.

### 3. Container Orchestration

- Kubernetes manifests (planned)
- Docker Swarm compatibility
- Cloud provider integrations

## Use Cases

### 1. Development & Debugging

- **Trace Complex Workflows**: Understand how multi-step agents execute
- **Debug Failed Runs**: Identify where and why agent executions fail
- **Performance Analysis**: Find bottlenecks in agent reasoning chains
- **Input/Output Inspection**: Examine data flow between components

### 2. Monitoring

- **Real-time Observability**: Monitor live agent performance
- **Error Tracking**: Get alerts when agents fail or perform poorly
- **Usage Analytics**: Understand how agents are being used
- **Resource Monitoring**: Track token usage and API costs

### 3. Research & Analysis

- **Experiment Tracking**: Compare different agent configurations
- **Behavioral Analysis**: Study agent decision-making patterns
- **Performance Benchmarking**: Measure improvements over time
- **Data Collection**: Gather training data from agent interactions

## Technology Stack

### Backend

- **Python 3.13+** with modern async/await patterns
- **FastAPI** for high-performance API development
- **SQLAlchemy 2.0** with async support for database operations
- **Pydantic** for data validation and serialization
- **uv** for fast dependency management

### Frontend

- **React 19** with TypeScript for type safety
- **Vite** for fast development and optimized builds
- **Ant Design** for professional UI components
- **TanStack Query** for efficient data fetching
- **Tailwind CSS** for utility-first styling
- **vis-timeline** for advanced timeline visualization

### Infrastructure

- **Docker & Docker Compose** for containerization
- **SQLite** for development (PostgreSQL planned for production)
- **Nginx** for serving frontend assets
- **Health checks** and monitoring built-in

## Project Status

### ✅ Completed Features

- Core trace ingestion and storage
- REST API with LangSmith compatibility
- React dashboard with real-time updates
- Docker containerization
- Smart completion detection
- Coordinated dashboard refresh
- Health monitoring and logging
- Comprehensive examples and testing

### 🚧 In Progress

- Performance optimizations
- Advanced filtering and search improvements
- Timeline visualization enhancements
- Documentation updates

### 📋 Planned Features

- PostgreSQL production support
- Authentication and authorization
- Advanced analytics and insights
- Alert system for anomalies
- Prometheus metrics export
- Popular framework integrations

## Recent Improvements

### Smart Completion Detection

- **Universal Pattern Recognition**: Automatically detects completion across all run types
- **Intelligent Status Management**: Marks runs as `completed` when they have both `end_time` and `outputs`
- **Error Handling**: Properly handles failed runs with `end_time` and `error` fields
- **No Configuration Required**: Works out-of-the-box without manual run type whitelisting

### Coordinated Dashboard Refresh

- **Synchronized Updates**: Refresh button updates both root traces table and selected trace details
- **Real-time Status**: Ensures all components show the latest completion status
- **Improved UX**: Single refresh action updates the entire dashboard view
- **Efficient Coordination**: Centralized refresh trigger mechanism prevents inconsistent states

### Examples

See `docs/EXAMPLES_GUIDE.md` for end-to-end examples and usage patterns.

## Getting Started

1. **Clone the repository**
2. **Choose deployment method** (local development or Docker)
3. **Configure environment** variables as needed
4. **Start Agent Spy** server and dashboard
5. **Configure your agents** to send traces
6. **Explore traces** in the web dashboard

For detailed setup instructions, see the main [README.md](../README.md) or the specific deployment guides in the `docs/` directory.

## Documentation Structure

- **[README.md](../README.md)**: Main project overview and quick start
- **[API Reference](API_REFERENCE.md)**: Comprehensive API documentation
- **[Development Guide](DEVELOPMENT_GUIDE.md)**: Developer setup and contribution guidelines
- **[Architecture](ARCHITECTURE.md)**: Detailed system architecture
- **[Backend API](BACKEND_API.md)**: Backend-specific documentation
- **[Frontend Dashboard](FRONTEND_DASHBOARD.md)**: Frontend component documentation
- **[Docker Setup](DOCKER_SETUP.md)**: Container deployment guide
- **[Examples Guide](EXAMPLES_GUIDE.md)**: Usage examples and tutorials

## Community & Support

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Comprehensive guides in the `docs/` directory
- **Examples**: Working examples in the `examples/` directory

## Contributing

Agent Spy welcomes contributions from the community! See the [Development Guide](DEVELOPMENT_GUIDE.md) for detailed information on:

- Setting up a development environment
- Code standards and testing requirements
- Contribution workflow
- Documentation guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
