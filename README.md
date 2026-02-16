# TPC Workshop Reporter

Generate draft track reports for TPC conferences from website data, scribe notes, and attendee lists.

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

```bash
pip install -e .
```

### 2. Configure

```bash
cp config/secrets.yaml.template config/secrets.yaml
# Add your OpenAI API key to secrets.yaml
```

### 3. Scrape the conference website

```bash
tpc_reporter scrape --url https://tpc25.org/sessions/ --output data/tpc25/conference.json
```

### 4. Collect Google Drive data

```bash
tpc_reporter collect --drive-folder "https://drive.google.com/drive/folders/..." --output data/tpc25/track_inputs/
```

### 5. Generate all reports

```bash
tpc_reporter generate-all --conference data/tpc25/conference.json --inputs data/tpc25/track_inputs/ --output output/tpc25/
```

Or generate a single track:

```bash
tpc_reporter generate --track workflows --conference data/tpc25/conference.json --inputs data/tpc25/track_inputs/ --output output/tpc25/
```

## Google Drive Setup

Create one shared folder per track:

```
TPC25 Track Reports/
  ├── Workflows/
  │   ├── Session1_Attendees    (Google Sheet)
  │   ├── Session1_Notes        (Google Doc)
  │   ├── Session2_Attendees    (Google Sheet)
  │   └── Session2_Notes        (Google Doc)
  ├── Initiatives/
  │   └── ...
  └── ...
```

**Attendees sheets**: Two columns — `Name` and `Organization`

**Notes docs**: Free-form text from session scribes. Suggested structure:
- Key discussion points
- Questions raised
- Action items / outcomes

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

## Configuration

Edit `config/configuration.yaml` to set your LLM endpoint:

```yaml
active_endpoint: "openai"   # or "nim_spark" for local NVIDIA NIM

endpoints:
  openai:
    model: "gpt-4o-mini"
    api_key_env: "OPENAI_API_KEY"
    parameters:
      temperature: 0.3
      max_tokens: 4000
```

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

```bash
# Run tests
pytest tests/

# Generate a single track report for development
python -m tpc_reporter.generator --bundle data/tpc25/bundles/workflows.json --output output/tpc25/workflows_draft.md
```

## Future: Agentic Mode (Phase 2)

The pipeline functions become tools for an LLM agent:

```
User: "Generate the Workflows track report for TPC26. 
       Website: tpc26.org, Drive folder: [URL]"

Agent: [calls scrape_website] → [calls collect_drive] → [calls assemble] → [calls generate] → [calls check]
       → "Here's your draft report. I flagged 2 potential issues for review."
```
