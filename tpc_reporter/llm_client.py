from __future__ import annotations

"""
LLM client wrapper for Workshop-Reporter.

Provides a unified interface for different LLM endpoints (OpenAI, NIM, etc.)
based on configuration.yaml settings.
"""

import json
import subprocess
from typing import Any

from tpc_reporter.config_loader import Config, load_config


class LLMClient:
    """Unified LLM client that works with multiple endpoints."""

    def __init__(self, config: Config | None = None):
        """
        Initialize LLM client.

        Args:
            config: Config object. If None, loads from configuration.yaml
        """
        self.config = config or load_config()
        self.client_params = self.config.get_llm_client_params()
        self.endpoint_type = self.client_params["type"]

        # Initialize appropriate client
        if self.endpoint_type == "openai":
            self._init_openai_client()
        elif self.endpoint_type == "nim_ssh":
            self._init_nim_ssh_client()
        else:
            raise ValueError(f"Unsupported endpoint type: {self.endpoint_type}")

    def _init_openai_client(self):
        """Initialize OpenAI-compatible client."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")

        self.client = OpenAI(
            base_url=self.client_params.get("base_url"),
            api_key=self.client_params.get("api_key", "dummy"),
        )

    def _init_nim_ssh_client(self):
        """Initialize NIM SSH client (uses SSH wrapper)."""
        self.ssh_host = self.client_params["ssh_host"]
        self.base_url = self.client_params["base_url"]
        # No actual client needed - we use SSH wrapper

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> str:
        """
        Generate chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Override parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response
        """
        # Merge config parameters with kwargs
        params = self.client_params.get("parameters", {}).copy()
        params.update(kwargs)

        if self.endpoint_type == "openai":
            return self._openai_completion(messages, params)
        elif self.endpoint_type == "nim_ssh":
            return self._nim_ssh_completion(messages, params)
        else:
            raise ValueError(f"Unsupported endpoint type: {self.endpoint_type}")

    def _openai_completion(
        self,
        messages: list[dict[str, str]],
        params: dict[str, Any],
    ) -> str:
        """OpenAI-compatible completion."""
        response = self.client.chat.completions.create(
            model=self.client_params["model"],
            messages=messages,
            temperature=params.get("temperature", 0.3),
            max_tokens=params.get("max_tokens", 4000),
            top_p=params.get("top_p", 1.0),
        )
        return response.choices[0].message.content

    def _nim_ssh_completion(
        self,
        messages: list[dict[str, str]],
        params: dict[str, Any],
    ) -> str:
        """NIM completion via SSH wrapper."""
        # Build curl command payload
        payload = {
            "model": self.client_params["model"],
            "messages": messages,
            "temperature": params.get("temperature", 0.3),
            "max_tokens": params.get("max_tokens", 4000),
            "top_p": params.get("top_p", 1.0),
        }

        payload_json = json.dumps(payload)

        # Use stdin to pass JSON payload - avoids shell escaping issues
        curl_cmd = (
            f"curl -s {self.base_url}/chat/completions "
            f"-H 'Content-Type: application/json' "
            f"--data-binary @-"
        )

        ssh_cmd = f'ssh {self.ssh_host} "{curl_cmd}"'

        try:
            result = subprocess.run(
                ssh_cmd,
                input=payload_json,
                capture_output=True,
                text=True,
                timeout=120,
                shell=True,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"SSH command failed with code {result.returncode}: {result.stderr}"
                )

            # Parse JSON response
            response = json.loads(result.stdout)

            if "error" in response:
                raise RuntimeError(f"LLM error: {response['error']}")

            # Debug: Check response structure
            if "choices" not in response:
                raise RuntimeError(
                    f"Unexpected NIM response format. Keys: {list(response.keys())}\n"
                    f"Full response: {json.dumps(response, indent=2)[:500]}"
                )

            return response["choices"][0]["message"]["content"]

        except subprocess.TimeoutExpired:
            raise RuntimeError("LLM request timed out after 120 seconds")
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to parse LLM response: {e}\nOutput: {result.stdout}"
            )

    @property
    def model(self) -> str:
        """Get the model name."""
        return self.client_params["model"]

    def __repr__(self):
        return (
            f"LLMClient(endpoint='{self.config.active_endpoint_name}', "
            f"type='{self.endpoint_type}', "
            f"model='{self.client_params['model']}')"
        )


def create_llm_client(endpoint: str | None = None) -> LLMClient:
    """
    Create LLM client with optional endpoint override.

    Args:
        endpoint: Endpoint name to use (overrides configuration.yaml)

    Returns:
        LLMClient instance
    """
    config = load_config()
    if endpoint:
        config.switch_endpoint(endpoint)
    return LLMClient(config)
