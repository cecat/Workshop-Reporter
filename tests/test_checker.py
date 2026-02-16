"""Tests for hallucination checker."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tpc_reporter.checker import (
    VerificationResult,
    check_report,
    check_report_from_files,
    extract_flags,
    load_checker_prompt,
    parse_verification_summary,
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


@pytest.fixture
def clean_report():
    """A report with no hallucinations."""
    return """# Data Workflows and Agents: Track Report

## Executive Summary
The track focused on agent-based systems for scientific computing.

## Session Reports

### DWARF: Keynote and Systems Software for Agents
**Time:** 2025-07-30T09:00
**Leaders:** Ian Foster (Argonne National Laboratory)

#### Lightning Talks
- Academy: Empowering Scientific Workflows with Federated Agents by Kyle Chard

#### Discussion and Outcomes
The group discussed standardized interfaces between agents.

---
## Verification Summary

**Total flags:** 0
**Verification status:** PASS
---
"""


@pytest.fixture
def flagged_report():
    """A report with hallucination flags."""
    return """# Data Workflows and Agents: Track Report

## Executive Summary
The track focused on agent-based systems, led by John Smith [FLAG: Unknown person "John Smith"].

## Session Reports

### DWARF: Keynote
**Time:** 2025-07-30T09:00

#### Lightning Talks
- Quantum Computing for Agents [FLAG: Unverified talk "Quantum Computing for Agents"]
- Academy: Empowering Scientific Workflows by Kyle Chard

#### Discussion
The group achieved 50% efficiency improvement [FLAG: Unsupported claim "50% efficiency improvement"].

---
## Verification Summary

**Total flags:** 3
**Flag breakdown:**
- Unknown persons: 1
- Unknown organizations: 0
- Unverified talks: 1
- Unsupported claims: 1
- Other issues: 0

**Flagged items:**
1. Unknown person: John Smith
2. Unverified talk: Quantum Computing for Agents
3. Unsupported claim: 50% efficiency improvement

**Verification status:** REVIEW NEEDED
---
"""


class TestLoadCheckerPrompt:
    """Tests for prompt loading."""

    def test_load_default_checker_prompt(self):
        """Test loading the default checker prompt."""
        prompt = load_checker_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "fact-checker" in prompt.lower()
        assert "FLAG" in prompt

    def test_load_prompt_missing_file(self):
        """Test that missing prompt file raises error."""
        with pytest.raises(FileNotFoundError):
            load_checker_prompt("nonexistent_prompt.yaml")


class TestExtractFlags:
    """Tests for flag extraction."""

    def test_extract_flags_with_quotes(self):
        """Test extracting flags with quoted descriptions."""
        text = 'Some text [FLAG: Unknown person "John Smith"] more text.'
        flags = extract_flags(text)
        assert len(flags) == 1
        assert flags[0]["type"] == "Unknown person"
        assert flags[0]["description"] == "John Smith"

    def test_extract_multiple_flags(self):
        """Test extracting multiple flags."""
        text = """
        [FLAG: Unknown person "Alice"]
        [FLAG: Unverified talk "Some Talk"]
        [FLAG: Unsupported claim "50% improvement"]
        """
        flags = extract_flags(text)
        assert len(flags) == 3
        assert flags[0]["type"] == "Unknown person"
        assert flags[1]["type"] == "Unverified talk"
        assert flags[2]["type"] == "Unsupported claim"

    def test_extract_no_flags(self):
        """Test extraction from text without flags."""
        text = "This is a clean report with no issues."
        flags = extract_flags(text)
        assert len(flags) == 0

    def test_extract_flags_from_flagged_report(self, flagged_report):
        """Test extracting flags from a realistic report."""
        flags = extract_flags(flagged_report)
        assert len(flags) == 3


class TestParseVerificationSummary:
    """Tests for parsing verification summary."""

    def test_parse_clean_summary(self, clean_report):
        """Test parsing a clean verification summary."""
        summary = parse_verification_summary(clean_report)
        assert summary["total_flags"] == 0
        assert summary["status"] == "PASS"

    def test_parse_flagged_summary(self, flagged_report):
        """Test parsing a summary with flags."""
        summary = parse_verification_summary(flagged_report)
        assert summary["total_flags"] == 3
        assert summary["status"] == "REVIEW NEEDED"
        assert summary["breakdown"]["unknown_persons"] == 1
        assert summary["breakdown"]["unverified_talks"] == 1
        assert summary["breakdown"]["unsupported_claims"] == 1

    def test_parse_missing_summary(self):
        """Test parsing text without a summary section."""
        text = "Just some report text without a summary."
        summary = parse_verification_summary(text)
        assert summary["total_flags"] == 0
        assert summary["status"] == "UNKNOWN"


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_passed_property(self):
        """Test the passed property."""
        result = VerificationResult(report="", total_flags=0, status="PASS")
        assert result.passed is True

        result2 = VerificationResult(report="", total_flags=1, status="REVIEW NEEDED")
        assert result2.passed is False

    def test_needs_review_property(self):
        """Test the needs_review property."""
        result = VerificationResult(report="", total_flags=3, status="REVIEW NEEDED")
        assert result.needs_review is True
        assert result.has_major_issues is False

    def test_has_major_issues_property(self):
        """Test the has_major_issues property."""
        result = VerificationResult(report="", total_flags=10, status="MAJOR ISSUES")
        assert result.has_major_issues is True
        assert result.needs_review is False


class TestCheckReport:
    """Tests for report checking."""

    def test_check_report_calls_llm(self, sample_bundle, clean_report):
        """Test that check_report calls the LLM client."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = clean_report

        result = check_report("# Draft Report", sample_bundle, client=mock_client)

        assert isinstance(result, VerificationResult)
        mock_client.chat_completion.assert_called_once()

    def test_check_report_includes_source_data(self, sample_bundle, clean_report):
        """Test that source data is included in the prompt."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = clean_report

        check_report("# Draft", sample_bundle, client=mock_client)

        call_args = mock_client.chat_completion.call_args
        messages = call_args[0][0]
        user_content = messages[1]["content"]

        # Source data should be included
        assert "Data Workflows and Agents" in user_content
        assert "Ian Foster" in user_content
        # Draft should be included
        assert "# Draft" in user_content

    def test_check_report_parses_flags(self, sample_bundle, flagged_report):
        """Test that flags are extracted from the response."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = flagged_report

        result = check_report("# Draft", sample_bundle, client=mock_client)

        assert result.total_flags == 3
        assert result.status == "REVIEW NEEDED"
        assert len(result.flags) == 3

    def test_check_report_clean_pass(self, sample_bundle, clean_report):
        """Test that clean reports pass verification."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = clean_report

        result = check_report("# Draft", sample_bundle, client=mock_client)

        assert result.passed is True
        assert result.status == "PASS"


class TestCheckReportFromFiles:
    """Tests for file-based report checking."""

    def test_check_from_files(self, sample_bundle_path, tmp_path, clean_report):
        """Test checking from files."""
        # Create a draft file
        draft_path = tmp_path / "draft.md"
        draft_path.write_text("# Draft Report\n\nSome content.")

        mock_client = MagicMock()
        mock_client.chat_completion.return_value = clean_report

        result = check_report_from_files(
            str(draft_path),
            str(sample_bundle_path),
            client=mock_client,
        )

        assert isinstance(result, VerificationResult)

    def test_check_from_files_with_output(
        self, sample_bundle_path, tmp_path, clean_report
    ):
        """Test checking and writing output."""
        draft_path = tmp_path / "draft.md"
        draft_path.write_text("# Draft")

        output_path = tmp_path / "output" / "checked.md"

        mock_client = MagicMock()
        mock_client.chat_completion.return_value = clean_report

        check_report_from_files(
            str(draft_path),
            str(sample_bundle_path),
            output_path=str(output_path),
            client=mock_client,
        )

        assert output_path.exists()
        assert output_path.read_text() == clean_report

    def test_check_from_files_missing_draft(self, sample_bundle_path):
        """Test error when draft file is missing."""
        mock_client = MagicMock()

        with pytest.raises(FileNotFoundError, match="Draft report not found"):
            check_report_from_files(
                "/nonexistent/draft.md",
                str(sample_bundle_path),
                client=mock_client,
            )

    def test_check_from_files_missing_bundle(self, tmp_path):
        """Test error when bundle file is missing."""
        draft_path = tmp_path / "draft.md"
        draft_path.write_text("# Draft")

        mock_client = MagicMock()

        with pytest.raises(FileNotFoundError, match="Bundle file not found"):
            check_report_from_files(
                str(draft_path),
                "/nonexistent/bundle.json",
                client=mock_client,
            )
