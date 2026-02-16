"""Tests for report generator."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tpc_reporter.generator import (
    format_track_bundle,
    generate_report,
    generate_report_from_file,
    load_prompt,
)


@pytest.fixture
def sample_bundle_path():
    """Path to the sample track bundle fixture."""
    return Path(__file__).parent / "fixtures" / "sample_track_bundle.json"


@pytest.fixture
def sample_bundle(sample_bundle_path):
    """Load the sample track bundle."""
    with open(sample_bundle_path) as f:
        return json.load(f)


class TestLoadPrompt:
    """Tests for prompt loading."""

    def test_load_default_prompt(self):
        """Test loading the default prompt."""
        prompt = load_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert "ANTI-HALLUCINATION" in prompt  # Key section exists

    def test_load_prompt_missing_file(self):
        """Test that missing prompt file raises error."""
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent_prompt.yaml")


class TestFormatTrackBundle:
    """Tests for bundle formatting."""

    def test_format_basic_bundle(self, sample_bundle):
        """Test formatting a complete bundle."""
        formatted = format_track_bundle(sample_bundle)

        # Check track info
        assert "# Track: Data Workflows and Agents" in formatted
        assert "Room: Main Plenary" in formatted

        # Check sessions
        assert "## Session: DWARF: Keynote and Systems Software for Agents" in formatted
        assert "## Session: DWARF: Agent Frameworks and Applications" in formatted

        # Check leaders
        assert "Ian Foster" in formatted
        assert "Argonne National Laboratory" in formatted

        # Check lightning talks
        assert "Academy: Empowering Scientific Workflows" in formatted
        assert "Kyle Chard" in formatted

        # Check attendees
        assert "Alice Johnson" in formatted
        assert "University of Chicago" in formatted

        # Check notes
        assert "standardized interfaces between agents" in formatted

        # Check sources
        assert "https://tpc26.org/sessions/" in formatted

    def test_format_empty_bundle(self):
        """Test formatting an empty bundle."""
        formatted = format_track_bundle({})
        assert "# Track: Unknown" in formatted

    def test_format_bundle_with_string_leaders(self):
        """Test formatting bundle with leaders as strings (not dicts)."""
        bundle = {
            "track": {"name": "Test Track"},
            "sessions": [
                {
                    "title": "Test Session",
                    "leaders": ["Alice Smith (Test Org)", "Bob Jones (Other Org)"],
                }
            ],
        }
        formatted = format_track_bundle(bundle)
        assert "Alice Smith (Test Org)" in formatted
        assert "Bob Jones (Other Org)" in formatted

    def test_format_bundle_with_string_attendees(self):
        """Test formatting bundle with attendees as strings."""
        bundle = {
            "track": {"name": "Test Track"},
            "sessions": [
                {
                    "title": "Test Session",
                    "attendees": ["Alice Smith", "Bob Jones"],
                }
            ],
        }
        formatted = format_track_bundle(bundle)
        assert "- Alice Smith" in formatted
        assert "- Bob Jones" in formatted

    def test_format_bundle_missing_optional_fields(self):
        """Test formatting bundle with missing optional fields."""
        bundle = {
            "track": {"id": "test", "name": "Minimal Track"},
            "sessions": [
                {
                    "id": "s1",
                    "title": "Minimal Session",
                    # No leaders, talks, attendees, or notes
                }
            ],
        }
        formatted = format_track_bundle(bundle)
        assert "# Track: Minimal Track" in formatted
        assert "## Session: Minimal Session" in formatted
        # Should not crash on missing fields


class TestGenerateReport:
    """Tests for report generation."""

    def test_generate_report_calls_llm(self, sample_bundle):
        """Test that generate_report calls the LLM client."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = "# Generated Report\n\nContent here."

        report = generate_report(sample_bundle, client=mock_client)

        assert report == "# Generated Report\n\nContent here."
        mock_client.chat_completion.assert_called_once()

        # Check that the call included the bundle data
        call_args = mock_client.chat_completion.call_args
        messages = call_args[0][0]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Data Workflows and Agents" in messages[1]["content"]

    def test_generate_report_uses_prompt(self, sample_bundle):
        """Test that generate_report uses the loaded prompt."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = "Report"

        generate_report(sample_bundle, client=mock_client)

        call_args = mock_client.chat_completion.call_args
        messages = call_args[0][0]
        system_prompt = messages[0]["content"]

        # Should contain key prompt elements
        assert "ANTI-HALLUCINATION" in system_prompt
        assert "track report" in system_prompt.lower()

    def test_generate_report_passes_parameters(self, sample_bundle):
        """Test that parameters are passed to the LLM."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = "Report"

        generate_report(
            sample_bundle,
            client=mock_client,
            max_tokens=5000,
            temperature=0.5,
        )

        call_kwargs = mock_client.chat_completion.call_args[1]
        assert call_kwargs["max_tokens"] == 5000
        assert call_kwargs["temperature"] == 0.5


class TestGenerateReportFromFile:
    """Tests for file-based report generation."""

    def test_generate_from_file(self, sample_bundle_path):
        """Test generating from a file."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = "# Report from file"

        report = generate_report_from_file(
            str(sample_bundle_path),
            client=mock_client,
        )

        assert report == "# Report from file"

    def test_generate_from_file_with_output(self, sample_bundle_path, tmp_path):
        """Test generating from file and writing output."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = "# Report content"

        output_path = tmp_path / "output" / "report.md"

        generate_report_from_file(
            str(sample_bundle_path),
            output_path=str(output_path),
            client=mock_client,
        )

        assert output_path.exists()
        assert output_path.read_text() == "# Report content"

    def test_generate_from_file_not_found(self):
        """Test error handling for missing bundle file."""
        mock_client = MagicMock()

        with pytest.raises(FileNotFoundError):
            generate_report_from_file(
                "/nonexistent/path/bundle.json",
                client=mock_client,
            )
