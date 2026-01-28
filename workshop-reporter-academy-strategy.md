# Workshop Reporter on Academy: Implementation Strategy

This document maps **our workshop‐reporter plan** (parse a workshop URL → extract session metadata → inventory a shared Google Drive → match docs to sessions → produce session pages / proceedings outputs) onto the **Academy** agent middleware from the `academy-agents` GitHub organization.

It also answers the design question: **yes — the system can (and should) have a continuously running orchestrator** that directs other agents and tools. In Academy terms, that orchestrator is simply an agent with one or more **control loops** (e.g., `@timer` loops) that (a) watches for new jobs or changed inputs and (b) calls actions on other agents via handles. The Academy docs explicitly describe “LLM as an orchestrator (agents as tools)” as a supported pattern.

---

## 1) Executive summary

### What we build
A **closed-loop, cooperative multi-agent system** that repeatedly:

1. **Ingests** a workshop program/schedule from a URL (and/or structured schedule input).
2. **Normalizes** sessions/talks/people into a canonical schema.
3. **Inventories** a Google Drive folder (metadata + optionally content extraction).
4. **Matches** Drive files to sessions/talks (rules + embeddings + confidence).
5. **Generates** outputs (Markdown/HTML/PDF, plus JSON manifests) and pushes to Drive/Git.
6. **Evaluates** quality (coverage, conflicts, low-confidence matches) and triggers fixes.
7. **Notifies** humans only when needed (low confidence, missing artifacts, approvals).

### Why Academy fits
Academy provides the primitives we need for a robust orchestrated system:

- **Agents**: stateful processes executing behavior (actions + control loops).
- **Actions**: remotely invocable methods for discrete steps (parse, index, match, render).
- **Control loops**: long-running “watcher” routines (poll Drive, run nightly rebuilds, etc.).
- **Handles**: typed references that let one agent call actions on another asynchronously.
- **Manager + Exchange + Launcher**: a clean separation between *behavior* and *deployment* across threads, processes, clusters, or federated resources.

---

## 2) Architecture overview

### 2.1 Agent roster (MVP → full)

**Core “pipeline” agents**
- **OrchestratorAgent** (always-on): owns the run state machine; dispatches tasks; retries; checkpoints.
- **ProgramIngestAgent**: fetches workshop schedule / agenda; extracts sessions, speakers, talk titles, times, links.
- **DriveIndexAgent**: lists files, permissions, metadata; optionally extracts text for embeddings.
- **DocExtractAgent**: converts PDFs/Docs to text and structured signals (title, authors, first page, keywords).
- **MatchAgent**: links files to sessions/talks using heuristics + embeddings + constraints.
- **SummarizeAgent**: creates per-talk/session summaries, agendas, “what’s missing” dashboards.
- **PublishAgent**: writes artifacts to Drive and/or a Git repo; produces a stable “proceedings” structure.

**Quality + governance agents**
- **QAAgent**: checks coverage, duplicates, conflicts; runs rubric-based checks and emits issues.
- **HumanGatekeeperAgent** (optional early; essential later): collects approvals for low-confidence decisions.

**Optional scale-out agents**
- **EmbeddingWorkerPool**: parallel embedding + similarity indexing.
- **MonitorAgent**: metrics + alerts, plus automatic run resumption after failures.

### 2.2 Control plane vs data plane
- **Control plane** (Academy messaging): small, frequent messages describing actions and results.
- **Data plane** (files, extracted text, embeddings): large objects stored out-of-band (Drive, blob store, local cache). In later phases, consider pass-by-reference patterns (e.g., ProxyStore) if large objects are frequently exchanged.

### 2.3 Orchestrator pattern (continuous supervisor)
The orchestrator is implemented as an Academy agent with:
- **Actions**: `submit_job()`, `resume_job()`, `get_status()`, `rebuild_outputs()`, `shutdown_all()`
- **Control loops**: `@timer` loop every N minutes to pick up new jobs and advance state; another loop for health checks and auto-restarts.

This turns our system into a service: “drop a workshop URL + Drive folder ID” and the orchestrator does the rest, asking humans only when needed.

---

## 3) Message contracts and data schemas

### 3.1 JobSpec (input)
A single “run” is driven by a **JobSpec**:

```json
{
  "job_id": "2026-01-28-osaka-workshop",
  "workshop_url": "https://…",
  "drive_root_folder_id": "…",
  "output_targets": {
    "drive_folder_id": "…",
    "git_repo": "org/repo",
    "branch": "main"
  },
  "policies": {
    "min_match_confidence": 0.80,
    "require_human_approval_below": 0.65,
    "allow_web_fetch": true
  }
}
```

### 3.2 CanonicalWorkshopModel (internal truth)
Normalize everything into a canonical structure:

- `workshop`: title, dates, timezone, location, URL(s)
- `sessions[]`: id, title, start/end, room, chair(s)
- `talks[]`: id, session_id, title, author list, abstract, keywords
- `people[]`: id, name variants, affiliations, emails (where permitted)
- `artifacts[]`: files + metadata + extracted signals
- `links[]`: talk↔artifact edges with confidence + explanation

This allows us to:
- regenerate outputs deterministically
- re-run matching without re-scraping
- compare versions over time

### 3.3 “Explainable matching” record
Every match should carry evidence:

```json
{
  "talk_id": "t-031",
  "file_id": "drive:1abC…",
  "confidence": 0.87,
  "evidence": {
    "title_similarity": 0.91,
    "author_overlap": ["Chard", "Foster"],
    "session_hint": "Session 3: Federated Agents",
    "embedding_cosine": 0.84,
    "rules_fired": ["pdf_first_page_title_match", "author_list_match"]
  }
}
```

---

## 4) Agent behaviors (what goes where)

### 4.1 ProgramIngestAgent
Actions:
- `fetch_program(url) -> raw_html`
- `extract_sessions(raw_html) -> CanonicalWorkshopModel.delta`
- `extract_talks(raw_html) -> CanonicalWorkshopModel.delta`

Notes:
- Keep the HTML parsing deterministic and testable.
- Support multiple “parsers” via strategy pattern: `IndicoParser`, `SchedParser`, `CustomHTMLParser`.

### 4.2 DriveIndexAgent
Actions:
- `list_files(folder_id) -> [FileMeta]`
- `watch_changes(folder_id, cursor) -> changes`
- `download_file(file_id) -> local_path` (optional; prefer streaming)

### 4.3 DocExtractAgent
Actions:
- `extract_text(file_meta) -> ExtractedDoc`
- `extract_signals(extracted_doc) -> {title, authors, keywords, fingerprints}`

Implementation tips:
- Use a cache keyed by `(file_id, modified_time, extractor_version)`.

### 4.4 MatchAgent
Actions:
- `propose_matches(model, artifacts) -> match_edges[]`
- `resolve_conflicts(match_edges) -> match_edges[]` (dedupe, 1:1 constraints)
- `flag_for_review(match_edges) -> review_queue[]`

### 4.5 PublishAgent
Actions:
- `render_session_pages(model, matches) -> outputs`
- `write_drive(outputs)`
- `write_git(outputs)`

Outputs should include:
- `workshop.json` (canonical)
- `matches.json` (explainable edges)
- `reports/` (Markdown pages, indices)
- `qa/` (coverage dashboards, issues)

---

## 5) State, checkpointing, and idempotency

### 5.1 Durable run state
Each job advances through states like:

`NEW → INGESTED → INDEXED → EXTRACTED → MATCHED → PUBLISHED → VERIFIED → DONE`

Store:
- the canonical model
- the artifact inventory
- the match graph
- the last completed stage
- errors + retry counters

Academy supports persistent, dictionary-like state utilities (e.g., file-backed state). Use that for:
- per-agent local state (caches, cursors)
- orchestrator job registry

### 5.2 Idempotency rules
To make “resume” safe:
- All actions should be **pure** or **idempotent** with respect to `(job_id, stage, inputs_version)`.
- Publishing should be “write to a new staging folder / branch, then swap pointer” when possible.

### 5.3 Replay / audit
Keep an append-only log per job:
- action requests + results (summaries)
- versions of inputs (program HTML hash, Drive file list hash)
- match explanations

---

## 6) Deployment strategy with Academy

### 6.1 Local development (fast iteration)
- **ThreadExchange + ThreadLauncher** for unit tests and local integration tests.
- Keep agents as behaviors with minimal external dependencies.

### 6.2 Single host production (simple, robust)
- **RedisExchange** (or other distributed exchange option) + **ProcessLauncher**.
- Run Orchestrator + indexing + publishing as long-lived processes.
- Scale extraction/embedding via a worker pool (either as agents-as-workers or internal executors).

### 6.3 Federated / HPC scale-out
When extraction/embedding or other heavy tasks need HPC-scale throughput:
- Use **Globus Compute** (or Parsl) to launch worker agents near compute/storage.
- Use the Academy *hosted exchange* / remote exchange pattern so agents can communicate across sites even with asymmetric networking constraints (NAT/firewalls).

This matches the “federated agents” vision in Academy’s design literature and case studies.

---

## 7) Tool integration patterns (agents directing tools)

### 7.1 “Tools inside actions”
Simplest: each agent action calls normal Python libraries (Drive API, HTML parsing, PDF extraction, embeddings).

### 7.2 LLM orchestrator (agents as tools)
If you want a reasoning layer that dynamically chooses which agent to invoke:
- Make an `LLMOrchestratorAgent` whose actions call the underlying agents via handles.
- Wrap each action invocation in a “tool” schema compatible with your LLM framework (LangChain, pydanticAI, etc.).
- Keep the LLM’s role constrained to **control decisions**; the heavy lifting is deterministic agent actions.

### 7.3 MCP connectivity (optional)
If you already have tools exposed via Model Context Protocol (MCP), you can connect Academy to MCP clients/servers to unify tool calling across your ecosystem. This is especially useful if you want:
- Chat-based operator control (“build proceedings for job X”)
- Human-in-the-loop corrections via chat interfaces

---

## 8) Observability and evaluation

### 8.1 Metrics to track
- Coverage: % talks with ≥1 matched artifact
- Confidence distribution: histogram by stage
- Conflict rate: # duplicates, many-to-one, etc.
- Time per stage; queue latency; retries

### 8.2 Automated QA checks (QAAgent)
- Missing talk artifacts
- Multiple candidate files with similar confidence
- Mismatch between extracted author list and program author list
- Duplicate file used for multiple talks (unless explicitly allowed)
- Broken links / missing permissions

---

## 9) Implementation roadmap (pragmatic phases)

### Phase 0 — Skeleton + “hello agents”
- Stand up an Academy `Manager` with ThreadExchange/ThreadLauncher
- Implement `OrchestratorAgent` with a persistent job registry
- Implement stub agents with “echo” actions

### Phase 1 — Deterministic pipeline MVP
- ProgramIngestAgent parses one workshop format reliably
- DriveIndexAgent lists Drive files and basic metadata
- MatchAgent does rules-only matching (filename/title heuristics)
- PublishAgent generates minimal Markdown outputs + JSON manifests

Deliverable: **one workshop end-to-end** with reproducible outputs.

### Phase 2 — Extraction + embeddings
- DocExtractAgent for PDF/Docs text extraction (cached)
- Add embeddings + similarity index
- Add explainable match evidence and conflict resolver

Deliverable: **high coverage with confidence scores** and a review queue.

### Phase 3 — Closed loop + human-in-the-loop
- QAAgent generates actionable “fix lists”
- HumanGatekeeperAgent gates low-confidence decisions
- Orchestrator supports incremental updates (Drive changes)

Deliverable: **continuous operation** during a live workshop.

### Phase 4 — Federated scale-out
- Move heavy tasks (extraction/embeddings) to a worker pool
- Optionally deploy workers on federated resources (Globus Compute/Parsl)

Deliverable: **throughput at scale** across multiple workshops.

---

## 10) Suggested repo layout for our implementation

```
workshop-reporter/
  pyproject.toml
  src/workshop_reporter/
    agents/
      orchestrator.py
      ingest_program.py
      drive_index.py
      doc_extract.py
      match.py
      summarize.py
      publish.py
      qa.py
    schemas/
      job_spec.py
      canonical_model.py
      match_graph.py
    tools/
      drive_client.py
      web_fetch.py
      pdf_extract.py
      embeddings.py
    cli.py
  tests/
    test_ingest.py
    test_match.py
    test_publish.py
  docs/
    ARCHITECTURE.md
    RUNBOOK.md
```

---

## 11) Concrete “next actions” to start implementing

1. **Define schemas first**: `JobSpec`, `CanonicalWorkshopModel`, `MatchEdge`, `OutputManifest`.
2. Build `OrchestratorAgent` with:
   - `submit_job()`
   - `advance_job(job_id)` (pure state machine)
   - `@timer` loop calling `advance_job()` for active jobs
3. Implement `ProgramIngestAgent` for the first workshop site you care about most.
4. Implement `DriveIndexAgent` using Drive API with a stable file inventory format.
5. Implement `PublishAgent` minimal output: `index.md`, per-session pages, `workshop.json`, `matches.json`.
6. Add matching heuristics; then add extraction; then embeddings.

---

## 12) Notes on the “Agentic Discovery” alignment

The “agentic discovery” framing is helpful because it pushes us toward:
- **closed-loop operation** (always improving outputs as new artifacts arrive),
- **cooperative agents** with specialized roles (ingest, match, publish, QA),
- **human oversight only when needed** (gate low-confidence decisions).

This workshop reporter is an “information-extraction discovery loop” rather than a lab loop, but the same cooperative-agent patterns apply.

---

## Appendix: Where to look in Academy docs

- “Get Started” for exchange/launcher patterns and local/distributed setups.
- “Building HPC Agents” for Globus Compute / hosted exchange deployment patterns.
- “LLM Agents” for “LLM as orchestrator” and “agents as tools” patterns.
- “academy.state” for file-backed, dictionary-like state persistence utilities.
- The arXiv preprint(s) and “Agentic Discovery” paper for conceptual grounding.

