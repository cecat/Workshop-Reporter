# Implementation Plan: TPC Workshop Reporter
## Distributed Hackathon Edition (March 31 - April 16)

This plan is optimized for a **4-8 person team** working through kickoff, remote sprints, and in-person hackathon days.

**Timeline:**
- March 31 (2-4h): Kickoff via Zoom
- April 1-6: Independent async work
- April 7 (6-8h): Remote sprint with open Zoom
- April 8-13: Independent async work
- April 14-16 (3×8h): In-person hackathon

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

### Input method
- **No web scraping in MVP** (TPC25 site blocks robots)
- Organizer will pre-download and organize all materials in `data/tpc25/`

### Config
- **YAML config is canonical** (`--config path/to/event.yaml`)

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

## 1) Team Roles (flexible based on team size)

### Minimum viable (4 people):
1. **Orchestration Lead** - Workflow runner, state management, CLI
2. **Ingestion/Extraction Lead** - File parsing, artifact collection
3. **Matching/Summarization Lead** - Session-artifact matching, LLM summarizer
4. **QA/Testing Lead** - Evaluator, testing, fixtures

### Optimal (6-8 people):
5. **Prompt Engineer** - Optimize summarizer and evaluator prompts
6. **DevOps/Infrastructure** - Setup, dependencies, CI, documentation
7. **Domain Expert** - TPC25 knowledge, validate outputs
8. **Flex/Integration** - Help wherever needed, integration work

**Organizer role**: Charlie will primarily organize/unblock/coordinate, but can code if time permits.

---

## 2) Before March 31: Organizer Prep (Charlie's checklist)

### Critical (must be done):
- [ ] **Prepare TPC25 dataset** (see `pre_hackathon_setup.md` for details):
  - Download all session materials from TPC25 site
  - Organize into `data/tpc25/artifacts/` folder
  - Create `data/tpc25/sessions.json` with session roster
  - Convert any PDFs to PPTX or extract to text files
- [ ] **Create repository structure** (run setup script from `pre_hackathon_setup.md`)
- [ ] **Set up communication channels**:
  - Slack workspace or Discord server
  - GitHub repository with issues enabled
  - Zoom room link for March 31 and April 7
- [ ] **Prepare schemas** (copy verbatim from `pre_hackathon_setup.md`)
- [ ] **Create fixture** for testing (`tests/fixtures/tpc24_mini/`)
- [ ] **Test environment setup** on your machine (verify all dependencies install)

### Nice to have:
- [ ] Set up GitHub Projects board with initial tasks
- [ ] Create PR template and contribution guidelines
- [ ] Set up basic CI (pytest on push)
- [ ] Invite team members to GitHub repo ahead of time

---

## 3) Before March 31: Participant Prep (send to team)

**Required** (everyone must do before March 31):
1. Clone the repository
2. Install dependencies (`pip install -e .`)
3. Verify Python 3.9+ installed
4. Get LLM API key (OpenAI or Anthropic) and test it
5. Join Slack/Discord channel
6. Review README.md and PLAN.md

**Helpful** (recommended):
- Familiarize with Pydantic if not already comfortable
- Review `python-docx` and `python-pptx` documentation
- Read through the schema definitions

---

## 4) March 31 (2-4 hours): Kickoff Session

### Agenda

**Hour 1: Orientation (everyone together)**
- Introductions (name, background, what excites you about this project)
- Charlie presents: TPC25 context, why we need this tool
- Demo of desired end state (show example report)
- Walk through architecture diagram
- Q&A on scope and goals

**Hour 2: Technical Deep Dive**
- Repository structure walkthrough
- Schema overview (Event, Session, Artifact, Match, Report)
- CLI contract and workflow phases
- Development workflow (branches, PRs, testing)
- Communication norms (when to use Slack vs GitHub issues vs Zoom)

**Hour 3-4: Setup & Task Assignment**
- **Environment verification** (everyone runs tests locally)
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -e .
  pytest  # should see fixture test
  ```
- **Role assignment** (based on interests and skills)
- **Task assignment for April 1-6** (see section 5 below)
- Create GitHub issues for all tasks
- Assign owners (primary + backup for each task)
- Set expectations for April 7

**Outcomes:**
- Everyone has working dev environment
- Everyone has 1-2 tasks assigned for April 1-6
- GitHub issues created and assigned
- Clear understanding of MVP scope

---

## 5) April 1-6: Independent Async Work

### Philosophy
Small, well-defined tasks that can be done independently without blocking. PRs should be reviewable in < 30 minutes.

### Task List (GitHub issues)

**Priority 1 (must be done before April 7):**

**Issue #1: Schema Implementation** [2-3 hours]
- Implement all Pydantic models in `tpc_reporter/schemas/`
- Copy verbatim from `pre_hackathon_setup.md`
- Add unit tests for schema validation
- **Owner**: Orchestration Lead

**Issue #2: Config Loader** [2-3 hours]
- Implement YAML config parser in `tpc_reporter/tools/config.py`
- Load Event object from YAML
- Handle file path resolution
- Add validation and helpful error messages
- **Owner**: Ingestion Lead

**Issue #3: File Inventory** [2-3 hours]
- Implement `tpc_reporter/tools/collect.py`
- Scan folder recursively for supported file types
- Create Artifact objects (without text extraction yet)
- Compute sha256 checksums
- **Owner**: Ingestion Lead

**Issue #4: Text Extractors** [3-4 hours]
- Implement extractors for: `.txt`, `.md`, `.csv`, `.docx`, `.pptx`
- Store extracted text in Artifact objects
- Handle extraction errors gracefully
- **Owner**: Extraction Lead

**Issue #5: State Persistence** [2-3 hours]
- Implement `tpc_reporter/storage/state_store.py`
- Save/load WorkflowState to JSON
- Create run directories with unique IDs
- **Owner**: Orchestration Lead

**Issue #6: CLI Stubs** [2 hours]
- Complete CLI in `tpc_reporter/cli.py`
- Wire up all commands (can call NotImplementedError stubs)
- Add help text and validation
- **Owner**: DevOps Lead

**Priority 2 (nice to have before April 7):**

**Issue #7: Session Ingestion** [2 hours]
- Parse `sessions.json` into Session objects
- Support basic CSV roster as well
- **Owner**: Ingestion Lead

**Issue #8: Basic Matcher Logic** [2-3 hours]
- Implement exact filename matching
- Implement fuzzy matching with fuzzywuzzy
- Return Match objects with confidence
- **Owner**: Matching Lead

**Issue #9: Fixture Expansion** [2 hours]
- Expand test fixture with more realistic data
- Create sample PPTX file
- Add expected outputs
- **Owner**: QA Lead

**Issue #10: Documentation** [1-2 hours]
- Add docstrings to all modules
- Update README with any learnings
- Create CONTRIBUTING.md
- **Owner**: DevOps Lead

### Coordination during April 1-6
- Post updates in Slack daily (doesn't need to be long)
- Open PRs early and request reviews
- If blocked, post in #help channel
- Aim for 2-3 PRs merged by April 6

---

## 6) April 7 (6-8 hours): Remote Sprint Day

### Goal
Get the pipeline working end-to-end through the MATCH phase.

### Structure

**9:00 AM: Daily Standup** (30 min)
- Everyone joins Zoom
- Quick status: what's done, what's in progress, any blockers
- Prioritize tasks for the day
- Assign any new work items
- **Keep Zoom open** for rest of day (mute when working, unmute to ask questions)

**9:30 AM - 12:00 PM: Morning Sprint**
Focus areas:
- **Team A** (Orchestration + Ingestion): Wire up `ingest` command end-to-end
- **Team B** (Extraction + Matching): Complete text extraction and basic matching
- **Team C** (QA + DevOps): Testing infrastructure, CI setup

**12:00 PM: Midday Check-in** (30 min)
- Demo what's working
- Surface any blockers
- Adjust afternoon priorities

**12:30 PM - 4:00 PM: Afternoon Sprint**
Integration work:
- Connect ingest → extract → match
- Test on real TPC25 data
- Fix bugs
- Documentation

**4:00 PM: End-of-Day Demo** (30 min)
- Demo the pipeline running (even if buggy)
- Celebrate progress
- Assign tasks for April 8-13

### Target Deliverables for April 7
- ✅ `tpc_reporter ingest --config` works and creates run directory
- ✅ Artifact collection extracts text from all supported formats
- ✅ `tpc_reporter match --run` produces matches with confidence scores
- ✅ State is persisted correctly
- ✅ Tests pass on fixture

---

## 7) April 8-13: Independent Async Work (Phase 2)

### Task List (assigned at end of April 7)

**Priority 1 (must be done before April 14):**

**Issue #11: Summarizer Prompt** [3-4 hours]
- Design prompt template for summarizer
- Enforce structured output format
- Require "Sources Used" list
- Test on sample session
- **Owner**: Prompt Engineer / Summarization Lead

**Issue #12: Summarizer Agent** [3-4 hours]
- Implement `tpc_reporter/agents/summarizer.py`
- Call LLM with session artifacts
- Parse and structure output
- Handle token limits
- **Owner**: Summarization Lead

**Issue #13: Evaluator Prompt** [2-3 hours]
- Design QA rubric (coverage, faithfulness, specificity, actionability)
- Create prompt template
- Test scoring on sample summaries
- **Owner**: Prompt Engineer / QA Lead

**Issue #14: Evaluator Agent** [2-3 hours]
- Implement `tpc_reporter/agents/evaluator.py`
- Score summaries with LLM
- Run deterministic checks (required sections, etc.)
- Flag issues for review queue
- **Owner**: QA Lead

**Issue #15: Review Queue Export** [2 hours]
- Export low-confidence matches to `review_queue/matches.json`
- Export flagged summaries to `review_queue/<session_id>_draft.md`
- Document review workflow
- **Owner**: Orchestration Lead

**Priority 2 (nice to have):**

**Issue #16: Publisher** [2-3 hours]
- Implement `tpc_reporter/agents/publisher.py`
- Assemble full report from session summaries
- Add executive summary
- **Owner**: Any available

**Issue #17: Integration Tests** [2-3 hours]
- End-to-end test on full fixture
- Add more unit tests
- **Owner**: QA Lead

**Issue #18: Error Handling** [2-3 hours]
- Add retry logic for LLM API calls
- Better error messages
- Logging
- **Owner**: DevOps Lead

### Coordination during April 8-13
- Less structured than April 7, but still communicate in Slack
- Focus on getting summarization working well
- Test on real TPC25 data if possible
- PR reviews within 24 hours

---

## 8) April 14-16 (3 days × 8h): In-Person Hackathon

### Day 1 (April 14): Integration & Bug Fixing

**Morning (9 AM - 12 PM):**
- Standup: status of all components
- Integration work: connect all phases
- Run full pipeline on TPC25 data
- Document all bugs and issues

**Afternoon (1 PM - 5 PM):**
- Bug bash: fix critical issues
- Improve prompts based on real outputs
- Performance testing (LLM costs, runtime)

**Goal for Day 1:** Full pipeline runs without crashing, produces output (even if quality needs work)

### Day 2 (April 15): Quality & Polish

**Morning (9 AM - 12 PM):**
- Review summarizer output quality
- Iterate on prompts to improve summaries
- Tune confidence thresholds
- Test review workflow

**Afternoon (1 PM - 5 PM):**
- Documentation pass
- User guide / tutorial
- Code cleanup
- Stretch features (if time)

**Goal for Day 2:** Outputs are high enough quality to be useful, documentation is complete

### Day 3 (April 16): Testing & Demo Prep

**Morning (9 AM - 12 PM):**
- Final testing on complete TPC25 dataset
- Validate all outputs manually
- Fix any last critical bugs
- Finalize documentation

**Afternoon (1 PM - 4 PM):**
- Prepare demo presentation
- Record demo video
- Create README with screenshots/examples
- Celebrate!

**4 PM - 5 PM: Final Demo**
- Show complete end-to-end workflow
- Present sample outputs
- Discuss lessons learned
- Plan for post-hackathon improvements

### Target Deliverables for April 14-16
- ✅ Complete, tested pipeline on real TPC25 data
- ✅ High-quality summaries that TPC can actually use
- ✅ All documentation complete
- ✅ Demo video/presentation
- ✅ Clear roadmap for future enhancements

---

## 9) Technical Implementation Details

### Workflow Phases (from `pre_hackathon_setup.md`)

1. **INGEST** (load config + sessions + artifacts; write state)
2. **MATCH** (produce matches + review queue if needed)
3. **SUMMARIZE** (draft per-session summaries)
4. **EVALUATE** (QA scores + flags; review queue if needed)
5. **PUBLISH** (assemble final `report.md`)

### WorkflowState (persisted)
`state.json` must include:
- `event`, `sessions[]`, `artifacts[]`
- `matches[]`, `unmatched_artifacts[]`
- `summaries{session_id: ReportSection}`
- `qa{session_id: QAResult}`
- `phase` (last completed)

### Review Gates
- After `MATCH`: gate if any match confidence < 0.70 or any unmatched artifacts exist
- After `EVALUATE`: gate if any QA flag present or any score < 3

---

## 10) Success Metrics

### MVP (must have):
- ✅ Works on real TPC25 conference data
- ✅ Generates accurate session summaries
- ✅ Produces full meeting report
- ✅ QA catches major issues
- ✅ Review workflow is usable
- ✅ Documentation is clear and complete
- ✅ Tests pass

### Stretch Goals (nice to have):
- Better matching with semantic embeddings
- PDF support
- Streamlit UI for review
- Cost optimization (cheaper models for some tasks)
- Parallel processing for speed

---

## 11) Post-Hackathon (explicitly out of scope)

- HTML agenda scraping
- Google Drive/Sheets connectors
- Multi-event corpus and cross-event retrieval
- Production deployment infrastructure
- Advanced citation/provenance tracking
- Multi-agent chat interface

---

## Appendix: Quick Reference

### Key Files to Create
```
tpc_reporter/schemas/event.py
tpc_reporter/schemas/artifact.py
tpc_reporter/schemas/match.py
tpc_reporter/schemas/report.py
tpc_reporter/schemas/state.py
tpc_reporter/tools/config.py
tpc_reporter/tools/collect.py
tpc_reporter/tools/extract.py
tpc_reporter/agents/matcher.py
tpc_reporter/agents/summarizer.py
tpc_reporter/agents/evaluator.py
tpc_reporter/agents/publisher.py
tpc_reporter/orchestrator/workflow.py
tpc_reporter/storage/state_store.py
tpc_reporter/cli.py
```

### Dependency Checklist
- pydantic >= 2.0
- python-docx >= 1.0
- python-pptx >= 0.6.21
- pyyaml >= 6.0
- click >= 8.0
- openai >= 1.0 (or anthropic)
- fuzzywuzzy
- pytest (dev)
- ruff, black (dev)
