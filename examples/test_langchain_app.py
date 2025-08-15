#!/usr/bin/env python3
"""
Test LangChain application for Agent Spy integration.

This script demonstrates how to use LangChain with local Ollama
and send traces to Agent Spy for observability.

Prerequisites:
1. Agent Spy server running on http://localhost:8000
2. Ollama running on http://localhost:11434
3. A small model like llama3.2:1b pulled in Ollama

Usage:
    PYTHONPATH=. uv run python scripts/test_langchain_app.py
"""

import os
import sys
import time

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def setup_agent_spy_tracing():
    """Configure LangChain to send traces to Agent Spy."""
    print("🔧 Configuring LangChain tracing for Agent Spy...")

    # Configure LangChain to send traces to our local Agent Spy server
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = "http://localhost:8000/api/v1"
    os.environ["LANGSMITH_API_KEY"] = "test-api-key-123"
    os.environ["LANGSMITH_PROJECT"] = "agent-spy-demo"

    print(f"  ✅ Tracing enabled: {os.environ['LANGSMITH_TRACING']}")
    print(f"  ✅ Endpoint: {os.environ['LANGSMITH_ENDPOINT']}")
    print(f"  ✅ Project: {os.environ['LANGSMITH_PROJECT']}")


def check_agent_spy_health() -> bool:
    """Check if Agent Spy server is running."""
    try:
        import requests

        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Agent Spy is healthy (v{data.get('version', 'unknown')})")
            return True
        else:
            print(f"  ❌ Agent Spy health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Agent Spy not accessible: {e}")
        return False


def check_ollama_availability() -> str | None:
    """Check if Ollama is running and find an available model."""
    try:
        import requests

        # Check if Ollama is running
        response = requests.get("http://aurora.local:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print(f"  ❌ Ollama API not accessible: {response.status_code}")
            return None

        models = response.json().get("models", [])
        if not models:
            print("  ❌ No models found in Ollama")
            return None

        # Look for a small model suitable for testing
        preferred_models = ["qwen3:1.7b", "llama3.2:1b", "llama3.2", "llama2", "phi3", "qwen2:0.5b"]
        available_models = [model["name"] for model in models]

        print(f"  📋 Available models: {', '.join(available_models)}")

        for preferred in preferred_models:
            if preferred in available_models:
                print(f"  ✅ Using model: {preferred}")
                return preferred

        # If no preferred model, use the first available
        model_name = available_models[0]
        print(f"  ✅ Using first available model: {model_name}")
        return model_name

    except Exception as e:
        print(f"  ❌ Ollama not accessible: {e}")
        return None


def run_basic_llm_test(model_name: str):
    """Run a basic LLM test with tracing."""
    print("\n🤖 Running basic LLM test...")

    try:
        from langchain_ollama import OllamaLLM

        # Initialize Ollama LLM
        llm = OllamaLLM(
            model=model_name,
            base_url="http://aurora.local:11434",
            temperature=0.1,
        )

        # Test prompt
        prompt = "What is artificial intelligence? Answer in one sentence."

        print(f"  📝 Prompt: {prompt}")
        print("  🔄 Generating response...")

        # Invoke the LLM - this should generate traces
        response = llm.invoke(prompt)

        print(f"  ✅ Response: {response}")
        print("  ⏳ Waiting for traces to be sent...")
        time.sleep(2)  # Give time for traces to be sent

        return True

    except Exception as e:
        print(f"  ❌ Basic LLM test failed: {e}")
        return False


def run_chain_test(model_name: str):
    """Run a LangChain chain test with tracing."""
    print("\n⛓️ Running LangChain chain test...")

    try:
        from langchain.chains import LLMChain
        from langchain.prompts import PromptTemplate
        from langchain_ollama import OllamaLLM

        # Initialize Ollama LLM
        llm = OllamaLLM(
            model=model_name,
            base_url="http://aurora.local:11434",
            temperature=0.1,
        )

        # Create a prompt template
        prompt_template = PromptTemplate(
            input_variables=["topic", "style"],
            template="Write a {style} explanation of {topic} in one sentence.",
        )

        # Create a chain
        chain = LLMChain(llm=llm, prompt=prompt_template)

        # Test inputs
        inputs = {"topic": "machine learning", "style": "simple"}

        print(f"  📝 Chain inputs: {inputs}")
        print("  🔄 Running chain...")

        # Run the chain - this should generate traces
        result = chain.invoke(inputs)

        print(f"  ✅ Chain result: {result.get('text', 'No text in result')}")
        print("  ⏳ Waiting for traces to be sent...")
        time.sleep(2)  # Give time for traces to be sent

        return True

    except Exception as e:
        print(f"  ❌ Chain test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 Agent Spy + LangChain Integration Test")
    print("=" * 50)

    # Step 1: Setup tracing
    setup_agent_spy_tracing()

    # Step 2: Check Agent Spy health
    print("\n🏥 Checking Agent Spy health...")
    if not check_agent_spy_health():
        print("\n❌ Agent Spy is not running. Please start it with:")
        print("   PYTHONPATH=. uv run python src/main.py")
        return 1

    # Step 3: Check Ollama availability
    print("\n🦙 Checking Ollama availability...")
    model_name = check_ollama_availability()
    if not model_name:
        print("\n❌ Ollama is not available or no models found.")
        print("Please ensure:")
        print("  1. Ollama is running: ollama serve")
        print("  2. A model is pulled: ollama pull llama3.2:1b")
        return 1

    # Step 4: Run tests
    success_count = 0
    total_tests = 2

    if run_basic_llm_test(model_name):
        success_count += 1

    if run_chain_test(model_name):
        success_count += 1

    # Step 5: Summary
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("✅ All tests passed! LangChain is sending traces to Agent Spy.")
        print("\n🔍 To see traces, check:")
        print("  - Agent Spy logs in the server console")
        print("  - Future: Agent Spy dashboard (Phase 5)")
        return 0
    else:
        print("❌ Some tests failed. Check the error messages above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
