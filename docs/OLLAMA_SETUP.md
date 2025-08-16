# Ollama Setup for Agent Spy Testing

This guide helps you set up Ollama for testing Agent Spy's LangChain integration.

## Quick Setup

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [ollama.ai](https://ollama.ai/)

### 2. Start Ollama Server

```bash
ollama serve
```

The server will run on `http://localhost:11434`

### 3. Pull a Small Model for Testing

For quick testing, use a small model:

```bash
# Recommended: Small and fast
ollama pull llama3.2:1b

# Alternatives:
ollama pull qwen2:0.5b    # Very small
ollama pull phi3:mini     # Microsoft's small model
ollama pull llama3.2:3b   # Larger but still reasonable
```

### 4. Test Ollama

```bash
# Test the model works
ollama run llama3.2:1b "Hello, how are you?"

# List available models
ollama list
```

## Integration with Agent Spy

Once Ollama is running with a model, you can test the integration:

```bash
# Make sure Agent Spy is running
PYTHONPATH=. uv run python src/main.py &

# Run the LangChain integration test
PYTHONPATH=. uv run python scripts/test_langchain_app.py
```

## Model Recommendations

For **development/testing**:
- `llama3.2:1b` - Fast, good for testing (1.3GB)
- `qwen2:0.5b` - Very fast, minimal resources (352MB)

For **production**:
- `llama3.2:3b` - Good balance of speed/quality (2.0GB)
- `llama3.1:8b` - High quality responses (4.7GB)

## Troubleshooting

### Ollama Not Starting
```bash
# Check if port 11434 is in use
lsof -i :11434

# Kill existing ollama processes
pkill ollama

# Start ollama again
ollama serve
```

### Model Not Found
```bash
# List available models
ollama list

# Pull the model if missing
ollama pull llama3.2:1b
```

### Memory Issues
- Use smaller models (`llama3.2:1b`, `qwen2:0.5b`)
- Close other applications
- Check available RAM: `free -h` (Linux) or Activity Monitor (macOS)

### Connection Issues
- Ensure Ollama is running: `curl http://localhost:11434/api/tags`
- Check firewall settings
- Try restarting Ollama

## Environment Variables

The test script automatically sets these for Agent Spy integration:

```bash
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_ENDPOINT="http://localhost:8000/api/v1"
export LANGCHAIN_API_KEY="test-api-key-123"
export LANGCHAIN_PROJECT="agent-spy-demo"
```

## Next Steps

After successful setup:
1. Run the integration test: `PYTHONPATH=. uv run python scripts/test_langchain_app.py`
2. Check Agent Spy logs for received traces
3. Proceed with Phase 2 development to implement actual trace handling
