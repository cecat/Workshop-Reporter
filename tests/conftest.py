"""Pytest fixtures for TPC Workshop Reporter tests."""

import pytest
import yaml


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory with test configuration files."""
    # Create test configuration
    config = {
        "active_endpoint": "test_openai",
        "endpoints": {
            "test_openai": {
                "type": "openai",
                "base_url": "http://localhost:8080/v1",
                "model": "test-model",
                "api_key_env": None,  # No API key required for tests
                "parameters": {
                    "temperature": 0.5,
                    "max_tokens": 1000,
                    "top_p": 0.9,
                },
            },
            "test_nim_ssh": {
                "type": "nim_ssh",
                "ssh_host": "test-host",
                "base_url": "http://localhost:8000/v1",
                "model": "test-nim-model",
                "api_key_env": None,
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 2000,
                },
            },
        },
        "app": {
            "data_dir": "./data",
            "output_dir": "./output",
            "log_level": "DEBUG",
        },
    }

    config_path = tmp_path / "configuration.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return tmp_path


@pytest.fixture
def mock_openai_response():
    """Mock response structure from OpenAI API."""

    class MockChoice:
        def __init__(self, content):
            self.message = type("Message", (), {"content": content})()

    class MockResponse:
        def __init__(self, content="Test response"):
            self.choices = [MockChoice(content)]

    return MockResponse


@pytest.fixture
def sample_messages():
    """Sample chat messages for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
    ]


@pytest.fixture
def sample_track_bundle():
    """Sample track bundle data for testing report generation."""
    return {
        "track": {"id": "track-1", "name": "Test Track"},
        "sessions": [
            {
                "id": "session-1",
                "title": "Test Session: Introduction to Testing",
                "slot": "2025-07-30T09:00",
                "leaders": ["Alice Smith (Test University)"],
                "lightning_talks": [
                    {
                        "title": "Unit Testing Best Practices",
                        "authors": [{"name": "Bob Jones", "affiliation": "Test Labs"}],
                        "abstract": "This talk covers best practices for unit testing.",
                    }
                ],
                "attendees": ["Alice Smith", "Bob Jones", "Carol White"],
                "notes": "Discussion focused on testing methodologies and CI/CD integration.",
            }
        ],
        "sources": ["test_data/conference.json", "test_data/track_inputs/"],
    }
