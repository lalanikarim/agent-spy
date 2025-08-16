# Agent Spy - Project Overview

## What is Agent Spy?

Agent Spy is a powerful, self-hosted observability platform specifically designed for AI agents and multi-step workflows. It provides comprehensive tracing, monitoring, and debugging capabilities for complex agent interactions, making it an essential tool for developers working with LangChain, LangGraph, and other AI agent frameworks.

## Key Value Propositions

### 🔍 **Comprehensive Agent Tracing**
- **Real-time Monitoring**: Track agent executions as they happen
- **Hierarchical Traces**: Visualize complex agent workflows with parent-child relationships
- **Multi-step Analysis**: Follow agent reasoning through tools, LLMs, and decision points
- **Universal Compatibility**: Works with any framework that supports LangSmith-compatible tracing

### 📊 **Advanced Analytics & Visualization**
- **Interactive Dashboard**: Clean, intuitive web interface for trace exploration
- **Real-time Statistics**: Monitor performance metrics, success rates, and resource consumption
- **Filtering & Search**: Find specific traces by project, status, time range, or content
- **Timeline Visualization**: Understand execution flow and identify bottlenecks

### 🏗️ **Production Ready Architecture**
- **High Performance**: Optimized for handling thousands of concurrent traces
- **Scalable Storage**: SQLite for development, PostgreSQL support planned for production
- **API-First Design**: RESTful API for integration with any agent framework
- **Containerized Deployment**: Docker Compose setup for easy deployment

## Architecture Overview

Agent Spy follows a modern, three-tier architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │   FastAPI       │    │   SQLite        │
│   (Dashboard)   │◄──►│   Backend       │◄──►│   Database      │
│                 │    │   (API Server)  │    │   (Storage)     │
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

### 2. React Frontend Dashboard (`frontend/`)
- **Modern React application** built with TypeScript and Vite
- **Ant Design UI components** for professional appearance
- **React Query** for efficient data fetching and caching
- **Master-detail interface** for trace exploration
- **Real-time statistics** and filtering capabilities

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
- `tool`: External tool usage
- `retrieval`: Knowledge base queries
- `prompt`: Template processing
- `parser`: Output parsing operations
- `embedding`: Vector embedding operations
- `custom`: User-defined trace types

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

### 2. Docker Compose (Recommended)
```bash
# Production deployment
docker compose -f docker/docker-compose.yml up -d

# Development with hot reloading
docker compose -f docker/docker-compose.dev.yml up -d
```

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

### 2. Production Monitoring
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

### Infrastructure
- **Docker & Docker Compose** for containerization
- **SQLite** for development (PostgreSQL planned for production)
- **Nginx** for serving frontend assets
- **Health checks** and monitoring built-in

## Project Status & Roadmap

### ✅ Completed Features
- Core trace ingestion and storage
- REST API with LangSmith compatibility
- React dashboard with real-time updates
- Docker containerization
- Smart completion detection
- Health monitoring and logging

### 🚧 In Progress
- Timeline visualization improvements
- Advanced filtering and search
- Performance optimizations
- Documentation and examples

### 📋 Planned Features
- PostgreSQL production support
- Authentication and authorization
- Advanced analytics and insights
- Alert system for anomalies
- Prometheus metrics export
- Popular framework integrations

## Getting Started

1. **Clone the repository**
2. **Choose deployment method** (local development or Docker)
3. **Configure environment** variables as needed
4. **Start Agent Spy** server and dashboard
5. **Configure your agents** to send traces
6. **Explore traces** in the web dashboard

For detailed setup instructions, see the main [README.md](../README.md) or the specific deployment guides in the `docs/` directory.
