#!/usr/bin/env python3
# /// script
# dependencies = [
#   "ollama>=0.3.0",
#   "opentelemetry-api>=1.20.0",
#   "opentelemetry-sdk>=1.20.0",
#   "opentelemetry-exporter-otlp-proto-http>=1.20.0",
# ]
# ///

"""
Ollama + OpenTelemetry Integration Example

This example demonstrates how to instrument Ollama API calls with OpenTelemetry
and send traces to Agent Spy. It connects to an Ollama instance running on the
host machine (outside the container).

Features:
- Automatic OpenTelemetry instrumentation for Ollama calls
- Rich tracing with model parameters, tokens, and performance metrics
- Multi-step LLM workflows with parent-child span relationships
- Connects to host Ollama instance from container environment
- Real-time trace visualization in Agent Spy

Prerequisites:
- Ollama running on host machine (accessible via host.docker.internal or 192.168.1.*)
- Agent Spy server running on http://localhost:8000
- At least one model pulled in Ollama (e.g., llama3.2:1b, qwen2.5:0.5b)

Usage:
    uv run python examples/ollama_otel_instrumentation.py
"""

import asyncio
import time
from typing import Any

import ollama
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class OllamaOTelInstrumentation:
    """OpenTelemetry instrumentation for Ollama API calls with Agent Spy integration."""

    def __init__(
        self,
        agent_spy_endpoint: str = "http://localhost:8000/v1/traces/",
        ollama_host: str = None,
        test_id: str = None,
    ):
        """Initialize Ollama OpenTelemetry instrumentation.

        Args:
            agent_spy_endpoint: Agent Spy OTLP endpoint URL
            ollama_host: Ollama host URL (auto-detected if None)
            test_id: Optional test identifier for unique service naming
        """
        self.agent_spy_endpoint = agent_spy_endpoint
        self.ollama_host = ollama_host or self._detect_ollama_host()
        self.test_id = test_id or f"test-{int(time.time())}"
        self.client = None
        self.tracer = None
        self.available_models = []
        self._setup_instrumentation()

    def _detect_ollama_host(self) -> str:
        """Auto-detect Ollama host URL for container environment."""
        # Try common container-to-host networking options
        potential_hosts = [
            "http://192.168.1.200:11434",  # Specified host IP
            "http://host.docker.internal:11434",  # Docker Desktop
            "http://172.17.0.1:11434",  # Default Docker bridge
            "http://localhost:11434",  # Local fallback
        ]

        print("🔍 Auto-detecting Ollama host...")
        for host in potential_hosts:
            try:
                test_client = ollama.Client(host=host)
                test_client.list()
                print(f"✅ Found Ollama at: {host}")
                return host
            except Exception:
                continue

        print("⚠️  Could not auto-detect Ollama. Using default: http://localhost:11434")
        return "http://localhost:11434"

    def _setup_instrumentation(self):
        """Set up OpenTelemetry instrumentation and Ollama client."""
        print("🔧 Setting up OpenTelemetry instrumentation...")

        # Create resource with service information including unique test identifier
        resource = Resource.create(
            {
                "service.name": f"ollama-llm-service-{self.test_id}",
                "service.version": "1.0.0",
                "deployment.environment": "development",
                "service.instance.id": "ollama-instance-1",
                "llm.vendor": "ollama",
                "test.id": self.test_id,
            }
        )

        # Create OTLP exporter pointing to Agent Spy with improved configuration
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.agent_spy_endpoint,
            timeout=30,  # Increased timeout
            headers={"Content-Type": "application/json"},  # Explicit content type
        )

        # Set up tracer provider with resource
        trace.set_tracer_provider(TracerProvider(resource=resource))

        # Add batch span processor with the OTLP exporter - smaller batches for faster export
        span_processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=1000,  # Smaller queue for faster processing
            export_timeout_millis=60000,  # Longer timeout
            max_export_batch_size=100,  # Smaller batch size for faster export
        )

        # Add the span processor to the tracer provider
        trace.get_tracer_provider().add_span_processor(span_processor)

        # Verify the span processor was added
        provider = trace.get_tracer_provider()
        if hasattr(provider, "_active_span_processor"):
            active_processor = provider._active_span_processor
            if active_processor:
                print(f"   ✅ Added span processor. Active processor: {type(active_processor).__name__}")
            else:
                print("   ❌ No active span processor found")
        else:
            print("   ❌ _active_span_processor attribute not found")

        # Get tracer instance
        self.tracer = trace.get_tracer(__name__)

        # Initialize Ollama client
        try:
            self.client = ollama.Client(host=self.ollama_host)
            # Test connection and get available models
            models_response = self.client.list()
            models_list = models_response.get("models", [])
            self.available_models = []

            for model in models_list:
                if hasattr(model, "model"):
                    # Ollama model object
                    model_name = model.model
                elif isinstance(model, dict):
                    model_name = model.get("name", model.get("model", ""))
                else:
                    model_name = str(model)
                if model_name:
                    self.available_models.append(model_name)

            if not self.available_models:
                print("⚠️  No models found. You may need to pull a model first.")
                print("   Try: ollama pull llama3.2:1b")

            print("✅ OpenTelemetry instrumentation configured")
            print(f"   Agent Spy Endpoint: {self.agent_spy_endpoint}")
            print(f"   Ollama Host: {self.ollama_host}")
            print(
                f"   Available Models: {', '.join(self.available_models[:3])}{'...' if len(self.available_models) > 3 else ''}"
            )

            # Test OTLP endpoint connectivity
            print("🔍 Testing OTLP endpoint connectivity...")
            try:
                import requests

                test_response = requests.get(self.agent_spy_endpoint, timeout=5)
                print(f"   OTLP endpoint status: {test_response.status_code}")
                if test_response.status_code == 200:
                    print("   ✅ OTLP endpoint is accessible")
                else:
                    print(f"   ⚠️  OTLP endpoint returned status: {test_response.status_code}")
            except Exception as e:
                print(f"   ❌ OTLP endpoint test failed: {e}")

        except Exception as e:
            print(f"❌ Failed to connect to Ollama: {e}")
            print(f"   Make sure Ollama is running on: {self.ollama_host}")
            raise

    def _get_best_model(self) -> str:
        """Get the best available model for testing."""
        # Prefer smaller, faster models for demos
        preferred_models = [
            "qwen3:0.6b",
            "qwen3:1.7b",
            "gemma3:latest",
            "deepseek-r1:latest",
            "qwen3:latest",
            "qwen3:14b",
            "qwen3:30b-a3b",
            "gemma3:4b-it-qat",
        ]

        print(f"🔍 Available models: {', '.join(self.available_models)}")

        for model in preferred_models:
            if model in self.available_models:
                print(f"✅ Selected model: {model}")
                return model

        # Fallback to first available model
        if self.available_models:
            fallback_model = self.available_models[0]
            print(f"⚠️  Preferred models not found. Using fallback: {fallback_model}")
            return fallback_model

        # If no models available, suggest pulling one and use a common default
        print("⚠️  No models available. Using 'qwen3:0.6b' as default.")
        print("   Make sure to pull a model first: ollama pull qwen3:0.6b")
        return "qwen3:0.6b"

    def call_ollama_generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        user_id: str = "anonymous",
        system_prompt: str = None,
        create_span: bool = True,
    ) -> dict[str, Any]:
        """Make an instrumented Ollama generate call.

        Args:
            prompt: The prompt to send to the model
            model: Model name (auto-selected if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            user_id: User identifier for tracking
            system_prompt: Optional system prompt

        Returns:
            Dict containing the generation response and metadata
        """
        model = model or self._get_best_model()

        print(f"🔍 Creating span for ollama_generate with tracer: {type(self.tracer).__name__}")
        with self.tracer.start_as_current_span(f"ollama_generate_{self.test_id}") as span:
            print(f"   ✅ Span created: {span.name} (ID: {span.get_span_context().span_id})")
            # Set span attributes following semantic conventions
            span.set_attribute("llm.vendor", "ollama")
            span.set_attribute("llm.request.model", model)
            span.set_attribute("llm.request.temperature", temperature)
            span.set_attribute("llm.request.max_tokens", max_tokens)
            span.set_attribute("llm.request.type", "generate")
            span.set_attribute("user.id", user_id)
            span.set_attribute("server.address", self.ollama_host)

            # Agent Spy specific attributes
            span.set_attribute("langsmith.span.kind", "LLM")
            span.set_attribute("langsmith.metadata.user_id", user_id)

            # Set input prompts as attributes
            span.set_attribute("llm.prompt.0.content", prompt)
            span.set_attribute("llm.prompt.0.role", "user")

            if system_prompt:
                span.set_attribute("llm.prompt.system.content", system_prompt)
                span.set_attribute("llm.prompt.system.role", "system")

            try:
                start_time = time.time()

                # Prepare options
                options = {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }

                # Make the Ollama API call
                response = self.client.generate(
                    model=model, prompt=prompt, system=system_prompt, options=options, stream=False
                )

                end_time = time.time()
                duration_ms = int((end_time - start_time) * 1000)

                # Extract response data
                generated_text = response.get("response", "")

                # Set response attributes
                span.set_attribute("llm.response.model", model)
                span.set_attribute("llm.completion.0.content", generated_text)
                span.set_attribute("llm.completion.0.role", "assistant")
                span.set_attribute("llm.completion.0.finish_reason", "stop")

                # Token usage (if available)
                eval_count = response.get("eval_count", 0)
                prompt_eval_count = response.get("prompt_eval_count", 0)
                total_tokens = eval_count + prompt_eval_count

                if eval_count > 0:
                    span.set_attribute("llm.usage.completion_tokens", eval_count)
                if prompt_eval_count > 0:
                    span.set_attribute("llm.usage.prompt_tokens", prompt_eval_count)
                if total_tokens > 0:
                    span.set_attribute("llm.usage.total_tokens", total_tokens)

                # Performance metrics
                span.set_attribute("llm.response.duration_ms", duration_ms)

                # Ollama-specific metrics
                if "eval_duration" in response:
                    span.set_attribute("llm.ollama.eval_duration_ns", response["eval_duration"])
                if "prompt_eval_duration" in response:
                    span.set_attribute("llm.ollama.prompt_eval_duration_ns", response["prompt_eval_duration"])
                if "total_duration" in response:
                    span.set_attribute("llm.ollama.total_duration_ns", response["total_duration"])

                # Success status
                span.set_attribute("llm.response.status", "success")

                return {
                    "success": True,
                    "content": generated_text,
                    "model": model,
                    "duration_ms": duration_ms,
                    "eval_count": eval_count,
                    "prompt_eval_count": prompt_eval_count,
                    "total_tokens": total_tokens,
                    "finish_reason": "stop",
                    "raw_response": response,
                }

            except Exception as e:
                # Set error attributes
                span.set_attribute("llm.response.status", "error")
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))

                # Record the exception
                span.record_exception(e)

                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }

    def _call_ollama_generate_direct(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        system_prompt: str = None,
    ) -> dict[str, Any]:
        """Make a direct Ollama generate call without creating a span."""
        model = model or self._get_best_model()

        try:
            start_time = time.time()

            # Prepare options
            options = {
                "temperature": temperature,
                "num_predict": max_tokens,
            }

            # Make the Ollama API call
            response = self.client.generate(model=model, prompt=prompt, system=system_prompt, options=options, stream=False)

            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)

            # Extract response data
            generated_text = response.get("response", "")

            # Token usage (if available)
            eval_count = response.get("eval_count", 0)
            prompt_eval_count = response.get("prompt_eval_count", 0)
            total_tokens = eval_count + prompt_eval_count

            return {
                "success": True,
                "content": generated_text,
                "model": model,
                "duration_ms": duration_ms,
                "eval_count": eval_count,
                "prompt_eval_count": prompt_eval_count,
                "total_tokens": total_tokens,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "model": model,
                "duration_ms": 0,
                "eval_count": 0,
                "prompt_eval_count": 0,
                "total_tokens": 0,
            }

    def _call_ollama_chat_direct(
        self,
        messages: list[dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> dict[str, Any]:
        """Make a direct Ollama chat call without creating a span."""
        model = model or self._get_best_model()

        try:
            start_time = time.time()

            # Prepare options
            options = {
                "temperature": temperature,
                "num_predict": max_tokens,
            }

            # Make the Ollama chat API call
            response = self.client.chat(model=model, messages=messages, options=options, stream=False)

            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)

            # Extract response data
            message_response = response.get("message", {})
            generated_text = message_response.get("content", "")

            # Token usage (if available)
            eval_count = response.get("eval_count", 0)
            prompt_eval_count = response.get("prompt_eval_count", 0)
            total_tokens = eval_count + prompt_eval_count

            return {
                "success": True,
                "content": generated_text,
                "model": model,
                "duration_ms": duration_ms,
                "eval_count": eval_count,
                "prompt_eval_count": prompt_eval_count,
                "total_tokens": total_tokens,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "model": model,
                "duration_ms": 0,
                "eval_count": 0,
                "prompt_eval_count": 0,
                "total_tokens": 0,
            }

    def call_ollama_chat(
        self,
        messages: list[dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        user_id: str = "anonymous",
    ) -> dict[str, Any]:
        """Make an instrumented Ollama chat call.

        Args:
            messages: List of chat messages
            model: Model name (auto-selected if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            user_id: User identifier for tracking

        Returns:
            Dict containing the chat response and metadata
        """
        model = model or self._get_best_model()

        with self.tracer.start_as_current_span("ollama_chat") as span:
            # Set span attributes
            span.set_attribute("llm.vendor", "ollama")
            span.set_attribute("llm.request.model", model)
            span.set_attribute("llm.request.temperature", temperature)
            span.set_attribute("llm.request.max_tokens", max_tokens)
            span.set_attribute("llm.request.type", "chat")
            span.set_attribute("user.id", user_id)
            span.set_attribute("server.address", self.ollama_host)

            # Agent Spy specific attributes
            span.set_attribute("langsmith.span.kind", "LLM")
            span.set_attribute("langsmith.metadata.user_id", user_id)

            # Set input messages as attributes
            for i, message in enumerate(messages):
                span.set_attribute(f"llm.prompt.{i}.content", str(message.get("content", "")))
                span.set_attribute(f"llm.prompt.{i}.role", str(message.get("role", "user")))

            try:
                start_time = time.time()

                # Prepare options
                options = {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }

                # Make the Ollama chat API call
                response = self.client.chat(model=model, messages=messages, options=options, stream=False)

                end_time = time.time()
                duration_ms = int((end_time - start_time) * 1000)

                # Extract response data
                message_response = response.get("message", {})
                generated_text = message_response.get("content", "")

                # Set response attributes
                span.set_attribute("llm.response.model", model)
                span.set_attribute("llm.completion.0.content", generated_text)
                span.set_attribute("llm.completion.0.role", "assistant")
                span.set_attribute("llm.completion.0.finish_reason", "stop")

                # Token usage (if available)
                eval_count = response.get("eval_count", 0)
                prompt_eval_count = response.get("prompt_eval_count", 0)
                total_tokens = eval_count + prompt_eval_count

                if eval_count > 0:
                    span.set_attribute("llm.usage.completion_tokens", eval_count)
                if prompt_eval_count > 0:
                    span.set_attribute("llm.usage.prompt_tokens", prompt_eval_count)
                if total_tokens > 0:
                    span.set_attribute("llm.usage.total_tokens", total_tokens)

                # Performance metrics
                span.set_attribute("llm.response.duration_ms", duration_ms)

                # Ollama-specific metrics
                if "eval_duration" in response:
                    span.set_attribute("llm.ollama.eval_duration_ns", response["eval_duration"])
                if "prompt_eval_duration" in response:
                    span.set_attribute("llm.ollama.prompt_eval_duration_ns", response["prompt_eval_duration"])
                if "total_duration" in response:
                    span.set_attribute("llm.ollama.total_duration_ns", response["total_duration"])

                # Success status
                span.set_attribute("llm.response.status", "success")

                return {
                    "success": True,
                    "content": generated_text,
                    "model": model,
                    "duration_ms": duration_ms,
                    "eval_count": eval_count,
                    "prompt_eval_count": prompt_eval_count,
                    "total_tokens": total_tokens,
                    "finish_reason": "stop",
                    "raw_response": response,
                }

            except Exception as e:
                # Set error attributes
                span.set_attribute("llm.response.status", "error")
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))

                # Record the exception
                span.record_exception(e)

                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }

    def run_creative_writing_workflow(self, topic: str = "space exploration") -> dict[str, Any]:
        """Run a creative writing workflow with multiple LLM calls and full instrumentation.

        Args:
            topic: Topic to write about

        Returns:
            Dict containing workflow results
        """
        with self.tracer.start_as_current_span(f"creative_writing_workflow_{self.test_id}") as workflow_span:
            # Set workflow-level attributes
            workflow_span.set_attribute("workflow.name", "creative_writing_pipeline")
            workflow_span.set_attribute("workflow.version", "1.0.0")
            workflow_span.set_attribute("workflow.input.topic", topic)
            workflow_span.set_attribute("langsmith.span.kind", "WORKFLOW")

            workflow_start = time.time()
            results = {}

            try:
                # Step 1: Generate story concept
                print(f"📝 Step 1: Generating story concept for '{topic}'...")
                with self.tracer.start_as_current_span("story_concept_generation") as concept_span:
                    concept_span.set_attribute("step.name", "concept_generation")
                    concept_span.set_attribute("step.number", 1)
                    concept_span.set_attribute("step.type", "generation")

                    concept_result = self._call_ollama_generate_direct(
                        prompt=(
                            f"Create a compelling story concept about {topic}. "
                            "Include the main character, setting, and central conflict. "
                            "Keep it to 2-3 sentences."
                        ),
                        system_prompt="You are a creative writing assistant. Generate engaging story concepts.",
                        temperature=0.8,
                        max_tokens=200,
                    )
                    results["concept"] = concept_result

                    if not concept_result["success"]:
                        raise Exception(f"Concept generation failed: {concept_result['error']}")

                # Step 2: Develop characters using chat format
                print("👥 Step 2: Developing main character...")
                with self.tracer.start_as_current_span("character_development") as character_span:
                    character_span.set_attribute("step.name", "character_development")
                    character_span.set_attribute("step.number", 2)
                    character_span.set_attribute("step.type", "chat")

                    character_result = self._call_ollama_chat_direct(
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a character development expert. Create detailed, memorable characters.",
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Based on this story concept:\n\n{concept_result['content']}\n\n"
                                    "Develop the main character in detail. Include their background, "
                                    "personality, motivation, and a unique trait."
                                ),
                            },
                        ],
                        temperature=0.7,
                        max_tokens=300,
                    )
                    results["character"] = character_result

                    if not character_result["success"]:
                        raise Exception(f"Character development failed: {character_result['error']}")

                # Step 3: Write opening scene
                print("🎬 Step 3: Writing opening scene...")
                with self.tracer.start_as_current_span("opening_scene_writing") as opening_span:
                    opening_span.set_attribute("step.name", "opening_scene_writing")
                    opening_span.set_attribute("step.number", 3)
                    opening_span.set_attribute("step.type", "generation")

                    opening_result = self._call_ollama_generate_direct(
                        prompt=(
                            f"Write the opening scene of a story with this concept:\n{concept_result['content']}\n\n"
                            f"And this main character:\n{character_result['content']}\n\n"
                            "Make it engaging and set the mood. Write 2-3 paragraphs."
                        ),
                        system_prompt="You are a skilled fiction writer. Write vivid, engaging scenes that draw readers in.",
                        temperature=0.8,
                        max_tokens=400,
                    )
                    results["opening"] = opening_result

                    if not opening_result["success"]:
                        raise Exception(f"Opening scene failed: {opening_result['error']}")

                # Step 4: Create story outline
                print("📋 Step 4: Creating story outline...")
                with self.tracer.start_as_current_span("story_outline_creation") as outline_span:
                    outline_span.set_attribute("step.name", "story_outline_creation")
                    outline_span.set_attribute("step.number", 4)
                    outline_span.set_attribute("step.type", "chat")

                    outline_result = self._call_ollama_chat_direct(
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a story structure expert. Create compelling story outlines.",
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Based on this concept and opening:\n\nConcept: {concept_result['content']}\n\n"
                                    f"Opening: {opening_result['content']}\n\n"
                                    "Create a 5-chapter story outline with key events and character development."
                                ),
                            },
                        ],
                        temperature=0.6,
                        max_tokens=400,
                    )
                    results["outline"] = outline_result

                    if not outline_result["success"]:
                        raise Exception(f"Outline creation failed: {outline_result['error']}")

                # Calculate workflow metrics
                workflow_end = time.time()
                total_duration = int((workflow_end - workflow_start) * 1000)

                # Calculate total token usage
                total_eval_tokens = sum(r.get("eval_count", 0) for r in results.values() if r.get("success"))
                total_prompt_tokens = sum(r.get("prompt_eval_count", 0) for r in results.values() if r.get("success"))
                total_tokens = total_eval_tokens + total_prompt_tokens

                # Set final workflow attributes
                workflow_span.set_attribute("workflow.status", "completed")
                workflow_span.set_attribute("workflow.duration_ms", total_duration)
                workflow_span.set_attribute("workflow.steps_completed", 4)
                workflow_span.set_attribute("workflow.total_llm_calls", 4)
                workflow_span.set_attribute("workflow.total_prompt_tokens", total_prompt_tokens)
                workflow_span.set_attribute("workflow.total_completion_tokens", total_eval_tokens)
                workflow_span.set_attribute("workflow.total_tokens", total_tokens)

                results["workflow_summary"] = {
                    "success": True,
                    "topic": topic,
                    "steps_completed": 4,
                    "total_duration_ms": total_duration,
                    "total_tokens": total_tokens,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_eval_tokens,
                    "model_used": self._get_best_model(),
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
        """Force flush any pending traces with debugging."""
        print("🔄 Flushing traces to Agent Spy...")

        try:
            # Get the tracer provider
            provider = trace.get_tracer_provider()
            print(f"   Tracer provider: {type(provider).__name__}")

            # Check if there are any span processors
            if hasattr(provider, "_active_span_processor"):
                active_processor = provider._active_span_processor
                if active_processor:
                    print(f"   Active span processor: {type(active_processor).__name__}")

                    # Try to access the underlying processors
                    if hasattr(active_processor, "_span_processors"):
                        span_processors = active_processor._span_processors
                        print(f"   Underlying span processors: {len(span_processors)}")

                        for i, processor in enumerate(span_processors):
                            print(f"   Processor {i}: {type(processor).__name__}")
                            if hasattr(processor, "_span_exporter"):
                                exporter = processor._span_exporter
                                print(f"     Exporter: {type(exporter).__name__}")
                                if hasattr(exporter, "endpoint"):
                                    print(f"     Endpoint: {exporter.endpoint}")
                    else:
                        print("   No underlying span processors found")
                else:
                    print("   No active span processor")
            else:
                print("   _active_span_processor attribute not found")

            # Force flush with longer timeout
            result = provider.force_flush(timeout_millis=60000)
            print(f"   Flush result: {result}")
            print("✅ Traces flushed successfully")

        except Exception as e:
            print(f"❌ Error during trace flush: {e}")
            import traceback

            traceback.print_exc()


async def main():
    """Main function demonstrating Ollama OpenTelemetry instrumentation with Agent Spy."""
    print("🚀 Ollama + OpenTelemetry + Agent Spy Integration Demo")
    print("=" * 70)

    try:
        # Generate unique test identifier
        test_id = f"test-{int(time.time())}"
        print(f"🧪 Test ID: {test_id}")

        # Initialize instrumentation
        instrumentation = OllamaOTelInstrumentation(test_id=test_id)

        # Test simple generation
        print("\n🤖 Testing simple text generation...")
        simple_result = instrumentation.call_ollama_generate(
            prompt="Write a haiku about artificial intelligence.", user_id="demo_user", temperature=0.8, max_tokens=100
        )

        if simple_result["success"]:
            print("✅ Text generation successful!")
            print(f"   Model: {simple_result['model']}")
            print(f"   Duration: {simple_result['duration_ms']}ms")
            print(f"   Tokens: {simple_result['total_tokens']} total")
            print(f"   Response: {simple_result['content'][:100]}...")
        else:
            print(f"❌ Text generation failed: {simple_result['error']}")

        print("\n" + "=" * 70)

        # Test chat format
        print("💬 Testing chat conversation...")
        chat_result = instrumentation.call_ollama_chat(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that explains concepts clearly."},
                {"role": "user", "content": "Explain quantum computing in simple terms."},
            ],
            user_id="demo_user",
            temperature=0.7,
            max_tokens=200,
        )

        if chat_result["success"]:
            print("✅ Chat conversation successful!")
            print(f"   Model: {chat_result['model']}")
            print(f"   Duration: {chat_result['duration_ms']}ms")
            print(f"   Tokens: {chat_result['total_tokens']} total")
            print(f"   Response: {chat_result['content'][:100]}...")
        else:
            print(f"❌ Chat conversation failed: {chat_result['error']}")

        print("\n" + "=" * 70)

        # Test multi-step creative writing workflow
        print("🎨 Running creative writing workflow...")
        workflow_results = instrumentation.run_creative_writing_workflow("time travel")

        summary = workflow_results.get("workflow_summary", {})
        if summary.get("success"):
            print("✅ Creative writing workflow completed successfully!")
            print(f"   Topic: {summary['topic']}")
            print(f"   Model: {summary['model_used']}")
            print(f"   Steps completed: {summary['steps_completed']}")
            print(f"   Total duration: {summary['total_duration_ms']}ms")
            print(f"   Total tokens used: {summary['total_tokens']}")
            print(f"   Prompt tokens: {summary['total_prompt_tokens']}")
            print(f"   Completion tokens: {summary['total_completion_tokens']}")

            # Show a sample of the generated content
            if "concept" in workflow_results and workflow_results["concept"]["success"]:
                print("\n📖 Generated Story Concept:")
                print(f"   {workflow_results['concept']['content'][:200]}...")

        else:
            print(f"❌ Creative writing workflow failed: {summary.get('error', 'Unknown error')}")

        # Force flush traces to Agent Spy
        print("\n" + "=" * 70)
        instrumentation.flush_traces()

        print("\n🎯 Demo completed!")
        print("   Check Agent Spy dashboard at http://localhost:8000 to view traces")
        print(f"   Look for traces from service: 'ollama-llm-service-{test_id}'")
        print("   Observe the hierarchical workflow with parent-child relationships")

        return summary.get("success", False)

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        print("   Make sure Ollama is running and accessible from the container")
        print("   Try: docker run -p 11434:11434 ollama/ollama")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
