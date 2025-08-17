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

### 3. Complex Multi-Step Workflow (`test_complex_langgraph_workflow.py`) 🆕

A sophisticated 7-step linear pipeline demonstrating deep trace hierarchies and structured outputs.

**Features demonstrated:**

- **Multi-step LLM pipeline**: 7 sequential processing stages
- **Multiple output parsers**: String, JSON, and structured Pydantic parsing
- **Structured output generation**: Using Pydantic models for type safety
- **Deep trace hierarchy**: Perfect for testing dashboard visualization
- **Error handling and validation**: Robust processing at each step
- **Historical analysis use case**: Leonardo da Vinci biographical analysis

**Workflow Architecture:**

```
Input → Prompt Template → LLM → Parser → LLM → Parser → Structured LLM → Final Parser → Output
```

**Usage:**

```bash
PYTHONPATH=. uv run python examples/test_complex_langgraph_workflow.py
```

### 4. Dual Chain Agent (`test_dual_chain_agent.py`) 🆕

A LangGraph agent with two nodes, each calling separate LLM chains for comprehensive text analysis.

**Features demonstrated:**

- **Two separate LLM chains**: Each with Prompt Template → LLM → Output Parser
- **Specialized analysis nodes**: Content analyzer and style critic
- **Sequential processing**: Content analysis → Style analysis → Summary
- **Multiple chain architectures**: Shows different trace patterns
- **Text analysis use case**: Comprehensive analysis from multiple perspectives

**Agent Architecture:**

```
Input Text → Content Analyzer Node → Style Critic Node → Summarizer Node → Output
             (Chain 1: Prompt→LLM→Parser)  (Chain 2: Prompt→LLM→Parser)  (Chain 3: Prompt→LLM→Parser)
```

**Usage:**

```bash
PYTHONPATH=. uv run python examples/test_dual_chain_agent.py
```

### 5. Simple Tracing Example (`test_simple_tracing.py`) 🆕

A basic tracing example using LangSmith without external AI services, demonstrating function-level tracing.

**Features demonstrated:**

- **Function-level tracing**: Using `@traceable` decorator on individual functions
- **Mock LLM client**: Simulates AI responses without external API calls
- **Multi-step pipeline**: Text analysis → Summary → Sentiment analysis
- **Structured output**: Returns organized results with metadata
- **No external dependencies**: Self-contained example for testing tracing

**Pipeline Architecture:**

```
Input Text → Text Analyzer → Summary Generator → Sentiment Analyzer → Final Result
```

**Usage:**

```bash
uv run examples/test_simple_tracing.py
```

## Configuration

All examples are configured to:

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
