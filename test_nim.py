#!/usr/bin/env python3
"""
Simple test script to interact with the NIM endpoint
"""

import yaml
from openai import OpenAI


def load_config(file_path="config.yml"):
    """Load configuration from config.yml"""
    with open(file_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def main():
    # Load config
    config = load_config()
    model_config = config["model"]

    # Initialize OpenAI client pointing to NIM
    client = OpenAI(
        base_url=model_config["endpoint"],
        api_key="not-needed",  # NIM doesn't require API key for local use
    )

    print("=" * 60)
    print("NIM Test - Chat with Llama 3.1 8B Instruct")
    print(f"Endpoint: {model_config['endpoint']}")
    print(f"Model: {model_config['name']}")
    print("=" * 60)
    print()

    # Interactive loop
    while True:
        try:
            # Get user input
            user_prompt = input("You: ").strip()

            if not user_prompt:
                continue

            # Exit commands
            if user_prompt.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            # Call the model
            print("\nAssistant: ", end="", flush=True)

            response = client.chat.completions.create(
                model=model_config["name"],
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=model_config.get("max_tokens", 512),
                temperature=model_config.get("temperature", 0.7),
                stream=True,  # Stream the response for better UX
            )

            # Print streaming response
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content

            print("\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
