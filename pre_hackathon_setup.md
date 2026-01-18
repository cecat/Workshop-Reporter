# Pre-Hackathon Setup Guide

This guide has two sections:
1. **Organizer Setup** (Charlie's responsibilities before March 31)
2. **Participant Setup** (what team members should do before March 31)

---

## Part 1: Organizer Setup (Charlie)

### Timeline
Complete by **March 28** to allow buffer before kickoff.

---

### A) Prepare TPC25 Dataset (Critical - 4-6 hours)

**Goal**: Organize real TPC25 conference materials into a format the system can process.

#### Step 1: Download materials from TPC25 website
Since the site blocks robots, manually download:
- Session schedules/agenda
- Session notes (any available)
- Presentation slides
- Participant lists
- Lightning talk submissions

#### Step 2: Convert PDFs if necessary
```bash
# For each PDF slide deck, either:
# Option A: Convert to PPTX (use online converter or LibreOffice)
# Option B: Extract text to .txt file
# Option C: Skip and use only notes

# Example using pdftotext (if available):
for pdf in *.pdf; do
    pdftotext "$pdf" "${pdf%.pdf}.txt"
done
```

#### Step 3: Organize into folder structure
```bash
mkdir -p data/tpc25/artifacts
cd data/tpc25/artifacts

# Organize files with clear naming:
# - plenary_keynote_slides.pptx
# - plenary_keynote_notes.md
# - breakout_federated_training_notes.txt
# - breakout_federated_training_participants.csv
# etc.
```

**Naming conventions** (important for matching):
- Include session identifier in filename
- Use consistent separators (underscore or dash)
- Use descriptive names

#### Step 4: Create sessions.json
```bash
cd data/tpc25
nano sessions.json
```

Example format:
```json
{
  "sessions": [
    {
      "id": "plenary_keynote",
      "title": "Plenary Keynote: Future of Large Language Models",
      "type": "plenary",
      "leaders": ["Dr. Jane Smith"],
      "abstract": "Discussion of LLM scaling trends...",
      "scheduled_time": "2025-03-15 09:00"
    },
    {
      "id": "breakout_federated",
      "title": "Breakout: Federated Training at Scale",
      "type": "breakout",
      "leaders": ["Dr. Bob Lee", "Dr. Alice Chen"],
      "track": "Infrastructure",
      "abstract": "Exploring federated approaches..."
    }
  ]
}
```

**Tips**:
- Session `id` should match filename patterns
- Include all sessions that have materials
- Abstract is optional but helpful for matching

---

### B) Create Repository Structure (Critical - 30 min)

```bash
cd ~/code/Workshop-Reporter

# Core package structure
mkdir -p tpc_reporter/{orchestrator,agents,tools,schemas,prompts,storage}
touch tpc_reporter/__init__.py

for d in orchestrator agents tools schemas prompts storage; do 
    touch "tpc_reporter/$d/__init__.py"
done

# Config and data directories
mkdir -p config/{events,templates}
mkdir -p tests/fixtures
mkdir -p runs

# Documentation
# (README.md, PLAN.md, and this file already exist)
```

---

### C) Create Schemas (Critical - 45 min)

Copy these files verbatim:

**`tpc_reporter/schemas/event.py`**:
```python
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

**`tpc_reporter/schemas/artifact.py`**:
```python
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

class Artifact(BaseModel):
    id: str
    path: str
    kind: str  # "md" | "txt" | "csv" | "docx" | "pptx"
    extracted_text: str
    sha256_12: str  # First 12 chars of sha256
    created_at: datetime
    metadata: Dict = Field(default_factory=dict)
    stem_norm: Optional[str] = None  # Normalized filename for matching
```

**`tpc_reporter/schemas/match.py`**:
```python
from __future__ import annotations
from pydantic import BaseModel

class Match(BaseModel):
    artifact_id: str
    session_id: str
    confidence: float  # 0.0 to 1.0
    method: str  # "filename_exact" | "filename_fuzzy" | "semantic"
    rationale: str
```

**`tpc_reporter/schemas/report.py`**:
```python
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict

class ReportSection(BaseModel):
    session_id: str
    markdown: str
    sources_used: List[str] = Field(default_factory=list)  # artifact_ids
    flags: List[str] = Field(default_factory=list)

class QAResult(BaseModel):
    session_id: str
    scores: Dict[str, int]  # coverage, faithfulness, etc. (0-5)
    flags: List[str] = Field(default_factory=list)
    rationale: str = ""
```

**`tpc_reporter/schemas/state.py`**:
```python
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from .event import Event, Session
from .artifact import Artifact
from .match import Match
from .report import ReportSection, QAResult

class WorkflowState(BaseModel):
    run_id: str
    phase: str = "INGEST"  # Current phase
    metadata: Dict = Field(default_factory=dict)
    
    # Data
    event: Optional[Event] = None
    sessions: List[Session] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    matches: List[Match] = Field(default_factory=list)
    unmatched_artifacts: List[str] = Field(default_factory=list)
    
    # Outputs
    summaries: Dict[str, ReportSection] = Field(default_factory=dict)
    qa_results: Dict[str, QAResult] = Field(default_factory=dict)
```

**`tpc_reporter/constants.py`**:
```python
# Matching thresholds
MATCH_CONFIDENCE_THRESHOLD = 0.70

# QA thresholds
MIN_QA_SCORE = 3

# Supported file formats
SUPPORTED_EXTENSIONS = [".md", ".txt", ".docx", ".pptx", ".csv"]

# LLM settings
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.3
MAX_TOKENS_SUMMARY = 2000
```

---

### D) Create Test Fixture (Critical - 1-2 hours)

Create `tests/fixtures/tpc24_mini/` as a smaller, simpler version for testing:

**`tests/fixtures/tpc24_mini/event.yaml`**:
```yaml
event:
  id: tpc24_mini
  name: "TPC24 Mini Test Fixture"
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

**`tests/fixtures/tpc24_mini/sessions.json`**:
```json
{
  "sessions": [
    {
      "id": "plenary",
      "title": "Plenary: Future of TPC",
      "type": "plenary",
      "leaders": ["Dr. Smith"]
    },
    {
      "id": "breakout_infra",
      "title": "Breakout: Infrastructure",
      "type": "breakout",
      "leaders": ["Dr. Lee", "Dr. Chen"]
    }
  ]
}
```

**`tests/fixtures/tpc24_mini/artifacts/plenary_notes.md`**:
```markdown
# Plenary Session Notes

Dr. Smith discussed the future direction of TPC.

Key points:
- Consortium membership growing
- Need for better coordination tools
- This reporter system is one example

Action items:
- Review governance model (Owner: Dr. Smith, Due: Q2 2025)
```

Create 2-3 more artifact files for the fixture.

---

### E) Set Up Dependencies (Critical - 15 min)

**`pyproject.toml`**:
```toml
[project]
name = "tpc-reporter"
version = "0.1.0"
description = "Agentic meeting report generator for TPC"
requires-python = ">=3.9"

dependencies = [
  "pydantic>=2.0",
  "python-docx>=1.0",
  "python-pptx>=0.6.21",
  "pyyaml>=6.0",
  "click>=8.0",
  "openai>=1.0",
  "python-Levenshtein>=0.21.0"  # For faster fuzzy matching
]

[project.optional-dependencies]
dev = [
  "pytest>=7.0",
  "pytest-cov",
  "ruff",
  "black"
]

[project.scripts]
tpc_reporter = "tpc_reporter.cli:cli"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

**`.gitignore`**:
```
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/

# Data and outputs
data/
runs/
*.db

# Secrets
.env
secrets.yml
*_api_key*

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
```

---

### F) Communication Setup (Critical - 30 min)

1. **Create Slack workspace or Discord server**
   - Channels: #general, #help, #github-notifications, #random
   - Integrate GitHub notifications

2. **GitHub repository setup**
   - Enable Issues
   - Create issue templates
   - Set up branch protection (optional)
   - Add team members as collaborators

3. **Zoom links**
   - Create recurring meeting for March 31 and April 7
   - Test screen sharing and breakout rooms

---

### G) Create Initial Issues (Recommended - 30 min)

In GitHub, create issues for Priority 1 tasks from PLAN.md:
- Issue #1: Schema Implementation
- Issue #2: Config Loader
- Issue #3: File Inventory
- Issue #4: Text Extractors
- Issue #5: State Persistence
- Issue #6: CLI Stubs

Label them "good first issue" and "priority-1".

---

### H) Test Your Setup (Critical - 30 min)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Test that imports work
python -c "from tpc_reporter.schemas.event import Event; print('✅ Schemas OK')"

# Verify fixture exists
ls tests/fixtures/tpc24_mini/

# Verify TPC25 data exists
ls data/tpc25/sessions.json
ls data/tpc25/artifacts/

echo "✅ Pre-hackathon setup complete!"
```

---

## Part 2: Participant Setup (Team Members)

### Before March 31 (Required - ~30 min)

#### 1. Clone the repository
```bash
git clone https://github.com/YOUR_ORG/workshop-reporter.git
cd workshop-reporter
```

#### 2. Verify Python version
```bash
python --version  # Should be 3.9 or higher
```

If not, install Python 3.9+:
- **macOS**: `brew install python@3.11`
- **Ubuntu**: `sudo apt install python3.11`
- **Windows**: Download from python.org

#### 3. Create virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### 4. Install dependencies
```bash
pip install -e ".[dev]"
```

#### 5. Get LLM API key

**Option A: OpenAI**
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Set environment variable:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```
4. Test:
   ```python
   from openai import OpenAI
   client = OpenAI()
   print("✅ OpenAI key works")
   ```

**Option B: Anthropic Claude**
1. Go to https://console.anthropic.com/
2. Create API key
3. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

**Make it permanent** (add to `~/.bashrc` or `~/.zshrc`):
```bash
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
```

#### 6. Join communication channels
- Join Slack/Discord (link provided by organizer)
- Watch the GitHub repository for notifications

#### 7. Review documentation
- Read README.md
- Skim PLAN.md
- Look through schema definitions

#### 8. Verify setup works
```bash
pytest  # Should show tests passing or skipping
python -c "from tpc_reporter.schemas.event import Event; print('✅ Ready!')"
```

---

### Optional (Helpful)

- **Review Pydantic docs**: https://docs.pydantic.dev/latest/
- **Review python-docx**: https://python-docx.readthedocs.io/
- **Review python-pptx**: https://python-pptx.readthedocs.io/
- **Set up your IDE** with Python linting (Ruff recommended)

---

## Troubleshooting

### "Module not found" errors
```bash
pip install -e ".[dev]"  # Make sure you're in the repo root
```

### "Python version too old"
```bash
python3.11 -m venv .venv  # Use specific Python version
```

### "API key not working"
```bash
# Verify key is set
echo $OPENAI_API_KEY

# Test with simple script
python Examples/chat.py
```

### "Permission denied" on Linux/Mac
```bash
chmod +x scripts/*  # If any scripts need execution permission
```

---

## Checklist Summary

### Organizer (Charlie):
- [ ] TPC25 dataset prepared (`data/tpc25/`)
- [ ] Repository structure created
- [ ] Schemas implemented
- [ ] Test fixture created
- [ ] Dependencies configured (`pyproject.toml`)
- [ ] Communication channels set up
- [ ] GitHub issues created
- [ ] Setup tested and working

### Participants:
- [ ] Repository cloned
- [ ] Python 3.9+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] LLM API key obtained and tested
- [ ] Communication channels joined
- [ ] Documentation reviewed
- [ ] Setup verified with `pytest`

---

## Questions?

Post in Slack #help channel or email the organizer.

See you on March 31! 🚀
