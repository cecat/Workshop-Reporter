#!/usr/bin/env python3
"""
Test NVIDIA NIM on spark-ts via SSH (no tunnel needed)

This script runs LLM completions on spark-ts by executing curl via SSH.
"""

import json
import subprocess
import sys


def call_nim_via_ssh(
    messages, model="meta/llama-3.1-8b-instruct", max_tokens=2000, temperature=0.3
):
    """
    Call NIM endpoint on spark-ts via SSH

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name (default: meta/llama-3.1-8b-instruct)
        max_tokens: Maximum tokens in response
        temperature: Temperature for sampling

    Returns:
        str: The completion text
    """
    # Build the curl command
    request_data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    curl_cmd = (
        f"curl -s http://localhost:8000/v1/chat/completions "
        f'-H "Content-Type: application/json" '
        f"-d '{json.dumps(request_data)}'"
    )

    # Execute via SSH
    ssh_cmd = ["ssh", "spark-ts", curl_cmd]

    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            raise Exception(f"SSH command failed: {result.stderr}")

        # Parse response
        response = json.loads(result.stdout)

        if "error" in response:
            raise Exception(f"NIM error: {response['error']}")

        return response["choices"][0]["message"]["content"]

    except subprocess.TimeoutExpired:
        raise Exception("Request timed out after 60 seconds")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response: {e}\nOutput: {result.stdout}")
    except Exception as e:
        raise Exception(f"Request failed: {e}")


def test_simple_completion():
    """Test a simple completion"""
    print("Testing simple completion...")
    print("=" * 60)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello from NVIDIA NIM!' in exactly 5 words."},
    ]

    try:
        response = call_nim_via_ssh(messages, max_tokens=50)
        print("✅ Success!")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_workshop_summary():
    """Test workshop-style summary generation"""
    print("\nTesting workshop summary generation...")
    print("=" * 60)

    sample_session = """
Session: Data Workflows and Agents (DWARF)
Leaders: Dr. Alice Smith, Dr. Bob Chen

Lightning Talk: Automated Data Pipeline for LLM Training
Author: Jane Doe, TechCorp
Abstract: We present a novel approach to automating data pipelines for large language model training workflows, focusing on scalability and reliability.

Lightning Talk: Multi-Agent Coordination Framework
Author: John Smith, ResearchLab
Abstract: This work introduces a framework for coordinating multiple AI agents in complex data processing scenarios.
"""

    messages = [
        {
            "role": "system",
            "content": "You are a technical report writer for academic conferences. Generate concise, professional summaries.",
        },
        {
            "role": "user",
            "content": f"Generate a 3-4 sentence summary of this session, highlighting key themes and contributions:\n\n{sample_session}",
        },
    ]

    try:
        response = call_nim_via_ssh(messages, max_tokens=300)
        print("✅ Success!")
        print(f"\nGenerated Summary:\n{response}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_tpc_reporter_style():
    """Test with actual TPC25 master prompt style"""
    print("\nTesting TPC reporter prompt style...")
    print("=" * 60)

    # Simplified version of the TPC25 master prompt
    prompt = """You are a report generator for TPC conference sessions. Generate a session summary.

Session: Model Architecture and Performance Evaluation (MAPE)
Leaders: Dr. Sarah Johnson

Lightning Talks:
1. Title: GPU Memory Optimization for Large Models
   Author: Mike Chen, TechCorp
   Abstract: We present techniques for optimizing GPU memory usage in trillion-parameter models.

2. Title: Performance Benchmarking Framework
   Author: Lisa Wang, ResearchU
   Abstract: A comprehensive framework for benchmarking model performance across different hardware.

Generate a 2-3 paragraph summary covering:
1. Session overview and key themes
2. Main contributions from lightning talks
3. Potential impact on the field"""

    messages = [
        {
            "role": "system",
            "content": "You are a technical report writer for conference proceedings.",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        response = call_nim_via_ssh(messages, max_tokens=500, temperature=0.3)
        print("✅ Success!")
        print(f"\nGenerated Report:\n{response}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


if __name__ == "__main__":
    print("NVIDIA NIM Test via SSH")
    print("=" * 60)
    print("Host: spark-ts")
    print("Model: meta/llama-3.1-8b-instruct")
    print("Method: SSH + curl (no tunnel needed)")
    print()

    all_passed = True

    # Run tests
    if not test_simple_completion():
        all_passed = False

    if not test_workshop_summary():
        all_passed = False

    if not test_tpc_reporter_style():
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        print("\nTo use in your code:")
        print("  from test_nim_via_ssh import call_nim_via_ssh")
        print("  result = call_nim_via_ssh(messages)")
    else:
        print("❌ Some tests failed")
        sys.exit(1)
