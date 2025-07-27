#!/usr/bin/env python3
"""
Simple chat script to demonstrate LLM API calls.
This script reads configuration from files and sends a prompt to OpenAI's API.

Usage:
    python chat.py

Requirements:
    pip install openai pyyaml
"""

import yaml
import sys
from pathlib import Path
from openai import OpenAI

def load_secrets():
    """Load API keys from secrets.yml"""
    try:
        with open('secrets.yml', 'r') as f:
            secrets = yaml.safe_load(f)

        # Try different possible formats
        if 'openai' in secrets and 'api_key' in secrets['openai']:
            return secrets['openai']['api_key']
        elif 'openai_api_key' in secrets:
            return secrets['openai_api_key']
        else:
            raise KeyError("API key not found")

    except FileNotFoundError:
        print("Error: secrets.yml file not found!")
        print("Please create secrets.yml and add your OpenAI API key.")
        sys.exit(1)
    except KeyError:
        print("Error: API key not found in secrets.yml")
        print("Expected format:")
        print("  openai:")
        print("    api_key: your-key-here")
        print("OR:")
        print("  openai_api_key: your-key-here")
        sys.exit(1)

def load_config():
    """Load configuration from config.py"""
    try:
        from config import OPENAI_CONFIG
        return OPENAI_CONFIG
    except ImportError:
        print("Error: config.py file not found!")
        sys.exit(1)

def load_prompt():
    """Load prompt from prompt.yml"""
    try:
        with open('prompt.yml', 'r') as f:
            prompt_data = yaml.safe_load(f)
        return prompt_data['prompt']
    except FileNotFoundError:
        print("Error: prompt.yml file not found!")
        sys.exit(1)
    except KeyError:
        print("Error: prompt not found in prompt.yml")
        sys.exit(1)

def call_llm(client, config, prompt):
    """Send prompt to LLM and return response"""
    try:
        response = client.chat.completions.create(
            model=config['model'],
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=config['temperature'],
            max_tokens=config['max_tokens'],
            timeout=config['timeout']
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None

def main():
    """Main function"""
    print("🤖 Simple LLM Chat Example")
    print("=" * 40)
    
    # Load configuration files
    print("Loading configuration...")
    api_key = load_secrets()
    config = load_config()
    prompt = load_prompt()
    
    # Initialize OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url=config['base_url']
    )
    
    print(f"Using model: {config['model']}")
    print(f"Prompt: {prompt}")
    print("\nSending request to LLM...")
    print("-" * 40)
    
    # Call LLM
    response = call_llm(client, config, prompt)
    
    if response:
        print("🤖 LLM Response:")
        print(response)
    else:
        print("❌ Failed to get response from LLM")
    
    print("-" * 40)
    print("Done!")

if __name__ == "__main__":
    main()
