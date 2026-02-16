"""
Data assembler for TPC Workshop Reporter.

Merges conference structure (from website/sheets) with track inputs
(attendees, notes) to create track bundles for report generation.
"""

import csv
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AssemblyWarning:
    """Warning generated during assembly."""

    track_id: str
    session_id: str | None
    message: str
    severity: str = "warning"  # "warning" or "error"


@dataclass
class AssemblyResult:
    """Result of assembling a track bundle."""

    bundle: dict[str, Any]
    warnings: list[AssemblyWarning] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    @property
    def has_errors(self) -> bool:
        return any(w.severity == "error" for w in self.warnings)


def load_conference_data(conference_path: str) -> dict[str, Any]:
    """
    Load conference structure from JSON file.

    Args:
        conference_path: Path to conference.json

    Returns:
        Conference data dictionary
    """
    path = Path(conference_path)
    if not path.exists():
        raise FileNotFoundError(f"Conference file not found: {path}")

    with open(path) as f:
        return json.load(f)


def load_lightning_talks_csv(csv_path: str) -> list[dict[str, Any]]:
    """
    Load lightning talks from CSV file.

    Expected columns (by position or header):
    - Speaker name (column C / index 2)
    - Institution (column D / index 3)
    - Title (column F / index 5)
    - Abstract (column G / index 6)
    - Track assignment (column H / index 7) - e.g., "Track-1"

    Args:
        csv_path: Path to lightning talks CSV

    Returns:
        List of lightning talk dictionaries
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Lightning talks CSV not found: {path}")

    talks = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header row

        for row in reader:
            if len(row) < 8:
                continue  # Skip incomplete rows

            # Extract by position (0-indexed)
            speaker = row[2].strip() if len(row) > 2 else ""
            institution = row[3].strip() if len(row) > 3 else ""
            title = row[5].strip() if len(row) > 5 else ""
            abstract = row[6].strip() if len(row) > 6 else ""
            track = row[7].strip() if len(row) > 7 else ""

            if not title:
                continue  # Skip rows without title

            talks.append(
                {
                    "title": title,
                    "authors": [{"name": speaker, "affiliation": institution}],
                    "abstract": abstract,
                    "track": track,
                }
            )

    return talks


def load_attendees_csv(csv_path: str) -> list[dict[str, str]]:
    """
    Load attendees from CSV file.

    Expected format: Name, Organization columns (or similar headers).

    Args:
        csv_path: Path to attendees CSV

    Returns:
        List of attendee dictionaries with 'name' and 'organization' keys
    """
    path = Path(csv_path)
    if not path.exists():
        return []  # Missing attendees is not an error

    attendees = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Try common header variations
            name = (
                row.get("Name")
                or row.get("name")
                or row.get("Full Name")
                or row.get("Attendee")
                or ""
            )
            org = (
                row.get("Organization")
                or row.get("organization")
                or row.get("Institution")
                or row.get("Affiliation")
                or ""
            )

            if name.strip():
                attendees.append({"name": name.strip(), "organization": org.strip()})

    return attendees


def load_notes_file(notes_path: str) -> str | None:
    """
    Load session notes from a text file.

    Args:
        notes_path: Path to notes file (txt or md)

    Returns:
        Notes content as string, or None if not found
    """
    path = Path(notes_path)
    if not path.exists():
        return None

    with open(path, encoding="utf-8") as f:
        return f.read()


def assemble_track_bundle(
    track_id: str,
    track_name: str,
    lightning_talks: list[dict[str, Any]],
    track_inputs_dir: str | None = None,
    room: str | None = None,
    sessions: list[dict[str, Any]] | None = None,
) -> AssemblyResult:
    """
    Assemble a track bundle from various data sources.

    Args:
        track_id: Track identifier (e.g., "Track-1")
        track_name: Human-readable track name
        lightning_talks: List of all lightning talks (will be filtered by track)
        track_inputs_dir: Directory containing attendees.csv and notes files
        room: Room assignment for the track
        sessions: Pre-defined session structure (optional)

    Returns:
        AssemblyResult with bundle and any warnings
    """
    warnings = []

    # Filter lightning talks for this track
    track_talks = [t for t in lightning_talks if t.get("track") == track_id]

    if not track_talks:
        warnings.append(
            AssemblyWarning(
                track_id=track_id,
                session_id=None,
                message=f"No lightning talks found for track {track_id}",
                severity="warning",
            )
        )

    # Load attendees if track_inputs_dir provided
    attendees = []
    notes = None

    if track_inputs_dir:
        inputs_path = Path(track_inputs_dir)

        # Try to find attendees file
        attendees_candidates = [
            inputs_path / "attendees.csv",
            inputs_path / "Attendees.csv",
            inputs_path / f"{track_id}_attendees.csv",
        ]
        for candidate in attendees_candidates:
            if candidate.exists():
                attendees = load_attendees_csv(str(candidate))
                break

        if not attendees:
            warnings.append(
                AssemblyWarning(
                    track_id=track_id,
                    session_id=None,
                    message=f"No attendees file found in {track_inputs_dir}",
                    severity="warning",
                )
            )

        # Try to find notes file
        notes_candidates = [
            inputs_path / f"{track_id}-notes.txt",
            inputs_path / f"{track_id}_notes.txt",
            inputs_path / "notes.txt",
            inputs_path / f"{track_id}-notes.md",
            inputs_path / "notes.md",
        ]
        for candidate in notes_candidates:
            if candidate.exists():
                notes = load_notes_file(str(candidate))
                break

        if not notes:
            warnings.append(
                AssemblyWarning(
                    track_id=track_id,
                    session_id=None,
                    message=f"No notes file found in {track_inputs_dir}",
                    severity="warning",
                )
            )

    # Add lightning talk speakers to attendees if not already present
    attendee_names = {a["name"].lower() for a in attendees}
    for talk in track_talks:
        for author in talk.get("authors", []):
            author_name = author.get("name", "")
            if author_name and author_name.lower() not in attendee_names:
                attendees.append(
                    {
                        "name": author_name,
                        "organization": author.get("affiliation", ""),
                    }
                )
                attendee_names.add(author_name.lower())

    # Build session(s) - if no pre-defined sessions, create a single session
    if sessions:
        assembled_sessions = sessions
    else:
        # Create a single session containing all talks
        assembled_sessions = [
            {
                "id": f"{track_id}-session-1",
                "title": f"{track_name} Session",
                "slot": None,
                "leaders": [],
                "lightning_talks": track_talks,
                "attendees": attendees,
                "notes": notes,
            }
        ]

    # Build sources list
    sources = []
    if track_inputs_dir:
        sources.append(f"Track inputs: {track_inputs_dir}")

    bundle = {
        "track": {
            "id": track_id,
            "name": track_name,
            "room": room,
        },
        "sessions": assembled_sessions,
        "sources": sources,
    }

    return AssemblyResult(bundle=bundle, warnings=warnings)


def assemble_all_tracks(
    lightning_talks_path: str,
    track_inputs_base_dir: str,
    output_dir: str,
    track_mapping: dict[str, str] | None = None,
) -> dict[str, AssemblyResult]:
    """
    Assemble bundles for all tracks.

    Args:
        lightning_talks_path: Path to lightning talks CSV
        track_inputs_base_dir: Base directory containing Track-N subdirectories
        output_dir: Directory to write track bundle JSON files
        track_mapping: Optional mapping of track_id to track_name

    Returns:
        Dictionary mapping track_id to AssemblyResult
    """
    # Load all lightning talks
    all_talks = load_lightning_talks_csv(lightning_talks_path)

    # Discover tracks from lightning talks
    tracks = set(t.get("track") for t in all_talks if t.get("track"))

    # Default track mapping if not provided
    if track_mapping is None:
        track_mapping = {t: t.replace("-", " ").title() for t in tracks}

    results = {}
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for track_id in sorted(tracks):
        track_name = track_mapping.get(track_id, track_id)
        track_inputs_dir = Path(track_inputs_base_dir) / track_id

        result = assemble_track_bundle(
            track_id=track_id,
            track_name=track_name,
            lightning_talks=all_talks,
            track_inputs_dir=(
                str(track_inputs_dir) if track_inputs_dir.exists() else None
            ),
        )

        # Write bundle to file
        bundle_path = output_path / f"{track_id}_bundle.json"
        with open(bundle_path, "w") as f:
            json.dump(result.bundle, f, indent=2)

        result.bundle["_output_path"] = str(bundle_path)
        results[track_id] = result

        # Log warnings
        for warning in result.warnings:
            logger.warning(f"[{track_id}] {warning.message}")

    return results


# CLI entry point
def main():
    """CLI entry point for assembler."""
    import argparse

    parser = argparse.ArgumentParser(description="Assemble track bundles from data")
    parser.add_argument("lightning_talks", help="Path to lightning talks CSV file")
    parser.add_argument(
        "track_inputs", help="Base directory containing Track-N subdirectories"
    )
    parser.add_argument(
        "-o", "--output", default="./data/bundles", help="Output directory"
    )

    args = parser.parse_args()

    results = assemble_all_tracks(
        args.lightning_talks,
        args.track_inputs,
        args.output,
    )

    print(f"\nAssembled {len(results)} track bundles:")
    for track_id, result in results.items():
        status = "⚠️" if result.has_warnings else "✓"
        print(f"  {status} {track_id}: {result.bundle['_output_path']}")
        for warning in result.warnings:
            print(f"      - {warning.message}")


if __name__ == "__main__":
    main()
