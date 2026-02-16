"""
Command-line interface for TPC Workshop Reporter.

Provides commands to assemble data, generate reports, and check for hallucinations.
"""

import json
import sys
from pathlib import Path

import click

from tpc_reporter.assembler import (
    assemble_all_tracks,
    assemble_track_bundle,
    load_lightning_talks_csv,
)
from tpc_reporter.checker import check_report, check_report_from_files
from tpc_reporter.config_loader import load_config
from tpc_reporter.generator import generate_report, generate_report_from_file
from tpc_reporter.llm_client import create_llm_client


@click.group()
@click.version_option(version="0.1.0", prog_name="tpc-reporter")
def main():
    """TPC Workshop Reporter - Generate track reports from conference data."""
    pass


@main.command("fetch-and-assemble")
@click.option(
    "--track",
    default="Track-1",
    help="Track name to filter (e.g., Track-1)",
)
@click.option(
    "-o",
    "--output",
    default="./data/track_bundle.json",
    help="Output path for bundle JSON file",
)
def fetch_and_assemble(track: str, output: str):
    """Fetch data from Google Drive URLs in config and create a track bundle.

    Reads Google Drive URLs from configuration.yaml, downloads the data,
    and assembles it into a track bundle JSON file.
    """
    import tempfile

    from tpc_reporter import gdrive

    click.echo("Loading configuration...")
    config = load_config()
    urls = config.get_google_drive_urls()

    # Validate URLs
    if not all(urls.values()):
        click.echo("Error: Missing Google Drive URLs in configuration.yaml", err=True)
        click.echo("Please ensure all URLs are configured:", err=True)
        click.echo("  - lightning_talks_url", err=True)
        click.echo("  - attendees_url", err=True)
        click.echo("  - notes_url", err=True)
        sys.exit(1)

    click.echo(f"\nFetching data from Google Drive...")

    # Create temp directory for downloads
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Download lightning talks
        click.echo(f"  Downloading lightning talks...")
        talks_path = tmpdir_path / "talks.csv"
        if not gdrive.download_sheet(urls["lightning_talks_url"], str(talks_path)):
            click.echo("Error: Failed to download lightning talks", err=True)
            sys.exit(1)

        # Download attendees
        click.echo(f"  Downloading attendees...")
        attendees_path = tmpdir_path / "attendees.csv"
        if not gdrive.download_sheet(urls["attendees_url"], str(attendees_path)):
            click.echo("Error: Failed to download attendees", err=True)
            sys.exit(1)

        # Download notes
        click.echo(f"  Downloading notes...")
        notes_path = tmpdir_path / "notes.txt"
        if not gdrive.download_doc(urls["notes_url"], str(notes_path)):
            click.echo("Error: Failed to download notes", err=True)
            sys.exit(1)

        # Read downloaded files
        with open(talks_path) as f:
            talks_csv = f.read()
        with open(attendees_path) as f:
            attendees_csv = f.read()
        with open(notes_path) as f:
            notes_text = f.read()

    click.echo("\nParsing data...")

    # Parse lightning talks CSV
    import csv
    import io

    talks_reader = csv.DictReader(io.StringIO(talks_csv))
    all_talks = list(talks_reader)

    # Filter for specified track
    track_talks = [t for t in all_talks if t.get("Track") == track]
    click.echo(f"  Found {len(track_talks)} talks for {track}")

    # Parse attendees CSV
    attendees_reader = csv.DictReader(io.StringIO(attendees_csv))
    attendees_list = list(attendees_reader)

    # Extract unique authors from talks
    authors = set()
    for talk in track_talks:
        author = talk.get("Your full name", "").strip()
        if author:
            authors.add(author)

    # Merge authors with attendees list
    attendees_names = {a.get("Name", "").strip() for a in attendees_list if a.get("Name")}
    all_attendees = sorted(authors | attendees_names)
    click.echo(f"  Found {len(all_attendees)} unique attendees")

    # Create bundle
    click.echo("\nAssembling bundle...")
    bundle = {
        "track": {
            "id": track,
            "name": track.replace("-", " ").title(),
        },
        "sessions": [],
        "lightning_talks": [
            {
                "title": talk.get("Title of your proposed lightning talk", ""),
                "authors": [talk.get("Your full name", "")],
                "abstract": talk.get("Abstract of your proposed lightning talk (80-100 words)", ""),
                "track": talk.get("Track", ""),
            }
            for talk in track_talks
        ],
        "attendees": [{"name": name} for name in all_attendees],
        "notes": notes_text,
    }

    # Write bundle
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(bundle, f, indent=2)

    click.echo(f"\n✓ Bundle written to {output_path}")
    click.echo(f"  Lightning talks: {len(track_talks)}")
    click.echo(f"  Attendees: {len(all_attendees)}")


@main.command()
@click.argument("lightning_talks", type=click.Path(exists=True))
@click.argument("track_inputs", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    default="./data/bundles",
    help="Output directory for bundle files",
)
@click.option(
    "--track",
    "track_id",
    default=None,
    help="Assemble only a specific track (e.g., Track-1)",
)
def assemble(lightning_talks: str, track_inputs: str, output: str, track_id: str):
    """Assemble track bundles from lightning talks CSV and track inputs.

    LIGHTNING_TALKS: Path to the lightning talks CSV file
    TRACK_INPUTS: Directory containing Track-N subdirectories with attendees/notes
    """
    click.echo(f"Loading lightning talks from {lightning_talks}...")

    if track_id:
        # Assemble single track
        talks = load_lightning_talks_csv(lightning_talks)
        track_inputs_dir = Path(track_inputs) / track_id

        result = assemble_track_bundle(
            track_id=track_id,
            track_name=track_id.replace("-", " ").title(),
            lightning_talks=talks,
            track_inputs_dir=(
                str(track_inputs_dir) if track_inputs_dir.exists() else None
            ),
        )

        # Write output
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        bundle_path = output_path / f"{track_id}_bundle.json"

        with open(bundle_path, "w") as f:
            json.dump(result.bundle, f, indent=2)

        click.echo(f"✓ Assembled {track_id} → {bundle_path}")

        if result.has_warnings:
            for warning in result.warnings:
                click.echo(f"  ⚠️  {warning.message}", err=True)
    else:
        # Assemble all tracks
        results = assemble_all_tracks(lightning_talks, track_inputs, output)

        click.echo(f"\nAssembled {len(results)} track bundles:")
        for tid, result in results.items():
            status = "⚠️" if result.has_warnings else "✓"
            click.echo(f"  {status} {tid}")
            for warning in result.warnings:
                click.echo(f"      - {warning.message}", err=True)


@main.command()
@click.argument("bundle", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    default=None,
    help="Output file path (default: stdout)",
)
@click.option(
    "--max-tokens",
    default=8000,
    help="Maximum tokens for generation",
)
@click.option(
    "--temperature",
    default=0.3,
    help="Temperature for generation",
)
@click.option(
    "--endpoint",
    default=None,
    help="LLM endpoint to use (overrides config)",
)
def generate(
    bundle: str,
    output: str | None,
    max_tokens: int,
    temperature: float,
    endpoint: str | None,
):
    """Generate a track report from a bundle file.

    BUNDLE: Path to the track bundle JSON file
    """
    click.echo(f"Generating report from {bundle}...", err=True)

    client = create_llm_client(endpoint=endpoint) if endpoint else None

    report = generate_report_from_file(
        bundle,
        output_path=output,
        client=client,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    if output:
        click.echo(f"✓ Report written to {output}", err=True)
    else:
        click.echo(report)


@main.command()
@click.argument("draft", type=click.Path(exists=True))
@click.argument("bundle", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    default=None,
    help="Output file path (default: stdout)",
)
@click.option(
    "--max-tokens",
    default=10000,
    help="Maximum tokens for checking",
)
@click.option(
    "--endpoint",
    default=None,
    help="LLM endpoint to use (overrides config)",
)
def check(
    draft: str,
    bundle: str,
    output: str | None,
    max_tokens: int,
    endpoint: str | None,
):
    """Check a draft report for hallucinations against source data.

    DRAFT: Path to the draft report markdown file
    BUNDLE: Path to the source bundle JSON file
    """
    click.echo(f"Checking {draft} against {bundle}...", err=True)

    client = create_llm_client(endpoint=endpoint) if endpoint else None

    result = check_report_from_files(
        draft,
        bundle,
        output_path=output,
        client=client,
        max_tokens=max_tokens,
    )

    if output:
        click.echo(f"✓ Checked report written to {output}", err=True)
    else:
        click.echo(result.report)

    # Print summary
    click.echo(f"\n--- Verification Status: {result.status} ---", err=True)
    click.echo(f"Total flags: {result.total_flags}", err=True)

    if result.flags:
        click.echo("\nFlags found:", err=True)
        for i, flag in enumerate(result.flags, 1):
            click.echo(f"  {i}. {flag['type']}: {flag['description']}", err=True)


@main.command()
@click.argument("bundle", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    default=None,
    help="Output file path for final report",
)
@click.option(
    "--draft-output",
    default=None,
    help="Output file path for draft (before checking)",
)
@click.option(
    "--max-tokens",
    default=8000,
    help="Maximum tokens for generation",
)
@click.option(
    "--endpoint",
    default=None,
    help="LLM endpoint to use (overrides config)",
)
@click.option(
    "--skip-check",
    is_flag=True,
    help="Skip hallucination checking",
)
def run(
    bundle: str,
    output: str | None,
    draft_output: str | None,
    max_tokens: int,
    endpoint: str | None,
    skip_check: bool,
):
    """Run the full pipeline: generate report and check for hallucinations.

    BUNDLE: Path to the track bundle JSON file
    """
    client = create_llm_client(endpoint=endpoint) if endpoint else create_llm_client()

    # Load bundle
    with open(bundle) as f:
        bundle_data = json.load(f)

    track_name = bundle_data.get("track", {}).get("name", "Unknown")
    click.echo(f"Processing track: {track_name}", err=True)

    # Step 1: Generate
    click.echo("Step 1: Generating draft report...", err=True)
    draft = generate_report(bundle_data, client=client, max_tokens=max_tokens)

    if draft_output:
        Path(draft_output).parent.mkdir(parents=True, exist_ok=True)
        with open(draft_output, "w") as f:
            f.write(draft)
        click.echo(f"  ✓ Draft saved to {draft_output}", err=True)

    if skip_check:
        # Output draft as final
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w") as f:
                f.write(draft)
            click.echo(f"✓ Report written to {output}", err=True)
        else:
            click.echo(draft)
        return

    # Step 2: Check
    click.echo("Step 2: Checking for hallucinations...", err=True)
    result = check_report(draft, bundle_data, client=client, max_tokens=10000)

    click.echo(f"  Verification status: {result.status}", err=True)
    click.echo(f"  Flags found: {result.total_flags}", err=True)

    # Output final report
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            f.write(result.report)
        click.echo(f"✓ Checked report written to {output}", err=True)
    else:
        click.echo(result.report)

    # Print warnings if any
    if result.flags:
        click.echo("\nFlags found:", err=True)
        for i, flag in enumerate(result.flags, 1):
            click.echo(f"  {i}. {flag['type']}: {flag['description']}", err=True)


@main.command("generate-all")
@click.argument("bundles_dir", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    default="./output",
    help="Output directory for reports",
)
@click.option(
    "--endpoint",
    default=None,
    help="LLM endpoint to use (overrides config)",
)
@click.option(
    "--skip-check",
    is_flag=True,
    help="Skip hallucination checking",
)
def generate_all(
    bundles_dir: str,
    output: str,
    endpoint: str | None,
    skip_check: bool,
):
    """Generate reports for all track bundles in a directory.

    BUNDLES_DIR: Directory containing track bundle JSON files
    """
    bundles_path = Path(bundles_dir)
    bundle_files = sorted(bundles_path.glob("*_bundle.json"))

    if not bundle_files:
        click.echo(f"No bundle files found in {bundles_dir}", err=True)
        sys.exit(1)

    click.echo(f"Found {len(bundle_files)} bundle files")

    client = create_llm_client(endpoint=endpoint) if endpoint else create_llm_client()
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    for bundle_file in bundle_files:
        track_id = bundle_file.stem.replace("_bundle", "")
        click.echo(f"\nProcessing {track_id}...")

        with open(bundle_file) as f:
            bundle_data = json.load(f)

        # Generate
        draft = generate_report(bundle_data, client=client)

        if skip_check:
            report_path = output_path / f"{track_id}_report.md"
            with open(report_path, "w") as f:
                f.write(draft)
            click.echo(f"  ✓ {report_path}")
        else:
            # Check
            result = check_report(draft, bundle_data, client=client)
            report_path = output_path / f"{track_id}_report.md"
            with open(report_path, "w") as f:
                f.write(result.report)

            status_icon = "✓" if result.passed else "⚠️"
            click.echo(f"  {status_icon} {report_path} ({result.status})")

    click.echo(f"\n✓ All reports written to {output}")


if __name__ == "__main__":
    main()
