"""
Configuration and secrets loader for Workshop-Reporter.

Loads configuration.yaml and secrets.yaml, merging them appropriately.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigurationError(Exception):
    """Raised when there's an issue with configuration."""

    pass


class Config:
    """Configuration manager for Workshop-Reporter."""

    def __init__(
        self,
        config_path: str = "configuration.yaml",
        secrets_path: str = "secrets.yaml",
    ):
        """
        Initialize configuration.

        Args:
            config_path: Path to configuration.yaml
            secrets_path: Path to secrets.yaml
        """
        self.config_path = Path(config_path)
        self.secrets_path = Path(secrets_path)

        # Load configuration
        self.config = self._load_yaml(self.config_path)

        # Load secrets (optional)
        self.secrets = {}
        if self.secrets_path.exists():
            self.secrets = self._load_yaml(self.secrets_path)

        # Get active endpoint configuration
        self.active_endpoint_name = self.config.get("active_endpoint")
        if not self.active_endpoint_name:
            raise ConfigurationError(
                "No active_endpoint specified in configuration.yaml"
            )

        self.active_endpoint = self._get_endpoint_config(self.active_endpoint_name)

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file."""
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")

        with open(path, "r") as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Error parsing {path}: {e}")

    def _get_endpoint_config(self, endpoint_name: str) -> Dict[str, Any]:
        """Get configuration for a specific endpoint."""
        endpoints = self.config.get("endpoints", {})
        if endpoint_name not in endpoints:
            raise ConfigurationError(
                f"Endpoint '{endpoint_name}' not found in configuration. "
                f"Available: {list(endpoints.keys())}"
            )

        endpoint = endpoints[endpoint_name].copy()

        # Load API key from secrets if specified
        api_key_env = endpoint.get("api_key_env")
        if api_key_env:
            # Try secrets file first, then environment variable
            api_key = self.secrets.get(api_key_env) or os.getenv(api_key_env)
            if not api_key:
                raise ConfigurationError(
                    f"API key '{api_key_env}' not found in secrets.yaml or environment. "
                    f"Please add it to secrets.yaml or set environment variable."
                )
            endpoint["api_key"] = api_key

        return endpoint

    def get_llm_client_params(self) -> Dict[str, Any]:
        """
        Get parameters for initializing LLM client.

        Returns:
            Dictionary with client initialization parameters
        """
        endpoint = self.active_endpoint
        endpoint_type = endpoint.get("type")

        params = {
            "type": endpoint_type,
            "model": endpoint.get("model"),
            "parameters": endpoint.get("parameters", {}),
        }

        if endpoint_type == "openai":
            params["base_url"] = endpoint.get("base_url")
            params["api_key"] = endpoint.get("api_key", "dummy")

        elif endpoint_type == "nim_ssh":
            params["ssh_host"] = endpoint.get("ssh_host")
            params["base_url"] = endpoint.get("base_url")

        return params

    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """Get application setting."""
        return self.config.get("app", {}).get(key, default)

    def list_endpoints(self) -> list:
        """List all available endpoints."""
        return list(self.config.get("endpoints", {}).keys())

    def switch_endpoint(self, endpoint_name: str):
        """
        Switch to a different endpoint.

        Args:
            endpoint_name: Name of endpoint to switch to
        """
        self.active_endpoint_name = endpoint_name
        self.active_endpoint = self._get_endpoint_config(endpoint_name)

    def __repr__(self):
        return (
            f"Config(active_endpoint='{self.active_endpoint_name}', "
            f"endpoints={self.list_endpoints()})"
        )


def load_config(
    config_path: str = "configuration.yaml", secrets_path: str = "secrets.yaml"
) -> Config:
    """
    Load configuration and secrets.

    Args:
        config_path: Path to configuration.yaml
        secrets_path: Path to secrets.yaml

    Returns:
        Config object
    """
    return Config(config_path, secrets_path)


# Example usage
if __name__ == "__main__":
    # Load configuration
    config = load_config()

    print(f"Active endpoint: {config.active_endpoint_name}")
    print(f"Available endpoints: {config.list_endpoints()}")
    print("\nLLM client parameters:")

    params = config.get_llm_client_params()
    for key, value in params.items():
        if key != "api_key":  # Don't print API keys
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {'*' * 10}")
