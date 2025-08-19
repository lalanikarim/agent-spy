#!/usr/bin/env python3
# /// script
# dependencies = [
#   "openai>=1.0.0",
#   "opentelemetry-api>=1.20.0",
#   "opentelemetry-sdk>=1.20.0",
#   "opentelemetry-exporter-otlp-proto-http>=1.20.0",
# ]
# ///

"""
OpenAI + OpenTelemetry SDK Integration Example

This example demonstrates how to use the OpenTelemetry SDK to automatically
instrument OpenAI API calls and send traces to Agent Spy via OTLP.

This is the recommended approach for production applications as it:
1. Uses the official OpenTelemetry SDK
2. Provides automatic instrumentation
3. Handles batching and retries
4. Follows OpenTelemetry semantic conventions
5. Integrates seamlessly with Agent Spy's OTLP receiver

Prerequisites:
- OpenAI API key (set OPENAI_API_KEY environment variable)
- Agent Spy server running on http://localhost:8000

Usage:
    export OPENAI_API_KEY="your-api-key-here"
    uv run python examples/openai_otel_instrumentation.py
"""

import os
import time
from typing import Any

from openai import OpenAI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class AgentSpyOTelInstrumentation:
    """OpenTelemetry instrumentation for OpenAI API calls with Agent Spy integration."""

    def __init__(self, agent_spy_endpoint: str = "http://localhost:8000/v1/traces/"):
        """Initialize OpenTelemetry instrumentation.

        Args:
            agent_spy_endpoint: Agent Spy OTLP endpoint URL
        """
        self.agent_spy_endpoint = agent_spy_endpoint
        self.client = None
        self.tracer = None
        self._setup_instrumentation()

    def _setup_instrumentation(self):
        """Set up OpenTelemetry instrumentation."""
        print("🔧 Setting up OpenTelemetry instrumentation...")

        # Create resource with service information
        resource = Resource.create(
            {
                "service.name": "openai-llm-service",
                "service.version": "1.0.0",
                "deployment.environment": "development",
                "service.instance.id": "instance-1",
            }
        )

        # Create OTLP exporter pointing to Agent Spy
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.agent_spy_endpoint,
            timeout=10,
            headers={},  # Add any required headers here
        )

        # Set up tracer provider with resource
        trace.set_tracer_provider(TracerProvider(resource=resource))

        # Add batch span processor with the OTLP exporter
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(
                otlp_exporter,
                max_queue_size=2048,
                export_timeout_millis=30000,
                max_export_batch_size=512,
            )
        )

        # Get tracer instance
        self.tracer = trace.get_tracer(__name__)

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  Warning: OPENAI_API_KEY not set. Using mock client.")
            self.client = MockOpenAIClient()
        else:
            self.client = OpenAI(api_key=api_key)

        print("✅ OpenTelemetry instrumentation configured")
        print(f"   Endpoint: {self.agent_spy_endpoint}")
        print("   Service: openai-llm-service")

    def call_openai_chat(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        user_id: str = "anonymous",
    ) -> dict[str, Any]:
        """Make an instrumented OpenAI chat completion call.

        Args:
            messages: List of chat messages
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            user_id: User identifier for tracking

        Returns:
            Dict containing the completion response and metadata
        """
        with self.tracer.start_as_current_span("openai_chat_completion") as span:
            # Set span attributes following semantic conventions
            span.set_attribute("llm.vendor", "openai")
            span.set_attribute("llm.request.model", model)
            span.set_attribute("llm.request.temperature", temperature)
            span.set_attribute("llm.request.max_tokens", max_tokens)
            span.set_attribute("llm.request.type", "chat")
            span.set_attribute("user.id", user_id)

            # Agent Spy specific attributes
            span.set_attribute("langsmith.span.kind", "LLM")
            span.set_attribute("langsmith.metadata.user_id", user_id)

            # Set input messages as attributes
            for i, message in enumerate(messages):
                span.set_attribute(f"llm.prompt.{i}.content", str(message["content"]))
                span.set_attribute(f"llm.prompt.{i}.role", str(message["role"]))

            try:
                start_time = time.time()

                # Make the OpenAI API call
                completion = self.client.chat.completions.create(
                    model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, user=user_id
                )

                end_time = time.time()
                duration_ms = int((end_time - start_time) * 1000)

                # Set response attributes
                span.set_attribute("llm.response.model", completion.model)
                span.set_attribute("llm.completion.0.content", str(completion.choices[0].message.content))
                span.set_attribute("llm.completion.0.role", "assistant")
                span.set_attribute("llm.completion.0.finish_reason", str(completion.choices[0].finish_reason))

                # Usage statistics
                if hasattr(completion, "usage") and completion.usage:
                    span.set_attribute("llm.usage.prompt_tokens", completion.usage.prompt_tokens)
                    span.set_attribute("llm.usage.completion_tokens", completion.usage.completion_tokens)
                    span.set_attribute("llm.usage.total_tokens", completion.usage.total_tokens)

                # Performance metrics
                span.set_attribute("llm.response.duration_ms", duration_ms)

                # Success status
                span.set_attribute("llm.response.status", "success")

                return {
                    "success": True,
                    "content": completion.choices[0].message.content,
                    "model": completion.model,
                    "usage": completion.usage._asdict() if completion.usage else None,
                    "duration_ms": duration_ms,
                    "finish_reason": completion.choices[0].finish_reason,
                }

            except Exception as e:
                # Set error attributes
                span.set_attribute("llm.response.status", "error")
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))

                # Record the exception
                span.record_exception(e)

                return {"success": False, "error": str(e), "error_type": type(e).__name__}

    def run_multi_step_llm_workflow(self, topic: str = "artificial intelligence") -> dict[str, Any]:
        """Run a multi-step LLM workflow with full instrumentation.

        Args:
            topic: Topic to generate content about

        Returns:
            Dict containing workflow results
        """
        with self.tracer.start_as_current_span("multi_step_llm_workflow") as workflow_span:
            # Set workflow-level attributes
            workflow_span.set_attribute("workflow.name", "content_generation_pipeline")
            workflow_span.set_attribute("workflow.version", "1.0.0")
            workflow_span.set_attribute("workflow.input.topic", topic)
            workflow_span.set_attribute("langsmith.span.kind", "WORKFLOW")

            workflow_start = time.time()
            results = {}

            try:
                # Step 1: Generate outline
                print(f"📝 Step 1: Generating outline for '{topic}'...")
                outline_result = self.call_openai_chat(
                    messages=[
                        {"role": "system", "content": "You are a content strategist. Create detailed outlines for topics."},
                        {
                            "role": "user",
                            "content": f"Create a detailed outline for an article about {topic}. Include 5 main sections with subsections.",
                        },
                    ],
                    model="gpt-4o-mini",
                    user_id="content_generator",
                )
                results["outline"] = outline_result

                if not outline_result["success"]:
                    raise Exception(f"Outline generation failed: {outline_result['error']}")

                # Step 2: Generate introduction
                print("📖 Step 2: Writing introduction...")
                intro_result = self.call_openai_chat(
                    messages=[
                        {"role": "system", "content": "You are a technical writer. Write engaging introductions."},
                        {
                            "role": "user",
                            "content": f"Based on this outline:\n\n{outline_result['content']}\n\nWrite a compelling introduction for an article about {topic}.",
                        },
                    ],
                    model="gpt-4o-mini",
                    temperature=0.8,
                    user_id="content_generator",
                )
                results["introduction"] = intro_result

                if not intro_result["success"]:
                    raise Exception(f"Introduction generation failed: {intro_result['error']}")

                # Step 3: Generate key points
                print("🔑 Step 3: Developing key points...")
                keypoints_result = self.call_openai_chat(
                    messages=[
                        {"role": "system", "content": "You are a subject matter expert. Explain complex topics clearly."},
                        {
                            "role": "user",
                            "content": f"Based on this outline:\n\n{outline_result['content']}\n\nWrite 3 key points about {topic} that would be valuable for readers to understand.",
                        },
                    ],
                    model="gpt-4o-mini",
                    temperature=0.6,
                    user_id="content_generator",
                )
                results["key_points"] = keypoints_result

                if not keypoints_result["success"]:
                    raise Exception(f"Key points generation failed: {keypoints_result['error']}")

                # Step 4: Generate conclusion
                print("🎯 Step 4: Writing conclusion...")
                conclusion_result = self.call_openai_chat(
                    messages=[
                        {"role": "system", "content": "You are a content editor. Write impactful conclusions."},
                        {
                            "role": "user",
                            "content": f"Based on this introduction:\n\n{intro_result['content']}\n\nAnd these key points:\n\n{keypoints_result['content']}\n\nWrite a strong conclusion for an article about {topic}.",
                        },
                    ],
                    model="gpt-4o-mini",
                    temperature=0.7,
                    user_id="content_generator",
                )
                results["conclusion"] = conclusion_result

                if not conclusion_result["success"]:
                    raise Exception(f"Conclusion generation failed: {conclusion_result['error']}")

                # Calculate workflow metrics
                workflow_end = time.time()
                total_duration = int((workflow_end - workflow_start) * 1000)

                # Calculate total token usage
                total_prompt_tokens = sum(r.get("usage", {}).get("prompt_tokens", 0) for r in results.values() if r["success"])
                total_completion_tokens = sum(
                    r.get("usage", {}).get("completion_tokens", 0) for r in results.values() if r["success"]
                )
                total_tokens = total_prompt_tokens + total_completion_tokens

                # Set final workflow attributes
                workflow_span.set_attribute("workflow.status", "completed")
                workflow_span.set_attribute("workflow.duration_ms", total_duration)
                workflow_span.set_attribute("workflow.steps_completed", 4)
                workflow_span.set_attribute("workflow.total_llm_calls", 4)
                workflow_span.set_attribute("workflow.total_prompt_tokens", total_prompt_tokens)
                workflow_span.set_attribute("workflow.total_completion_tokens", total_completion_tokens)
                workflow_span.set_attribute("workflow.total_tokens", total_tokens)

                results["workflow_summary"] = {
                    "success": True,
                    "topic": topic,
                    "steps_completed": 4,
                    "total_duration_ms": total_duration,
                    "total_tokens": total_tokens,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_completion_tokens,
                }

                return results

            except Exception as e:
                # Handle workflow errors
                workflow_end = time.time()
                total_duration = int((workflow_end - workflow_start) * 1000)

                workflow_span.set_attribute("workflow.status", "failed")
                workflow_span.set_attribute("workflow.duration_ms", total_duration)
                workflow_span.set_attribute("error.type", type(e).__name__)
                workflow_span.set_attribute("error.message", str(e))
                workflow_span.record_exception(e)

                results["workflow_summary"] = {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "total_duration_ms": total_duration,
                }

                return results

    def flush_traces(self):
        """Force flush any pending traces."""
        print("🔄 Flushing traces to Agent Spy...")
        trace.get_tracer_provider().force_flush(timeout_millis=30000)
        print("✅ Traces flushed")


class MockOpenAIClient:
    """Mock OpenAI client for testing without API key."""

    def __init__(self):
        self.chat = self.MockChatCompletions()

    class MockChatCompletions:
        def __init__(self):
            self.completions = MockOpenAIClient.MockCompletions()

    class MockCompletions:
        def create(self, **kwargs):
            """Mock chat completion creation."""
            time.sleep(0.5)  # Simulate API delay

            model = kwargs.get("model", "gpt-4o-mini")
            messages = kwargs.get("messages", [])

            # Generate mock response based on the last user message
            last_message = messages[-1]["content"] if messages else "Hello"

            if "outline" in last_message.lower():
                content = f"""# Article Outline: {kwargs.get("user", "Topic")}

## 1. Introduction
- Definition and overview
- Historical context
- Current relevance

## 2. Core Concepts
- Fundamental principles
- Key terminology
- Basic mechanisms

## 3. Applications and Use Cases
- Real-world examples
- Industry applications
- Success stories

## 4. Challenges and Limitations
- Current obstacles
- Technical limitations
- Ethical considerations

## 5. Future Outlook
- Emerging trends
- Potential developments
- Long-term implications"""

            elif "introduction" in last_message.lower():
                content = f"In today's rapidly evolving technological landscape, understanding the fundamentals and implications of {kwargs.get('user', 'this topic')} has become increasingly important. This comprehensive exploration will guide you through the essential concepts, practical applications, and future possibilities that define this fascinating field."

            elif "key points" in last_message.lower():
                content = f"""Here are three key points about {kwargs.get("user", "this topic")}:

1. **Foundational Understanding**: The core principles provide a solid framework for comprehending how this technology works and its potential applications across various industries.

2. **Practical Implementation**: Real-world applications demonstrate the tangible benefits and transformative potential of this technology in solving complex problems.

3. **Future Implications**: The ongoing development and refinement of these concepts will continue to shape how we approach challenges and opportunities in the coming years."""

            elif "conclusion" in last_message.lower():
                content = f"As we've explored throughout this discussion, {kwargs.get('user', 'this topic')} represents a significant advancement in our technological capabilities. The insights we've covered highlight both the immediate opportunities and long-term potential that lie ahead. By understanding these concepts and their applications, we position ourselves to better navigate and contribute to this exciting field."

            else:
                content = f"This is a mock response about {last_message[:50]}... The content would be generated by OpenAI's API in a real scenario."

            # Create mock response object
            class MockUsage:
                def __init__(self):
                    self.prompt_tokens = len(last_message.split()) + 10
                    self.completion_tokens = len(content.split())
                    self.total_tokens = self.prompt_tokens + self.completion_tokens

                def _asdict(self):
                    return {
                        "prompt_tokens": self.prompt_tokens,
                        "completion_tokens": self.completion_tokens,
                        "total_tokens": self.total_tokens,
                    }

            class MockMessage:
                def __init__(self, content):
                    self.content = content
                    self.role = "assistant"

            class MockChoice:
                def __init__(self, content):
                    self.message = MockMessage(content)
                    self.finish_reason = "stop"

            class MockCompletion:
                def __init__(self, content, model):
                    self.choices = [MockChoice(content)]
                    self.model = model
                    self.usage = MockUsage()

            return MockCompletion(content, model)


async def main():
    """Main function demonstrating OpenTelemetry instrumentation with Agent Spy."""
    print("🚀 OpenAI + OpenTelemetry + Agent Spy Integration Demo")
    print("=" * 60)

    # Initialize instrumentation
    instrumentation = AgentSpyOTelInstrumentation()

    # Test basic chat completion
    print("\n📞 Testing basic OpenAI chat completion...")
    simple_result = instrumentation.call_openai_chat(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a haiku about recursion in programming."},
        ],
        user_id="demo_user",
    )

    if simple_result["success"]:
        print("✅ Chat completion successful!")
        print(f"   Response: {simple_result['content'][:100]}...")
        print(f"   Duration: {simple_result['duration_ms']}ms")
        if simple_result["usage"]:
            print(f"   Tokens: {simple_result['usage']['total_tokens']} total")
    else:
        print(f"❌ Chat completion failed: {simple_result['error']}")

    print("\n" + "=" * 60)

    # Test multi-step workflow
    print("🔄 Running multi-step LLM workflow...")
    workflow_results = instrumentation.run_multi_step_llm_workflow("machine learning")

    summary = workflow_results.get("workflow_summary", {})
    if summary.get("success"):
        print("✅ Multi-step workflow completed successfully!")
        print(f"   Topic: {summary['topic']}")
        print(f"   Steps completed: {summary['steps_completed']}")
        print(f"   Total duration: {summary['total_duration_ms']}ms")
        print(f"   Total tokens used: {summary['total_tokens']}")
        print(f"   Prompt tokens: {summary['total_prompt_tokens']}")
        print(f"   Completion tokens: {summary['total_completion_tokens']}")
    else:
        print(f"❌ Multi-step workflow failed: {summary.get('error', 'Unknown error')}")

    # Force flush traces to Agent Spy
    print("\n" + "=" * 60)
    instrumentation.flush_traces()

    print("\n🎯 Demo completed!")
    print("   Check Agent Spy dashboard at http://localhost:8000 to view traces")
    print("   Look for traces from service: 'openai-llm-service'")

    return summary.get("success", False)


if __name__ == "__main__":
    import asyncio

    success = asyncio.run(main())
    exit(0 if success else 1)
