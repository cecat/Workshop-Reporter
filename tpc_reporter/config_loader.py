from __future__ import annotations

"""
Configuration and secrets loader for Workshop-Reporter.

Loads configuration.yaml and secrets.yaml, merging them appropriately.
"""

import os
from pathlib import Path
from typing import Any


class ConfigurationError(Exception):
    """Raised when there's an issue with configuration."""

    pass


def _find_project_root() -> Path:
    """Find the project root by looking for configuration.yaml."""
    # Start from this file's location and search upward
    current = Path(__file__).parent
    for _ in range(5):  # Don't search too far up
        if (current / "configuration.yaml").exists():
            return current
        current = current.parent

    # Fall back to current working directory
    cwd = Path.cwd()
    if (cwd / "configuration.yaml").exists():
        return cwd

    raise ConfigurationError(
        "Could not find configuration.yaml. "
        "Ensure you're running from the project directory."
    )


class Config:
    """Configuration manager for Workshop-Reporter."""

    def __init__(
        self,
        config_path: str | None = None,
        secrets_path: str | None = None,
    ):
        """
        Initialize configuration.

        Args:
            config_path: Path to configuration.yaml (default: project root)
            secrets_path: Path to secrets.yaml (default: project root)
        """
        if config_path is None:
            project_root = _find_project_root()
            config_path = project_root / "configuration.yaml"
            secrets_path = secrets_path or project_root / "secrets.yaml"

        self.config_path = Path(config_path)
        self.secrets_path = Path(secrets_path) if secrets_path else None

        # Load configuration
        self.config = self._load_yaml(self.config_path)

        # Load secrets (optional)
        self.secrets = {}
        if self.secrets_path and self.secrets_path.exists():
            self.secrets = self._load_yaml(self.secrets_path)

        # Get active endpoint configuration
        self.active_endpoint_name = self.config.get("active_endpoint")
        if not self.active_endpoint_name:
            raise ConfigurationError(
                "No active_endpoint specified in configuration.yaml"
            )

        self.active_endpoint = self._get_endpoint_config(self.active_endpoint_name)

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load YAML file."""
        import yaml

        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")

        with open(path) as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Error parsing {path}: {e}")

    def _get_endpoint_config(self, endpoint_name: str) -> dict[str, Any]:
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

    def get_llm_client_params(self) -> dict[str, Any]:
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
    config_path: str | None = None,
    secrets_path: str | None = None,
) -> Config:
    """
    Load configuration and secrets.

    Args:
        config_path: Path to configuration.yaml (default: auto-detect)
        secrets_path: Path to secrets.yaml (default: auto-detect)

    Returns:
        Config object
    """
    return Config(config_path, secrets_path)
