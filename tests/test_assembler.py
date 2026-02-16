"""Tests for data assembler."""

import json

import pytest

from tpc_reporter.assembler import (
    AssemblyResult,
    AssemblyWarning,
    assemble_all_tracks,
    assemble_track_bundle,
    load_attendees_csv,
    load_lightning_talks_csv,
    load_notes_file,
)


@pytest.fixture
def sample_lightning_talks_csv(tmp_path):
    """Create a sample lightning talks CSV file."""
    csv_content = """ID,Status,Speaker,Institution,Email,Title,Abstract,Track
1,Accepted,Alice Smith,University of Chicago,alice@uchicago.edu,Federated Learning for Science,Abstract about federated learning,Track-1
2,Accepted,Bob Jones,Argonne National Lab,bob@anl.gov,Agent-Based Workflows,Abstract about agents,Track-1
3,Accepted,Carol White,Stanford University,carol@stanford.edu,Climate Modeling,Abstract about climate,Track-2
4,Accepted,David Brown,MIT,david@mit.edu,Quantum Computing,Abstract about quantum,Track-2
"""
    csv_path = tmp_path / "lightning_talks.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_track_inputs(tmp_path):
    """Create sample track input directories."""
    # Track-1 directory
    track1_dir = tmp_path / "Track-1"
    track1_dir.mkdir()

    # Attendees CSV
    attendees_csv = """Name,Organization
Alice Smith,University of Chicago
Eve Green,NOAA
Frank Black,NASA
"""
    (track1_dir / "attendees.csv").write_text(attendees_csv)

    # Notes file
    notes = """Session discussion focused on federated learning approaches.
Key points:
1. Data privacy is critical
2. Need for standardized protocols
3. Performance benchmarks needed
"""
    (track1_dir / "Track-1-notes.txt").write_text(notes)

    # Track-2 directory (no attendees, no notes - to test warnings)
    track2_dir = tmp_path / "Track-2"
    track2_dir.mkdir()

    return tmp_path


class TestLoadLightningTalksCsv:
    """Tests for loading lightning talks CSV."""

    def test_load_talks_basic(self, sample_lightning_talks_csv):
        """Test loading talks from CSV."""
        talks = load_lightning_talks_csv(str(sample_lightning_talks_csv))

        assert len(talks) == 4
        assert talks[0]["title"] == "Federated Learning for Science"
        assert talks[0]["authors"][0]["name"] == "Alice Smith"
        assert talks[0]["authors"][0]["affiliation"] == "University of Chicago"
        assert talks[0]["track"] == "Track-1"

    def test_load_talks_filters_by_position(self, sample_lightning_talks_csv):
        """Test that talks are loaded by column position."""
        talks = load_lightning_talks_csv(str(sample_lightning_talks_csv))

        # Track-1 should have 2 talks
        track1_talks = [t for t in talks if t["track"] == "Track-1"]
        assert len(track1_talks) == 2

        # Track-2 should have 2 talks
        track2_talks = [t for t in talks if t["track"] == "Track-2"]
        assert len(track2_talks) == 2

    def test_load_talks_missing_file(self):
        """Test error on missing file."""
        with pytest.raises(FileNotFoundError):
            load_lightning_talks_csv("/nonexistent/path.csv")


class TestLoadAttendeesCsv:
    """Tests for loading attendees CSV."""

    def test_load_attendees_basic(self, sample_track_inputs):
        """Test loading attendees from CSV."""
        attendees_path = sample_track_inputs / "Track-1" / "attendees.csv"
        attendees = load_attendees_csv(str(attendees_path))

        assert len(attendees) == 3
        assert attendees[0]["name"] == "Alice Smith"
        assert attendees[0]["organization"] == "University of Chicago"

    def test_load_attendees_missing_file(self, tmp_path):
        """Test that missing file returns empty list."""
        attendees = load_attendees_csv(str(tmp_path / "nonexistent.csv"))
        assert attendees == []

    def test_load_attendees_different_headers(self, tmp_path):
        """Test loading with alternative header names."""
        csv_content = """Full Name,Institution
John Doe,Example Corp
"""
        csv_path = tmp_path / "attendees.csv"
        csv_path.write_text(csv_content)

        attendees = load_attendees_csv(str(csv_path))
        assert len(attendees) == 1
        assert attendees[0]["name"] == "John Doe"
        assert attendees[0]["organization"] == "Example Corp"


class TestLoadNotesFile:
    """Tests for loading notes files."""

    def test_load_notes_basic(self, sample_track_inputs):
        """Test loading notes from file."""
        notes_path = sample_track_inputs / "Track-1" / "Track-1-notes.txt"
        notes = load_notes_file(str(notes_path))

        assert notes is not None
        assert "federated learning" in notes
        assert "Data privacy" in notes

    def test_load_notes_missing_file(self, tmp_path):
        """Test that missing file returns None."""
        notes = load_notes_file(str(tmp_path / "nonexistent.txt"))
        assert notes is None


class TestAssembleTrackBundle:
    """Tests for assembling track bundles."""

    def test_assemble_basic_bundle(
        self, sample_lightning_talks_csv, sample_track_inputs
    ):
        """Test assembling a complete track bundle."""
        talks = load_lightning_talks_csv(str(sample_lightning_talks_csv))
        track_inputs_dir = sample_track_inputs / "Track-1"

        result = assemble_track_bundle(
            track_id="Track-1",
            track_name="Data Workflows",
            lightning_talks=talks,
            track_inputs_dir=str(track_inputs_dir),
        )

        assert isinstance(result, AssemblyResult)
        assert result.bundle["track"]["id"] == "Track-1"
        assert result.bundle["track"]["name"] == "Data Workflows"

        # Check sessions
        assert len(result.bundle["sessions"]) == 1
        session = result.bundle["sessions"][0]

        # Should have 2 lightning talks for Track-1
        assert len(session["lightning_talks"]) == 2

        # Should have attendees (3 from CSV + Bob Jones from talks)
        assert len(session["attendees"]) >= 3

        # Should have notes
        assert session["notes"] is not None
        assert "federated learning" in session["notes"]

    def test_assemble_adds_speakers_to_attendees(
        self, sample_lightning_talks_csv, sample_track_inputs
    ):
        """Test that lightning talk speakers are added to attendees."""
        talks = load_lightning_talks_csv(str(sample_lightning_talks_csv))
        track_inputs_dir = sample_track_inputs / "Track-1"

        result = assemble_track_bundle(
            track_id="Track-1",
            track_name="Data Workflows",
            lightning_talks=talks,
            track_inputs_dir=str(track_inputs_dir),
        )

        attendee_names = [
            a["name"].lower() for a in result.bundle["sessions"][0]["attendees"]
        ]

        # Alice Smith is in both CSV and talks - should appear once
        assert attendee_names.count("alice smith") == 1

        # Bob Jones is only in talks - should be added
        assert "bob jones" in attendee_names

    def test_assemble_warns_on_missing_inputs(
        self, sample_lightning_talks_csv, sample_track_inputs
    ):
        """Test that warnings are generated for missing inputs."""
        talks = load_lightning_talks_csv(str(sample_lightning_talks_csv))
        track_inputs_dir = sample_track_inputs / "Track-2"  # Has no attendees/notes

        result = assemble_track_bundle(
            track_id="Track-2",
            track_name="Climate Science",
            lightning_talks=talks,
            track_inputs_dir=str(track_inputs_dir),
        )

        assert result.has_warnings
        warning_messages = [w.message for w in result.warnings]

        # Should warn about missing attendees and notes
        assert any("attendees" in m.lower() for m in warning_messages)
        assert any("notes" in m.lower() for m in warning_messages)

    def test_assemble_no_track_inputs_dir(self, sample_lightning_talks_csv):
        """Test assembly without track inputs directory."""
        talks = load_lightning_talks_csv(str(sample_lightning_talks_csv))

        result = assemble_track_bundle(
            track_id="Track-1",
            track_name="Data Workflows",
            lightning_talks=talks,
            track_inputs_dir=None,
        )

        # Should still create bundle with talks
        assert len(result.bundle["sessions"][0]["lightning_talks"]) == 2

        # Attendees should only include speakers
        attendees = result.bundle["sessions"][0]["attendees"]
        assert len(attendees) == 2  # Alice and Bob from talks

    def test_assemble_warns_on_no_talks(self, sample_track_inputs):
        """Test warning when no talks found for track."""
        result = assemble_track_bundle(
            track_id="Track-99",
            track_name="Nonexistent Track",
            lightning_talks=[],  # Empty talks
        )

        assert result.has_warnings
        assert any("No lightning talks" in w.message for w in result.warnings)


class TestAssemblyResult:
    """Tests for AssemblyResult dataclass."""

    def test_has_warnings(self):
        """Test has_warnings property."""
        result_clean = AssemblyResult(bundle={}, warnings=[])
        assert not result_clean.has_warnings

        result_warn = AssemblyResult(
            bundle={},
            warnings=[
                AssemblyWarning(
                    track_id="T1", session_id=None, message="test", severity="warning"
                )
            ],
        )
        assert result_warn.has_warnings

    def test_has_errors(self):
        """Test has_errors property."""
        result_warn = AssemblyResult(
            bundle={},
            warnings=[
                AssemblyWarning(
                    track_id="T1", session_id=None, message="test", severity="warning"
                )
            ],
        )
        assert not result_warn.has_errors

        result_error = AssemblyResult(
            bundle={},
            warnings=[
                AssemblyWarning(
                    track_id="T1", session_id=None, message="test", severity="error"
                )
            ],
        )
        assert result_error.has_errors


class TestAssembleAllTracks:
    """Tests for assembling all tracks at once."""

    def test_assemble_all_tracks(
        self, sample_lightning_talks_csv, sample_track_inputs, tmp_path
    ):
        """Test assembling all tracks from CSV."""
        output_dir = tmp_path / "output"

        results = assemble_all_tracks(
            str(sample_lightning_talks_csv),
            str(sample_track_inputs),
            str(output_dir),
        )

        # Should have 2 tracks
        assert len(results) == 2
        assert "Track-1" in results
        assert "Track-2" in results

        # Check output files created
        assert (output_dir / "Track-1_bundle.json").exists()
        assert (output_dir / "Track-2_bundle.json").exists()

        # Verify Track-1 bundle content
        with open(output_dir / "Track-1_bundle.json") as f:
            bundle = json.load(f)
        assert bundle["track"]["id"] == "Track-1"
        assert len(bundle["sessions"][0]["lightning_talks"]) == 2

    def test_assemble_all_with_custom_mapping(
        self, sample_lightning_talks_csv, sample_track_inputs, tmp_path
    ):
        """Test assembly with custom track name mapping."""
        output_dir = tmp_path / "output"

        track_mapping = {
            "Track-1": "Data Workflows and Agents",
            "Track-2": "Climate and Earth Science",
        }

        results = assemble_all_tracks(
            str(sample_lightning_talks_csv),
            str(sample_track_inputs),
            str(output_dir),
            track_mapping=track_mapping,
        )

        assert results["Track-1"].bundle["track"]["name"] == "Data Workflows and Agents"
        assert results["Track-2"].bundle["track"]["name"] == "Climate and Earth Science"
