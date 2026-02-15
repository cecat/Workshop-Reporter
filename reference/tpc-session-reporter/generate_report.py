#!/usr/bin/env python3
"""
TPC Session Report Generator
Uses master prompt to generate reports via OpenAI GPT-4.1 nano
"""

import argparse
import csv
import os
import re
import shutil
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup
from openai import OpenAI


def load_secrets(file_path="secrets.yml"):
    """Load API credentials from secrets.yml"""
    try:
        with open(file_path, "r") as f:
            secrets = yaml.safe_load(f)
        return secrets.get("openai_api_key")
    except FileNotFoundError:
        print(f"❌ Error: {file_path} not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        sys.exit(1)


def load_config(file_path="config.yml"):
    """Load configuration from config.yml"""
    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ Error: {file_path} not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)


def setup_input_directory():
    """Create _INPUT directory and preserve HTML files"""
    input_dir = Path("_INPUT")

    # Preserve HTML files if directory exists
    html_backup = None
    if input_dir.exists():
        # Look for any HTML file to preserve
        html_files = list(input_dir.glob("*.html"))
        if html_files:
            html_backup = html_files[0].read_text(encoding="utf-8")
            print(f"📄 Preserving HTML file: {html_files[0].name}")

        # Remove existing directory
        shutil.rmtree(input_dir)
        print("🧹 Cleared existing _INPUT directory (preserving HTML)")

    # Create fresh directory
    input_dir.mkdir(exist_ok=True)
    print("📁 Created fresh _INPUT directory")

    # Restore HTML file if we had one
    if html_backup:
        restored_html = input_dir / "program_sessions.html"
        restored_html.write_text(html_backup, encoding="utf-8")
        print("✅ Restored HTML file to _INPUT directory")


def download_to_input(url, filename):
    """Download content from URL to _INPUT/filename"""
    try:
        input_path = Path("_INPUT") / filename

        # Add headers to mimic a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Write content based on file type
        if filename.endswith(".csv"):
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        else:
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(response.text)

        print(f"✅ Downloaded {filename} from URL")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        return False


def copy_local_to_input(source_path, filename):
    """Copy local file to _INPUT directory"""
    try:
        source = Path(source_path)
        if not source.exists():
            print(f"⚠️  Local file not found: {source_path}")
            return False

        dest = Path("_INPUT") / filename
        shutil.copy2(source, dest)
        print(f"✅ Copied local {filename} to _INPUT")
        return True
    except Exception as e:
        print(f"❌ Error copying {filename}: {e}")
        return False


def download_all_sources(config, args):
    """Download all configured and provided data sources"""
    print("\n📥 Downloading data sources...")

    success_count = 0
    total_sources = 0

    # 1. Always download program sessions
    total_sources += 1
    program_url = config["data_sources"]["program_url"]
    if download_to_input(program_url, "program_sessions.html"):
        success_count += 1

    # 2. Always download lightning talks
    total_sources += 1
    lightning_url = config["data_sources"]["lightning_talks_url"]
    if download_to_input(lightning_url, "lightning_talks.csv"):
        success_count += 1

    # 3. Handle participants data
    total_sources += 1
    if args.participants:
        if args.participants.startswith("http"):
            if "docs.google.com" in args.participants:
                # Convert Google Sheets URL to export CSV format
                sheet_id = args.participants.split("/d/")[1].split("/")[0]
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                if download_to_input(csv_url, "attendees.csv"):
                    success_count += 1
            else:
                # Download from standard URL
                if download_to_input(args.participants, "attendees.csv"):
                    success_count += 1
        else:
            # Copy from local file
            if copy_local_to_input(args.participants, "attendees.csv"):
                success_count += 1
    else:
        # Check for local attendees.csv
        if copy_local_to_input("attendees.csv", "attendees.csv"):
            success_count += 1

    # 4. Handle discussion notes
    total_sources += 1
    if args.notes:
        if args.notes.startswith("http"):
            # Convert Google Docs URL to export format if needed
            if "docs.google.com" in args.notes:
                # Convert to export format
                if "/document/" in args.notes:
                    # Google Doc
                    doc_id = args.notes.split("/d/")[1].split("/")[0]
                    notes_url = (
                        f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
                    )
                elif "/spreadsheets/" in args.notes:
                    # Google Sheet
                    sheet_id = args.notes.split("/d/")[1].split("/")[0]
                    notes_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                else:
                    notes_url = args.notes

                if download_to_input(notes_url, "discussion_notes.txt"):
                    success_count += 1
            else:
                # Download from standard URL
                if download_to_input(args.notes, "discussion_notes.txt"):
                    success_count += 1
        else:
            # Copy from local file
            if copy_local_to_input(args.notes, "discussion_notes.txt"):
                success_count += 1
    else:
        # Check for local discussion notes files
        found_local_notes = False
        for ext in [".txt", ".docx", ".pdf"]:
            for pattern in ["discussion_notes", "notes", "meeting_notes"]:
                filename = f"{pattern}{ext}"
                if copy_local_to_input(filename, "discussion_notes.txt"):
                    success_count += 1
                    found_local_notes = True
                    break
            if found_local_notes:
                break

        if not found_local_notes:
            print("⚠️  No discussion notes found (will proceed without)")

    print(f"\n📊 Downloaded {success_count}/{total_sources} data sources successfully")
    return success_count


def load_master_prompt(file_path="tpc25_master_prompt.yaml"):
    """Load the master prompt from YAML file"""
    try:
        with open(file_path, "r") as f:
            prompt_data = yaml.safe_load(f)
        return prompt_data.get("master_prompt")
    except FileNotFoundError:
        print(f"❌ Error: {file_path} not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading master prompt: {e}")
        sys.exit(1)


def filter_lightning_talks_for_session(breakout_group):
    """Filter lightning talks CSV data for the specific session"""
    input_dir = Path("_INPUT")
    lightning_file = input_dir / "lightning_talks.csv"

    if not lightning_file.exists():
        return None, 0

    try:
        import csv
        from io import StringIO

        with open(lightning_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse CSV
        reader = csv.DictReader(StringIO(content))
        filtered_talks = []

        for row in reader:
            session_col = "Which session is best fit for your proposed lightning talk?  Some sessions have already filled up but please submit and if full you will be put on a standby list."
            session_label = row.get(session_col, "")

            # Check if this talk matches the target session
            if session_matches(breakout_group, session_label):
                title = row.get("Title of your proposed lightning talk", "No title")
                author = row.get("Your full name", "No author")
                institution = row.get("Your institution", "No institution")
                abstract = row.get(
                    "Abstract of your proposed lightning talk (80-100 words)",
                    "No abstract",
                )

                filtered_talks.append(
                    {
                        "title": title,
                        "author": author,
                        "institution": institution,
                        "abstract": abstract,
                    }
                )

        # Format for the model
        if filtered_talks:
            formatted_talks = []
            for i, talk in enumerate(filtered_talks, 1):
                formatted = f"Talk {i}:\n**Title**: {talk['title']}\n**Author**: {talk['author']}\n**Institution**: {talk['institution']}\n**Abstract**: {talk['abstract']}\n"
                formatted_talks.append(formatted)
            return "\n".join(formatted_talks), len(filtered_talks)
        else:
            return None, 0

    except Exception as e:
        print(f"⚠️  Error filtering lightning talks: {e}")
        return None, 0


def session_matches(target_group, session_label):
    """Check if session label matches target group using flexible matching"""
    if not target_group or not session_label:
        return False

    target = target_group.upper().strip()
    session = session_label.upper().strip()

    # Exact match
    if target == session:
        return True

    # Target contained in session (for acronyms like DWARF)
    if target in session:
        return True

    # Session contained in target (for full names)
    if session in target:
        return True

    # Word-based matching for partial matches
    target_words = set(target.replace(",", "").replace(":", "").split())
    session_words = set(session.replace(",", "").replace(":", "").split())

    # If most target words appear in session
    if len(target_words & session_words) >= min(2, len(target_words)):
        return True

    return False


def create_sample_session_yaml():
    """Create a sample session.yaml file for user to fill out"""
    sample_content = """# Session Information Configuration
# Use this file when the program cannot automatically extract session details from the website
# 
# Instructions:
# 1. Replace the sample data below with your actual session information
# 2. Save this file as 'session.yaml' in the same directory as the report generator
# 3. Run the report generator again

session:
  title: "Your Session Title Here (e.g., Model Architecture and Performance Evaluation)"
  
  leaders:
    - name: "First Leader Name"
      institution: "Leader's Institution"
    - name: "Second Leader Name" 
      institution: "Leader's Institution"
  
  description: |
    Enter your session description here. You can use multiple lines.
    Describe the session's goals, topics covered, and key themes.
    This will appear in the generated report.

# Optional: Additional session metadata
metadata:
  date: "Session Date (e.g., Thursday, July 31, 2025)"
  time: "Session Time (e.g., 8:30 AM - 5:00 PM)"
  track: "Track Name (e.g., Scale, Applications, etc.)"
  session_type: "Session Type (e.g., Breakout, Plenary, etc.)"
"""

    try:
        with open("session.yaml", "w", encoding="utf-8") as f:
            f.write(sample_content)
        print("📝 Created sample session.yaml file")
        return True
    except Exception as e:
        print(f"❌ Error creating session.yaml: {e}")
        return False


def load_session_yaml():
    """Load session information from session.yaml file"""
    session_file = Path("session.yaml")
    if not session_file.exists():
        return None

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        session_data = data.get("session", {})

        # Format leaders
        leaders_list = session_data.get("leaders", [])
        if leaders_list:
            formatted_leaders = []
            for leader in leaders_list:
                name = leader.get("name", "")
                institution = leader.get("institution", "")
                if name and institution:
                    formatted_leaders.append(f"{name}, {institution}")
                elif name:
                    formatted_leaders.append(name)
            leaders_str = "; ".join(formatted_leaders)
        else:
            leaders_str = ""

        session_info = {
            "title": session_data.get("title", ""),
            "leaders": leaders_str,
            "description": session_data.get("description", ""),
        }

        print("✅ Loaded session information from session.yaml")
        return session_info

    except Exception as e:
        print(f"⚠️  Error loading session.yaml: {e}")
        return None


def extract_session_details(session_acronym, html_content=None):
    """Extract session title, leaders, description from program HTML or session.yaml"""
    input_dir = Path("_INPUT")

    session_info = {
        "title": f"Session: {session_acronym}",
        "leaders": "",
        "description": "",
    }

    # First try session.yaml if it exists
    yaml_info = load_session_yaml()
    if yaml_info:
        return yaml_info

    # Then try to find any HTML file in _INPUT directory
    html_file = None
    html_files = list(input_dir.glob("*.html"))
    if html_files:
        html_file = html_files[0]  # Use the first HTML file found
        print(f"✅ Using session data from _INPUT: {html_file.name}")
    else:
        # Then try the local HTML version if available
        local_html_file = Path("tpc25_sessions.html")
        if local_html_file.exists():
            html_file = local_html_file
            print(f"✅ Using local session data: {local_html_file}")
        else:
            print("⚠️  No HTML file found in _INPUT directory or locally")
            print("📝 Please create a session.yaml file with session details")
            create_sample_session_yaml()
            print("\n📋 Instructions:")
            print("   1. Edit the newly created session.yaml file")
            print("   2. Replace sample data with your actual session information")
            print("   3. Run the report generator again")
            return session_info

    try:
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # General session parsing for other sessions
        headers = soup.find_all(["h3", "h4"])

        for header in headers:
            header_text = header.get_text(strip=True)
            if session_acronym.upper() in header_text.upper():
                session_info["title"] = header_text

                # Look for description in following paragraphs
                next_elem = header.find_next_sibling()
                description_parts = []

                while next_elem and next_elem.name not in ["h1", "h2", "h3", "h4"]:
                    if next_elem.name == "p" and next_elem.get_text(strip=True):
                        text = next_elem.get_text(strip=True)
                        if "leader" in text.lower() or "organizer" in text.lower():
                            session_info["leaders"] = text
                        else:
                            description_parts.append(text)
                    next_elem = next_elem.find_next_sibling()

                if description_parts:
                    session_info["description"] = " ".join(
                        description_parts[:2]
                    )  # First 2 paragraphs
                break

        print(f"✅ Extracted session info: {session_info['title']}")
        return session_info

    except Exception as e:
        print(f"⚠️  Error parsing HTML: {e}")
        print("📝 To provide session details manually, create a session.yaml file")
        create_sample_session_yaml()
        print("\n📋 Instructions:")
        print("   1. Edit the newly created session.yaml file")
        print("   2. Replace sample data with your actual session information")
        print("   3. Run the report generator again")

        return session_info


def filter_talks_by_exact_acronym(breakout_group):
    """Filter lightning talks by exact acronym match"""
    input_dir = Path("_INPUT")
    lightning_file = input_dir / "lightning_talks.csv"

    if not lightning_file.exists():
        return []

    try:
        with open(lightning_file, "r", encoding="utf-8") as f:
            content = f.read()

        reader = csv.DictReader(StringIO(content))
        filtered_talks = []

        session_col = "Which session is best fit for your proposed lightning talk?  Some sessions have already filled up but please submit and if full you will be put on a standby list."

        for row in reader:
            session_label = row.get(session_col, "")

            # Simple exact acronym match - look for acronym in parentheses
            if (
                f"({breakout_group})" in session_label
                or f"({breakout_group.upper()})" in session_label
            ):
                filtered_talks.append(
                    {
                        "title": row.get(
                            "Title of your proposed lightning talk", "No title"
                        ),
                        "author": row.get("Your full name", "No author"),
                        "institution": row.get("Your institution", "No institution"),
                        "abstract": row.get(
                            "Abstract of your proposed lightning talk (80-100 words)",
                            "No abstract",
                        ),
                        "session_label": session_label,
                    }
                )

        print(f"✅ Found {len(filtered_talks)} lightning talks for {breakout_group}")
        return filtered_talks

    except Exception as e:
        print(f"⚠️  Error filtering lightning talks: {e}")
        return []


def generate_attendees_appendix():
    """Generate formatted attendees table"""
    input_dir = Path("_INPUT")
    attendees_file = input_dir / "attendees.csv"

    if not attendees_file.exists():
        return "## Appendix A: Attendees\n\nAttendees list not available.\n\n"

    try:
        with open(attendees_file, "r", encoding="utf-8") as f:
            content = f.read()

        reader = csv.DictReader(StringIO(content))
        attendees = []

        for row in reader:
            first = row.get("First", "").strip()
            last = row.get("Last", "").strip()
            org = row.get("Organization", "").strip()

            if first and last:
                name = f"{first} {last}"
                attendees.append({"name": name, "organization": org})

        if not attendees:
            return "## Appendix A: Attendees\n\nAttendees list not available.\n\n"

        # Sort by last name
        attendees.sort(key=lambda x: x["name"].split()[-1] if x["name"] else "")

        appendix = "## Appendix A: Attendees\n\n"
        appendix += "| Name | Organization |\n"
        appendix += "|------|--------------|\n"

        for attendee in attendees:
            name = attendee["name"] or "N/A"
            org = attendee["organization"] or "N/A"
            appendix += f"| {name} | {org} |\n"

        appendix += "\n"

        print(f"✅ Generated attendees appendix with {len(attendees)} attendees")
        return appendix

    except Exception as e:
        print(f"⚠️  Error generating attendees appendix: {e}")
        return "## Appendix A: Attendees\n\nError loading attendees list.\n\n"


def generate_lightning_talks_appendix(filtered_talks):
    """Generate formatted lightning talks appendix with full abstracts"""
    if not filtered_talks:
        return "## Appendix B: Lightning Talks\n\nNo lightning talks found for this session.\n\n"

    appendix = "## Appendix B: Lightning Talks\n\n"

    for i, talk in enumerate(filtered_talks, 1):
        appendix += f"### {i}. {talk['title']}\n\n"
        appendix += f"**Author:** {talk['author']}\n\n"
        appendix += f"**Institution:** {talk['institution']}\n\n"
        appendix += f"**Abstract:** {talk['abstract']}\n\n"
        appendix += "---\n\n"

    print(f"✅ Generated lightning talks appendix with {len(filtered_talks)} talks")
    return appendix


def generate_report_framework(session_info, filtered_talks):
    """Generate the static parts of the report (title, appendices)"""

    # Title section
    report = f"# {session_info['title']}\n\n"

    if session_info.get("leaders"):
        report += f"**Session Leaders:** {session_info['leaders']}\n\n"

    if session_info.get("description"):
        report += f"**Description:** {session_info['description']}\n\n"

    # Placeholder for AI-generated content
    report += "<!-- AI_CONTENT_PLACEHOLDER -->\n\n"

    # Generate appendices
    attendees_appendix = generate_attendees_appendix()
    talks_appendix = generate_lightning_talks_appendix(filtered_talks)

    report += attendees_appendix
    report += talks_appendix

    return report


def read_input_files(breakout_group):
    """Read CSV files and return their content as text"""
    input_dir = Path("_INPUT")
    files_content = {}

    # Read and filter lightning talks CSV for the specific session
    filtered_talks, talk_count = filter_lightning_talks_for_session(breakout_group)
    if filtered_talks:
        files_content["lightning_talks"] = filtered_talks
        files_content["talk_count"] = talk_count
        print(f"✅ Found {talk_count} lightning talks for session")

    # Read attendees CSV
    attendees_file = input_dir / "attendees.csv"
    if attendees_file.exists():
        try:
            with open(attendees_file, "r", encoding="utf-8") as f:
                files_content["attendees"] = f.read()
        except Exception as e:
            print(f"⚠️  Error reading attendees.csv: {e}")

    # Read discussion notes if available
    notes_file = input_dir / "discussion_notes.txt"
    if notes_file.exists():
        try:
            with open(notes_file, "r", encoding="utf-8") as f:
                files_content["notes"] = f.read()
        except Exception as e:
            print(f"⚠️  Error reading discussion_notes.txt: {e}")

    return files_content


def call_openai_api(client, prompt, config):
    """Make API call using configuration settings"""
    try:
        model_config = config["model"]
        model_name = model_config["name"]

        print(f"🤖 Calling {model_config['provider']} API with model: {model_name}")
        print(f"📝 Prompt length: {len(prompt)} characters")

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": config["system"]["system_message"]},
                {"role": "user", "content": prompt},
            ],
            max_tokens=model_config.get("max_tokens", 4000),
            temperature=model_config.get("temperature", 0.7),
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ Error calling OpenAI API: {e}")
        sys.exit(1)


def check_for_errors(content):
    """Check if the response contains error codes and handle them"""
    lines = content.strip().split("\n")
    if not lines:
        return False, None

    first_line = lines[0].strip()

    # Check for known error codes
    error_codes = [
        "ERROR: lightning talks URL not accessible",
        "ERROR: program information not found",
        "ERROR: notes URL not found",
        "ERROR: participants URL not found",
        "ERROR: local files not found",
        "ERROR: missing input",
    ]

    for error_code in error_codes:
        if error_code in first_line:
            return True, error_code

    return False, None


def generate_report_filename(session_info, session_acronym):
    """Generate session-specific filename"""
    # Try to extract acronym from session title
    title = session_info.get("title", f"Session: {session_acronym}")

    # Look for acronym in parentheses first

    acronym_match = re.search(r"\(([A-Z]+)\)", title)
    if acronym_match:
        name = acronym_match.group(1)
    else:
        # If no acronym found, use the provided session_acronym if it looks like an acronym
        if session_acronym and len(session_acronym) <= 6 and session_acronym.isupper():
            name = session_acronym
        else:
            # Convert full title to CamelCase
            # Remove "Session:" prefix if present
            clean_title = re.sub(r"^Session:\s*", "", title)
            # Remove "BOF:" prefix if present
            clean_title = re.sub(r"^BOF:\s*", "", clean_title)
            # Split on spaces and punctuation, then capitalize each word
            words = re.findall(r"\b\w+\b", clean_title)
            name = "".join(word.capitalize() for word in words)

    return f"draft-report-{name}.md"


def save_output(content, session_info, session_acronym):
    """Save the generated content to a session-specific file"""
    filename = generate_report_filename(session_info, session_acronym)

    try:
        with open(filename, "w", encoding="utf-8") as f:
            # Add header with timestamp
            f.write("# TPC Session Report Draft\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# Model: GPT-4.1 nano\n\n")
            f.write(content)

        print(f"✅ Report saved to: {filename}")
        print(f"📄 File size: {len(content)} characters")
        return filename

    except Exception as e:
        print(f"❌ Error saving file: {e}")
        sys.exit(1)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate TPC session reports using OpenAI GPT-4.1 nano",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -g "DWARF"
  %(prog)s --group "Data, Workflows, Agents, and Reasoning Frameworks"
  %(prog)s -g "DWARF" -p "https://example.com/attendees.csv"
  %(prog)s -g "AI" --participants "./local_attendees.csv"
  %(prog)s -g "DWARF" -n "https://docs.google.com/document/d/abc123/edit"
  %(prog)s -g "AI" -p "./attendees.csv" -n "./discussion_notes.docx"
""",
    )

    parser.add_argument(
        "-g",
        "--group",
        required=True,
        help='Breakout group name or acronym (e.g., "DWARF" or "Data, Workflows, Agents, and Reasoning Frameworks")',
    )

    parser.add_argument(
        "-p",
        "--participants",
        help="URL or file path for participant/attendee data (CSV format with First, Last, Organization columns)",
    )

    parser.add_argument(
        "-n",
        "--notes",
        help="URL or file path for discussion notes (DOCX, PDF, or Google Docs URL)",
    )

    return parser.parse_args()


def main():
    """Main execution function"""
    print("🚀 TPC Session Report Generator")
    print("=" * 50)

    # Parse command line arguments
    args = parse_arguments()
    breakout_group = args.group
    participants_source = args.participants
    notes_source = args.notes

    print(f"🎯 Target breakout group: {breakout_group}")
    if participants_source:
        print(f"👥 Participants source: {participants_source}")
    else:
        print(
            "👥 Participants source: Will check for local attendees.csv or proceed without"
        )

    if notes_source:
        print(f"📋 Discussion notes: {notes_source}")
    else:
        print(
            "📋 Discussion notes: Will check for local DOCX/PDF files or proceed without"
        )

    # Load configuration
    print("\n📖 Loading configuration...")
    config = load_config()
    api_key = load_secrets()
    master_prompt = load_master_prompt()

    if not api_key:
        print("❌ Error: OpenAI API key not found in secrets.yml")
        sys.exit(1)

    if not master_prompt:
        print("❌ Error: Master prompt not found in tpc25_master_prompt.yaml")
        sys.exit(1)

    print("✅ Configuration loaded successfully")

    # Set up OpenAI client
    client = OpenAI(api_key=api_key)

    # Setup input directory and download all sources
    setup_input_directory()
    download_all_sources(config, args)

    # NEW ARCHITECTURE: Generate report framework using Python
    print("\n📊 Processing data and generating report framework...")

    # 1. Extract session details from HTML
    session_info = extract_session_details(breakout_group)

    # 2. Filter lightning talks by exact acronym match
    filtered_talks = filter_talks_by_exact_acronym(breakout_group)

    # 3. Generate the report framework (title + appendices)
    report_framework = generate_report_framework(session_info, filtered_talks)

    print("\n📄 Report framework generated:")
    print(f"   - Session: {session_info['title']}")
    print(f"   - Lightning talks: {len(filtered_talks)}")
    print(f"   - Report length: {len(report_framework)} characters")

    # For now, save the framework without AI content
    print("\n💾 Saving report framework...")
    filename = save_output(report_framework, session_info, breakout_group)

    print("\n🎉 Report framework generation completed!")
    print(
        "\n📝 Next step: Add AI-generated content for report body (discussion summary, etc.)"
    )


if __name__ == "__main__":
    main()
