# Implementation Plan: Workshop Agent

## Overview

We will implement a goal-driven agent loop that performs autonomous session extraction and document matching. The system will maintain memory, reason about its state, and dynamically choose next steps using LLM calls.

To the extent possible we will vibe code to attempt to get a basic working system in place within 30 hours during the 
[TPC25](tpc25.org) Hackathon.

For the *big picture* objectives, see [README.md](./README.md)

---

## Phases and Tasks

### Phase 1: Setup and Inputs
- [ ] Accept a workshop URL (via API or downloaded html source).
- [ ] Accept a Google Drive folder URL (via API or downloaded *session.csv* participants and *sessionname.doc* discussion notes)).
- [ ] Accept a Google Sheets file URL (via API or download) with all lightning talks metadata (author, title, abstract, session name, etc.)
- [ ] Initialize agent memory state (sessions list, documents list, match records, outstanding questions).

### Phase 2: Session Extraction
- [ ] Scrape the workshop page (HTML).
- [ ] Extract sessions, leaders, talk titles, and session abstracts using LLM.
- [ ] Extract talk abstracts using LLM (from lightning talk metadata URL or downloaded CSV)
- [ ] Store as structured metadata (e.g. JSON format).

### Phase 3: Document Loading and Representation
- [ ] List all files in the Google Drive folder.
- [ ] For each file, extract the filename and contents (text).
- [ ] Normalize filenames for easier comparison (e.g. lowercase, remove punctuation).
- [ ] Store document summaries or embeddings for similarity comparison.

### Phase 4: Document–Session Matching
- [ ] Implement string similarity and/or embedding-based matching.
- [ ] Use LLM to generate candidate matches and justification.
- [ ] For ambiguous cases, add to a `questions_for_user` queue.

### Phase 5: Agent Loop and Planning
- [ ] Create a stateful agent loop: observe → reason → act.
- [ ] Use the LLM to select the next best tool (e.g., "match documents", "ask user").
- [ ] Define tools: extract_sessions, extract_metadata, match_docs, ask_user, output_report.

### Phase 6: Output and User Feedback
- [ ] Generate a final structured report linking sessions to files.
- [ ] Output unmatched sessions and files.
- [ ] Optionally prompt the user for unresolved items.

---

## Division of Labor

- **Web/Data Ingestion**: Workshop HTML scraping and Drive file loading.
- **LLM Tooling**: Prompt templates for extraction and matching.
- **Matching Logic**: Heuristics and semantic similarity.
- **Agent Framework**: Memory, loop, tool execution.
- **Reporting/UI**: Output structured results, user prompts.

---

## Stretch Goals

- Use LangGraph or CrewAI for planning.
- Add embeddings for matching via FAISS or similar.
- Build a simple Streamlit or CLI UI.

