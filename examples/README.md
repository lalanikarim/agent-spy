# Agent Spy Examples

This directory contains example scripts demonstrating how to use Agent Spy with various LangChain applications.

## Examples

### 1. Basic LangChain Integration (`test_langchain_app.py`)
A simple example showing how to configure LangChain to send traces to Agent Spy using a basic LLM call.

**Features demonstrated:**
- Basic LangChain tracing configuration
- Simple LLM invocation with Ollama
- Trace data capture and storage

**Usage:**
```bash
PYTHONPATH=. uv run python examples/test_langchain_app.py
```

### 2. LangGraph Agent (`test_langgraph_agent.py`)
A more complex example using LangGraph to create an agent with LLM and tool nodes.

**Features demonstrated:**
- Multi-node agent execution
- Tool invocation (clock tool)
- Complex trace hierarchy capture
- Parent-child relationship tracking
- Conditional routing between nodes

**Usage:**
```bash
PYTHONPATH=. uv run python examples/test_langgraph_agent.py
```

## Configuration

Both examples are configured to:
- **Ollama server**: `aurora.local:11434`
- **Model**: `qwen3:8b`
- **Agent Spy endpoint**: `http://localhost:8000/api/v1`
- **Tracing**: Enabled via `LANGCHAIN_TRACING_V2=true`

## Prerequisites

1. **Agent Spy server** running on `localhost:8000`
2. **Ollama server** accessible at `aurora.local:11434`
3. **qwen3:8b model** available in Ollama

## Viewing Traces

After running the examples, you can view the captured traces:

1. **Stats endpoint**: `curl http://localhost:8000/api/v1/stats`
2. **Database direct**: `sqlite3 agentspy.db "SELECT * FROM runs ORDER BY created_at DESC LIMIT 10;"`
3. **Server logs**: Check the Agent Spy server console for detailed trace ingestion logs
