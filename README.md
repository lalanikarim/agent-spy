# Agent Spy

A LangSmith-compatible observability layer for AI agents and LangChain applications. Agent Spy provides local trace collection and analysis capabilities, allowing you to monitor and debug your AI applications without relying on external services.

## Features

- **LangSmith Compatible**: Drop-in replacement for LangSmith tracing endpoints
- **Local Deployment**: Keep your trace data private and secure
- **FastAPI Backend**: High-performance async API with automatic documentation  
- **SQLite/PostgreSQL**: Flexible database options for development and production
- **Real-time Monitoring**: Live trace collection and analysis
- **Easy Integration**: Works with existing LangChain applications via environment variables

## Quick Start

### Environment Variables

Point your LangChain application to Agent Spy by setting these environment variables:

```bash
export LANGCHAIN_ENDPOINT="http://localhost:8000/api/v1"
export LANGCHAIN_API_KEY="your-api-key"
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_PROJECT="your-project-name"
```

### Running Agent Spy

```bash
# Install dependencies
uv sync

# Start the server
uv run python src/main.py
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## Development Status

This project is currently in active development. See the [implementation plan](docs/plans/langsmith-compatible-observability-layer.md) for detailed progress tracking.

## Project Structure

```
agentspy/
├── src/
│   ├── api/          # FastAPI route handlers
│   ├── core/         # Core configuration and utilities
│   ├── db/           # Database connection and setup
│   ├── models/       # SQLAlchemy database models
│   ├── repositories/ # Data access layer
│   ├── schemas/      # Pydantic data models
│   ├── services/     # Business logic
│   └── main.py       # Application entry point
├── tests/            # Test suite
├── docs/             # Documentation and planning
└── scripts/          # Utility scripts
```

## Contributing

This project follows conventional commit messages and uses:
- **uv** for dependency management
- **FastAPI** for the web framework
- **SQLAlchemy** for database ORM
- **Pydantic** for data validation
- **pytest** for testing
- **ruff** for linting and formatting
