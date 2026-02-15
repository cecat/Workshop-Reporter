#!/usr/bin/env python3
"""
Test script for NVIDIA NIM endpoint on spark-ts

Prerequisites:
1. Set up SSH tunnel first:
   ssh -L 8000:localhost:8000 spark-ts

2. Then run this script:
   python test_nim_endpoint.py
"""

from openai import OpenAI

# Configure for NIM endpoint via SSH tunnel
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key-not-needed",  # NIM doesn't require auth for local access
)


def test_connection():
    """Test basic connectivity to NIM endpoint"""
    print("Testing NIM endpoint connection...")

    try:
        # List available models
        models = client.models.list()
        print("✅ Connected successfully!")
        print("\nAvailable models:")
        for model in models.data:
            print(f"  - {model.id}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure you have SSH tunnel running:")
        print("  ssh -L 8000:localhost:8000 spark-ts")
        return False


def test_completion():
    """Test text completion with llama-3.1-8b-instruct"""
    print("\n" + "=" * 60)
    print("Testing text completion with meta/llama-3.1-8b-instruct...")
    print("=" * 60)

    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": "Say 'Hello from NVIDIA NIM!' in exactly 5 words.",
                },
            ],
            max_tokens=50,
            temperature=0.3,
        )

        result = response.choices[0].message.content
        print("\n✅ Completion successful!")
        print(f"\nModel: {response.model}")
        print(f"Response: {result}")
        print("\nUsage:")
        print(f"  Prompt tokens: {response.usage.prompt_tokens}")
        print(f"  Completion tokens: {response.usage.completion_tokens}")
        print(f"  Total tokens: {response.usage.total_tokens}")
        return True

    except Exception as e:
        print(f"❌ Completion failed: {e}")
        return False


def test_workshop_reporter_style():
    """Test with a workshop reporter-style prompt"""
    print("\n" + "=" * 60)
    print("Testing workshop reporter-style summary generation...")
    print("=" * 60)

    sample_session = """
Session: Data Workflows and Agents (DWARF)
Leaders: Dr. Alice Smith, Dr. Bob Chen

Lightning Talk: Automated Data Pipeline for LLM Training
Author: Jane Doe, TechCorp
Abstract: We present a novel approach to automating data pipelines for large language model training workflows.
"""

    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical report writer for academic conferences.",
                },
                {
                    "role": "user",
                    "content": f"Generate a 2-sentence summary of this session:\n\n{sample_session}",
                },
            ],
            max_tokens=200,
            temperature=0.3,
        )

        result = response.choices[0].message.content
        print("\n✅ Summary generated!")
        print(f"\nSummary:\n{result}")
        return True

    except Exception as e:
        print(f"❌ Summary generation failed: {e}")
        return False


if __name__ == "__main__":
    print("NVIDIA NIM Endpoint Test")
    print("=" * 60)
    print("Target: http://localhost:8000/v1 (via SSH tunnel)")
    print("Model: meta/llama-3.1-8b-instruct")
    print()

    # Test connection
    if not test_connection():
        exit(1)

    # Test completion
    if not test_completion():
        exit(1)

    # Test workshop reporter style
    if not test_workshop_reporter_style():
        exit(1)

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nYou can now use this configuration in your workshop reporter:")
    print("  client = OpenAI(")
    print('      base_url="http://localhost:8000/v1",')
    print('      api_key="dummy"')
    print("  )")
    print('  model="meta/llama-3.1-8b-instruct"')
