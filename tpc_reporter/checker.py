"""
Hallucination checker for TPC Workshop Reporter.

Performs a second LLM pass to verify generated reports against source data
and flag potential hallucinations.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from tpc_reporter.generator import format_track_bundle
from tpc_reporter.llm_client import LLMClient, create_llm_client


@dataclass
class VerificationResult:
    """Result of report verification."""

    report: str
    flags: list[dict[str, str]] = field(default_factory=list)
    total_flags: int = 0
    status: str = "UNKNOWN"

    @property
    def passed(self) -> bool:
        """Check if verification passed with no flags."""
        return self.total_flags == 0

    @property
    def needs_review(self) -> bool:
        """Check if report needs human review."""
        return 1 <= self.total_flags <= 5

    @property
    def has_major_issues(self) -> bool:
        """Check if report has major issues."""
        return self.total_flags > 5


def _find_prompts_dir() -> Path:
    """Find the prompts directory."""
    current = Path(__file__).parent
    for _ in range(5):
        prompts_dir = current / "prompts"
        if prompts_dir.exists():
            return prompts_dir
        current = current.parent

    cwd = Path.cwd()
    if (cwd / "prompts").exists():
        return cwd / "prompts"

    raise FileNotFoundError("Could not find prompts directory.")


def load_checker_prompt(prompt_name: str = "checker_prompt.yaml") -> str:
    """
    Load the checker prompt template.

    Args:
        prompt_name: Name of the prompt file

    Returns:
        The checker_prompt string from the YAML file
    """
    prompts_dir = _find_prompts_dir()
    prompt_path = prompts_dir / prompt_name

    if not prompt_path.exists():
        raise FileNotFoundError(f"Checker prompt not found: {prompt_path}")

    with open(prompt_path) as f:
        prompt_data = yaml.safe_load(f)

    if "checker_prompt" not in prompt_data:
        raise ValueError(f"Prompt file {prompt_name} missing 'checker_prompt' key")

    return prompt_data["checker_prompt"]


def extract_flags(checked_report: str) -> list[dict[str, str]]:
    """
    Extract [FLAG: ...] annotations from a checked report.

    Args:
        checked_report: Report text with inline flags

    Returns:
        List of flag dictionaries with 'type' and 'description' keys
    """
    # Pattern matches [FLAG: type "description"] or [FLAG: type description]
    pattern = r'\[FLAG:\s*([^"\]]+?)(?:\s+"([^"]+)")?\]'
    matches = re.findall(pattern, checked_report)

    flags = []
    for match in matches:
        flag_type = match[0].strip()
        description = match[1] if match[1] else ""
        flags.append({"type": flag_type, "description": description})

    return flags


def parse_verification_summary(checked_report: str) -> dict[str, Any]:
    """
    Parse the verification summary section from a checked report.

    Args:
        checked_report: Report text with verification summary

    Returns:
        Dictionary with summary information
    """
    summary = {
        "total_flags": 0,
        "status": "UNKNOWN",
        "breakdown": {},
    }

    # Extract total flags
    total_match = re.search(r"\*\*Total flags:\*\*\s*(\d+)", checked_report)
    if total_match:
        summary["total_flags"] = int(total_match.group(1))

    # Extract status
    status_match = re.search(
        r"\*\*Verification status:\*\*\s*(PASS|REVIEW NEEDED|MAJOR ISSUES)",
        checked_report,
    )
    if status_match:
        summary["status"] = status_match.group(1)

    # Extract breakdown counts
    breakdown_patterns = [
        (r"Unknown persons:\s*(\d+)", "unknown_persons"),
        (r"Unknown organizations:\s*(\d+)", "unknown_organizations"),
        (r"Unverified talks:\s*(\d+)", "unverified_talks"),
        (r"Unsupported claims:\s*(\d+)", "unsupported_claims"),
        (r"Other issues:\s*(\d+)", "other_issues"),
    ]

    for pattern, key in breakdown_patterns:
        match = re.search(pattern, checked_report)
        if match:
            summary["breakdown"][key] = int(match.group(1))

    return summary


def check_report(
    draft_report: str,
    bundle: dict[str, Any],
    client: LLMClient | None = None,
    prompt_name: str = "checker_prompt.yaml",
    max_tokens: int = 10000,
    temperature: float = 0.1,
) -> VerificationResult:
    """
    Check a draft report for hallucinations against source data.

    Args:
        draft_report: The generated draft report to verify
        bundle: The source track bundle data
        client: Optional LLMClient instance
        prompt_name: Name of the checker prompt file
        max_tokens: Maximum tokens for the response
        temperature: Temperature for generation (low for consistency)

    Returns:
        VerificationResult with checked report and flag information
    """
    if client is None:
        client = create_llm_client()

    # Load checker prompt
    system_prompt = load_checker_prompt(prompt_name)

    # Format the source data
    source_text = format_track_bundle(bundle)

    # Build the user message
    user_content = f"""## Source Data (Ground Truth)

{source_text}

## Draft Report to Verify

{draft_report}

Please verify this report against the source data and flag any hallucinations."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    # Call LLM
    checked_report = client.chat_completion(
        messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # Extract flags and parse summary
    flags = extract_flags(checked_report)
    summary = parse_verification_summary(checked_report)

    # Use extracted flags count if summary parsing failed
    total_flags = summary["total_flags"] if summary["total_flags"] > 0 else len(flags)

    # Determine status if not parsed
    status = summary["status"]
    if status == "UNKNOWN":
        if total_flags == 0:
            status = "PASS"
        elif total_flags <= 5:
            status = "REVIEW NEEDED"
        else:
            status = "MAJOR ISSUES"

    return VerificationResult(
        report=checked_report,
        flags=flags,
        total_flags=total_flags,
        status=status,
    )


def check_report_from_files(
    draft_path: str,
    bundle_path: str,
    output_path: str | None = None,
    client: LLMClient | None = None,
    **kwargs,
) -> VerificationResult:
    """
    Check a report from files.

    Args:
        draft_path: Path to the draft report markdown file
        bundle_path: Path to the source bundle JSON file
        output_path: Optional path to write the checked report
        client: Optional LLMClient instance
        **kwargs: Additional arguments passed to check_report

    Returns:
        VerificationResult
    """
    draft_path = Path(draft_path)
    bundle_path = Path(bundle_path)

    if not draft_path.exists():
        raise FileNotFoundError(f"Draft report not found: {draft_path}")
    if not bundle_path.exists():
        raise FileNotFoundError(f"Bundle file not found: {bundle_path}")

    with open(draft_path) as f:
        draft_report = f.read()

    with open(bundle_path) as f:
        bundle = json.load(f)

    result = check_report(draft_report, bundle, client=client, **kwargs)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(result.report)

    return result


# CLI entry point
def main():
    """CLI entry point for checker."""
    import argparse

    parser = argparse.ArgumentParser(description="Check report for hallucinations")
    parser.add_argument("draft", help="Path to draft report markdown file")
    parser.add_argument("bundle", help="Path to source bundle JSON file")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument(
        "--max-tokens", type=int, default=10000, help="Max tokens (default: 10000)"
    )

    args = parser.parse_args()

    result = check_report_from_files(
        args.draft,
        args.bundle,
        output_path=args.output,
        max_tokens=args.max_tokens,
    )

    if not args.output:
        print(result.report)

    print(f"\n--- Verification Status: {result.status} ---")
    print(f"Total flags: {result.total_flags}")

    if result.flags:
        print("\nFlags found:")
        for i, flag in enumerate(result.flags, 1):
            print(f"  {i}. {flag['type']}: {flag['description']}")


if __name__ == "__main__":
    main()
