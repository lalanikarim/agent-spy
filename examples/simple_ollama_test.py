#!/usr/bin/env python3
# /// script
# dependencies = [
#   "ollama>=0.3.0",
# ]
# ///

"""
Simple Ollama Test

Quick test to verify Ollama connection and model availability.
"""

import os

import ollama


def test_ollama_connection():
    """Test basic Ollama connection and model listing."""
    print("🔍 Testing Ollama connection...")

    # First check if OLLAMA_HOST environment variable is set
    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host:
        print(f"   Using OLLAMA_HOST: {ollama_host}")
        try:
            client = ollama.Client(host=ollama_host)
            models = client.list()
            print(f"✅ Connected to {ollama_host}")
            print(f"   Available models: {[m.model for m in models.get('models', [])]}")

            # Test a simple generation
            if models.get('models'):
                model_name = models['models'][0].model
                print(f"   Testing generation with {model_name}...")
                response = client.generate(
                    model=model_name,
                    prompt="Hello, how are you?",
                    stream=False
                )
                print("✅ Generation successful!")
                print(f"   Response: {response.get('response', '')[:100]}...")
                return True
        except Exception as e:
            print(f"   ❌ Failed to connect to {ollama_host}: {e}")

    # Fall back to auto-detection if OLLAMA_HOST is not set or fails
    print("   Auto-detecting Ollama host...")
    hosts = [
        "http://192.168.1.200:11434",  # Specified host IP
        "http://host.docker.internal:11434",
        "http://172.17.0.1:11434",
        "http://localhost:11434"
    ]

    for host in hosts:
        try:
            print(f"   Trying {host}...")
            client = ollama.Client(host=host)
            models = client.list()
            print(f"✅ Connected to {host}")
            print(f"   Available models: {[m.model for m in models.get('models', [])]}")

            # Test a simple generation
            if models.get('models'):
                model_name = models['models'][0].model
                print(f"   Testing generation with {model_name}...")
                response = client.generate(
                    model=model_name,
                    prompt="Hello, how are you?",
                    stream=False
                )
                print("✅ Generation successful!")
                print(f"   Response: {response.get('response', '')[:100]}...")
                return True

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            continue

    print("❌ Could not connect to Ollama")
    return False

if __name__ == "__main__":
    success = test_ollama_connection()
    exit(0 if success else 1)
