#!/usr/bin/env python3
"""
Example usage of Workshop-Reporter configuration system.

This demonstrates how to use the configuration system to switch between
different LLM endpoints (OpenAI, NIM on spark-ts, etc.)
"""

from config_loader import load_config
from llm_client import create_llm_client


def example_basic_usage():
    """Basic usage: use whatever endpoint is active in configuration.yaml"""
    print("=== Example 1: Basic Usage ===\n")

    # Create client (uses active_endpoint from configuration.yaml)
    client = create_llm_client()
    print(f"Using: {client}\n")

    # Generate a completion
    messages = [
        {"role": "system", "content": "You are a technical report writer."},
        {
            "role": "user",
            "content": "Write a one-sentence summary of a workshop on AI workflows.",
        },
    ]

    response = client.chat_completion(messages, max_tokens=200)
    print(f"Response: {response}\n")


def example_endpoint_switching():
    """Switch between different endpoints programmatically"""
    print("=== Example 2: Endpoint Switching ===\n")

    # Load config
    config = load_config()
    print(f"Available endpoints: {config.list_endpoints()}\n")

    # Try with OpenAI
    try:
        print("Trying OpenAI endpoint...")
        client_openai = create_llm_client(endpoint="openai")
        print(f"Created: {client_openai}\n")
    except Exception as e:
        print(f"OpenAI not available: {e}\n")

    # Try with NIM
    try:
        print("Trying NIM endpoint...")
        client_nim = create_llm_client(endpoint="nim_spark")
        print(f"Created: {client_nim}\n")
    except Exception as e:
        print(f"NIM not available: {e}\n")


def example_parameter_override():
    """Override generation parameters"""
    print("=== Example 3: Parameter Override ===\n")

    client = create_llm_client()

    messages = [
        {"role": "system", "content": "You are a creative writer."},
        {"role": "user", "content": "Generate a creative one-liner about workshops."},
    ]

    # Use higher temperature for more creativity
    print("With temperature=0.9 (creative):")
    response1 = client.chat_completion(messages, temperature=0.9, max_tokens=50)
    print(f"{response1}\n")

    # Use lower temperature for more deterministic
    print("With temperature=0.1 (focused):")
    response2 = client.chat_completion(messages, temperature=0.1, max_tokens=50)
    print(f"{response2}\n")


def example_workshop_report_style():
    """Example mimicking actual workshop report generation"""
    print("=== Example 4: Workshop Report Style ===\n")

    client = create_llm_client()

    # Simulate a session summary request
    session_info = """
    Session: Data Workflows and Agents (DWARF)
    
    Lightning Talks:
    1. "Automated Pipeline for LLM Training" by Jane Smith
       - Developed scalable data pipeline handling 100TB+ datasets
       - Reduced preprocessing time by 60%
    
    2. "Multi-Agent Coordination Framework" by John Doe
       - Novel approach to coordinating autonomous agents
       - Applied to climate modeling workflows
    """

    messages = [
        {
            "role": "system",
            "content": "You are a technical report writer for conference proceedings.",
        },
        {
            "role": "user",
            "content": f"Write a 2-paragraph summary of this session:\n\n{session_info}",
        },
    ]

    print("Generating session summary...")
    response = client.chat_completion(messages, max_tokens=500, temperature=0.3)
    print(f"\n{response}\n")


if __name__ == "__main__":
    import sys

    examples = {
        "1": example_basic_usage,
        "2": example_endpoint_switching,
        "3": example_parameter_override,
        "4": example_workshop_report_style,
    }

    if len(sys.argv) > 1 and sys.argv[1] in examples:
        # Run specific example
        examples[sys.argv[1]]()
    else:
        # Run all examples
        print("Workshop-Reporter Configuration System Examples")
        print("=" * 50)
        print()

        try:
            for example_func in examples.values():
                example_func()
                print("-" * 50)
                print()
        except Exception as e:
            print(f"\nError: {e}")
            print("\nMake sure you have:")
            print("1. Created secrets.yaml from secrets.yaml.template")
            print("2. Set active_endpoint in configuration.yaml")
            print("3. Installed required packages: pip install openai pyyaml")
