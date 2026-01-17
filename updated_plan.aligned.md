# Implementation Plan: TPC Workshop Reporter
## 3-Day Hackathon Edition (workflow-first, multi-agent)

This plan is optimized for a 3–6 person team to build a **reliable, reproducible meeting-report pipeline** in 3 days.

> **Hackathon MVP scope**: We do **not** promise claim-level provenance or line/slide citations. Each summary includes a **Sources Used** list, and a QA agent flags likely unsupported/vague content for human review.

---

## 0) Decisions locked in (to avoid hackathon thrash)

### Runtime style
- **Workflow-first**: a stateful pipeline with explicit phases, persisted state, and review gates.
- Multi-agent chat is **out of scope** for the MVP.

### Supported file types (MVP)
- Notes: `.md`, `.txt`
- Docs: `.docx`
- Slides: `.pptx`
- Tables: `.csv`
- **PDF: not supported in MVP** (skip with warning). Convert PDFs to PPTX or provide notes.

### Config
- **YAML config is canonical** (`--config path/to/event.yaml`).

### CLI contract (canonical)
Commands and arguments are fixed for the MVP:
- `tpc_reporter ingest --config <event.yaml>` → prints/returns a run directory
- `tpc_reporter match --run <run_dir>`
- `tpc_reporter summarize --run <run_dir>`
- `tpc_reporter evaluate --run <run_dir>`
- `tpc_reporter publish --run <run_dir>`
- `tpc_reporter run --config <event.yaml> --request "..."` (wrapper that runs the phases)
- `tpc_reporter resume --run <run_dir>` (continues from next incomplete phase after review)

---

## 1) Team structure (recommended)

**Minimum (3 people):**
- Orchestrator/State/CLI
- Ingestion/Extraction/Matching
- Summarization/QA/Publishing

**Nice to have (+1–3):**
- QA/tests + fixtures
- Prompt/LLM integration
- DevOps/packaging

---

## 2) Pre-hackathon prep (solo, 2–4 hours)

### 2.1 Repo skeleton
Create folders:

```
tpc_reporter/
  orchestrator/
  agents/
  tools/
  schemas/
  prompts/
  storage/
config/
  events/
  templates/
tests/
  fixtures/
runs/
```

### 2.2 Schemas (Pydantic) — copy verbatim
Create these models in `tpc_reporter/schemas/`:

```python
# tpc_reporter/schemas/event.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class Event(BaseModel):
    id: str
    name: str
    dates: str  # e.g. "2025-03-15 to 2025-03-17"
    timezone: str = "America/Chicago"

class Session(BaseModel):
    id: str
    title: str
    type: str  # "plenary" | "breakout" | "lightning" | "other"
    leaders: List[str] = Field(default_factory=list)
    track: Optional[str] = None
    abstract: Optional[str] = None
    scheduled_time: Optional[str] = None
```

```python
# tpc_reporter/schemas/artifact.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

class Artifact(BaseModel):
    id: str
    path: str
    kind: str  # "md" | "txt" | "csv" | "docx" | "pptx"
    extracted_text: str
    sha256_12: str
    created_at: datetime
    metadata: Dict = Field(default_factory=dict)

    # For matching (cached)
    stem_norm: Optional[str] = None
```

```python
# tpc_reporter/schemas/match.py
from __future__ import annotations
from pydantic import BaseModel

class Match(BaseModel):
    artifact_id: str
    session_id: str
    confidence: float  # 0.0 to 1.0
    method: str        # "filename_exact" | "filename_fuzzy" | "other"
    rationale: str
```

```python
# tpc_reporter/schemas/report.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ReportSection(BaseModel):
    session_id: str
    markdown: str
    sources_used: List[str] = Field(default_factory=list)  # artifact_ids
    flags: List[str] = Field(default_factory=list)

class QAResult(BaseModel):
    session_id: str
    scores: Dict[str, int]  # 0..5 values
    flags: List[str] = Field(default_factory=list)
    rationale: str = ""
```

### 2.3 Event config (canonical YAML)
Example fixture config `tests/fixtures/tpc24_mini/event.yaml`:

```yaml
event:
  id: tpc24_mini
  name: "TPC24 Mini Test"
  dates: "2024-03-15 to 2024-03-17"
  timezone: "America/Chicago"

sources:
  sessions:
    type: json
    path: tests/fixtures/tpc24_mini/sessions.json

  artifacts:
    type: folder
    path: tests/fixtures/tpc24_mini/artifacts/

outputs:
  run_dir: runs/
```

### 2.4 Golden fixture (acceptance test)
Create `tests/fixtures/tpc24_mini/`:

- `sessions.json` (3 sessions)
- `artifacts/` (3 source files)
- `expected_output/report.md` (no citations; includes Sources Used)

### 2.5 Dependencies
Add to `pyproject.toml`:

```toml
[project]
dependencies = [
  "pydantic>=2.0",
  "click>=8.0",
  "python-docx>=1.0",
  "python-pptx>=1.0",
  "pyyaml>=6.0",
  "openai>=1.0",  # or anthropic
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff", "black"]

[project.scripts]
tpc_reporter = "tpc_reporter.cli:cli"
```

---

## 3) Orchestrator contract (must be implemented Day 1)

### Phases
1. `INGEST`  (load config + sessions + artifacts; write state)
2. `MATCH`   (produce matches + review queue if needed)
3. `SUMMARIZE` (draft per-session summaries)
4. `EVALUATE` (QA scores + flags; review queue if needed)
5. `PUBLISH` (assemble final `report.md`)

### WorkflowState (persisted)
`state.json` must include:
- `event`, `sessions[]`, `artifacts[]`
- `matches[]`, `unmatched_artifacts[]`
- `summaries{session_id: ReportSection}`
- `qa{session_id: QAResult}`
- `phase` (last completed)

### Review gates
- After `MATCH`: gate if any match confidence < 0.70 or any unmatched artifacts exist.
- After `EVALUATE`: gate if any QA flag present or any score < 3.

---

## 4) Day 1: Foundation (6–8 hours)

### Goal
Get the pipeline through `INGEST` and `MATCH` with persisted state.

### Task 1.1 — Config loader
- Read YAML config into `Event` + paths.

### Task 1.2 — Session ingestion
Support:
- JSON roster (preferred)
- CSV roster (optional; if time)

### Task 1.3 — Artifact collection + extraction
Implement `tools/collect.py`:
- scan folder recursively
- support `.md`, `.txt`, `.csv`, `.docx`, `.pptx`
- compute sha256(text) and store `sha256_12`
- set `stem_norm` for matching

Extraction hints:
- `.docx`: `python-docx`
- `.pptx`: `python-pptx` (extract text frames)

### Task 1.4 — Deterministic matching
Implement `agents/matcher.py`:
- exact match: session id substring in filename
- fuzzy match: SequenceMatcher between filename and session title
- output `Match` with confidence and rationale
- produce `unmatched_artifacts`

### Task 1.5 — CLI wiring
Implement:
- `ingest --config`: creates run dir, writes state, prints run dir
- `match --run`: loads state, computes matches, writes state, exports review queue

### Day 1 deliverable
Running on the fixture:
```bash
RUN_DIR=$(tpc_reporter ingest --config tests/fixtures/tpc24_mini/event.yaml)
tpc_reporter match --run "$RUN_DIR"
```
Produces `runs/<run_id>/state.json` and (if needed) `review_queue/matches.json`.

---

## 5) Day 2: Summarization + QA (6–8 hours)

### Goal
Draft per-session summaries and produce QA scorecards.

### Task 2.1 — Summarizer prompt (no citations)
Create `prompts/summarizer.txt`:
- enforce a stable structure
- require **Sources Used** list (filenames)
- forbid introducing new facts not present in sources
- allow "Unknown" / "Not specified" rather than guessing

### Task 2.2 — Summarizer agent
Implement `agents/summarizer.py`:
- for each session, gather matched artifacts
- call LLM with sources excerpts (truncate)
- store `ReportSection(markdown, sources_used=[artifact_ids])`

### Task 2.3 — Evaluator rubric (no citation scoring)
Create `prompts/evaluator.txt` scoring (0–5):
- Coverage
- Faithfulness
- Specificity
- Actionability
Flags:
- `low_coverage`, `likely_unsupported`, `vague_action_items`, `missing_sections`

### Task 2.4 — Deterministic checks
In addition to LLM QA, add simple checks:
- required headings exist in each session summary
- every session has a summary (or explicit "No sources" placeholder)
- `Sources Used` list is present and only references known artifacts

### Day 2 deliverable
```bash
tpc_reporter summarize --run runs/<run_id>
tpc_reporter evaluate --run runs/<run_id>
```
Produces:
- `sessions/*.md`
- `qa_scorecard.json`
- `review_queue/<session_id>_draft.md` for flagged sessions

---

## 6) Day 3: Publishing + polish + tests (6–8 hours)

### Goal
Generate `report.md` and pass an end-to-end test.

### Task 3.1 — Publisher
Implement `agents/publisher.py`:
- assemble executive summary (simple: counts, QA stats)
- include each session summary
- include appendix: unmatched artifacts + review notes

### Task 3.2 — Orchestrator wrapper
Implement `tpc_reporter run --config ... --request "..."`:
- for MVP, parse request minimally:
  - if it mentions session ids/titles, filter sessions
  - else generate full report
- execute phases sequentially
- stop for review gates unless `--no-review-gates`

### Task 3.3 — Resume
Implement `resume --run`:
- detect which phase is incomplete
- re-run from next phase

### Task 3.4 — End-to-end test
A `pytest` test should:
- run the pipeline on the fixture
- assert outputs exist and contain expected headings

### Day 3 deliverable
One command demo:
```bash
tpc_reporter run --config tests/fixtures/tpc24_mini/event.yaml --request "Generate full report"
```

---

## 7) Post-hackathon (explicitly out of scope)

- PDF support (best-effort)
- HTML agenda scraping
- Google Drive/Sheets connectors
- Embedding-based matching
- Stronger grounding (optional citations / evidence excerpts)
- UI for review
