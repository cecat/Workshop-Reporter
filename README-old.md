# TPC Workshop Reporter (Agentic Meeting Summaries)

A **workflow-based reporting system** for the Trillion Parameter Consortium (TPC), using LangGraph for orchestration.

It ingests TPC meeting materials (session rosters + notes + slide decks + docs) and produces:
- **Per-session summaries** (consistent structure)
- **A full meeting report** (roll-up)
- **A QA scorecard** + **review queue** (so humans can quickly fix what the system is unsure about)

This is designed for the TPC Executive Director to issue requests like:
- "Pull reports together for breakouts A, B, and C."
- "Create a summary of plenary X."
- "Generate the full post-meeting report for TPC25."

> **Important scope note (Hackathon MVP)**: we do **not** promise claim-level provenance ("every claim is traceable to a line/slide"). Instead, each summary includes a **Sources Used** list and the QA agent flags likely unsupported content for review. Note: Selective generation (e.g. "Breakouts A/B only") is a stretch goal; the MVP defaults to full report generation for stability.

## Built on Prior Work

This implementation incorporates tested components from an earlier TPC-Session-Reporter prototype:
- **Tested LLM prompt** for session summaries (`config/prompts/tpc25_master_prompt.yaml`)
- **Session matching logic** (flexible acronym and keyword matching)
- **Data pipeline** (Google Sheets/Docs integration, HTML parsing)
- **Hybrid approach** (Python for structured data, LLM for narrative)

See `reference/tpc-session-reporter/` for details on what was preserved and why.

---

## Hackathon Timeline

**March 31 (2-4 hours)**: Kickoff session via Zoom
- Team introductions and role assignments
- Repository walkthrough
- Environment setup verification
- Task assignment for first sprint

**April 1-6**: Independent async work (encouraged)
- Small, parallelizable tasks
- Communication via Slack/Discord + GitHub issues

**April 7 (6-8 hours)**: Remote sprint day
- Open Zoom room for coordination
- Core pipeline implementation
- Check-ins at start, midday, end

**April 8-13**: Independent async work (encouraged)
- Bug fixes and testing
- Documentation improvements
- Stretch features

**April 14-16 (3 days × 8 hours)**: In-person hackathon
- Integration and end-to-end testing
- Real TPC25 data validation
- Polish and demo preparation

**Team size**: 4-8 developers (mixed skill levels, all proficient in Python + GitHub)

See [PLAN.md](./PLAN.md) for detailed task breakdown and [COORDINATION.md](./COORDINATION.md) for organizational guidance.

---

## Strategy

### LangGraph Workflow Orchestration
The system is implemented as a **stateful workflow graph** using LangGraph:
- **State machine**: Deterministic phase boundaries (INGEST → MATCH → SUMMARIZE → EVALUATE → PUBLISH)
- **Nodes**: Specialized functions for each processing step
- **Edges**: Conditional routing with review gates
- **Persistence**: Checkpointing for resume capability
- **Human-in-the-loop**: Review gates for low-confidence decisions

LangGraph provides:
- Proven workflow orchestration for LLM applications
- Built-in state persistence and checkpointing
- Conditional edges for branching logic (review gates)
- Streaming and async support
- Simple Python API (no complex distributed systems)
- Wide adoption and good documentation

### Why PPTX (not PDF) for slide decks
For the MVP we **support `.pptx`** and **do not support PDF**.

Reason: PPTX is a structured, editable format (Office Open XML) with straightforward text extraction, while PDFs are layout-oriented and typically require more complex heuristics to extract usable text. If your source materials are PDFs, convert to PPTX (or provide notes) for best results.

### No web scraping in MVP
The TPC25 website blocks robots, so the MVP expects **pre-downloaded materials** organized into a local folder structure. The organizer will prepare this dataset before the hackathon.

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

### LangGraph Workflow Nodes
Each node is a Python function that processes state and returns updated state.

**Workflow State:**
```python
class WorkflowState(TypedDict):
    run_id: str
    event: Event
    sessions: List[Session]
    artifacts: List[Artifact]
    matches: List[Match]
    summaries: Dict[str, ReportSection]
    qa_results: Dict[str, QAResult]
    phase: str  # Current phase
    needs_review: bool
```

**Workflow Nodes:**

- **ingest_node**
  - Parses session roster from JSON/CSV/HTML
  - Produces canonical `Event` + `Session` objects
  - Inventories files from configured folders
  - Extracts text from supported formats
  - Uses tested extraction logic from TPC-Session-Reporter

- **match_node**
  - Links artifacts to sessions (filename heuristics + fuzzy matching)
  - Produces `Match` objects with confidence
  - Uses tested `session_matches()` logic from TPC-Session-Reporter
  - **Conditional edge**: Routes to `review_gate` if confidence < threshold

- **summarize_node**
  - Produces structured summaries using tested prompt
  - Uses `config/prompts/tpc25_master_prompt.yaml`
  - Adds "Sources Used" (file list)
  - Hybrid approach: Python generates appendices, LLM generates discussion/outcomes
  - Avoids introducing information not present in sources

- **evaluate_node**
  - Scores summaries (coverage, faithfulness, specificity, actionability)
  - Runs deterministic checks (missing sections, session coverage)
  - **Conditional edge**: Routes to `review_gate` if QA flags issues

- **publish_node**
  - Assembles the full meeting report
  - Generates per-session Markdown files
  - Exports review queue when needed

- **review_gate** (conditional)
  - Exports files to `review_queue/` for human editing
  - Workflow pauses until `resume` command
  - Human edits are loaded and workflow continues

---

## Repository Layout

```
workshop-reporter/
├── tpc_reporter/
│   ├── workflow.py          # LangGraph workflow definition
│   ├── nodes/               # Workflow node functions
│   │   ├── ingest.py        # Ingestion + extraction
│   │   ├── match.py         # Session matching (uses TPC-Session-Reporter logic)
│   │   ├── summarize.py     # LLM summary generation (uses tested prompt)
│   │   ├── evaluate.py      # QA checks
│   │   └── publish.py       # Report assembly (uses tested appendix logic)
│   ├── schemas/
│   │   ├── event.py         # Event, Session models
│   │   ├── artifact.py      # Artifact model
│   │   ├── match.py         # Match model with evidence
│   │   ├── report.py        # ReportSection, QAResult
│   │   └── state.py         # WorkflowState (LangGraph)
│   ├── tools/
│   │   ├── extractors.py    # Text extraction (.md, .txt, .csv, .docx, .pptx)
│   │   ├── matching.py      # Tested session_matches() from TPC-Session-Reporter
│   │   └── web_fetch.py     # URL download with Google Sheets/Docs support
│   ├── prompts/
│   │   └── summarizer.yaml  # Tested prompt from TPC-Session-Reporter
│   └── cli.py               # Command-line interface
├── config/
│   ├── events/
│   │   └── tpc25.yaml       # Event configuration
│   └── templates/           # Report templates
├── reference/
│   └── tpc-session-reporter/  # Preserved prototype code
├── data/                    # Local input files (TPC25 materials)
├── runs/                    # Job outputs with checkpoints
├── tests/
│   ├── fixtures/
│   │   └── tpc24_mini/      # Test data
│   ├── test_workflow.py
│   ├── test_nodes.py
│   └── test_tools.py
└── README.md
```

---

## Quickstart

### 1) Install

```bash
# Create conda environment (recommended)
conda create -n workshop-reporter python=3.11
conda activate workshop-reporter

# Install dependencies
pip install -e .
```

This installs:
- `langgraph` - Workflow orchestration
- `langchain` - LLM integration
- `pydantic` - Data validation
- `python-docx`, `python-pptx` - Document parsing
- Other dependencies from `pyproject.toml`

### 2) Configure LLM endpoint

Workshop-Reporter uses a YAML-based configuration system for LLM endpoints.

**Quick setup:**
```bash
# Copy secrets template
cp secrets.yaml.template secrets.yaml

# Edit secrets.yaml and add your OpenAI API key (if using OpenAI)
# OR leave it empty if using NIM on spark-ts (no API key needed)
```

**Configure your endpoint in `configuration.yaml`:**
```yaml
# Choose one: "openai" or "nim_spark"
active_endpoint: "nim_spark"
```

**Available endpoints:**
- **OpenAI** (`active_endpoint: "openai"`)
  - Uses OpenAI API (gpt-4o-mini by default)
  - Requires `OPENAI_API_KEY` in secrets.yaml
  - Cost: ~$0.15-0.60 per 1M tokens

- **NIM on spark-ts** (`active_endpoint: "nim_spark"`)
  - Uses NVIDIA NIM (Llama 3.1 8B) via SSH
  - No API key required
  - Free (uses your hardware)
  - Requires SSH access to spark-ts

See [CONFIG_README.md](./CONFIG_README.md) for detailed configuration options and how to add new endpoints.

**Alternative: Environment variables (legacy)**
```bash
export OPENAI_API_KEY=...
# This still works but configuration.yaml is recommended
```

### 3) Verify installation

```bash
python -c "from langgraph.graph import StateGraph; print('✅ LangGraph installed')"
python -c "from tpc_reporter.workflow import create_workflow; print('✅ TPC Reporter ready')"
```

### 4) Configure an event

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

### 5) Run

**One-shot run** (recommended):
```bash
tpc_reporter run --config config/events/tpc25.yaml
```

The workflow will:
1. **Ingest**: Parse session roster and extract text from artifacts
2. **Match**: Link artifacts to sessions using tested matching logic
3. **Summarize**: Generate session summaries using tested prompt
4. **Evaluate**: Run QA checks on summaries
5. **Publish**: Assemble full meeting report

**Resume after human review**:

If the workflow pauses for review (low-confidence matches or QA flags):
```bash
# Edit files in runs/<run_id>/review_queue/
# Then resume:
tpc_reporter resume --run runs/<run_id>/
```

**Step-by-step execution** (useful for debugging):
```bash
RUN_DIR=$(tpc_reporter ingest --config config/events/tpc25.yaml)

tpc_reporter match --run "$RUN_DIR"
tpc_reporter summarize --run "$RUN_DIR"
tpc_reporter evaluate --run "$RUN_DIR"
tpc_reporter publish --run "$RUN_DIR"
```

**Inspect workflow state**:
```bash
tpc_reporter status --run runs/<run_id>/
```

---

## Human Review Workflow

The system generates review artifacts when confidence is low.

### After matching
If any match is below the threshold, you'll get:
- `review_queue/matches.json` (edit to approve/override)

### After QA
If QA flags issues, you'll get:
- `review_queue/<session_id>_draft.md` (edit the draft)

Then run:
```bash
tpc_reporter resume --run runs/<run_id>/
```

---

## Hackathon MVP: Definition of Done

The hackathon deliverable is a **repeatable pipeline** that works on **real TPC25 data**:
- ✅ Ingests session roster and artifacts from local folder
- ✅ Matches artifacts to sessions with confidence scores
- ✅ Generates per-session summaries with "Sources Used" lists
- ✅ Produces full meeting report (`report.md`)
- ✅ Runs QA scoring and flags low-confidence summaries
- ✅ Exports review queue for human editing
- ✅ Passes end-to-end test on TPC25 fixture
- ✅ Documentation for running and extending

**What's explicitly out of scope for MVP:**
- ❌ PDF support (convert to PPTX or notes)
- ❌ Web scraping (materials pre-downloaded)
- ❌ Claim-level provenance (only file-level "Sources Used")
- ❌ Selective session generation (MVP does full report)
- ❌ Embedding-based semantic matching (MVP uses rule-based matching from TPC-Session-Reporter)
- ❌ Real-time collaboration features

---

## Post-Hackathon Enhancements

### Phase 2: Production Features
- PDF support (best-effort text layer only)
- Embedding-based semantic matching (vector similarity for better confidence)
- Streamlit review UI (replace file-based review queue)
- Stronger grounding (optional citations and evidence excerpts)
- Selective session report generation
- Google Drive integration (real-time monitoring)

### Phase 3: Advanced Features
- Multi-workshop corpus with cross-event retrieval
- Continuous learning from review corrections
- Automated slide-to-talk matching using computer vision
- Speaker identification and tracking across events

### Phase 4: Integration
- HTML agenda scraping from common conference platforms
- Google Sheets/Docs connectors for collaborative editing
- Webhook notifications for workflow completion
- API for programmatic access
