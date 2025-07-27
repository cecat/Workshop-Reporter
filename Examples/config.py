"""
Configuration settings for LLM API calls
"""

# OpenAI API Configuration
OPENAI_CONFIG = {
    "model": "gpt-4o-mini",  # Options: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
    "base_url": "https://api.openai.com/v1",  # Standard OpenAI endpoint
    "temperature": 0.7,  # Controls randomness (0.0 = deterministic, 1.0 = very random)
    "max_tokens": 1000,  # Maximum tokens in response
    "timeout": 30  # Request timeout in seconds
}

# Alternative models you might want to try:
# "gpt-4o" - Most capable but more expensive
# "gpt-4o-mini" - Good balance of capability and cost (recommended for development)
# "gpt-3.5-turbo" - Faster and cheaper, but less capable

# You can also use other providers like:
# - Anthropic Claude (requires different API)
# - Local models via Ollama
# - Azure OpenAI (requires different base_url)
