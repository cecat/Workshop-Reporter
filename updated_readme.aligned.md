# TPC Workshop Reporter (Agentic Meeting Summaries)

A **workflow-first, multi-agent reporting assistant** for the Trillion Parameter Consortium (TPC).

It ingests TPC meeting materials (session rosters + notes + slide decks + docs) and produces:
- **Per-session summaries** (consistent structure)
- A **full meeting report** (roll-up)
- A **QA scorecard** + **review queue** (so humans can quickly fix what the system is unsure about)

This is designed for the TPC Executive Director to issue requests like:
- “Pull reports together for breakouts A, B, and C.”
- “Create a summary of plenary X.”
- “Generate the full post-meeting report for TPC25.”

> **Important scope note (Hackathon MVP)**: we do **not** promise claim-level provenance ("every claim is traceable to a line/slide"). Instead, each summary includes a **Sources Used** list and the QA agent flags likely unsupported content for review. Note: Selective generation (e.g. "Breakouts A/B only") is a stretch goal; the MVP defaults to full report generation for stability.

---

## Strategy

### Workflow-first orchestration (recommended)
For reliability and reproducibility, the system is implemented as a **stateful workflow**:
- deterministic phase boundaries
- persisted run state
- explicit review gates

A “multi-agent chat” style is optional and can be added later for drafting or rewriting, but the **runtime** is a workflow.

### Why PPTX (not PDF) for slide decks
For the MVP we **support `.pptx`** and **do not support PDF**.

Reason: PPTX is a structured, editable format (Office Open XML) with straightforward text extraction, while PDFs are layout-oriented and typically require more complex heuristics to extract usable text. If your source materials are PDFs, convert to PPTX (or provide notes) for best results.

---

## What It Does

### Inputs
**Session roster** (required):
- `sessions.json` (preferred) or `schedule.csv`

**Artifacts** (required):
- Notes: `.md`, `.txt`
- Docs: `.docx`
- Slides: `.pptx`
- Tables: `.csv`

### Outputs
Per run directory `runs/<run_id>/`:
- `sessions/<session_id>.md` – per-session summary
- `report.md` – full meeting report
- `qa_scorecard.json` – QA scores + flags (per session)
- `review_queue/` – files for humans to edit (low-confidence matches or flagged drafts)
- `state.json` – persisted workflow state (inputs + matches + outputs)

---

## Architecture Overview

### Roles
- **Director (Orchestrator)**
  - Parses the user request (e.g., “breakouts A/B/C”)
  - Selects the workflow
  - Manages phase execution, retries, budgets, and review gates

- **Ingestion**
  - Parses session roster from JSON/CSV
  - Produces canonical `Event` + `Session` objects

- **Artifact Collector**
  - Inventories files from configured folders
  - Extracts text from supported formats

- **Matcher**
  - Links artifacts to sessions (filename heuristics + fuzzy matching)
  - Produces `Match` objects with confidence

- **Summarizer (Scientific Writer)**
  - Produces structured summaries in a consistent template
  - Adds “Sources Used” (file list)
  - Avoids introducing information not present in sources

- **Evaluator (Scientific Critic / QA)**
  - Scores summaries (coverage, faithfulness, specificity, actionability)
  - Runs deterministic checks (missing sections, session coverage, suspicious claims)
  - Triggers review gates when needed

- **Publisher**
  - Assembles the full meeting report

---

## Repository Layout

```
workshop-reporter/
├── tpc_reporter/
│   ├── orchestrator/      # Director + workflow runner
│   ├── agents/            # ingest, collect, match, summarize, evaluate, publish
│   ├── tools/             # file parsers, text extractors
│   ├── schemas/           # Pydantic models
│   ├── prompts/           # summarizer + evaluator templates
│   └── storage/           # run state load/save
├── config/
│   ├── events/            # event YAML configs
│   └── templates/         # report templates
├── data/                  # local input files
├── runs/                  # outputs
├── tests/
│   └── fixtures/
└── README.md
```

---

## Quickstart

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

Set your LLM provider key:
```bash
export OPENAI_API_KEY=...
# or ANTHROPIC_API_KEY=...
```

### 2) Configure an event

Create `config/events/tpc25.yaml`:

```yaml
event:
  id: tpc25
  name: "TPC25 Annual Meeting"
  dates: "2025-03-15 to 2025-03-17"
  timezone: "America/Chicago"

sources:
  sessions:
    type: json
    path: data/tpc25/sessions.json

  artifacts:
    type: folder
    path: data/tpc25/artifacts/

outputs:
  run_dir: runs/
  formats: [markdown]
```

### 3) Run

**One-shot run** (recommended):
```bash
tpc_reporter run --config config/events/tpc25.yaml \
  --request "Generate the post-meeting report for TPC25"
```

**Step-by-step** (useful for debugging):
```bash
RUN_DIR=$(tpc_reporter ingest --config config/events/tpc25.yaml)

tpc_reporter match --run "$RUN_DIR"
tpc_reporter summarize --run "$RUN_DIR"
tpc_reporter evaluate --run "$RUN_DIR"
tpc_reporter publish --run "$RUN_DIR"
```

**Resume after review**:
```bash
tpc_reporter resume --run runs/<run_id>/
```

---

## Human Review Workflow

The system generates review artifacts when confidence is low.

### After matching
If any match is below the threshold, you’ll get:
- `review_queue/matches.json` (edit to approve/override)

### After QA
If QA flags issues, you’ll get:
- `review_queue/<session_id>_draft.md` (edit the draft)

Then run:
```bash
tpc_reporter resume --run runs/<run_id>/
```

---

## Hackathon MVP: Definition of Done

The hackathon deliverable is a **repeatable pipeline** that can run on a small fixture:
- produces `report.md` + per-session markdown
- produces `qa_scorecard.json`
- exports a review queue when uncertain
- passes an end-to-end test (`pytest`) on the fixture

---

## Post-Hackathon Enhancements

- PDF support (best-effort text layer only)
- HTML agenda scraping
- Google Drive/Sheets connectors
- Embedding-based matching and cross-event retrieval
- Review UI (Streamlit)
- Stronger grounding (optional citations and evidence excerpts)

