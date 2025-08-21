#!/usr/bin/env uv run --python 3.13

# /// script
# dependencies = [
#   "langsmith",
# ]
# ///

"""
Simple Tracing Example with LangSmith

This example demonstrates basic tracing functionality using LangSmith
without requiring external AI services. It creates a simple pipeline
that processes text through multiple steps and traces each operation.
"""

import os
import time
from typing import Any

from langsmith import traceable


class MockLLMClient:
    """Mock LLM client that simulates AI responses without external calls."""

    def __init__(self):
        self.response_templates = {
            "greeting": "Hello! I'm a mock AI assistant. How can I help you today?",
            "analysis": "Based on my analysis, this appears to be a {text_type} text with {word_count} words.",
            "summary": "Here's a summary: {content}",
            "sentiment": "The sentiment appears to be {sentiment} based on the content analysis.",
        }

    def chat(self):
        return self.ChatCompletions(self.response_templates)

    class ChatCompletions:
        def __init__(self, templates):
            self.templates = templates

        def create(self, messages, model=None, **kwargs):
            # Simulate processing time
            time.sleep(0.1)

            user_message = messages[-1]["content"] if messages else ""

            # Simple response logic based on input
            if "hello" in user_message.lower():
                response = self.templates["greeting"]
            elif "analyze" in user_message.lower():
                word_count = len(user_message.split())
                text_type = "informative" if word_count > 10 else "brief"
                response = self.templates["analysis"].format(text_type=text_type, word_count=word_count)
            elif "summarize" in user_message.lower():
                response = self.templates["summary"].format(content=user_message[:50] + "...")
            else:
                response = "I understand you said: " + user_message

            return self.MockResponse(response)

        class MockResponse:
            def __init__(self, content):
                self.choices = [self.MockChoice(content)]

            class MockChoice:
                def __init__(self, content):
                    self.message = self.MockMessage(content)

                class MockMessage:
                    def __init__(self, content):
                        self.content = content


@traceable(name="text_processor")
def process_text(text: str) -> str:
    """Process input text through multiple steps."""
    # Step 1: Analyze the text
    analysis = analyze_text(text)

    # Step 2: Generate a summary
    summary = generate_summary(analysis)

    # Step 3: Determine sentiment
    sentiment = determine_sentiment(summary)

    return f"Final result: {sentiment}"


@traceable(name="text_analyzer")
def analyze_text(text: str) -> str:
    """Analyze the input text."""
    mock_client = MockLLMClient()
    result = mock_client.chat().create(
        messages=[{"role": "user", "content": f"Analyze this text: {text}"}], model="mock-model"
    )
    return result.choices[0].message.content


@traceable(name="summary_generator")
def generate_summary(analysis: str) -> str:
    """Generate a summary of the analysis."""
    mock_client = MockLLMClient()
    result = mock_client.chat().create(
        messages=[{"role": "user", "content": f"Summarize this analysis: {analysis}"}], model="mock-model"
    )
    return result.choices[0].message.content


@traceable(name="sentiment_analyzer")
def determine_sentiment(summary: str) -> str:
    """Determine the sentiment of the summary."""
    mock_client = MockLLMClient()
    result = mock_client.chat().create(
        messages=[{"role": "user", "content": f"Determine sentiment: {summary}"}], model="mock-model"
    )
    return result.choices[0].message.content


@traceable(name="main_pipeline")
def main_pipeline(user_input: str) -> dict[str, Any]:
    """Main pipeline that orchestrates the entire process."""
    print(f"Processing input: {user_input}")

    # Process the text through our pipeline
    result = process_text(user_input)

    # Return structured output
    return {"input": user_input, "output": result, "timestamp": time.time(), "steps_completed": 3}


def main():
    """Main function to demonstrate tracing."""
    # Set up LangSmith configuration
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    # Read endpoint from environment variable, fallback to default if not set
    if "LANGCHAIN_ENDPOINT" not in os.environ:
        os.environ["LANGCHAIN_ENDPOINT"] = "http://localhost:8000/api/v1"
    os.environ["LANGCHAIN_API_KEY"] = "test-key"
    os.environ["LANGCHAIN_PROJECT"] = "simple-tracing-example"

    print("🚀 Starting Simple Tracing Example")
    print("=" * 50)

    # Test cases
    test_inputs = [
        "Hello, how are you today?",
        "This is a longer text that needs to be analyzed for its content and structure.",
        "Analyze this short text",
        "Please summarize the following information about artificial intelligence and machine learning.",
    ]

    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Input: {test_input}")

        try:
            result = main_pipeline(test_input)
            print(f"✅ Result: {result['output']}")
            print(f"⏱️  Steps completed: {result['steps_completed']}")
        except Exception as e:
            print(f"❌ Error: {e}")

        print("-" * 30)

    print("\n🎉 Tracing example completed!")
    print("Check your Agent Spy dashboard to see the captured traces.")


if __name__ == "__main__":
    main()
