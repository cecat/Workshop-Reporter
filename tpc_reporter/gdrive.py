"""
Google Drive collector for TPC Workshop Reporter.

Downloads Google Sheets and Docs from shared folders using public export URLs.
No API authentication required for publicly shared files.
"""

import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Export URL templates
SHEET_EXPORT_URL = "https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"
DOC_EXPORT_URL = "https://docs.google.com/document/d/{file_id}/export?format=txt"
DRIVE_FILE_URL = "https://drive.google.com/uc?export=download&id={file_id}"


@dataclass
class DriveFile:
    """Represents a Google Drive file."""

    file_id: str
    name: str
    file_type: str  # "sheet", "doc", or "file"
    url: str

    @property
    def export_url(self) -> str:
        """Get the export URL for this file."""
        if self.file_type == "sheet":
            return SHEET_EXPORT_URL.format(file_id=self.file_id)
        elif self.file_type == "doc":
            return DOC_EXPORT_URL.format(file_id=self.file_id)
        else:
            return DRIVE_FILE_URL.format(file_id=self.file_id)


def extract_file_id(url: str) -> str | None:
    """
    Extract Google Drive file ID from various URL formats.

    Supports:
    - https://docs.google.com/spreadsheets/d/{id}/...
    - https://docs.google.com/document/d/{id}/...
    - https://drive.google.com/file/d/{id}/...
    - https://drive.google.com/open?id={id}

    Args:
        url: Google Drive URL

    Returns:
        File ID or None if not found
    """
    # Pattern for /d/{id}/ format
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)

    # Pattern for ?id={id} format
    match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)

    return None


def detect_file_type(url: str) -> str:
    """
    Detect the file type from a Google Drive URL.

    Args:
        url: Google Drive URL

    Returns:
        "sheet", "doc", or "file"
    """
    if "spreadsheets" in url:
        return "sheet"
    elif "document" in url:
        return "doc"
    else:
        return "file"


def download_file(
    url: str,
    output_path: str,
    timeout: int = 30,
    retries: int = 3,
) -> bool:
    """
    Download a file from Google Drive.

    Args:
        url: URL to download from (export URL or direct URL)
        output_path: Path to save the file
        timeout: Request timeout in seconds
        retries: Number of retry attempts

    Returns:
        True if successful, False otherwise
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()

            # Check for Google's "too many requests" page
            if "Too many requests" in response.text[:1000]:
                logger.warning(f"Rate limited, waiting before retry {attempt + 1}")
                time.sleep(5 * (attempt + 1))
                continue

            # Check for HTML error pages
            if response.text.startswith("<!DOCTYPE html>"):
                if "not found" in response.text.lower():
                    logger.error(f"File not found: {url}")
                    return False

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            logger.info(f"Downloaded: {output_path}")
            return True

        except requests.RequestException as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
            continue

    logger.error(f"Failed to download after {retries} attempts: {url}")
    return False


def download_sheet(
    url_or_id: str,
    output_path: str,
    sheet_gid: str | None = None,
) -> bool:
    """
    Download a Google Sheet as CSV.

    Args:
        url_or_id: Google Sheets URL or file ID
        output_path: Path to save the CSV file
        sheet_gid: Optional sheet GID for multi-sheet documents

    Returns:
        True if successful, False otherwise
    """
    # Extract file ID if URL provided
    if url_or_id.startswith("http"):
        file_id = extract_file_id(url_or_id)
        if not file_id:
            logger.error(f"Could not extract file ID from: {url_or_id}")
            return False
    else:
        file_id = url_or_id

    export_url = SHEET_EXPORT_URL.format(file_id=file_id)
    if sheet_gid:
        export_url += f"&gid={sheet_gid}"

    return download_file(export_url, output_path)


def download_doc(url_or_id: str, output_path: str) -> bool:
    """
    Download a Google Doc as plain text.

    Args:
        url_or_id: Google Docs URL or file ID
        output_path: Path to save the text file

    Returns:
        True if successful, False otherwise
    """
    # Extract file ID if URL provided
    if url_or_id.startswith("http"):
        file_id = extract_file_id(url_or_id)
        if not file_id:
            logger.error(f"Could not extract file ID from: {url_or_id}")
            return False
    else:
        file_id = url_or_id

    export_url = DOC_EXPORT_URL.format(file_id=file_id)
    return download_file(export_url, output_path)


@dataclass
class CollectionConfig:
    """Configuration for collecting data from Google Drive."""

    lightning_talks_url: str
    track_folders: dict  # {track_id: {"attendees_url": ..., "notes_url": ...}}
    output_dir: str


def collect_track_data(
    track_id: str,
    attendees_url: str | None,
    notes_url: str | None,
    output_dir: str,
) -> dict:
    """
    Collect data for a single track.

    Args:
        track_id: Track identifier (e.g., "Track-1")
        attendees_url: URL to attendees Google Sheet (optional)
        notes_url: URL to notes Google Doc (optional)
        output_dir: Base output directory

    Returns:
        Dictionary with paths to downloaded files and any errors
    """
    result = {
        "track_id": track_id,
        "attendees_path": None,
        "notes_path": None,
        "errors": [],
    }

    track_dir = Path(output_dir) / track_id
    track_dir.mkdir(parents=True, exist_ok=True)

    # Download attendees
    if attendees_url:
        attendees_path = track_dir / "attendees.csv"
        if download_sheet(attendees_url, str(attendees_path)):
            result["attendees_path"] = str(attendees_path)
        else:
            result["errors"].append(f"Failed to download attendees: {attendees_url}")

    # Download notes
    if notes_url:
        notes_path = track_dir / f"{track_id}-notes.txt"
        if download_doc(notes_url, str(notes_path)):
            result["notes_path"] = str(notes_path)
        else:
            result["errors"].append(f"Failed to download notes: {notes_url}")

    return result


def collect_all_data(
    lightning_talks_url: str,
    track_configs: dict,
    output_dir: str,
) -> dict:
    """
    Collect all data from Google Drive.

    Args:
        lightning_talks_url: URL to the master lightning talks sheet
        track_configs: Dict mapping track_id to {"attendees_url": ..., "notes_url": ...}
        output_dir: Base output directory

    Returns:
        Dictionary with results for each track and the lightning talks
    """
    results = {
        "lightning_talks_path": None,
        "tracks": {},
        "errors": [],
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Download lightning talks
    talks_path = output_path / "lightning_talks.csv"
    if download_sheet(lightning_talks_url, str(talks_path)):
        results["lightning_talks_path"] = str(talks_path)
    else:
        results["errors"].append(
            f"Failed to download lightning talks: {lightning_talks_url}"
        )

    # Download each track's data
    for track_id, config in track_configs.items():
        track_result = collect_track_data(
            track_id=track_id,
            attendees_url=config.get("attendees_url"),
            notes_url=config.get("notes_url"),
            output_dir=output_dir,
        )
        results["tracks"][track_id] = track_result
        results["errors"].extend(track_result["errors"])

    return results


# CLI entry point
def main():
    """CLI entry point for Google Drive collector."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Download data from Google Drive for TPC reports"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to JSON config file with URLs",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="./data/track_inputs",
        help="Output directory",
    )

    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = json.load(f)

    # Collect data
    results = collect_all_data(
        lightning_talks_url=config["lightning_talks_url"],
        track_configs=config.get("tracks", {}),
        output_dir=args.output,
    )

    # Print results
    print(f"\n{'='*50}")
    print("Collection Results")
    print(f"{'='*50}")

    if results["lightning_talks_path"]:
        print(f"✓ Lightning talks: {results['lightning_talks_path']}")
    else:
        print("✗ Lightning talks: FAILED")

    for track_id, track_result in results["tracks"].items():
        print(f"\n{track_id}:")
        if track_result["attendees_path"]:
            print(f"  ✓ Attendees: {track_result['attendees_path']}")
        if track_result["notes_path"]:
            print(f"  ✓ Notes: {track_result['notes_path']}")
        for error in track_result["errors"]:
            print(f"  ✗ {error}")

    if results["errors"]:
        print(f"\n{len(results['errors'])} errors occurred")
        return 1

    print("\n✓ Collection complete!")
    return 0


if __name__ == "__main__":
    exit(main())
