# Pre-Hackathon Setup (Solo)

## Goal
Arrive at Day 1 with a **runnable skeleton**: schemas + fixture + CLI stubs + failing end-to-end test.

> **MVP guardrails**: workflow-first; `.pptx` supported; PDF out of scope; no claim-level provenance.

---

## 1) Create repo structure (15 min)

```bash
mkdir tpc-workshop-reporter && cd tpc-workshop-reporter

# Core package
mkdir -p tpc_reporter/{orchestrator,agents,tools,schemas,prompts,storage}
touch tpc_reporter/__init__.py
for d in orchestrator agents tools schemas prompts storage; do touch "tpc_reporter/$d/__init__.py"; done

# Config + data + runs
mkdir -p config/{events,templates} data tests/fixtures examples runs

# Top-level docs
touch README.md PLAN.md pyproject.toml .gitignore
```

---

## 2) Copy schemas (30 min)

Create these files **verbatim** from `updated_plan.aligned.md`:
- `tpc_reporter/schemas/event.py` (Event, Session)
- `tpc_reporter/schemas/artifact.py` (Artifact)
- `tpc_reporter/schemas/match.py` (Match)
- `tpc_reporter/schemas/report.py` (ReportSection, QAScorecard)

**`tpc_reporter/constants.py`**:
```python
MATCH_CONFIDENCE_THRESHOLD = 0.70
MIN_QA_SCORE = 3
SUPPORTED_EXTENSIONS = [".md", ".txt", ".docx", ".pptx", ".csv"]
```

**`tpc_reporter/schemas/state.py`**:
```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class WorkflowState(BaseModel):
    run_id: str
    phase: str = "INGEST"
    metadata: Dict = Field(default_factory=dict) # Tracks timestamps/request context
    event: Optional[Event] = None
    sessions: List[Session] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    matches: List[Match] = Field(default_factory=list)
    summaries: Dict[str, ReportSection] = Field(default_factory=dict)
    qa_results: Dict[str, QAResult] = Field(default_factory=dict)
```

Why: schemas and constants are the contract between phases.

---

## 3) Create a fixture dataset (60–90 min)

Create this folder:

```
tests/fixtures/tpc24_mini/
  event.yaml
  sessions.json
  artifacts/
    plenary_keynote_notes.md
    breakout_a_notes.txt
    breakout_b_slides.pptx   (optional: can be .md if you don’t want to generate pptx yet)
  expected_output/
    report.md
```

### 3.1 `event.yaml`

`tests/fixtures/tpc24_mini/event.yaml`:

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
  formats: [markdown]
```

### 3.2 `sessions.json`

`tests/fixtures/tpc24_mini/sessions.json`:

```json
{
  "sessions": [
    {
      "id": "plenary_keynote",
      "title": "Plenary Keynote: Future of Large Models",
      "type": "plenary",
      "leaders": ["Dr. Jane Smith"]
    },
    {
      "id": "breakout_a",
      "title": "Breakout A: Federated Training",
      "type": "breakout",
      "leaders": ["Dr. Bob Lee", "Dr. Alice Chen"]
    },
    {
      "id": "breakout_b",
      "title": "Breakout B: Model Compression",
      "type": "breakout",
      "leaders": ["Dr. Carlos Rodriguez"]
    }
  ]
}
```

### 3.3 Artifacts

`tests/fixtures/tpc24_mini/artifacts/plenary_keynote_notes.md`:

```markdown
# Plenary Keynote Notes

Dr. Smith discussed the trajectory of large language models.

Key points:
- Models are approaching 10T parameters
- Training costs are becoming prohibitive for academic institutions
- Proposed consortium-wide resource sharing model
- NSF funding opportunity opening in Q2 2025

Action items:
- Form working group to draft resource sharing proposal (Owner: Dr. Smith)
- Survey member institutions on compute availability by March 31
```

Create similar artifacts for Breakout A and B.

### 3.4 Expected output (no citations)

`tests/fixtures/tpc24_mini/expected_output/report.md`:

```markdown
# TPC24 Mini Test Post-Meeting Report

**Dates**: 2024-03-15 to 2024-03-17

---

## Executive Summary

This report covers 3 sessions. Draft summaries were generated from the provided notes/slides and may require minor human edits.

---

## Session Summaries

### Plenary Keynote: Future of Large Models
**Leaders**: Dr. Jane Smith
**Sources Used**: plenary_keynote_notes.md

**Key Discussion Points**:
- Models are approaching 10T parameters.
- Training costs are becoming prohibitive for academia.
- A consortium-wide resource sharing model was proposed.

**Decisions Made**:
- ✅ Form a working group to draft a resource-sharing proposal.

**Action Items**:
- Draft resource sharing proposal (Owner: Dr. Smith).
- Survey member institutions on compute availability by March 31.

**Open Questions**:
- What governance model should the working group use?

---

### Breakout A: Federated Training
...
```

---

## 4) Dependencies (15 min)

`pyproject.toml`:

```toml
[project]
name = "tpc-reporter"
version = "0.1.0"
dependencies = [
  "pydantic>=2.0",
  "python-docx>=1.0",
  "python-pptx>=0.6.21",
  "pyyaml>=6.0",
  "click>=8.0",
  "openai>=1.0"  # or anthropic, or both
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff", "black"]

[project.scripts]
tpc_reporter = "tpc_reporter.cli:cli"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

---

## 5) Stub files (30–45 min)

Create empty modules with docstrings and NotImplementedError:

- `tpc_reporter/tools/ingest.py`
- `tpc_reporter/tools/collect.py`
- `tpc_reporter/agents/matcher.py`
- `tpc_reporter/agents/summarizer.py`
- `tpc_reporter/agents/evaluator.py`
- `tpc_reporter/agents/publisher.py`
- `tpc_reporter/orchestrator/workflow.py`
- `tpc_reporter/storage/state_store.py`

---

## 6) CLI stub (15–20 min)

`tpc_reporter/cli.py`:

```python
"""TPC Workshop Reporter CLI.

MVP contract:
- ingest --config <event.yaml> prints run_dir
- match|summarize|evaluate|publish --run <run_dir>
- run --config <event.yaml> --request "..." runs all phases
- resume --run <run_dir> continues after review
"""

import click

@click.group()
def cli():
    pass

@cli.command()
@click.option('--config', required=True)
def ingest(config):
    click.echo("TODO: ingest")

@cli.command()
@click.option('--run', 'run_dir', required=True)
def match(run_dir):
    click.echo("TODO: match")

@cli.command()
@click.option('--run', 'run_dir', required=True)
def summarize(run_dir):
    click.echo("TODO: summarize")

@cli.command()
@click.option('--run', 'run_dir', required=True)
def evaluate(run_dir):
    click.echo("TODO: evaluate")

@cli.command()
@click.option('--run', 'run_dir', required=True)
def publish(run_dir):
    click.echo("TODO: publish")

@cli.command()
@click.option('--config', required=True)
@click.option('--request', required=False, default="Generate the full post-meeting report")
def run(config, request):
    click.echo("TODO: run all phases")

@cli.command()
@click.option('--run', 'run_dir', required=True)
def resume(run_dir):
    click.echo("TODO: resume")

if __name__ == '__main__':
    cli()
```

---

## 7) A failing end-to-end test (15–30 min)

`tests/test_e2e.py`:

```python
from pathlib import Path

def test_fixture_pipeline_smoke():
    fixture = Path("tests/fixtures/tpc24_mini/event.yaml")
    assert fixture.exists()

    # The hackathon goal is to make this test pass by:
    # 1) running the workflow on the fixture config
    # 2) producing runs/<run_id>/report.md
    # 3) producing runs/<run_id>/qa_scorecard.json
    # 4) producing per-session summaries
    assert True
```

---

## Day 1 outcome

Your team should be able to:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

tpc_reporter ingest --config tests/fixtures/tpc24_mini/event.yaml
pytest
```

They’ll see clear TODOs and a fixture that defines “done.”
