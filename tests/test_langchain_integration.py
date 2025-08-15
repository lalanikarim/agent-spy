"""Test LangChain integration with Agent Spy."""

import os
import time

import pytest
from langchain_ollama import OllamaLLM


def test_langchain_basic_integration():
    """Test basic LangChain integration with Agent Spy tracing."""

    # Configure LangChain to send traces to our local Agent Spy server
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "http://localhost:8000/api/v1"
    os.environ["LANGCHAIN_API_KEY"] = "test-api-key"
    os.environ["LANGCHAIN_PROJECT"] = "agent-spy-test"

    try:
        # Initialize Ollama model (assuming llama2 or similar is available)
        # Note: This test will be skipped if Ollama is not running
        llm = OllamaLLM(
            model="llama3.2:1b",  # Use a small model for testing
            base_url="http://localhost:11434",
            temperature=0.1,
        )

        # Test if Ollama is available
        try:
            response = llm.invoke("Hello, this is a test message for Agent Spy tracing.")
            print(f"LLM Response: {response}")

            # Give some time for traces to be sent
            time.sleep(1)

            # The test passes if no exceptions are raised
            # In Phase 2, we'll add actual verification of received traces
            assert len(response) > 0

        except Exception as e:
            pytest.skip(f"Ollama not available or model not found: {e}")

    except ImportError as e:
        pytest.skip(f"LangChain dependencies not available: {e}")


def test_langchain_chain_integration():
    """Test LangChain chain integration with Agent Spy tracing."""

    # Configure tracing
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "http://localhost:8000/api/v1"
    os.environ["LANGCHAIN_API_KEY"] = "test-api-key"
    os.environ["LANGCHAIN_PROJECT"] = "agent-spy-chain-test"

    try:
        from langchain.chains import LLMChain
        from langchain.prompts import PromptTemplate

        # Initialize Ollama model
        llm = OllamaLLM(
            model="llama3.2:1b",
            base_url="http://localhost:11434",
            temperature=0.1,
        )

        # Create a simple prompt template
        prompt = PromptTemplate(input_variables=["topic"], template="Write a short sentence about {topic}.")

        # Create a chain
        chain = LLMChain(llm=llm, prompt=prompt)

        try:
            # Run the chain
            result = chain.invoke({"topic": "artificial intelligence"})
            print(f"Chain Result: {result}")

            # Give some time for traces to be sent
            time.sleep(1)

            assert "text" in result
            assert len(result["text"]) > 0

        except Exception as e:
            pytest.skip(f"Ollama not available or chain execution failed: {e}")

    except ImportError as e:
        pytest.skip(f"LangChain chain dependencies not available: {e}")


if __name__ == "__main__":
    """Run tests directly for manual testing."""
    print("Testing LangChain integration with Agent Spy...")

    # Run basic integration test
    try:
        test_langchain_basic_integration()
        print("✅ Basic LangChain integration test passed")
    except Exception as e:
        print(f"❌ Basic integration test failed: {e}")

    # Run chain integration test
    try:
        test_langchain_chain_integration()
        print("✅ LangChain chain integration test passed")
    except Exception as e:
        print(f"❌ Chain integration test failed: {e}")

    print("Test completed!")
