"""Tests for CLI module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from tpc_reporter.cli import main


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_bundle(tmp_path):
    """Create a sample bundle file."""
    bundle = {
        "track": {"id": "Track-1", "name": "Test Track", "room": "Room A"},
        "sessions": [
            {
                "id": "session-1",
                "title": "Test Session",
                "lightning_talks": [
                    {
                        "title": "Test Talk",
                        "authors": [{"name": "Alice", "affiliation": "Test U"}],
                        "abstract": "Test abstract",
                    }
                ],
                "attendees": [{"name": "Alice", "organization": "Test U"}],
                "notes": "Test notes",
            }
        ],
        "sources": ["test"],
    }
    bundle_path = tmp_path / "test_bundle.json"
    with open(bundle_path, "w") as f:
        json.dump(bundle, f)
    return bundle_path


@pytest.fixture
def sample_lightning_talks_csv(tmp_path):
    """Create a sample lightning talks CSV."""
    csv_content = """ID,Status,Speaker,Institution,Email,Title,Abstract,Track
1,Accepted,Alice,Test U,alice@test.edu,Test Talk,Abstract,Track-1
"""
    csv_path = tmp_path / "talks.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_track_inputs(tmp_path):
    """Create sample track inputs directory."""
    track_dir = tmp_path / "Track-1"
    track_dir.mkdir()
    (track_dir / "attendees.csv").write_text("Name,Organization\nAlice,Test U\n")
    (track_dir / "Track-1-notes.txt").write_text("Test notes")
    return tmp_path


class TestMainGroup:
    """Tests for the main CLI group."""

    def test_version(self, runner):
        """Test --version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self, runner):
        """Test --help flag."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "TPC Workshop Reporter" in result.output
        assert "assemble" in result.output
        assert "generate" in result.output
        assert "check" in result.output
        assert "run" in result.output


class TestAssembleCommand:
    """Tests for the assemble command."""

    def test_assemble_all_tracks(
        self, runner, sample_lightning_talks_csv, sample_track_inputs, tmp_path
    ):
        """Test assembling all tracks."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            main,
            [
                "assemble",
                str(sample_lightning_talks_csv),
                str(sample_track_inputs),
                "-o",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Assembled" in result.output
        assert (output_dir / "Track-1_bundle.json").exists()

    def test_assemble_single_track(
        self, runner, sample_lightning_talks_csv, sample_track_inputs, tmp_path
    ):
        """Test assembling a single track."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            main,
            [
                "assemble",
                str(sample_lightning_talks_csv),
                str(sample_track_inputs),
                "-o",
                str(output_dir),
                "--track",
                "Track-1",
            ],
        )

        assert result.exit_code == 0
        assert "Track-1" in result.output
        assert (output_dir / "Track-1_bundle.json").exists()

    def test_assemble_missing_file(self, runner, tmp_path):
        """Test error on missing input file."""
        result = runner.invoke(
            main,
            [
                "assemble",
                str(tmp_path / "nonexistent.csv"),
                str(tmp_path),
            ],
        )

        assert result.exit_code != 0


class TestGenerateCommand:
    """Tests for the generate command."""

    def test_generate_to_stdout(self, runner, sample_bundle):
        """Test generating report to stdout."""
        with patch("tpc_reporter.cli.generate_report_from_file") as mock_gen:
            mock_gen.return_value = "# Test Report"

            result = runner.invoke(main, ["generate", str(sample_bundle)])

            assert result.exit_code == 0
            assert "# Test Report" in result.output

    def test_generate_to_file(self, runner, sample_bundle, tmp_path):
        """Test generating report to file."""
        output_file = tmp_path / "report.md"

        with patch("tpc_reporter.cli.generate_report_from_file") as mock_gen:
            mock_gen.return_value = "# Test Report"

            result = runner.invoke(
                main,
                ["generate", str(sample_bundle), "-o", str(output_file)],
            )

            assert result.exit_code == 0
            assert "Report written to" in result.output

    def test_generate_with_options(self, runner, sample_bundle):
        """Test generate with custom options."""
        with patch("tpc_reporter.cli.generate_report_from_file") as mock_gen:
            mock_gen.return_value = "# Report"

            result = runner.invoke(
                main,
                [
                    "generate",
                    str(sample_bundle),
                    "--max-tokens",
                    "5000",
                    "--temperature",
                    "0.5",
                ],
            )

            assert result.exit_code == 0
            # Verify options were passed
            call_kwargs = mock_gen.call_args[1]
            assert call_kwargs["max_tokens"] == 5000
            assert call_kwargs["temperature"] == 0.5


class TestCheckCommand:
    """Tests for the check command."""

    def test_check_report(self, runner, sample_bundle, tmp_path):
        """Test checking a report."""
        # Create a draft file
        draft_path = tmp_path / "draft.md"
        draft_path.write_text("# Draft Report")

        mock_result = MagicMock()
        mock_result.report = "# Checked Report"
        mock_result.status = "PASS"
        mock_result.total_flags = 0
        mock_result.flags = []

        with patch("tpc_reporter.cli.check_report_from_files") as mock_check:
            mock_check.return_value = mock_result

            result = runner.invoke(
                main,
                ["check", str(draft_path), str(sample_bundle)],
            )

            assert result.exit_code == 0
            assert "Verification Status: PASS" in result.output

    def test_check_with_flags(self, runner, sample_bundle, tmp_path):
        """Test checking a report that has flags."""
        draft_path = tmp_path / "draft.md"
        draft_path.write_text("# Draft")

        mock_result = MagicMock()
        mock_result.report = "# Checked"
        mock_result.status = "REVIEW NEEDED"
        mock_result.total_flags = 2
        mock_result.flags = [
            {"type": "Unknown person", "description": "John"},
            {"type": "Unsupported claim", "description": "50%"},
        ]

        with patch("tpc_reporter.cli.check_report_from_files") as mock_check:
            mock_check.return_value = mock_result

            result = runner.invoke(
                main,
                ["check", str(draft_path), str(sample_bundle)],
            )

            assert result.exit_code == 0
            assert "REVIEW NEEDED" in result.output
            assert "Total flags: 2" in result.output
            assert "Unknown person" in result.output


class TestRunCommand:
    """Tests for the run command (full pipeline)."""

    def test_run_full_pipeline(self, runner, sample_bundle, tmp_path):
        """Test running the full pipeline."""
        output_file = tmp_path / "output" / "report.md"

        mock_result = MagicMock()
        mock_result.report = "# Final Report"
        mock_result.status = "PASS"
        mock_result.total_flags = 0
        mock_result.flags = []

        with patch("tpc_reporter.cli.create_llm_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client

            with patch("tpc_reporter.cli.generate_report") as mock_gen:
                mock_gen.return_value = "# Draft"

                with patch("tpc_reporter.cli.check_report") as mock_check:
                    mock_check.return_value = mock_result

                    result = runner.invoke(
                        main,
                        ["run", str(sample_bundle), "-o", str(output_file)],
                    )

                    assert result.exit_code == 0
                    assert "Generating draft" in result.output
                    assert "Checking for hallucinations" in result.output
                    assert "PASS" in result.output

    def test_run_skip_check(self, runner, sample_bundle, tmp_path):
        """Test running with --skip-check flag."""
        output_file = tmp_path / "report.md"

        with patch("tpc_reporter.cli.create_llm_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client

            with patch("tpc_reporter.cli.generate_report") as mock_gen:
                mock_gen.return_value = "# Draft Report"

                result = runner.invoke(
                    main,
                    [
                        "run",
                        str(sample_bundle),
                        "-o",
                        str(output_file),
                        "--skip-check",
                    ],
                )

                assert result.exit_code == 0
                assert output_file.exists()
                # Check should not have been called
                assert "Checking for hallucinations" not in result.output


class TestGenerateAllCommand:
    """Tests for the generate-all command."""

    def test_generate_all(self, runner, tmp_path):
        """Test generating all reports."""
        # Create bundles directory
        bundles_dir = tmp_path / "bundles"
        bundles_dir.mkdir()

        # Create bundle files
        for i in range(2):
            bundle = {
                "track": {"id": f"Track-{i+1}", "name": f"Track {i+1}"},
                "sessions": [],
            }
            with open(bundles_dir / f"Track-{i+1}_bundle.json", "w") as f:
                json.dump(bundle, f)

        output_dir = tmp_path / "output"

        mock_result = MagicMock()
        mock_result.report = "# Report"
        mock_result.passed = True
        mock_result.status = "PASS"

        with patch("tpc_reporter.cli.create_llm_client"):
            with patch("tpc_reporter.cli.generate_report") as mock_gen:
                mock_gen.return_value = "# Draft"

                with patch("tpc_reporter.cli.check_report") as mock_check:
                    mock_check.return_value = mock_result

                    result = runner.invoke(
                        main,
                        [
                            "generate-all",
                            str(bundles_dir),
                            "-o",
                            str(output_dir),
                        ],
                    )

                    assert result.exit_code == 0
                    assert "Found 2 bundle files" in result.output
                    assert "All reports written" in result.output

    def test_generate_all_no_bundles(self, runner, tmp_path):
        """Test error when no bundles found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(main, ["generate-all", str(empty_dir)])

        assert result.exit_code != 0
        assert "No bundle files found" in result.output
