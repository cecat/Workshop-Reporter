# TPC Workshop Reporter

Generate draft track reports for TPC conferences from website data, scribe notes, and attendee lists.

**Important**: This repository includes test data with specific CSV column formats. If you're using your own Google Sheets or CSV files with different column names, you'll need to update the `csv_schema` section in `configuration.yaml` to match your column names or indices. See the [CSV Schema Configuration](#csv-schema-configuration) section below.

## What It Does

Given a TPC conference website and Google Drive folders with session notes and attendee lists, this tool produces **one draft Markdown report per track**, ready for human review by track organizers.

Each report includes:
- **Executive Summary** synthesizing themes across all sessions in the track
- **Per-session summaries** with lightning talk overviews and discussion outcomes
- **Cross-cutting themes** identified across sessions
- **Appendices** with full attendee lists and complete lightning talk details
- **Hallucination flags** where the checker found unsupported claims

## Conference Structure

TPC conferences use this hierarchy:

```
Conference (e.g., TPC25 — 6 tracks, TPC26 — 8 tracks)
  └── Track (thematic grouping in one room, e.g., "Workflows")
        └── Session (90-min slot, e.g., "DWARF: Keynote and Systems Software for Agents")
              ├── Lightning Talks (4-6 per session, from website)
              ├── Attendees (from Google Sheet)
              └── Notes/Transcript (from Google Doc)
```

We produce **one report per track**. For TPC26 that means 8 reports.

## Pipeline

```
Website ──scrape──→ conference.json  ─┐
                                      ├──assemble──→ track_bundle.json ──generate──→ draft.md ──check──→ report.md
Google Drive ──collect──→ track_inputs/ ─┘
```

Each step is a standalone Python module. No framework dependencies.

## Quick Start

### 1. Install

Install Google Drive and scraping support.

```bash
pip install -e ".[scraper]"  
```

### 2. Configure LLM Endpoint

Edit `configuration.yaml` to set your LLM provider, e.g.:
```yaml
active_endpoint: "openai"  
```

Create `secrets.yaml` with your API key:
```yaml
OPENAI_API_KEY: "sk-your-key-here"
```

### 3. Configure Google Drive URLs

You'll need three publicly shared Google Drive URLs:
1. **Lightning talks sheet**: Google Sheet with columns for Title, Authors, Institution, Abstract, Track
2. **Attendees sheet**: Google Sheet with Name and Institution columns (or customize the schema)
3. **Notes document**: Google Doc with session notes and discussion outcomes

Add these URLs to `configuration.yaml`:

```yaml
data_sources:
  google_drive:
    lightning_talks_url: "https://docs.google.com/spreadsheets/d/YOUR_ID/edit?usp=sharing"
    attendees_url: "https://docs.google.com/spreadsheets/d/YOUR_ID/edit?usp=sharing"
    notes_url: "https://docs.google.com/document/d/YOUR_ID/edit?usp=sharing"
```

**Important**: If your CSV files have different column names, update the `csv_schema` section in `configuration.yaml`. See [CSV Schema Configuration](#csv-schema-configuration).

Note: a CSV file uploaded to Google Drive needs to be opened and saved as a Google Sheets file.

### 4. Fetch Data and Create Bundle

Use the `fetch-and-assemble` command to download data from Google Drive and create a track bundle in one step:

```bash
tpc-reporter fetch-and-assemble --track Track-1 -o data/track1_bundle.json
```

This will:
- Download lightning talks, attendees, and notes from the URLs in `configuration.yaml`
- Parse the data using the CSV schema mappings
- Filter talks by the specified track
- Create a bundle JSON file

**Alternative: Manual download**

You can also download files manually using Python:

```python
from tpc_reporter.gdrive import download_sheet, download_doc

# Download files
download_sheet("https://docs.google.com/spreadsheets/d/YOUR_ID/edit", "lightning_talks.csv")
download_sheet("https://docs.google.com/spreadsheets/d/YOUR_ID/edit", "attendees.csv")
download_doc("https://docs.google.com/document/d/YOUR_ID/edit", "notes.txt")
```

Generate report from the bundle:

```bash
tpc-reporter run data/track1_bundle.json -o output/track1_report.md
```

This runs:
1. **Generation**: Creates draft report using LLM
2. **Verification**: Checks for hallucinations against source data
3. **Output**: Saves final report with any flags marked

## Advanced: Manual Bundle Creation

If you need more control over the bundle creation process, you can create the bundle JSON manually.

**Bundle format:**
```json
{
  "track": {
    "id": "track-1",
    "name": "Track Name",
    "room": "Room Name"
  },
  "sessions": [
    {
      "id": "session-1",
      "title": "Session Title",
      "slot": "2025-07-30T09:00",
      "leaders": [],
      "lightning_talks": [{"title": "...", "authors": [...], "abstract": "..."}],
      "attendees": [{"name": "...", "organization": "..."}],
      "notes": "Discussion notes text..."
    }
  ],
  "sources": ["List of data sources"]
}
```

**Helper script template:**
See the repository's test scripts for examples of parsing Google Drive data into bundles.

## Manual Bundle Creation Scripts

You'll need to write a Python script to parse your downloaded CSV/text files and create a bundle JSON. Here's a template:

```python
import json
import csv
from pathlib import Path

def create_bundle(talks_csv, attendees_csv, notes_txt, track_name):
    """Create bundle from your data files."""
    
    # Parse lightning talks
    talks = []
    with open(talks_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Track") == track_name:  # Filter by track
                talks.append({
                    "title": row["Title"],
                    "authors": [{"name": row["Author"], "affiliation": row["Institution"]}],
                    "abstract": row["Abstract"]
                })
    
    # Parse attendees
    attendees = []
    with open(attendees_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            attendees.append({
                "name": f"{row['First']} {row['Last']}",
                "organization": row["Organization"]
            })
    
    # Add talk authors to attendees
    attendee_names = {a["name"] for a in attendees}
    for talk in talks:
        for author in talk["authors"]:
            if author["name"] not in attendee_names:
                attendees.append({
                    "name": author["name"],
                    "organization": author["affiliation"]
                })
                attendee_names.add(author["name"])
    
    # Read notes
    with open(notes_txt) as f:
        notes = f.read()
    
    # Create bundle
    bundle = {
        "track": {"id": "track-1", "name": track_name, "room": "TBD"},
        "sessions": [{
            "id": "session-1",
            "title": f"{track_name} Session",
            "slot": "2025-07-30T09:00",
            "leaders": [],
            "lightning_talks": talks,
            "attendees": attendees,
            "notes": notes
        }],
        "sources": [talks_csv, attendees_csv, notes_txt]
    }
    
    # Save bundle
    Path("data/bundles").mkdir(parents=True, exist_ok=True)
    output = "data/bundles/track_bundle.json"
    with open(output, "w") as f:
        json.dump(bundle, f, indent=2)
    
    return output

# Usage
create_bundle(
    "data/lightning_talks.csv",
    "data/attendees.csv", 
    "data/notes.txt",
    "Track-1"
)
```

## Command Line Options

### Generate Report from Bundle
```bash
python3 -m tpc_reporter.cli run BUNDLE_FILE.json [OPTIONS]

Options:
  -o, --output PATH         Output file for final report
  --draft-output PATH       Save draft before checking
  --max-tokens INTEGER      Maximum tokens for generation (default: 8000)
  --endpoint TEXT           Override LLM endpoint from config
  --skip-check             Skip hallucination checking
```

### Generate Without Checking
```bash
python3 -m tpc_reporter.cli generate BUNDLE_FILE.json -o draft.md
```

### Check Existing Draft
```bash
python3 -m tpc_reporter.cli check draft.md BUNDLE_FILE.json -o final.md
```

## Complete Example Workflow

Here's the full process:

```bash
# 1. Download Google Drive files
python3 -c '
from tpc_reporter.gdrive import download_sheet, download_doc
import os
os.makedirs("data/track1", exist_ok=True)
download_sheet("YOUR_TALKS_URL", "data/track1/talks.csv")
download_sheet("YOUR_ATTENDEES_URL", "data/track1/attendees.csv")
download_doc("YOUR_NOTES_URL", "data/track1/notes.txt")
'

# 2. Create bundle using the template code above
# Save it as create_my_bundle.py and run:
python3 create_my_bundle.py
# Output: data/bundles/track_bundle.json

# 3. Generate report
python3 -m tpc_reporter.cli run data/bundles/track_bundle.json -o output/track_report.md

# 4. Review the report
cat output/track_report.md
```

## Google Drive Setup

### Required Google Drive Files

You need three publicly shared files per track:

1. **Lightning Talks Sheet** - Columns:
   - Timestamp
   - Email Address
   - Your full name
   - Your institution  
   - Your job title or position in your institution
   - Title of your proposed lightning talk
   - Abstract of your proposed lightning talk (80-100 words)
   - Track (e.g., "Track-1", "Track-2")

2. **Attendees Sheet** - Columns:
   - First
   - Last
   - Organization

3. **Notes Document** - Free-form text with:
   - Key discussion points
   - Questions raised
   - Action items / outcomes
   - Decisions made

### Make Files Public

For each file:
1. Right-click → Share
2. Change to "Anyone with the link can view"
3. Copy the share URL

## Outputs

```
output/tpc25/
  ├── workflows.md          # Draft report for Workflows track
  ├── initiatives.md        # Draft report for Initiatives track
  ├── life_sciences.md
  ├── evaluation.md
  ├── scale_services.md
  └── applications.md
```

Each report contains `[FLAG: ...]` annotations where the hallucination checker found potential issues. Track organizers review and finalize these drafts.

## Configuration Files

### configuration.yaml

Edit `configuration.yaml` in the project root to set your LLM endpoint. Here we are using OpenAI as an example.  The OPENAI_API_KEY will need to be in your secrets.yaml file.  If you are using a local model the example here is for a NVIDIA/Dell Spark using NIM to serve a llama series model.

### CSV Schema Configuration

The tool uses configurable CSV column mappings to parse your data. The repository includes test data with specific column formats. **If your CSV files use different column names or structures, you must update the `csv_schema` section in `configuration.yaml`**.

```yaml
data_sources:
  csv_schema:
    lightning_talks:
      title: "Title of your proposed lightning talk"  # Column name (string)
      author: "Your full name"  # Column name (string)
      abstract: "Abstract of your proposed lightning talk (80-100 words)"  # Column name
      track: "Track"  # Column name
    attendees:
      name: 0  # Column index (integer, 0-based)
      institution: 1  # Column index (integer)
```

**Key points:**
- **Lightning talks**: Use exact column name strings from your Google Form or CSV headers
- **Attendees**: Can use column indices (integers) for simple 2-column spreadsheets, or column names (strings) for named headers
- **Column indices are 0-based**: First column is 0, second is 1, etc.

If you're using the included test URLs, these mappings are already configured correctly. If you're using your own data:

1. Download your CSV file or view it in Google Sheets
2. Check the exact column header names
3. Update the `csv_schema` section in `configuration.yaml` to match your headers

**Example for different column names:**
```yaml
csv_schema:
  lightning_talks:
    title: "Talk Title"  # Your CSV uses "Talk Title" instead
    author: "Speaker Name"  # Your CSV uses "Speaker Name"
    abstract: "Description"  # Your CSV uses "Description"
    track: "Session Track"  # Your CSV uses "Session Track"
  attendees:
    name: "Full Name"  # Using column name instead of index
    institution: "Company"  # Your CSV uses "Company"
```

```yaml
active_endpoint: "openai"  

endpoints:
  openai:
    type: "openai"
    base_url: "https://api.openai.com/v1"
    model: "gpt-4o-mini"
    api_key_env: "OPENAI_API_KEY"  
    parameters:
      temperature: 0.3
      max_tokens: 4000
      
  nim_spark:
    type: "nim_ssh"
    ssh_host: "your-nim-host"  
    base_url: "http://localhost:8000/v1"
    model: "meta/llama-3.1-8b-instruct"
    parameters:
      temperature: 0.3
      max_tokens: 3000  # Smaller for 8B models
```

### secrets.yaml

Create `secrets.yaml` in the project root:

```yaml
# OpenAI API Key
OPENAI_API_KEY: "sk-your-key-here"
```

**Note**: `secrets.yaml` is gitignored and never committed.

## Architecture

No frameworks. Just Python functions:

| Module | What it does |
|--------|-------------|
| `scraper.py` | Parses TPC website HTML → `conference.json` |
| `gdrive.py` | Downloads Google Sheets/Docs → CSV and text files |
| `assembler.py` | Merges website data + Drive data → `track_bundle.json` |
| `generator.py` | Calls LLM with master prompt + track bundle → draft Markdown |
| `checker.py` | Second LLM pass to flag hallucinations |
| `llm_client.py` | Unified interface for OpenAI-compatible APIs |
| `cli.py` | Command-line interface |

## Development

See [PLAN.md](./PLAN.md) for the hackathon implementation plan and [ANALYSIS.md](./ANALYSIS.md) for architectural decisions.

To run tests and generate a single conference track report for development
```bash
# Run tests
pytest tests/
python -m tpc_reporter.generator --bundle data/tpc25/bundles/workflows.json --output output/tpc25/workflows_draft.md
```

## Troubleshooting

### "Configuration file not found"

Make sure `configuration.yaml` and `secrets.yaml` exist in the project root:
```bash
ls -la configuration.yaml secrets.yaml
```

### "OPENAI_API_KEY not found"

Either:
1. Add to `secrets.yaml`: `OPENAI_API_KEY: "sk-..."`
2. Or export as environment variable: `export OPENAI_API_KEY="sk-..."`

### "NIM request timed out"

Local NIM models (especially 8B) are slower. Either:
1. Reduce `max_tokens` in config (e.g., 2000)
2. Use OpenAI for faster generation
3. Process fewer talks at once

### "max_tokens too large" with NIM

Llama 3.1 8B has 8192 total context. If your input is 4000 tokens, max_tokens must be < 4192.
Reduce in `configuration.yaml`:
```yaml
max_tokens: 3000  # Leave room for input
```

### Google Drive downloads fail

Make sure files are publicly shared:
1. Right-click file → Share
2. Set to "Anyone with the link can view"
3. Use the share URL (not the browser URL)

## Future: Agentic Mode (Phase 2)

The pipeline functions become tools for an LLM agent:

```
User: "Generate the Workflows track report for TPC26. 
       Website: tpc26.org, Drive folder: [URL]"

Agent: [calls scrape_website] → [calls collect_drive] → [calls assemble] → [calls generate] → [calls check]
       → "Here's your draft report. I flagged 2 potential issues for review."
```
