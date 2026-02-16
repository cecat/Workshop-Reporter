"""
Report generator for TPC Workshop Reporter.

Takes a track bundle (assembled data) and generates a markdown report using an LLM.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from tpc_reporter.llm_client import LLMClient, create_llm_client


def _find_prompts_dir() -> Path:
    """Find the prompts directory."""
    # Start from this file's location and search upward
    current = Path(__file__).parent
    for _ in range(5):
        prompts_dir = current / "prompts"
        if prompts_dir.exists():
            return prompts_dir
        current = current.parent

    # Fall back to current working directory
    cwd = Path.cwd()
    if (cwd / "prompts").exists():
        return cwd / "prompts"

    raise FileNotFoundError(
        "Could not find prompts directory. "
        "Ensure you're running from the project directory."
    )


def load_prompt(prompt_name: str = "tpc_master_prompt_v2.yaml") -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        prompt_name: Name of the prompt file (with .yaml extension)

    Returns:
        The master_prompt string from the YAML file
    """
    prompts_dir = _find_prompts_dir()
    prompt_path = prompts_dir / prompt_name

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r") as f:
        prompt_data = yaml.safe_load(f)

    if "master_prompt" not in prompt_data:
        raise ValueError(f"Prompt file {prompt_name} missing 'master_prompt' key")

    return prompt_data["master_prompt"]


def format_track_bundle(bundle: Dict[str, Any]) -> str:
    """
    Format a track bundle as a string for the LLM prompt.

    Args:
        bundle: Track bundle dictionary with track info, sessions, etc.

    Returns:
        Formatted string representation of the bundle
    """
    lines = []

    # Track info
    track = bundle.get("track", {})
    lines.append(f"# Track: {track.get('name', 'Unknown')}")
    if track.get("room"):
        lines.append(f"Room: {track['room']}")
    lines.append("")

    # Sessions
    sessions = bundle.get("sessions", [])
    for session in sessions:
        lines.append(f"## Session: {session.get('title', 'Untitled')}")
        lines.append(f"Time: {session.get('slot', 'Not specified')}")

        # Leaders
        leaders = session.get("leaders", [])
        if leaders:
            if isinstance(leaders[0], dict):
                leader_strs = [
                    f"{leader.get('name', 'Unknown')} ({leader.get('affiliation', '')})"
                    for leader in leaders
                ]
            else:
                leader_strs = leaders
            lines.append(f"Leaders: {', '.join(leader_strs)}")
        lines.append("")

        # Lightning talks
        talks = session.get("lightning_talks", [])
        if talks:
            lines.append("### Lightning Talks")
            for talk in talks:
                if isinstance(talk, dict):
                    lines.append(f"**{talk.get('title', 'Untitled')}**")
                    authors = talk.get("authors", [])
                    if authors:
                        if isinstance(authors[0], dict):
                            author_strs = [
                                f"{a.get('name', '')} ({a.get('affiliation', '')})"
                                for a in authors
                            ]
                        else:
                            author_strs = authors
                        lines.append(f"Authors: {', '.join(author_strs)}")
                    if talk.get("abstract"):
                        lines.append(f"Abstract: {talk['abstract']}")
                    lines.append("")
                else:
                    lines.append(f"- {talk}")
            lines.append("")

        # Attendees
        attendees = session.get("attendees", [])
        if attendees:
            lines.append("### Attendees")
            for attendee in attendees:
                if isinstance(attendee, dict):
                    lines.append(
                        f"- {attendee.get('name', 'Unknown')} "
                        f"({attendee.get('organization', '')})"
                    )
                else:
                    lines.append(f"- {attendee}")
            lines.append("")

        # Notes
        notes = session.get("notes")
        if notes:
            lines.append("### Discussion Notes")
            lines.append(notes)
            lines.append("")

    # Sources
    sources = bundle.get("sources", [])
    if sources:
        lines.append("## Data Sources")
        for source in sources:
            lines.append(f"- {source}")

    return "\n".join(lines)


def generate_report(
    bundle: Dict[str, Any],
    client: Optional[LLMClient] = None,
    prompt_name: str = "tpc_master_prompt_v2.yaml",
    max_tokens: int = 8000,
    temperature: float = 0.3,
) -> str:
    """
    Generate a track report from a bundle.

    Args:
        bundle: Track bundle dictionary
        client: Optional LLMClient instance (creates one if not provided)
        prompt_name: Name of the prompt file to use
        max_tokens: Maximum tokens for the response
        temperature: Temperature for generation

    Returns:
        Generated markdown report
    """
    if client is None:
        client = create_llm_client()

    # Load prompt
    system_prompt = load_prompt(prompt_name)

    # Format the bundle data
    bundle_text = format_track_bundle(bundle)

    # Build messages
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Generate the track report for the following data:\n\n{bundle_text}",
        },
    ]

    # Call LLM
    report = client.chat_completion(
        messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    return report


def generate_report_from_file(
    bundle_path: str,
    output_path: Optional[str] = None,
    client: Optional[LLMClient] = None,
    **kwargs,
) -> str:
    """
    Generate a report from a bundle JSON file.

    Args:
        bundle_path: Path to the track bundle JSON file
        output_path: Optional path to write the report (if not provided, just returns)
        client: Optional LLMClient instance
        **kwargs: Additional arguments passed to generate_report

    Returns:
        Generated markdown report
    """
    bundle_path = Path(bundle_path)
    if not bundle_path.exists():
        raise FileNotFoundError(f"Bundle file not found: {bundle_path}")

    with open(bundle_path, "r") as f:
        bundle = json.load(f)

    report = generate_report(bundle, client=client, **kwargs)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)

    return report


# Convenience function for CLI
def main():
    """CLI entry point for generator."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate track report from bundle")
    parser.add_argument("bundle", help="Path to track bundle JSON file")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument(
        "--max-tokens", type=int, default=8000, help="Max tokens (default: 8000)"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.3, help="Temperature (default: 0.3)"
    )

    args = parser.parse_args()

    report = generate_report_from_file(
        args.bundle,
        output_path=args.output,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )

    if not args.output:
        print(report)


if __name__ == "__main__":
    main()
