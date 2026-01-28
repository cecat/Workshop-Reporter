# Implementation Plan: TPC Workshop Reporter
## LangGraph Workflow Edition (March 31 - April 16, 2026)

**Team**: 4-8 developers (Python proficient, some LLM experience helpful)  
**Architecture**: LangGraph workflow + tested components from TPC-Session-Reporter

---

## Executive Summary

We're building a **document processing workflow** that generates structured reports from TPC conference materials. After evaluating Academy (federated HPC middleware), we determined **LangGraph** is the right tool:

- ✅ Purpose-built for LLM workflows
- ✅ Simple Python API (no distributed systems complexity)
- ✅ Built-in state management and checkpointing
- ✅ Conditional edges for review gates
- ✅ Wide adoption and documentation

### What We're Building On

We have an incomplete TPC-Session-Reporter prototype (~70% done) with:
- ✅ **Tested LLM prompt** (carefully tuned for TPC25 sessions)
- ✅ **Session matching logic** (handles acronyms, fuzzy matching)
- ✅ **Data pipeline** (Google Sheets/Docs, HTML parsing)
- ✅ **Appendix generation** (Python for tables, LLM for narrative)
- ❌ **Missing**: LLM integration (~50 lines), multi-session orchestration

**Strategy**: Complete the prototype first, then refactor into LangGraph workflow.

---

## 0) Architecture: LangGraph Workflow

### Workflow Graph

```
[START]
   ↓
[ingest_node]
   ↓
[match_node] ──(low confidence?)──> [review_gate] ──> [match_node]
   ↓ (good matches)
[summarize_node]
   ↓
[evaluate_node] ──(QA flags?)──> [review_gate] ──> [publish_node]
   ↓ (pass QA)
[publish_node]
   ↓
[END]
```

### Workflow State

```python
from typing import TypedDict, List, Dict
from tpc_reporter.schemas import Event, Session, Artifact, Match, ReportSection, QAResult

class WorkflowState(TypedDict):
    """LangGraph state passed between nodes"""
    # Input
    run_id: str
    config_path: str
    
    # Data
    event: Event
    sessions: List[Session]
    artifacts: List[Artifact]
    
    # Processing
    matches: List[Match]
    unmatched_artifacts: List[str]
    
    # Output
    summaries: Dict[str, ReportSection]  # session_id -> summary
    qa_results: Dict[str, QAResult]      # session_id -> QA
    
    # Control
    phase: str  # Current node
    needs_review: bool
    review_queue_path: str
```

### Node Functions

Each node is a Python function with signature:
```python
def node_name(state: WorkflowState) -> WorkflowState:
    # Process state
    # Return updated state
    pass
```

**Nodes:**
1. `ingest_node` - Parse sessions, extract text from files
2. `match_node` - Link artifacts to sessions
3. `summarize_node` - Generate summaries via LLM
4. `evaluate_node` - Run QA checks
5. `publish_node` - Assemble final reports
6. `review_gate` - Export for human review, pause workflow

---

## 1) Timeline

### March 31 (2-4 hours): Kickoff
- Team introductions
- Demo TPC-Session-Reporter progress
- LangGraph overview
- Repository walkthrough
- Task assignment

### April 1-6: Async Work Phase 1
**Goal**: Complete TPC-Session-Reporter, test on one session

### April 7 (6-8 hours): Remote Sprint
**Goal**: Refactor into LangGraph, test multi-session

### April 8-13: Async Work Phase 2
**Goal**: QA checks, review workflow, polish

### April 14-16 (3 days): In-Person Hackathon
**Goal**: Full TPC25 data, quality tuning, demo

---

## 2) Team Roles

### Minimum (4 people)
1. **Workflow Lead** - LangGraph orchestration, state management
2. **Data Pipeline Lead** - Ingestion, extraction, matching
3. **LLM Lead** - Summarization, prompt engineering
4. **QA/Testing Lead** - Evaluation, testing, fixtures

### Optimal (6-8 people)
5. **Prompt Engineer** - Tune LLM outputs
6. **DevOps** - Setup, docs, CI
7. **Domain Expert** - TPC knowledge, validate outputs
8. **Flex** - Help where needed

---

## 3) Pre-Hackathon Prep (Organizer: Charlie)

### Critical (~8-10 hours, complete by March 28)

#### A) Complete TPC-Session-Reporter LLM Integration (2-3 hours)

The prototype is ~70% done. Wire in the missing LLM call:

```python
# In generate_report.py, around line 820:
# Replace this stub:
#     print("📝 Next step: Add AI-generated content...")

# With actual LLM call:
def generate_ai_content(session_info, filtered_talks, notes_content, master_prompt):
    """Call LLM to generate discussion/outcomes sections"""
    from openai import OpenAI
    client = OpenAI()  # Uses OPENAI_API_KEY from env
    
    # Build prompt with session data
    prompt = master_prompt.format(
        session_title=session_info['title'],
        session_leaders=session_info['leaders'],
        lightning_talks=format_talks_for_prompt(filtered_talks),
        discussion_notes=notes_content or "No discussion notes available"
    )
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a technical report writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    return response.choices[0].message.content

# Then insert AI content into report_framework
ai_content = generate_ai_content(session_info, filtered_talks, notes, master_prompt)
report = report_framework.replace("<!-- AI_CONTENT_PLACEHOLDER -->", ai_content)
```

**Test**: Run on MAPE session, verify complete report generated.

#### B) Prepare TPC25 Dataset (3-4 hours)

1. Download materials from TPC25.org:
   - Session HTML: `curl https://tpc25.org/sessions/ > data/tpc25/sessions.html`
   - Lightning talks: Copy Google Sheets URL, convert to CSV export URL
   - Attendee list (if available)

2. Organize:
   ```bash
   mkdir -p data/tpc25/artifacts
   # Copy all files with clear names:
   # - breakout_dwarf_notes.txt
   # - breakout_mape_slides.pptx
   # - plenary_keynote.pptx
   ```

3. Create `data/tpc25/sessions.json` manually (or use working extractor from prototype)

#### C) Install LangGraph (15 min)

```bash
conda create -n workshop-reporter python=3.11
conda activate workshop-reporter
pip install langgraph langchain langchain-openai
pip install pydantic python-docx python-pptx pyyaml
pip install beautifulsoup4 requests

# Test
python -c "from langgraph.graph import StateGraph; print('✅ LangGraph ready')"
```

#### D) Create Repository Structure (30 min)

```bash
cd ~/Dropbox/MyCode/Workshop-Reporter

# Package structure
mkdir -p tpc_reporter/{nodes,schemas,tools,prompts}
touch tpc_reporter/__init__.py
touch tpc_reporter/nodes/__init__.py
touch tpc_reporter/schemas/__init__.py
touch tpc_reporter/tools/__init__.py

# Config and tests
mkdir -p config/{events,templates}
mkdir -p tests/{fixtures/tpc24_mini,unit,integration}
mkdir -p runs
```

####E) Port Key Components to Tools (1-2 hours)

Extract from TPC-Session-Reporter `generate_report.py`:

**`tpc_reporter/tools/matching.py`**:
```python
def session_matches(target_group: str, session_label: str) -> float:
    """
    Flexible session matching with confidence score.
    Returns 0.0-1.0.
    
    Tested on TPC25 data (MAPE, DWARF sessions).
    """
    if not target_group or not session_label:
        return 0.0
    
    target = target_group.upper().strip()
    session = session_label.upper().strip()
    
    # Exact match
    if target == session:
        return 1.0
    
    # Acronym in parentheses
    if f"({target})" in session:
        return 0.95
    
    # Containment
    if target in session:
        return 0.85
    if session in target:
        return 0.80
    
    # Word overlap
    target_words = set(target.replace(',', '').replace(':', '').split())
    session_words = set(session.replace(',', '').replace(':', '').split())
    overlap = len(target_words & session_words)
    
    if overlap >= min(2, len(target_words)):
        return 0.70
    
    return 0.0
```

**`tpc_reporter/tools/web_fetch.py`**: Copy `download_from_url()` function

**`tpc_reporter/tools/extractors.py`**: Copy text extraction functions

#### F) Copy Tested Prompt (Already Done)

The tested prompt is in `config/prompts/tpc25_master_prompt.yaml`

#### G) Create Test Fixture (1 hour)

```bash
mkdir -p tests/fixtures/tpc24_mini/artifacts
```

Copy MAPE session data from TPC-Session-Reporter:
- Lightning talks CSV (filtered for MAPE)
- Attendees CSV (sample)
- Session HTML snippet
- Expected output (draft-report-MAPE.md)

#### H) Test Setup End-to-End (30 min)

```bash
conda activate workshop-reporter

# Test TPC-Session-Reporter with LLM
cd ~/Dropbox/MyCode/TPC-Session-Reporter
python generate_report.py -g "MAPE"
# Should produce complete draft-report-MAPE.md

# Verify Workshop-Reporter setup
cd ~/Dropbox/MyCode/Workshop-Reporter
python -c "from tpc_reporter.tools.matching import session_matches; print('✅ Tools OK')"
ls tests/fixtures/tpc24_mini/
ls data/tpc25/
```

---

## 4) Participant Prep (Before March 31)

### Required (Everyone)
1. Clone repository
2. Install Python 3.11
3. Create conda environment: `conda create -n workshop-reporter python=3.11`
4. Install dependencies: `pip install langgraph langchain pydantic`
5. Get OpenAI API key, test it
6. Join Slack/Discord
7. Review README.md and PLAN.md

### Recommended
- Read LangGraph docs: https://langchain-ai.github.io/langgraph/
- Review TPC-Session-Reporter: `reference/tpc-session-reporter/`
- Familiarize with Pydantic
- Review `python-docx`, `python-pptx` docs

---

## 5) March 31 Kickoff Agenda

### Hour 1: Orientation
- Introductions
- TPC context, demo working TPC-Session-Reporter output
- Why LangGraph (not Academy)
- Architecture overview

### Hour 2: Technical Deep Dive
- LangGraph crash course:
  - `StateGraph`, nodes, edges
  - State passing
  - Checkpointing
  - Conditional edges (review gates)
- Walk through TPC-Session-Reporter code
- Show what to preserve

### Hour 3-4: Setup & Tasks
- Environment verification
- Role assignments
- Task assignments for April 1-6
- Create GitHub issues

---

## 6) April 1-6: Complete TPC-Session-Reporter

### Priority 1 (Must Complete Before April 7)

**Issue #1: Wire LLM into TPC-Session-Reporter** [2-3 hours]  
Owner: LLM Lead
- Add `generate_ai_content()` function
- Call OpenAI API with tested prompt
- Insert result into report framework
- Test on MAPE session

**Issue #2: Test on Multiple Sessions** [1-2 hours]  
Owner: QA Lead
- Run on MAPE, DWARF, one other session
- Verify outputs are correct
- Document any issues

**Issue #3: Port to tools/matching.py** [1-2 hours]  
Owner: Data Pipeline Lead
- Extract `session_matches()` from generate_report.py
- Add unit tests
- Verify works identically

**Issue #4: Port to tools/extractors.py** [2 hours]  
Owner: Data Pipeline Lead
- Extract text extraction functions
- Add unit tests for each file type

**Issue #5: Create Schemas** [2 hours]  
Owner: Workflow Lead
- `tpc_reporter/schemas/state.py` - WorkflowState TypedDict
- `tpc_reporter/schemas/event.py` - Event, Session
- `tpc_reporter/schemas/artifact.py` - Artifact
- `tpc_reporter/schemas/match.py` - Match
- `tpc_reporter/schemas/report.py` - ReportSection, QAResult

**Issue #6: LangGraph Hello World** [1-2 hours]  
Owner: Workflow Lead
- Create minimal 2-node workflow
- Test state passing
- Verify checkpointing works

---

## 7) April 7: Remote Sprint (6-8 hours)

### Goal
Refactor TPC-Session-Reporter into LangGraph workflow, test multi-session

### Morning (9 AM - 12 PM)

**9:00 Standup** (30 min)
- Status updates
- Verify TPC-Session-Reporter works
- Plan refactoring approach

**9:30-12:00 Sprint**
- **Team A** (Workflow + DevOps): Create LangGraph workflow skeleton
- **Team B** (Data + LLM): Refactor functions into node functions
- **Team C** (QA): Create integration tests

### Midday (12:00-12:30)
- Demo progress
- Surface blockers

### Afternoon (12:30-4:00 PM)

**Integration**:
- Wire all nodes into workflow
- Test on fixture (single session)
- Test on real data (MAPE session)
- Fix bugs

**4:00 PM Demo** (30 min)
- Show workflow running end-to-end
- Celebrate progress

### Target Deliverables
- ✅ LangGraph workflow with 5 nodes
- ✅ Works on single session
- ✅ State persists to disk
- ✅ Can checkpoint and resume

---

## 8) April 8-13: Multi-Session + QA

### Priority 1

**Issue #7: Multi-Session Processing** [3-4 hours]  
Owner: Workflow Lead
- Loop over all sessions in `summarize_node`
- Generate summary for each
- Test on 3-5 sessions

**Issue #8: QA Checks** [2-3 hours]  
Owner: QA Lead
- Implement `evaluate_node`
- Check: coverage, completeness, confidence
- Flag issues for review

**Issue #9: Review Gate** [2-3 hours]  
Owner: Workflow Lead
- Implement conditional edge after `match_node`
- Export low-confidence matches to `review_queue/`
- Implement `resume` command

**Issue #10: Publisher** [2-3 hours]  
Owner: Any available
- Implement `publish_node`
- Generate per-session Markdown files
- Assemble full meeting report

**Issue #11: Appendix Generation** [2 hours]  
Owner: LLM Lead
- Port `generate_attendees_appendix()` from prototype
- Port `generate_lightning_talks_appendix()`
- Integrate into publisher

### Priority 2

**Issue #12: CLI** [1-2 hours]  
Owner: DevOps
- Implement `tpc_reporter run --config <event.yaml>`
- Implement `tpc_reporter resume --run <run_id>`
- Add status command

**Issue #13: Documentation** [2 hours]  
Owner: DevOps
- Update docstrings
- Create simple architecture diagram
- Create quickstart guide

---

## 9) April 14-16: In-Person Hackathon

### Day 1 (April 14): Full Pipeline
**Morning**: Run on all TPC25 sessions  
**Afternoon**: Bug bash, fix critical issues  
**Goal**: Complete reports for all sessions

### Day 2 (April 15): Quality
**Morning**: Review outputs, tune prompts  
**Afternoon**: Documentation, code cleanup  
**Goal**: High-quality outputs ready for TPC use

### Day 3 (April 16): Demo
**Morning**: Final testing, validate outputs  
**Afternoon**: Demo prep, celebrate  
**4 PM**: Demo presentation  
**Goal**: Deliver working system to TPC

---

## 10) Success Metrics

### MVP (Must Have)
- ✅ Works on real TPC25 data (all sessions)
- ✅ Accurate summaries using tested prompt
- ✅ Full meeting report generated
- ✅ QA catches issues
- ✅ Review workflow usable
- ✅ Documentation clear
- ✅ Tests pass

### Stretch Goals
- Embedding-based matching
- Streamlit review UI
- Cost tracking
- Parallel processing

---

## 11) Key Differences from Earlier Plans

### What Changed
- ❌ **Not using Academy** - Architectural overkill for document processing
- ✅ **Using LangGraph** - Purpose-built for LLM workflows
- ✅ **Simpler architecture** - Just Python, no distributed systems
- ✅ **Complete prototype first** - Then refactor, not build from scratch

### What Stayed
- ✅ Tested prompt from TPC-Session-Reporter
- ✅ Session matching logic
- ✅ Appendix generation patterns
- ✅ Data pipeline (Google Sheets/Docs)
- ✅ Hybrid Python + LLM approach

---

## 12) Dependencies

```
# Core
langgraph >= 0.1
langchain >= 0.1
langchain-openai >= 0.1
pydantic >= 2.0

# Document processing
python-docx >= 1.0
python-pptx >= 0.6.21
beautifulsoup4 >= 4.12

# Utilities
pyyaml >= 6.0
requests >= 2.31

# Dev
pytest >= 7.0
black
ruff
```

---

## Appendix: LangGraph Example

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    message: str
    count: int

def node1(state: State) -> State:
    return {"message": "Hello", "count": state["count"] + 1}

def node2(state: State) -> State:
    return {"message": f"{state['message']} World", "count": state["count"] + 1}

# Build graph
workflow = StateGraph(State)
workflow.add_node("node1", node1)
workflow.add_node("node2", node2)
workflow.add_edge("node1", "node2")
workflow.add_edge("node2", END)
workflow.set_entry_point("node1")

# Compile
app = workflow.compile()

# Run
result = app.invoke({"message": "", "count": 0})
# {"message": "Hello World", "count": 2}
```

---

## Quick Reference

### Key Files to Create
```
tpc_reporter/
  workflow.py              # LangGraph workflow definition
  nodes/
    ingest.py
    match.py
    summarize.py
    evaluate.py
    publish.py
  schemas/
    state.py               # WorkflowState TypedDict
    event.py, artifact.py, match.py, report.py
  tools/
    matching.py            # From TPC-Session-Reporter
    extractors.py
    web_fetch.py
  cli.py
```

### Important Links
- LangGraph: https://langchain-ai.github.io/langgraph/
- TPC-Session-Reporter: `reference/tpc-session-reporter/`
- TPC25 sessions: https://tpc25.org/sessions/
