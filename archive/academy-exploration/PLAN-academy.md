# Implementation Plan: TPC Workshop Reporter (Academy Edition)
## Distributed Hackathon with Academy System Developers

**Target Date**: March 31 - April 16, 2026  
**Team**: 4-8 developers (mix of Academy framework experts and Python devs)  
**Architecture**: Academy multi-agent system with proven components from TPC-Session-Reporter

---

## Executive Summary

This plan builds a **cooperative multi-agent workshop reporting system** using the Academy framework. It incorporates tested components from an earlier TPC-Session-Reporter prototype (prompt, session matching, data pipeline) while adopting Academy's async agent architecture for scalability and resilience.

### Key Design Decisions

1. **Academy-based** multi-agent system (not simple workflow pipeline)
2. **Continuously running orchestrator** with `@timer` loops (not one-shot execution)
3. **Preserve tested components**: prompt, session matching logic, appendix generation
4. **Hybrid approach**: Python for structured data, LLM for narrative summaries
5. **MVP focus**: Local/single-host deployment (federated scale-out is Phase 2)

### What We're Building On

From TPC-Session-Reporter prototype:
- ✅ **Tested LLM prompt** (`config/prompts/tpc25_master_prompt.yaml`)
- ✅ **Session matching logic** (flexible acronym/keyword/fuzzy matching)
- ✅ **Data pipeline** (Google Sheets URL conversion, file download, HTML parsing)
- ✅ **Appendix generation** (attendees table, lightning talks list)
- ❌ Never completed: LLM integration, multi-session orchestration

See `reference/tpc-session-reporter/README.md` for integration details.

---

## 0) Architecture: Academy Agents

### Agent Roster

Each agent is an Academy `Agent` with `@action` methods and optional `@timer` control loops.

#### **OrchestratorAgent** (always-on)
- **Purpose**: Workflow state machine and task dispatcher
- **Actions**:
  - `submit_job(job_spec)` → accepts new jobs
  - `advance_job(job_id)` → moves job through states
  - `get_status(job_id)` → returns current state
  - `resume_job(job_id)` → continues after human review
- **Control loop**: `@timer(interval=60)` checks for new jobs and advances active jobs
- **State machine**: NEW → INGESTED → INDEXED → EXTRACTED → MATCHED → SUMMARIZED → EVALUATED → PUBLISHED → DONE

#### **ProgramIngestAgent**
- **Purpose**: Fetch and parse workshop session roster
- **Actions**:
  - `fetch_program(url)` → downloads HTML/JSON
  - `extract_sessions(html)` → produces `Session` objects
- **Reuses**: `extract_session_details()` logic from TPC-Session-Reporter
- **Supports**: TPC25 HTML format (BeautifulSoup), Indico JSON, Sched JSON

#### **DriveIndexAgent** 
- **Purpose**: Inventory artifacts from Google Drive or local folder
- **Actions**:
  - `list_files(source_spec)` → produces `Artifact` metadata
  - `watch_changes(folder_id)` → detects new files (post-MVP)
- **MVP**: Supports local folder scanning; Drive API is stretch goal
- **Reuses**: `download_to_input()` and `setup_input_directory()` patterns

#### **DocExtractAgent**
- **Purpose**: Extract text from files
- **Actions**:
  - `extract_text(artifact)` → returns plain text
  - `extract_signals(artifact)` → returns metadata (title, authors, keywords)
- **Supports**: `.md`, `.txt`, `.csv`, `.docx`, `.pptx`
- **Cache**: Results keyed by `(file_id, modified_time, extractor_version)`

#### **MatchAgent**
- **Purpose**: Link artifacts to sessions with confidence scores
- **Actions**:
  - `propose_matches(sessions, artifacts)` → produces `Match` edges
  - `resolve_conflicts(matches)` → deduplicates and enforces constraints
  - `flag_for_review(matches)` → exports low-confidence matches
- **Reuses**: `session_matches()` logic from TPC-Session-Reporter
- **Evidence**: Each match includes rationale (title similarity, author overlap, etc.)

#### **SummarizeAgent**
- **Purpose**: Generate session summary narratives via LLM
- **Actions**:
  - `generate_summary(session, artifacts)` → calls LLM, returns `ReportSection`
- **Prompt**: Uses tested `config/prompts/tpc25_master_prompt.yaml`
- **Reuses**: Appendix generation logic (`generate_attendees_appendix`, `generate_lightning_talks_appendix`)
- **Pattern**: Python generates appendices, LLM generates discussion/outcomes sections

#### **EvaluatorAgent (QA)**
- **Purpose**: Quality checks on summaries
- **Actions**:
  - `evaluate_summary(session, summary)` → produces `QAResult`
  - `check_coverage(model)` → verifies all sessions have artifacts
- **Checks**: Coverage, completeness, confidence thresholds
- **Gates**: Triggers review queue when issues detected

#### **PublishAgent**
- **Purpose**: Assemble and export final reports
- **Actions**:
  - `render_session_pages(model, matches)` → generates per-session Markdown
  - `assemble_report(summaries)` → creates full meeting report
  - `write_outputs(outputs, targets)` → publishes to Drive/Git
- **Reuses**: Report framework structure from TPC-Session-Reporter

### Communication Pattern

Agents communicate via Academy's **exchange** (message bus):
- **Local dev**: `ThreadExchange` (single process, multiple threads)
- **Production**: `RedisExchange` (distributed, multiple processes)
- **Messages**: Small control messages (not large data blobs)
- **Data plane**: Large artifacts stored out-of-band (filesystem, blob store)

### Deployment Modes

#### Mode 1: Local Development (ThreadExchange)
```python
from academy import Manager, ThreadExchange, ThreadLauncher

exchange = ThreadExchange()
launcher = ThreadLauncher()
manager = Manager(exchange, launcher)

# Register agents
orchestrator = manager.register(OrchestratorAgent())
ingest = manager.register(ProgramIngestAgent())
# ... etc

manager.start()
```

#### Mode 2: Single-Host Production (RedisExchange)
```python
from academy import Manager, RedisExchange, ProcessLauncher

exchange = RedisExchange(host='localhost', port=6379)
launcher = ProcessLauncher()
manager = Manager(exchange, launcher)
# ... register agents
```

#### Mode 3: Federated (Post-MVP)
- Use Globus Compute for worker agents (extraction, embeddings)
- Use Academy's hosted exchange for cross-site communication

---

## 1) Timeline

### March 31 (2-4 hours): Kickoff Session
- Team introductions and role assignments
- Academy overview for non-experts
- Repository walkthrough
- Environment setup verification
- Task assignment for April 1-6

### April 1-6: Independent Async Work
- Small, parallelizable tasks
- Communication via Slack/Discord + GitHub issues
- Focus: Core infrastructure (agents, schemas, tools)

### April 7 (6-8 hours): Remote Sprint Day
- Open Zoom room for coordination
- Goal: End-to-end pipeline for single session
- Check-ins at start, midday, end

### April 8-13: Independent Async Work
- Bug fixes and testing
- QA checks and review workflow
- Stretch features

### April 14-16 (3 days × 8 hours): In-Person Hackathon
- Integration and multi-session testing
- Real TPC25 data validation
- Polish and demo preparation

---

## 2) Team Roles

### Minimum Viable (4 people)

1. **Academy Lead** - Orchestrator, state machine, agent registration
2. **Ingestion/Extraction Lead** - ProgramIngestAgent, DocExtractAgent, file I/O
3. **Matching/Summarization Lead** - MatchAgent, SummarizeAgent, LLM integration
4. **QA/Testing Lead** - EvaluatorAgent, testing, fixtures

### Optimal (6-8 people)

5. **Prompt Engineer** - Optimize LLM prompts, tune summarization
6. **DevOps/Infrastructure** - Setup, dependencies, CI, documentation
7. **Domain Expert** - TPC25 knowledge, validate outputs
8. **Flex/Integration** - Help wherever needed

**Organizer role**: Charlie will organize/unblock/coordinate; can code if time permits.

---

## 3) Before March 31: Organizer Prep (Charlie's Checklist)

### Critical (Must Complete by March 28)

#### A) Prepare TPC25 Dataset (4-6 hours)
1. **Download from TPC25.org**:
   - Session roster (copy HTML or export to JSON)
   - Lightning talk submissions (Google Sheets → CSV)
   - Attendee list (if available)
   - Discussion notes (if available)

2. **Organize into `data/tpc25/`**:
   ```bash
   mkdir -p data/tpc25/{sessions,artifacts}
   
   # Save session roster
   curl https://tpc25.org/sessions/ > data/tpc25/sessions/program.html
   
   # Download lightning talks CSV (convert Google Sheets URL)
   # From: https://docs.google.com/spreadsheets/d/ID/edit
   # To: https://docs.google.com/spreadsheets/d/ID/export?format=csv
   
   # Organize artifacts with clear naming:
   # - breakout_dwarf_notes.txt
   # - breakout_mape_slides.pptx
   # - plenary_keynote_slides.pptx
   ```

3. **Convert PDFs to PPTX or text** (if any PDF slides exist)

#### B) Install Academy Framework (30 min)
```bash
# Create conda environment
conda create -n workshop-reporter python=3.11
conda activate workshop-reporter

# Install Academy
pip install academy-agents

# Verify installation
python -c "from academy import Agent, action, timer; print('✅ Academy installed')"

# For local dev (ThreadExchange)
# No additional dependencies needed

# For production (RedisExchange)
pip install redis
```

Test Academy with a hello-world example:
```python
from academy import Agent, Manager, ThreadExchange, ThreadLauncher, action

class HelloAgent(Agent):
    @action
    async def greet(self, name: str) -> str:
        return f"Hello, {name}!"

exchange = ThreadExchange()
launcher = ThreadLauncher()
manager = Manager(exchange, launcher)
agent = manager.register(HelloAgent())
manager.start()

# Call action
handle = manager.get_handle(HelloAgent)
result = await handle.greet("World")
print(result)  # "Hello, World!"
```

#### C) Create Repository Structure (30 min)
```bash
cd ~/Dropbox/MyCode/Workshop-Reporter

# Core package structure (src layout)
mkdir -p src/workshop_reporter/{agents,schemas,tools}
touch src/workshop_reporter/__init__.py
touch src/workshop_reporter/agents/__init__.py
touch src/workshop_reporter/schemas/__init__.py
touch src/workshop_reporter/tools/__init__.py

# Config and reference
mkdir -p config/{events,prompts,templates}
mkdir -p reference/tpc-session-reporter

# Tests
mkdir -p tests/{fixtures/tpc24_mini,unit,integration}

# Documentation
mkdir -p docs

# Outputs
mkdir -p runs
```

#### D) Create Schemas (1 hour)

Copy schemas from `pre_hackathon_setup.md` and adapt for Academy:

**`src/workshop_reporter/schemas/job_spec.py`**:
```python
from pydantic import BaseModel, Field
from typing import Dict, Optional

class JobSpec(BaseModel):
    """Job submission specification"""
    job_id: str
    workshop_url: Optional[str] = None
    drive_folder_id: Optional[str] = None
    local_data_path: Optional[str] = None  # For MVP: use local files
    output_dir: str
    policies: Dict = Field(default_factory=lambda: {
        "min_match_confidence": 0.70,
        "require_human_approval_below": 0.65,
        "allow_web_fetch": True
    })
```

**`src/workshop_reporter/schemas/canonical_model.py`**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Workshop(BaseModel):
    """Workshop/conference metadata"""
    id: str
    name: str
    dates: str
    timezone: str = "America/Chicago"
    url: Optional[str] = None

class Session(BaseModel):
    """Individual session/breakout"""
    id: str
    title: str
    type: str  # "plenary" | "breakout" | "lightning" | "other"
    leaders: List[str] = Field(default_factory=list)
    track: Optional[str] = None
    abstract: Optional[str] = None
    scheduled_time: Optional[str] = None

class Artifact(BaseModel):
    """File with extracted content"""
    id: str
    path: str
    kind: str  # "md" | "txt" | "csv" | "docx" | "pptx"
    extracted_text: str
    sha256_12: str
    created_at: datetime
    metadata: Dict = Field(default_factory=dict)
    
class CanonicalWorkshopModel(BaseModel):
    """Complete workshop data model"""
    workshop: Workshop
    sessions: List[Session] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
```

**`src/workshop_reporter/schemas/match_graph.py`**:
```python
from pydantic import BaseModel

class MatchEvidence(BaseModel):
    """Explainable match evidence"""
    title_similarity: float
    author_overlap: List[str] = Field(default_factory=list)
    session_hint: Optional[str] = None
    rules_fired: List[str] = Field(default_factory=list)

class Match(BaseModel):
    """Artifact-to-session link"""
    artifact_id: str
    session_id: str
    confidence: float  # 0.0 to 1.0
    method: str  # "filename_exact" | "filename_fuzzy" | "semantic"
    evidence: MatchEvidence
```

**`src/workshop_reporter/schemas/report.py`**:
```python
from pydantic import BaseModel, Field
from typing import List, Dict

class ReportSection(BaseModel):
    """Single session report"""
    session_id: str
    markdown: str
    sources_used: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)

class QAResult(BaseModel):
    """Quality assessment"""
    session_id: str
    scores: Dict[str, int]  # coverage, faithfulness, etc. (0-5)
    flags: List[str] = Field(default_factory=list)
    rationale: str = ""
```

#### E) Port Key Functions to Tools (2 hours)

Extract and clean up logic from TPC-Session-Reporter:

**`src/workshop_reporter/tools/session_matching.py`**:
```python
def session_matches(target_group: str, session_label: str) -> float:
    """
    Flexible session matching with confidence score.
    Returns 0.0-1.0 confidence.
    
    Reused from TPC-Session-Reporter (tested on TPC25 data).
    """
    if not target_group or not session_label:
        return 0.0
    
    target = target_group.upper().strip()
    session = session_label.upper().strip()
    
    # Exact match
    if target == session:
        return 1.0
    
    # Acronym in parentheses
    if f"({target})" in session or f"({target.upper()})" in session:
        return 0.95
    
    # Target contained in session
    if target in session:
        return 0.85
    
    # Session contained in target
    if session in target:
        return 0.80
    
    # Word-based matching
    target_words = set(target.replace(',', '').replace(':', '').split())
    session_words = set(session.replace(',', '').replace(':', '').split())
    overlap = len(target_words & session_words)
    
    if overlap >= min(2, len(target_words)):
        return 0.70
    
    return 0.0
```

**`src/workshop_reporter/tools/web_fetch.py`**:
```python
import requests
from pathlib import Path

def download_from_url(url: str, dest_path: Path) -> bool:
    """
    Download content from URL with browser headers.
    Handles Google Sheets/Docs URL conversion.
    
    Reused from TPC-Session-Reporter.
    """
    # Convert Google URLs
    if 'docs.google.com/spreadsheets' in url and '/edit' in url:
        # Convert to CSV export
        sheet_id = url.split('/d/')[1].split('/')[0]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    elif 'docs.google.com/document' in url and '/edit' in url:
        # Convert to text export
        doc_id = url.split('/d/')[1].split('/')[0]
        url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(response.text, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False
```

#### F) Create Test Fixture (1-2 hours)

Create `tests/fixtures/tpc24_mini/` with:
- `job_spec.yaml` (job configuration)
- `sessions.json` (2-3 sessions)
- `artifacts/` (sample files)
- `expected_outputs/` (expected session reports)

Use subset of real TPC25 data (MAPE and DWARF sessions).

#### G) Set Up Communication Channels (30 min)
- Slack workspace or Discord server
- GitHub repository with issues enabled
- Zoom room links for March 31 and April 7

#### H) Test Setup End-to-End (1 hour)
```bash
conda activate workshop-reporter
pip install -e ".[dev]"

# Test Academy hello-world
python tests/test_academy_hello.py

# Test imports
python -c "from workshop_reporter.schemas.job_spec import JobSpec; print('✅ Schemas OK')"
python -c "from workshop_reporter.tools.session_matching import session_matches; print('✅ Tools OK')"

# Verify fixture exists
ls tests/fixtures/tpc24_mini/

# Verify TPC25 data exists
ls data/tpc25/sessions/
ls data/tpc25/artifacts/
```

---

## 4) Before March 31: Participant Prep

### Required (Everyone)
1. Clone repository
2. Install conda and Python 3.11
3. Create environment: `conda create -n workshop-reporter python=3.11`
4. Install Academy: `pip install academy-agents`
5. Get OpenAI API key and test it
6. Join Slack/Discord
7. Review README.md and this PLAN.md

### Recommended
- Read Academy documentation: https://github.com/AD-SDL/academy-agents
- Review `reference/tpc-session-reporter/README.md`
- Familiarize with Pydantic if not already comfortable
- Review `python-docx` and `python-pptx` documentation

---

## 5) March 31 Kickoff Agenda (2-4 hours)

### Hour 1: Orientation
- Introductions
- TPC context and demo of desired output
- Architecture overview: Academy agents
- Walk through preserved TPC-Session-Reporter components

### Hour 2: Technical Deep Dive
- Academy crash course for non-experts
  - `Agent`, `@action`, `@timer`
  - `Manager`, `Exchange`, `Launcher`
  - Handles and async messaging
- Repository structure walkthrough
- Schema overview
- CLI contract and job submission

### Hour 3-4: Setup & Task Assignment
- **Environment verification**: Everyone runs Academy hello-world
- **Role assignment** based on interests/skills
- **Task assignment** for April 1-6 (see section 6)
- Create GitHub issues for all tasks
- Set expectations for April 7

---

## 6) April 1-6: Independent Async Work

### Priority 1 Tasks (Must Complete Before April 7)

**Issue #1: OrchestratorAgent Skeleton** [3-4 hours]  
Owner: Academy Lead
- Implement `OrchestratorAgent` with state machine
- Actions: `submit_job()`, `advance_job()`, `get_status()`
- `@timer` loop that checks for active jobs
- Persistent job registry (JSON file for MVP)

**Issue #2: ProgramIngestAgent** [3-4 hours]  
Owner: Ingestion Lead
- Implement `fetch_program()` and `extract_sessions()`
- Port session extraction logic from TPC-Session-Reporter
- Support TPC25 HTML format
- Unit tests with real TPC25 HTML

**Issue #3: DocExtractAgent** [3-4 hours]  
Owner: Extraction Lead
- Implement text extraction for `.txt`, `.md`, `.csv`, `.docx`, `.pptx`
- Use `python-docx` and `python-pptx` libraries
- Cache results by file hash
- Unit tests

**Issue #4: MatchAgent** [3-4 hours]  
Owner: Matching Lead
- Implement `propose_matches()` using `session_matches()` tool
- Produce `Match` objects with confidence and evidence
- Unit tests with fixture data

**Issue #5: Manager Setup Script** [2-3 hours]  
Owner: Academy Lead
- Create `src/workshop_reporter/manager.py` that registers all agents
- Support both ThreadExchange and RedisExchange
- CLI command: `workshop_reporter start --config <event.yaml>`

**Issue #6: State Persistence** [2-3 hours]  
Owner: Academy Lead
- Implement job state save/load (JSON for MVP)
- Each job gets `runs/<job_id>/state.json`
- Orchestrator loads state on restart

### Priority 2 Tasks (Nice to Have Before April 7)

**Issue #7: SummarizeAgent Skeleton** [2-3 hours]  
Owner: Summarization Lead
- Implement `generate_summary()` action
- Load prompt from `config/prompts/tpc25_master_prompt.yaml`
- Stub LLM call (return placeholder for now)

**Issue #8: Integration Test** [2-3 hours]  
Owner: QA Lead
- End-to-end test on fixture
- Submit job → verify state transitions
- Check that agents receive tasks

**Issue #9: Documentation** [1-2 hours]  
Owner: DevOps Lead
- Update docstrings
- Create ARCHITECTURE.md
- Create RUNBOOK.md

---

## 7) April 7: Remote Sprint Day (6-8 hours)

### Goal
Get orchestrator dispatching tasks to agents; complete single-session pipeline.

### Morning (9 AM - 12 PM)

**9:00 Standup** (30 min)
- Status updates
- Prioritize tasks
- Keep Zoom open for collaboration

**9:30-12:00 Sprint**
- **Team A** (Academy Lead + DevOps): Wire orchestrator to dispatch tasks
- **Team B** (Ingestion + Extraction): Complete file processing pipeline
- **Team C** (Matching + Summarization): Integrate matching logic, start LLM

### Midday Check-in (12:00-12:30)
- Demo what's working
- Surface blockers
- Adjust priorities

### Afternoon (12:30-4:00 PM)

**Integration work**:
- Connect orchestrator → ingest → extract → match
- Test on real TPC25 data (MAPE session)
- Fix bugs

**4:00 PM Demo** (30 min)
- Show pipeline running (even if buggy)
- Celebrate progress
- Assign April 8-13 tasks

### Target Deliverables
- ✅ Orchestrator dispatches jobs to agents
- ✅ ProgramIngestAgent extracts sessions from HTML
- ✅ DocExtractAgent processes all file types
- ✅ MatchAgent produces matches with confidence
- ✅ State persisted correctly
- ✅ Tests pass on fixture

---

## 8) April 8-13: Async Work Phase 2

### Priority 1 (Must Complete Before April 14)

**Issue #10: Complete SummarizeAgent** [4-5 hours]  
Owner: Summarization Lead
- Wire LLM call (OpenAI client)
- Use tested prompt from `config/prompts/tpc25_master_prompt.yaml`
- Port appendix generation logic (Python-generated tables)
- Test on MAPE session

**Issue #11: EvaluatorAgent** [3-4 hours]  
Owner: QA Lead
- Implement `evaluate_summary()` action
- Checks: coverage, completeness, confidence thresholds
- Produce `QAResult` with flags

**Issue #12: Review Queue Export** [2-3 hours]  
Owner: Academy Lead
- Export low-confidence matches to `runs/<job_id>/review_queue/`
- Export flagged summaries for editing
- Document review workflow

**Issue #13: PublishAgent** [3-4 hours]  
Owner: Any available
- Implement `render_session_pages()` and `assemble_report()`
- Generate per-session Markdown files
- Generate full meeting report
- Use report framework from TPC-Session-Reporter

### Priority 2

**Issue #14: Multi-Session Pipeline** [3-4 hours]  
Owner: Academy Lead
- Process ALL sessions in batch (not just one)
- Orchestrator loops over sessions for summarization

**Issue #15: Resume Capability** [2-3 hours]  
Owner: Academy Lead
- Implement `resume_job()` action
- Load edited review queue files
- Continue from interrupted state

---

## 9) April 14-16: In-Person Hackathon

### Day 1 (April 14): Integration
**Morning**: End-to-end multi-session pipeline  
**Afternoon**: Bug bash, test on full TPC25 data  
**Goal**: All sessions processed, even if quality needs work

### Day 2 (April 15): Quality
**Morning**: Review output quality, tune prompts  
**Afternoon**: Documentation, code cleanup  
**Goal**: Outputs are high quality, documentation complete

### Day 3 (April 16): Polish & Demo
**Morning**: Final testing, validate all outputs  
**Afternoon**: Demo prep, celebrate  
**4 PM**: Final demo presentation  
**Goal**: Complete proceedings generation ready for TPC use

---

## 10) Success Metrics

### MVP (Must Have)
- ✅ Works on real TPC25 data (all sessions)
- ✅ Accurate session summaries using tested prompt
- ✅ Full meeting report generated
- ✅ QA catches major issues
- ✅ Review workflow is usable
- ✅ Documentation is clear
- ✅ Tests pass

### Stretch Goals
- Better matching with semantic embeddings
- Streamlit UI for review
- Real-time Drive monitoring
- Cost optimization

---

## 11) What Makes This Plan Different

### vs. Original Plan (workflow pipeline)
- **Academy agents** instead of phase-based pipeline
- **Continuously running** instead of one-shot execution
- **Async messaging** instead of direct function calls
- **More complex** but more scalable and resilient

### vs. Academy Strategy Doc (full vision)
- **MVP-focused**: Local deployment, no federation
- **Rule-based matching**: No embeddings initially
- **Pre-downloaded data**: No real-time Drive monitoring
- **3-day achievable**: Aggressive but realistic with Academy experts

### What We Preserved from TPC-Session-Reporter
- ✅ Tested prompt (proven with real TPC25 data)
- ✅ Session matching logic (handles acronyms, fuzzy matching)
- ✅ Appendix generation (Python for tables, LLM for prose)
- ✅ Google Sheets/Docs URL handling
- ✅ Graceful degradation patterns

---

## 12) Risk Mitigation

### Risk: Team unfamiliar with Academy
**Mitigation**: 
- Academy experts lead core infrastructure
- Provide crash course on Day 1
- Start with hello-world examples
- Pair programming during sprint days

### Risk: LLM costs during development
**Mitigation**:
- Use `gpt-4o-mini` for testing (cheaper)
- Cache LLM responses by input hash
- Limit fixture size

### Risk: Not finishing in 3 days
**Mitigation**:
- MVP is clearly scoped (no embeddings, no federation)
- Fallback: Working single-session pipeline is still valuable
- Stretch features clearly marked

### Risk: Data quality issues
**Mitigation**:
- Use real TPC25 data from start (not synthetic)
- Test with actual sessions (MAPE, DWARF) that have data
- Graceful degradation when data missing

---

## 13) Post-Hackathon Roadmap

See README.md for full post-hackathon phases. Key next steps:

**Phase 2**: Production features (embeddings, Drive monitoring, Streamlit UI)  
**Phase 3**: Scale-out (federated deployment, worker pools)  
**Phase 4**: Advanced features (LLM-as-orchestrator, MCP integration)

---

## Appendix: Quick Reference

### Key Files Created Pre-Hackathon
```
src/workshop_reporter/
  agents/orchestrator.py
  agents/ingest_program.py
  agents/doc_extract.py
  agents/match.py
  agents/summarize.py (stub)
  agents/evaluate.py (stub)
  agents/publish.py (stub)
  schemas/job_spec.py
  schemas/canonical_model.py
  schemas/match_graph.py
  schemas/report.py
  tools/session_matching.py
  tools/web_fetch.py
  manager.py

config/prompts/tpc25_master_prompt.yaml
tests/fixtures/tpc24_mini/
```

### Dependencies
```
academy-agents >= 0.1.0
pydantic >= 2.0
python-docx >= 1.0
python-pptx >= 0.6.21
pyyaml >= 6.0
openai >= 1.0
beautifulsoup4 >= 4.12
requests >= 2.31
pytest (dev)
```

### Important Links
- Academy: https://github.com/AD-SDL/academy-agents
- TPC25 sessions: https://tpc25.org/sessions/
- TPC-Session-Reporter reference: `reference/tpc-session-reporter/`
