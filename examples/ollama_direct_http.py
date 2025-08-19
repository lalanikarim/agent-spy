#!/usr/bin/env python3
# /// script
# dependencies = [
#   "ollama>=0.3.0",
#   "requests>=2.31.0",
# ]
# ///

"""
Ollama + Direct HTTP Integration Example

This example demonstrates how to instrument Ollama API calls and send traces
directly to Agent Spy via HTTP POST. It connects to an Ollama instance running
on the host machine (outside the container).

Features:
- Direct HTTP POST to Agent Spy OTLP endpoint
- Rich tracing with model parameters, tokens, and performance metrics
- Multi-step LLM workflows with parent-child span relationships
- Connects to host Ollama instance from container environment
- Real-time trace visualization in Agent Spy

Prerequisites:
- Ollama running on host machine (accessible via host.docker.internal or 192.168.1.*)
- Agent Spy server running on http://localhost:8000
- At least one model pulled in Ollama (e.g., llama3.2:1b, qwen2.5:0.5b)

Usage:
    uv run python examples/ollama_direct_http.py
"""

import asyncio
import time
import uuid
from typing import Any

import requests


class OllamaDirectHTTPInstrumentation:
    """Direct HTTP instrumentation for Ollama API calls with Agent Spy integration."""

    def __init__(
        self,
        agent_spy_endpoint: str = "http://localhost:8000/v1/traces/",
        ollama_host: str = None,
        test_id: str = None,
    ):
        """Initialize Ollama direct HTTP instrumentation.

        Args:
            agent_spy_endpoint: Agent Spy OTLP endpoint URL
            ollama_host: Ollama host URL (auto-detected if None)
            test_id: Optional test identifier for unique service naming
        """
        self.agent_spy_endpoint = agent_spy_endpoint
        self.ollama_host = ollama_host or self._detect_ollama_host()
        self.test_id = test_id or f"test-{int(time.time())}"
        self.client = None
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
                import ollama

                test_client = ollama.Client(host=host)
                test_client.list()
                print(f"✅ Found Ollama at: {host}")
                return host
            except Exception:
                continue

        print("⚠️  Could not auto-detect Ollama. Using default: http://localhost:11434")
        return "http://localhost:11434"

    def _setup_instrumentation(self):
        """Set up direct HTTP instrumentation and Ollama client."""
        print("🔧 Setting up direct HTTP instrumentation...")

        # Initialize Ollama client
        try:
            import ollama

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

            print("✅ Direct HTTP instrumentation configured")
            print(f"   Agent Spy Endpoint: {self.agent_spy_endpoint}")
            print(f"   Ollama Host: {self.ollama_host}")
            print(
                f"   Available Models: {', '.join(self.available_models[:3])}{'...' if len(self.available_models) > 3 else ''}"
            )

            # Test OTLP endpoint connectivity
            print("🔍 Testing OTLP endpoint connectivity...")
            try:
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

    def _send_trace_to_agent_spy(self, trace_data: dict[str, Any]) -> bool:
        """Send trace data directly to Agent Spy via HTTP POST."""
        try:
            response = requests.post(
                self.agent_spy_endpoint, headers={"Content-Type": "application/json"}, json=trace_data, timeout=30
            )

            if response.status_code == 200:
                print("   ✅ Trace sent successfully to Agent Spy")
                return True
            else:
                print(f"   ❌ Failed to send trace: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Error sending trace: {e}")
            return False

    def _create_otlp_trace(
        self,
        span_name: str,
        span_id: str,
        trace_id: str,
        parent_span_id: str = None,
        attributes: dict[str, Any] = None,
        start_time: int = None,
        end_time: int = None,
    ) -> dict[str, Any]:
        """Create OTLP trace format for Agent Spy."""

        if start_time is None:
            start_time = int(time.time() * 1_000_000_000)
        if end_time is None:
            end_time = start_time

        # Convert attributes to OTLP format
        otlp_attributes = []
        if attributes:
            for key, value in attributes.items():
                if isinstance(value, str):
                    otlp_attributes.append({"key": key, "value": {"stringValue": value}})
                elif isinstance(value, int):
                    otlp_attributes.append({"key": key, "value": {"intValue": value}})
                elif isinstance(value, float):
                    otlp_attributes.append({"key": key, "value": {"doubleValue": value}})
                elif isinstance(value, bool):
                    otlp_attributes.append({"key": key, "value": {"boolValue": value}})
                else:
                    otlp_attributes.append({"key": key, "value": {"stringValue": str(value)}})

        # Create OTLP trace structure
        trace_data = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": f"ollama-llm-service-{self.test_id}"}},
                            {"key": "service.version", "value": {"stringValue": "1.0.0"}},
                            {"key": "deployment.environment", "value": {"stringValue": "development"}},
                            {"key": "service.instance.id", "value": {"stringValue": "ollama-instance-1"}},
                            {"key": "llm.vendor", "value": {"stringValue": "ollama"}},
                            {"key": "test.id", "value": {"stringValue": self.test_id}},
                        ]
                    },
                    "scopeSpans": [
                        {
                            "spans": [
                                {
                                    "traceId": trace_id,
                                    "spanId": span_id,
                                    "parentSpanId": parent_span_id,
                                    "name": span_name,
                                    "startTimeUnixNano": str(start_time),
                                    "endTimeUnixNano": str(end_time),
                                    "attributes": otlp_attributes,
                                    "status": {"code": 1, "message": "OK"},  # OK status
                                }
                            ]
                        }
                    ],
                }
            ]
        }

        return trace_data

    def call_ollama_generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        user_id: str = "anonymous",
        system_prompt: str = None,
        parent_span_id: str = None,
    ) -> dict[str, Any]:
        """Make an instrumented Ollama generate call with direct HTTP tracing.

        Args:
            prompt: The prompt to send to the model
            model: Model name (auto-selected if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            user_id: User identifier for tracking
            system_prompt: Optional system prompt
            parent_span_id: Optional parent span ID for hierarchical traces

        Returns:
            Dict containing the generation response and metadata
        """
        model = model or self._get_best_model()

        # Generate unique IDs for this span
        span_id = str(uuid.uuid4()).replace("-", "")[:16]
        trace_id = str(uuid.uuid4()).replace("-", "")

        print(f"🔍 Creating span for ollama_generate: {span_id}")

        # Record start time
        start_time = int(time.time() * 1_000_000_000)

        # Prepare span attributes
        attributes = {
            "llm.vendor": "ollama",
            "llm.request.model": model,
            "llm.request.temperature": temperature,
            "llm.request.max_tokens": max_tokens,
            "llm.request.type": "generate",
            "user.id": user_id,
            "server.address": self.ollama_host,
            "langsmith.span.kind": "LLM",
            "langsmith.metadata.user_id": user_id,
            "llm.prompt.0.content": prompt,
            "llm.prompt.0.role": "user",
        }

        if system_prompt:
            attributes["llm.prompt.system.content"] = system_prompt
            attributes["llm.prompt.system.role"] = "system"

        try:
            # Prepare options
            options = {
                "temperature": temperature,
                "num_predict": max_tokens,
            }

            # Make the Ollama API call
            response = self.client.generate(model=model, prompt=prompt, system=system_prompt, options=options, stream=False)

            # Record end time
            end_time = int(time.time() * 1_000_000_000)
            duration_ms = int((end_time - start_time) / 1_000_000)

            # Extract response data
            generated_text = response.get("response", "")

            # Add response attributes
            attributes.update(
                {
                    "llm.response.model": model,
                    "llm.completion.0.content": generated_text,
                    "llm.completion.0.role": "assistant",
                    "llm.completion.0.finish_reason": "stop",
                    "llm.response.duration_ms": duration_ms,
                    "llm.response.status": "success",
                }
            )

            # Token usage (if available)
            eval_count = response.get("eval_count", 0)
            prompt_eval_count = response.get("prompt_eval_count", 0)
            total_tokens = eval_count + prompt_eval_count

            if eval_count > 0:
                attributes["llm.usage.completion_tokens"] = eval_count
            if prompt_eval_count > 0:
                attributes["llm.usage.prompt_tokens"] = prompt_eval_count
            if total_tokens > 0:
                attributes["llm.usage.total_tokens"] = total_tokens

            # Ollama-specific metrics
            if "eval_duration" in response:
                attributes["llm.ollama.eval_duration_ns"] = response["eval_duration"]
            if "prompt_eval_duration" in response:
                attributes["llm.ollama.prompt_eval_duration_ns"] = response["prompt_eval_duration"]
            if "total_duration" in response:
                attributes["llm.ollama.total_duration_ns"] = response["total_duration"]

            # Create and send trace
            trace_data = self._create_otlp_trace(
                span_name=f"ollama_generate_{self.test_id}",
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                attributes=attributes,
                start_time=start_time,
                end_time=end_time,
            )

            self._send_trace_to_agent_spy(trace_data)

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
                "span_id": span_id,
                "trace_id": trace_id,
            }

        except Exception as e:
            # Record end time for error case
            end_time = int(time.time() * 1_000_000_000)

            # Add error attributes
            attributes.update(
                {
                    "llm.response.status": "error",
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                }
            )

            # Create and send error trace
            trace_data = self._create_otlp_trace(
                span_name=f"ollama_generate_{self.test_id}",
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                attributes=attributes,
                start_time=start_time,
                end_time=end_time,
            )

            self._send_trace_to_agent_spy(trace_data)

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "span_id": span_id,
                "trace_id": trace_id,
            }

    def call_ollama_chat(
        self,
        messages: list[dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        user_id: str = "anonymous",
        parent_span_id: str = None,
    ) -> dict[str, Any]:
        """Make an instrumented Ollama chat call with direct HTTP tracing.

        Args:
            messages: List of chat messages
            model: Model name (auto-selected if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            user_id: User identifier for tracking
            parent_span_id: Optional parent span ID for hierarchical traces

        Returns:
            Dict containing the chat response and metadata
        """
        model = model or self._get_best_model()

        # Generate unique IDs for this span
        span_id = str(uuid.uuid4()).replace("-", "")[:16]
        trace_id = str(uuid.uuid4()).replace("-", "")

        print(f"🔍 Creating span for ollama_chat: {span_id}")

        # Record start time
        start_time = int(time.time() * 1_000_000_000)

        # Prepare span attributes
        attributes = {
            "llm.vendor": "ollama",
            "llm.request.model": model,
            "llm.request.temperature": temperature,
            "llm.request.max_tokens": max_tokens,
            "llm.request.type": "chat",
            "user.id": user_id,
            "server.address": self.ollama_host,
            "langsmith.span.kind": "LLM",
            "langsmith.metadata.user_id": user_id,
        }

        # Set input messages as attributes
        for i, message in enumerate(messages):
            attributes[f"llm.prompt.{i}.content"] = str(message.get("content", ""))
            attributes[f"llm.prompt.{i}.role"] = str(message.get("role", "user"))

        try:
            # Prepare options
            options = {
                "temperature": temperature,
                "num_predict": max_tokens,
            }

            # Make the Ollama chat API call
            response = self.client.chat(model=model, messages=messages, options=options, stream=False)

            # Record end time
            end_time = int(time.time() * 1_000_000_000)
            duration_ms = int((end_time - start_time) / 1_000_000)

            # Extract response data
            message_response = response.get("message", {})
            generated_text = message_response.get("content", "")

            # Add response attributes
            attributes.update(
                {
                    "llm.response.model": model,
                    "llm.completion.0.content": generated_text,
                    "llm.completion.0.role": "assistant",
                    "llm.completion.0.finish_reason": "stop",
                    "llm.response.duration_ms": duration_ms,
                    "llm.response.status": "success",
                }
            )

            # Token usage (if available)
            eval_count = response.get("eval_count", 0)
            prompt_eval_count = response.get("prompt_eval_count", 0)
            total_tokens = eval_count + prompt_eval_count

            if eval_count > 0:
                attributes["llm.usage.completion_tokens"] = eval_count
            if prompt_eval_count > 0:
                attributes["llm.usage.prompt_tokens"] = prompt_eval_count
            if total_tokens > 0:
                attributes["llm.usage.total_tokens"] = total_tokens

            # Ollama-specific metrics
            if "eval_duration" in response:
                attributes["llm.ollama.eval_duration_ns"] = response["eval_duration"]
            if "prompt_eval_duration" in response:
                attributes["llm.ollama.prompt_eval_duration_ns"] = response["prompt_eval_duration"]
            if "total_duration" in response:
                attributes["llm.ollama.total_duration_ns"] = response["total_duration"]

            # Create and send trace
            trace_data = self._create_otlp_trace(
                span_name="ollama_chat",
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                attributes=attributes,
                start_time=start_time,
                end_time=end_time,
            )

            self._send_trace_to_agent_spy(trace_data)

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
                "span_id": span_id,
                "trace_id": trace_id,
            }

        except Exception as e:
            # Record end time for error case
            end_time = int(time.time() * 1_000_000_000)

            # Add error attributes
            attributes.update(
                {
                    "llm.response.status": "error",
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                }
            )

            # Create and send error trace
            trace_data = self._create_otlp_trace(
                span_name="ollama_chat",
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                attributes=attributes,
                start_time=start_time,
                end_time=end_time,
            )

            self._send_trace_to_agent_spy(trace_data)

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "span_id": span_id,
                "trace_id": trace_id,
            }

    def run_creative_writing_workflow(self, topic: str = "space exploration") -> dict[str, Any]:
        """Run a creative writing workflow with multiple LLM calls and direct HTTP tracing.

        Args:
            topic: Topic to write about

        Returns:
            Dict containing workflow results
        """
        # Generate workflow-level IDs
        workflow_span_id = str(uuid.uuid4()).replace("-", "")[:16]
        workflow_trace_id = str(uuid.uuid4()).replace("-", "")

        print(f"🔍 Creating workflow span: {workflow_span_id}")

        # Record workflow start time
        workflow_start = int(time.time() * 1_000_000_000)

        # Prepare workflow attributes
        workflow_attributes = {
            "workflow.name": "creative_writing_pipeline",
            "workflow.version": "1.0.0",
            "workflow.input.topic": topic,
            "langsmith.span.kind": "WORKFLOW",
        }

        workflow_start_time = time.time()
        results = {}

        try:
            # Step 1: Generate story concept
            print(f"📝 Step 1: Generating story concept for '{topic}'...")
            concept_result = self.call_ollama_generate(
                prompt=(
                    f"Create a compelling story concept about {topic}. "
                    "Include the main character, setting, and central conflict. "
                    "Keep it to 2-3 sentences."
                ),
                system_prompt="You are a creative writing assistant. Generate engaging story concepts.",
                temperature=0.8,
                max_tokens=200,
                parent_span_id=workflow_span_id,
            )
            results["concept"] = concept_result

            if not concept_result["success"]:
                raise Exception(f"Concept generation failed: {concept_result['error']}")

            # Step 2: Develop characters using chat format
            print("👥 Step 2: Developing main character...")
            character_result = self.call_ollama_chat(
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
                parent_span_id=workflow_span_id,
            )
            results["character"] = character_result

            if not character_result["success"]:
                raise Exception(f"Character development failed: {character_result['error']}")

            # Step 3: Write opening scene
            print("🎬 Step 3: Writing opening scene...")
            opening_result = self.call_ollama_generate(
                prompt=(
                    f"Write the opening scene of a story with this concept:\n{concept_result['content']}\n\n"
                    f"And this main character:\n{character_result['content']}\n\n"
                    "Make it engaging and set the mood. Write 2-3 paragraphs."
                ),
                system_prompt="You are a skilled fiction writer. Write vivid, engaging scenes that draw readers in.",
                temperature=0.8,
                max_tokens=400,
                parent_span_id=workflow_span_id,
            )
            results["opening"] = opening_result

            if not opening_result["success"]:
                raise Exception(f"Opening scene failed: {opening_result['error']}")

            # Step 4: Create story outline
            print("📋 Step 4: Creating story outline...")
            outline_result = self.call_ollama_chat(
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
                parent_span_id=workflow_span_id,
            )
            results["outline"] = outline_result

            if not outline_result["success"]:
                raise Exception(f"Outline creation failed: {outline_result['error']}")

            # Calculate workflow metrics
            workflow_end_time = time.time()
            total_duration = int((workflow_end_time - workflow_start_time) * 1000)

            # Calculate total token usage
            total_eval_tokens = sum(r.get("eval_count", 0) for r in results.values() if r.get("success"))
            total_prompt_tokens = sum(r.get("prompt_eval_count", 0) for r in results.values() if r.get("success"))
            total_tokens = total_eval_tokens + total_prompt_tokens

            # Record workflow end time
            workflow_end = int(time.time() * 1_000_000_000)

            # Add final workflow attributes
            workflow_attributes.update(
                {
                    "workflow.status": "completed",
                    "workflow.duration_ms": total_duration,
                    "workflow.steps_completed": 4,
                    "workflow.total_llm_calls": 4,
                    "workflow.total_prompt_tokens": total_prompt_tokens,
                    "workflow.total_completion_tokens": total_eval_tokens,
                    "workflow.total_tokens": total_tokens,
                }
            )

            # Create and send workflow trace
            workflow_trace_data = self._create_otlp_trace(
                span_name=f"creative_writing_workflow_{self.test_id}",
                span_id=workflow_span_id,
                trace_id=workflow_trace_id,
                attributes=workflow_attributes,
                start_time=workflow_start,
                end_time=workflow_end,
            )

            self._send_trace_to_agent_spy(workflow_trace_data)

            results["workflow_summary"] = {
                "success": True,
                "topic": topic,
                "steps_completed": 4,
                "total_duration_ms": total_duration,
                "total_tokens": total_tokens,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_eval_tokens,
                "model_used": self._get_best_model(),
                "workflow_span_id": workflow_span_id,
                "workflow_trace_id": workflow_trace_id,
            }

            return results

        except Exception as e:
            # Handle workflow errors
            workflow_end_time = time.time()
            total_duration = int((workflow_end_time - workflow_start_time) * 1000)

            # Record workflow end time
            workflow_end = int(time.time() * 1_000_000_000)

            # Add error attributes
            workflow_attributes.update(
                {
                    "workflow.status": "failed",
                    "workflow.duration_ms": total_duration,
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                }
            )

            # Create and send error workflow trace
            workflow_trace_data = self._create_otlp_trace(
                span_name=f"creative_writing_workflow_{self.test_id}",
                span_id=workflow_span_id,
                trace_id=workflow_trace_id,
                attributes=workflow_attributes,
                start_time=workflow_start,
                end_time=workflow_end,
            )

            self._send_trace_to_agent_spy(workflow_trace_data)

            results["workflow_summary"] = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "total_duration_ms": total_duration,
                "workflow_span_id": workflow_span_id,
                "workflow_trace_id": workflow_trace_id,
            }

            return results


async def main():
    """Main function demonstrating Ollama direct HTTP instrumentation with Agent Spy."""
    print("🚀 Ollama + Direct HTTP + Agent Spy Integration Demo")
    print("=" * 70)

    try:
        # Generate unique test identifier
        test_id = f"test-{int(time.time())}"
        print(f"🧪 Test ID: {test_id}")

        # Initialize instrumentation
        instrumentation = OllamaDirectHTTPInstrumentation(test_id=test_id)

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
            print(f"   Span ID: {simple_result['span_id']}")
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
            print(f"   Span ID: {chat_result['span_id']}")
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
            print(f"   Workflow Span ID: {summary['workflow_span_id']}")

            # Show a sample of the generated content
            if "concept" in workflow_results and workflow_results["concept"]["success"]:
                print("\n📖 Generated Story Concept:")
                print(f"   {workflow_results['concept']['content'][:200]}...")

        else:
            print(f"❌ Creative writing workflow failed: {summary.get('error', 'Unknown error')}")

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
