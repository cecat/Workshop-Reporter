"""
Website scraper for TPC Workshop Reporter.

Scrapes speaker and session information from TPC conference websites.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Default timeout for requests
DEFAULT_TIMEOUT = 30


@dataclass
class Speaker:
    """Represents a conference speaker."""

    name: str
    title: str = ""
    institution: str = ""
    bio: str = ""
    image_url: str = ""


@dataclass
class Session:
    """Represents a conference session."""

    title: str
    session_type: str = ""  # "plenary", "breakout", "tutorial", "hackathon"
    datetime: str = ""
    description: str = ""
    speakers: list[str] = field(default_factory=list)
    track: str = ""


@dataclass
class ScrapeResult:
    """Result of scraping a TPC website."""

    speakers: list[Speaker] = field(default_factory=list)
    sessions: list[Session] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    base_url: str = ""


def fetch_page(url: str, timeout: int = DEFAULT_TIMEOUT) -> str | None:
    """
    Fetch a webpage and return its HTML content.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content or None if request failed
    """
    try:
        headers = {"User-Agent": "TPC-Workshop-Reporter/1.0 (Educational/Research)"}
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def parse_speakers_page(html: str) -> list[Speaker]:
    """
    Parse speakers from a TPC speakers page.

    Handles Elementor image-box format commonly used on TPC sites.

    Args:
        html: HTML content of the speakers page

    Returns:
        List of Speaker objects
    """
    soup = BeautifulSoup(html, "html.parser")
    speakers = []

    # Find Elementor image-box widgets (common format on TPC sites)
    image_boxes = soup.find_all("div", class_=re.compile(r"elementor-image-box"))

    seen_names = set()
    for box in image_boxes:
        # Get speaker name from title
        title_elem = box.find(class_="elementor-image-box-title")
        if not title_elem:
            continue

        name = title_elem.get_text(strip=True)
        if not name:
            continue

        # Skip duplicates (responsive layouts often have duplicate elements)
        if name in seen_names:
            continue
        seen_names.add(name)

        # Get description (title/institution)
        desc_elem = box.find(class_="elementor-image-box-description")
        description = desc_elem.get_text(strip=True) if desc_elem else ""

        # Parse title and institution from description
        # Format is often "Title, Institution" or "Title | Institution"
        title, institution = _parse_speaker_description(description)

        # Get image URL
        img = box.find("img")
        image_url = img.get("src", "") if img else ""

        speakers.append(
            Speaker(
                name=name,
                title=title,
                institution=institution,
                bio=description,
                image_url=image_url,
            )
        )

    return speakers


def _parse_speaker_description(description: str) -> tuple:
    """
    Parse a speaker description into title and institution.

    Args:
        description: Raw description string

    Returns:
        Tuple of (title, institution)
    """
    if not description:
        return "", ""

    # Try splitting on common delimiters
    for delimiter in [" | ", ", ", " - "]:
        if delimiter in description:
            parts = description.split(delimiter, 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

    # If no delimiter found, treat whole thing as title
    return description, ""


def parse_sessions_page(html: str) -> list[Session]:
    """
    Parse sessions from a TPC sessions page.

    Args:
        html: HTML content of the sessions page

    Returns:
        List of Session objects
    """
    soup = BeautifulSoup(html, "html.parser")
    sessions = []

    # Find session entries - TPC uses various heading levels
    # Look for h2/h3 elements with session titles
    headings = soup.find_all(["h2", "h3"], class_=re.compile(r"elementor-heading"))

    current_section = ""
    for heading in headings:
        title = heading.get_text(strip=True)
        if not title:
            continue

        # Detect section headers vs actual sessions
        title_lower = title.lower()

        # Section headers (categories)
        if title_lower in [
            "sessions",
            "plenary sessions",
            "breakout groups",
            "workflows",
            "initiatives",
            "life sciences",
            "tutorials",
            "hackathons",
        ]:
            current_section = title
            continue

        # Skip countdown/marketing sections
        if "countdown" in title_lower:
            continue

        # Detect session type from title or section
        session_type = _detect_session_type(title, current_section)

        # Look for datetime in following h4
        datetime_str = ""
        next_sibling = heading.find_next_sibling()
        if next_sibling:
            h4 = next_sibling.find("h4") if hasattr(next_sibling, "find") else None
            if h4:
                datetime_str = h4.get_text(strip=True)
        else:
            # Check parent container for h4
            parent = heading.find_parent(class_=re.compile(r"elementor-widget"))
            if parent:
                container = parent.find_parent(class_=re.compile(r"elementor-element"))
                if container:
                    h4 = container.find("h4")
                    if h4:
                        datetime_str = h4.get_text(strip=True)

        sessions.append(
            Session(
                title=title,
                session_type=session_type,
                datetime=datetime_str,
                track=current_section,
            )
        )

    return sessions


def _detect_session_type(title: str, section: str) -> str:
    """
    Detect session type from title and section context.

    Args:
        title: Session title
        section: Current section header

    Returns:
        Session type string
    """
    title_lower = title.lower()
    section_lower = section.lower()

    if "plenary" in title_lower or "plenary" in section_lower:
        return "plenary"
    elif "bof" in title_lower or "breakout" in section_lower:
        return "breakout"
    elif "tutorial" in title_lower or "tutorial" in section_lower:
        return "tutorial"
    elif "hackathon" in title_lower or "hackathon" in section_lower:
        return "hackathon"
    elif "panel" in title_lower:
        return "panel"
    elif "lunch" in title_lower:
        return "break"
    else:
        return "session"


def scrape_speakers(
    base_url: str, speakers_path: str = "/agenda/speakers/"
) -> list[Speaker]:
    """
    Scrape speakers from a TPC website.

    Args:
        base_url: Base URL of the TPC site (e.g., "https://tpc25.org")
        speakers_path: Path to the speakers page

    Returns:
        List of Speaker objects
    """
    url = urljoin(base_url, speakers_path)
    logger.info(f"Scraping speakers from {url}")

    html = fetch_page(url)
    if not html:
        return []

    return parse_speakers_page(html)


def scrape_sessions(base_url: str, sessions_path: str = "/sessions/") -> list[Session]:
    """
    Scrape sessions from a TPC website.

    Args:
        base_url: Base URL of the TPC site (e.g., "https://tpc25.org")
        sessions_path: Path to the sessions page

    Returns:
        List of Session objects
    """
    url = urljoin(base_url, sessions_path)
    logger.info(f"Scraping sessions from {url}")

    html = fetch_page(url)
    if not html:
        return []

    return parse_sessions_page(html)


def scrape_site(base_url: str) -> ScrapeResult:
    """
    Scrape all relevant data from a TPC website.

    Args:
        base_url: Base URL of the TPC site (e.g., "https://tpc25.org")

    Returns:
        ScrapeResult with speakers, sessions, and any errors
    """
    result = ScrapeResult(base_url=base_url)

    # Scrape speakers
    try:
        result.speakers = scrape_speakers(base_url)
        logger.info(f"Found {len(result.speakers)} speakers")
    except Exception as e:
        error_msg = f"Failed to scrape speakers: {e}"
        logger.error(error_msg)
        result.errors.append(error_msg)

    # Brief delay between requests
    time.sleep(0.5)

    # Scrape sessions
    try:
        result.sessions = scrape_sessions(base_url)
        logger.info(f"Found {len(result.sessions)} sessions")
    except Exception as e:
        error_msg = f"Failed to scrape sessions: {e}"
        logger.error(error_msg)
        result.errors.append(error_msg)

    return result


def speakers_to_csv(speakers: list[Speaker]) -> str:
    """
    Convert speakers to CSV format.

    Args:
        speakers: List of Speaker objects

    Returns:
        CSV string with header
    """
    lines = ["Name,Title,Institution,Image URL"]
    for s in speakers:
        # Escape commas and quotes in fields
        name = _csv_escape(s.name)
        title = _csv_escape(s.title)
        institution = _csv_escape(s.institution)
        image_url = _csv_escape(s.image_url)
        lines.append(f"{name},{title},{institution},{image_url}")
    return "\n".join(lines)


def sessions_to_csv(sessions: list[Session]) -> str:
    """
    Convert sessions to CSV format.

    Args:
        sessions: List of Session objects

    Returns:
        CSV string with header
    """
    lines = ["Title,Type,DateTime,Track,Description"]
    for s in sessions:
        title = _csv_escape(s.title)
        session_type = _csv_escape(s.session_type)
        datetime = _csv_escape(s.datetime)
        track = _csv_escape(s.track)
        description = _csv_escape(s.description)
        lines.append(f"{title},{session_type},{datetime},{track},{description}")
    return "\n".join(lines)


def _csv_escape(value: str) -> str:
    """Escape a value for CSV format."""
    if not value:
        return ""
    # If contains comma, newline, or quote, wrap in quotes
    if "," in value or "\n" in value or '"' in value:
        value = value.replace('"', '""')
        return f'"{value}"'
    return value


# CLI entry point
def main():
    """CLI entry point for website scraper."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape speaker and session data from TPC websites"
    )
    parser.add_argument(
        "url",
        help="Base URL of the TPC site (e.g., https://tpc25.org)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="./data",
        help="Output directory for CSV files",
    )
    parser.add_argument(
        "--speakers-only",
        action="store_true",
        help="Only scrape speakers",
    )
    parser.add_argument(
        "--sessions-only",
        action="store_true",
        help="Only scrape sessions",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Normalize URL
    base_url = args.url.rstrip("/")
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"

    print(f"\nScraping {base_url}...")
    print("=" * 50)

    from pathlib import Path

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Scrape based on options
    if args.sessions_only:
        sessions = scrape_sessions(base_url)
        print(f"\n✓ Found {len(sessions)} sessions")

        csv_path = output_dir / "sessions.csv"
        csv_path.write_text(sessions_to_csv(sessions))
        print(f"✓ Saved to {csv_path}")

    elif args.speakers_only:
        speakers = scrape_speakers(base_url)
        print(f"\n✓ Found {len(speakers)} speakers")

        csv_path = output_dir / "speakers.csv"
        csv_path.write_text(speakers_to_csv(speakers))
        print(f"✓ Saved to {csv_path}")

    else:
        result = scrape_site(base_url)

        print(f"\n✓ Found {len(result.speakers)} speakers")
        print(f"✓ Found {len(result.sessions)} sessions")

        if result.errors:
            print(f"\n⚠ {len(result.errors)} errors occurred:")
            for err in result.errors:
                print(f"  - {err}")

        # Save CSV files
        speakers_path = output_dir / "speakers.csv"
        speakers_path.write_text(speakers_to_csv(result.speakers))
        print(f"\n✓ Speakers saved to {speakers_path}")

        sessions_path = output_dir / "sessions.csv"
        sessions_path.write_text(sessions_to_csv(result.sessions))
        print(f"✓ Sessions saved to {sessions_path}")

    print("\n✓ Scraping complete!")
    return 0


if __name__ == "__main__":
    exit(main())
