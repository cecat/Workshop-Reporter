# Implementation Plan: TPC Workshop Reporter (Simplified)
## Hackathon Edition

**Team**: 4-6 developers (Python proficient)  
**Goal**: Generate 8 draft track reports from TPC25 data, ready for human review  
**Architecture**: Simple Python pipeline (no framework dependencies)

---

## What We're Building

A pipeline that:
1. **Scrapes** the TPC website to get the conference structure (tracks, sessions, lightning talks)
2. **Collects** notes and attendees from Google Drive (one folder per track)
3. **Assembles** a data bundle per track (website data + Drive data)
4. **Generates** a draft report per track using an LLM
5. **Checks** each draft for hallucinations using a second LLM pass
6. **Outputs** 8 Markdown reports for human review

### What It Does NOT Do (MVP Scope)
- No LangGraph, no workflow framework
- No PDF/PPTX parsing (lightning talks come from the website, notes from Google Docs)
- No embedding-based matching (we have structured data)
- No real-time collaboration
- No automated retry/recovery (just re-run)

---

## Data Flow

```
tpc25.org/sessions/ ──scrape──→ conference.json
                                      │
Google Drive folders ──collect──→ track_inputs/
                                      │
                              ┌───assemble───┐
                              │              │
                        track_bundle_1.json ... track_bundle_8.json
                              │              │
                        ┌──generate──┐  ┌──generate──┐
                        │            │  │            │
                  draft_1.md    draft_2.md  ...  draft_8.md
                        │            │
                  ┌──check──┐  ┌──check──┐
                  │         │  │         │
            report_1.md  report_2.md  ...  report_8.md
                  │
            (human review)
```

---

## Data Model

### Conference Structure (from website)

```json
{
  "conference": {
    "id": "tpc25",
    "name": "TPC25",
    "website": "https://tpc25.org"
  },
  "tracks": [
    {
      "id": "workflows",
      "name": "Workflows",
      "room": "Main Plenary",
      "sessions": [
        {
          "id": "dwarf-1",
          "title": "DWARF: Keynote and Systems Software for Agents",
          "parent_workshop": "Data Workflows, Agents, and Reasoning Frameworks (DWARF)",
          "slot": "2025-07-30T16:00",
          "duration_minutes": 90,
          "leaders": [
            {"name": "Ian Foster", "affiliation": "Argonne National Laboratory"}
          ],
          "lightning_talks": [
            {
              "title": "Academy: Empowering Scientific Workflows with Federated Agents",
              "authors": [{"name": "Kyle Chard", "affiliation": "University of Chicago"}],
              "abstract": "..."
            }
          ]
        }
      ]
    }
  ]
}
```

### Google Drive Layout (one folder per track)

```
TPC25 Track Reports/
  ├── Workflows/
  │   ├── Session1_Attendees    (Google Sheet: Name, Organization columns)
  │   ├── Session1_Notes        (Google Doc: free-form scribe notes)
  │   ├── Session2_Attendees
  │   ├── Session2_Notes
  │   └── ...
  ├── Initiatives/
  │   └── ...
  └── ... (8 folders total for TPC26)
```

### Track Bundle (assembled per track, fed to LLM)

```json
{
  "track": {"id": "workflows", "name": "Workflows"},
  "sessions": [
    {
      "id": "dwarf-1",
      "title": "DWARF: Keynote and Systems Software for Agents",
      "slot": "2025-07-30T16:00",
      "leaders": ["Ian Foster (ANL)", "Neeraj Kumar (PNNL)"],
      "lightning_talks": ["... from website ..."],
      "attendees": ["... from Google Sheet ..."],
      "notes": "... from Google Doc ..."
    }
  ],
  "sources": ["tpc25.org/sessions/", "Drive: Workflows/Session1_Notes", "..."]
}
```

---

## Repository Structure

```
workshop-reporter/
├── tpc_reporter/
│   ├── __init__.py
│   ├── scraper.py          # Parse TPC website → conference.json
│   ├── gdrive.py           # Collect Google Drive data → track_inputs/
│   ├── assembler.py         # Merge website + Drive → track_bundle.json
│   ├── generator.py         # LLM report generation
│   ├── checker.py           # Hallucination check (second LLM pass)
│   ├── llm_client.py        # Unified LLM interface (OpenAI-compatible)
│   └── cli.py               # Command-line interface
├── prompts/
│   └── tpc_master_prompt_v2.yaml
├── config/
│   ├── configuration.yaml   # LLM endpoint config
│   └── secrets.yaml.template
├── data/                    # Scraped/collected input data
│   └── tpc25/
│       ├── conference.json
│       └── track_inputs/
├── output/                  # Generated reports
│   └── tpc25/
│       ├── workflows.md
│       ├── initiatives.md
│       └── ...
├── tests/
│   ├── test_scraper.py
│   ├── test_assembler.py
│   └── fixtures/
│       └── sample_track_bundle.json
├── ANALYSIS.md
├── PLAN.md
├── README.md
└── pyproject.toml
```

---

## Implementation Steps

### Step 1: Website Scraper (`scraper.py`)
**Effort**: 3-4 hours | **Owner**: Data person  
**Dependencies**: `beautifulsoup4`, `requests`

Parse the TPC sessions page and extract:
- Track names and rooms
- Session titles, times, leaders
- Lightning talk titles, authors, affiliations, abstracts
- Session descriptions

Output: `data/tpc25/conference.json`

**Key challenge**: The TPC25 sessions page is a single long HTML page with sections per track. The scraper needs to correctly identify track boundaries and session-within-track boundaries. The HTML uses headings (h2 for tracks, h3/h4 for sessions) which makes this tractable.

**Test**: Verify all 6 tracks, ~30 sessions, ~120 lightning talks are captured with correct track/session associations.

```bash
python -m tpc_reporter.scraper --url https://tpc25.org/sessions/ --output data/tpc25/conference.json
```

### Step 2: Google Drive Collector (`gdrive.py`)
**Effort**: 2-3 hours | **Owner**: Data person  
**Dependencies**: `google-api-python-client` or simple URL export

Two approaches (team picks one):
1. **Google API** (robust): Use Google Drive/Sheets/Docs API with service account
2. **Export URLs** (simpler): Use public sharing + export links
   - Sheets: `https://docs.google.com/spreadsheets/d/{ID}/export?format=csv`
   - Docs: `https://docs.google.com/document/d/{ID}/export?format=txt`

Output: `data/tpc25/track_inputs/{track_id}/session{N}_attendees.csv` and `session{N}_notes.txt`

**Test**: Create a sample Google Drive folder with one track's data, verify extraction.

```bash
python -m tpc_reporter.gdrive --folder-url "https://drive.google.com/..." --output data/tpc25/track_inputs/
```

### Step 3: Data Assembler (`assembler.py`)
**Effort**: 1-2 hours | **Owner**: Anyone  

Merge `conference.json` with `track_inputs/` to create one `track_bundle.json` per track.

Logic:
- Match Google Drive files to sessions by filename convention or folder structure
- Handle missing data: if no notes for a session, set `notes: null`
- Validate: warn if a session has no notes AND no attendees

```bash
python -m tpc_reporter.assembler --conference data/tpc25/conference.json --inputs data/tpc25/track_inputs/ --output data/tpc25/bundles/
```

### Step 4: Report Generator (`generator.py`)
**Effort**: 2-3 hours | **Owner**: LLM person  

Load the master prompt + track bundle, call the LLM, save the output.

**Context window consideration**: A full track bundle (5 sessions × ~6 lightning talks with abstracts + notes) could be 15-30K tokens of input. GPT-4o-mini handles 128K context, so this is fine. For very large tracks, consider:
- Sending lightning talk abstracts in a condensed format (title + author + first sentence)
- Generating the appendix (full abstracts) separately from the narrative

```bash
python -m tpc_reporter.generator --bundle data/tpc25/bundles/workflows.json --output output/tpc25/workflows_draft.md
```

### Step 5: Hallucination Checker (`checker.py`)
**Effort**: 1-2 hours | **Owner**: LLM person  

Second LLM pass that compares the draft against source data and flags:
- Names/organizations not in source data
- Specific claims not supported by notes
- Lightning talks that appear fabricated

Output: The draft with inline `[FLAG: ...]` annotations, plus a summary of flags.

```bash
python -m tpc_reporter.checker --draft output/tpc25/workflows_draft.md --bundle data/tpc25/bundles/workflows.json --output output/tpc25/workflows.md
```

### Step 6: CLI & Orchestration (`cli.py`)
**Effort**: 1-2 hours | **Owner**: Anyone  

Simple CLI that chains the steps:

```bash
# Full pipeline for all tracks
tpc_reporter run --config config/tpc25.yaml

# Individual steps
tpc_reporter scrape --url https://tpc25.org/sessions/
tpc_reporter collect --drive-folder <URL>
tpc_reporter generate --track workflows
tpc_reporter generate-all
tpc_reporter check --track workflows
```

---

## Hackathon Schedule

### Day 1: Data Pipeline (6-8 hours)
- **Morning**: Scraper (Step 1) — get conference.json working
- **Afternoon**: Google Drive collector (Step 2) + Assembler (Step 3)
- **End of day**: One complete track_bundle.json assembled from real data

### Day 2: Report Generation (6-8 hours)
- **Morning**: Generator (Step 4) — get one report working, iterate on prompt
- **Afternoon**: Checker (Step 5) + CLI (Step 6)
- **End of day**: One complete track report, end-to-end

### Day 3: Scale & Polish (6-8 hours)
- **Morning**: Run all 6 TPC25 tracks (or 8 for TPC26), fix issues
- **Afternoon**: Review outputs, tune prompt, documentation
- **End of day**: All reports generated, demo ready

---

## Team Roles

| Role | Focus | Steps |
|------|-------|-------|
| **Data Lead** | Scraping, Google Drive, data assembly | Steps 1-3 |
| **LLM Lead** | Prompt engineering, generation, checking | Steps 4-5 |
| **Integration Lead** | CLI, testing, documentation | Step 6 + testing |
| **Domain Expert** | Review outputs, validate quality | Quality review |

With 4 people, everyone picks a role. With 6+, pair up on the bigger steps.

---

## Dependencies

```toml
[project]
dependencies = [
    "beautifulsoup4>=4.12",
    "requests>=2.31",
    "openai>=1.0",
    "pyyaml>=6.0",
    "click>=8.0",        # CLI framework
]

[project.optional-dependencies]
google = [
    "google-api-python-client>=2.0",
    "google-auth>=2.0",
]
dev = [
    "pytest>=7.0",
]
```

---

## Definition of Done

- [ ] `conference.json` captures all TPC25 tracks, sessions, and lightning talks
- [ ] At least one track has complete input data (website + notes + attendees)
- [ ] Draft reports generated for all available tracks
- [ ] Hallucination checker runs and flags issues
- [ ] End-to-end pipeline runs with a single command
- [ ] Documentation explains how to set up and run
- [ ] At least one track report reviewed by a human and deemed "good draft"

---

## Post-Hackathon: Path to Agentic (Phase 2)

Once the pipeline works, making it agentic is wrapping each step as an LLM tool:

```python
tools = [
    {"name": "scrape_website", "fn": scraper.scrape, "description": "..."},
    {"name": "collect_drive", "fn": gdrive.collect, "description": "..."},
    {"name": "assemble_track", "fn": assembler.assemble, "description": "..."},
    {"name": "generate_report", "fn": generator.generate, "description": "..."},
    {"name": "check_report", "fn": checker.check, "description": "..."},
]

# User says: "Generate the Workflows track report for TPC26"
# LLM with tool-use decides which tools to call and in what order
```

This is where LangGraph or similar may add value for managing multi-step tool calling with error recovery. But the tools themselves are just the functions we built.
