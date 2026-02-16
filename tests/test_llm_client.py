"""Tests for LLM client and configuration loader."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tpc_reporter.config_loader import Config, ConfigurationError, load_config
from tpc_reporter.llm_client import LLMClient, create_llm_client


class TestConfigLoader:
    """Tests for configuration loading."""

    def test_load_config_from_path(self, temp_config_dir):
        """Test loading configuration from a specific path."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))

        assert config.active_endpoint_name == "test_openai"
        assert "test_openai" in config.list_endpoints()
        assert "test_nim_ssh" in config.list_endpoints()

    def test_get_llm_client_params_openai(self, temp_config_dir):
        """Test getting OpenAI client parameters."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))

        params = config.get_llm_client_params()

        assert params["type"] == "openai"
        assert params["model"] == "test-model"
        assert params["base_url"] == "http://localhost:8080/v1"
        assert params["parameters"]["temperature"] == 0.5

    def test_switch_endpoint(self, temp_config_dir):
        """Test switching between endpoints."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))

        assert config.active_endpoint_name == "test_openai"

        config.switch_endpoint("test_nim_ssh")

        assert config.active_endpoint_name == "test_nim_ssh"
        params = config.get_llm_client_params()
        assert params["type"] == "nim_ssh"
        assert params["ssh_host"] == "test-host"

    def test_invalid_endpoint_raises_error(self, temp_config_dir):
        """Test that invalid endpoint name raises ConfigurationError."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))

        with pytest.raises(ConfigurationError, match="not found in configuration"):
            config.switch_endpoint("nonexistent_endpoint")

    def test_get_app_setting(self, temp_config_dir):
        """Test getting application settings."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))

        assert config.get_app_setting("log_level") == "DEBUG"
        assert config.get_app_setting("nonexistent", "default") == "default"

    def test_missing_config_file_raises_error(self, tmp_path):
        """Test that missing config file raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="not found"):
            load_config(config_path=str(tmp_path / "nonexistent.yaml"))


class TestLLMClient:
    """Tests for LLM client."""

    def test_create_openai_client(self, temp_config_dir):
        """Test creating an OpenAI-type client."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))

        with patch("openai.OpenAI") as mock_openai:
            client = LLMClient(config)

            assert client.endpoint_type == "openai"
            assert client.model == "test-model"
            mock_openai.assert_called_once()

    def test_create_nim_ssh_client(self, temp_config_dir):
        """Test creating a NIM SSH client."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))
        config.switch_endpoint("test_nim_ssh")

        client = LLMClient(config)

        assert client.endpoint_type == "nim_ssh"
        assert client.ssh_host == "test-host"
        assert client.base_url == "http://localhost:8000/v1"

    def test_chat_completion_openai(
        self, temp_config_dir, sample_messages, mock_openai_response
    ):
        """Test chat completion with OpenAI endpoint."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))

        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_openai_response(
                "Hello! I'm doing well."
            )

            client = LLMClient(config)
            response = client.chat_completion(sample_messages)

            assert response == "Hello! I'm doing well."
            mock_client.chat.completions.create.assert_called_once()

    def test_chat_completion_with_overrides(
        self, temp_config_dir, sample_messages, mock_openai_response
    ):
        """Test that kwargs override default parameters."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))

        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_openai_response()

            client = LLMClient(config)
            client.chat_completion(sample_messages, temperature=0.9, max_tokens=500)

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.9
            assert call_kwargs["max_tokens"] == 500

    def test_nim_ssh_completion(self, temp_config_dir, sample_messages):
        """Test NIM SSH completion."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))
        config.switch_endpoint("test_nim_ssh")

        client = LLMClient(config)

        mock_response = {"choices": [{"message": {"content": "SSH response content"}}]}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(mock_response),
                stderr="",
            )

            response = client.chat_completion(sample_messages)

            assert response == "SSH response content"
            mock_run.assert_called_once()

    def test_nim_ssh_timeout_raises_error(self, temp_config_dir, sample_messages):
        """Test that SSH timeout raises RuntimeError."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))
        config.switch_endpoint("test_nim_ssh")

        client = LLMClient(config)

        with patch("subprocess.run") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=120)

            with pytest.raises(RuntimeError, match="timed out"):
                client.chat_completion(sample_messages)

    def test_client_repr(self, temp_config_dir):
        """Test client string representation."""
        config_path = temp_config_dir / "configuration.yaml"
        config = load_config(config_path=str(config_path))

        with patch("openai.OpenAI"):
            client = LLMClient(config)
            repr_str = repr(client)

            assert "test_openai" in repr_str
            assert "openai" in repr_str
            assert "test-model" in repr_str


class TestCreateLLMClient:
    """Tests for the create_llm_client convenience function.

    Note: create_llm_client() auto-detects the project config from the module
    location, so these tests use the real project configuration.
    """

    def test_create_with_default_endpoint(self):
        """Test creating client with default endpoint from project config."""
        # This uses the real project config (nim_spark is the default)
        client = create_llm_client()
        # Just verify it creates successfully with the configured endpoint
        assert client.endpoint_type in ["openai", "nim_ssh"]
        assert client.model is not None

    def test_create_with_endpoint_override(self, monkeypatch):
        """Test creating client with endpoint override using real config."""
        # Switch to openai endpoint (which exists in real config)
        # Set dummy API key since openai endpoint requires it
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-for-testing")
        with patch("openai.OpenAI"):
            client = create_llm_client(endpoint="openai")
            assert client.endpoint_type == "openai"
