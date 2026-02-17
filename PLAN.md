# Implementation Plan: TPC Workshop Reporter
## Hackathon Edition

**Team**: 4-6 developers (Python proficient)
**Goal**: Generate 8 draft track reports from TPC25 data, ready for human review

---

## Status: Baseline Pipeline Complete

The initial pipeline described below has been built and is working. The hackathon goal is now to use this baseline to **explore building an agentic system with LangGraph**.

---

## What We Built

A working Python pipeline that:
1. **Scrapes** the TPC website to get the conference structure (tracks, sessions, lightning talks)
2. **Collects** notes and attendees from Google Drive (one folder per track)
3. **Assembles** a data bundle per track (website data + Drive data)
4. **Generates** a draft report per track using an LLM
5. **Checks** each draft for hallucinations using a second LLM pass
6. **Outputs** Markdown reports for human review

---

## Hackathon Goal: LangGraph Agentic System

The baseline pipeline is a linear sequence of function calls. The hackathon explores wrapping it as an agentic system using **LangGraph**, where an LLM decides which tools to call and in what order, with built-in error recovery and state management.

Each pipeline step is already a clean function — these become LangGraph tools:

```python
tools = [
    {"name": "scrape_website",  "fn": scraper.scrape_website,         "description": "..."},
    {"name": "collect_drive",   "fn": gdrive.download_sheet,          "description": "..."},
    {"name": "assemble_track",  "fn": assembler.assemble_track_bundle, "description": "..."},
    {"name": "generate_report", "fn": generator.generate_report,       "description": "..."},
    {"name": "check_report",    "fn": checker.check_report,            "description": "..."},
]

# User says: "Generate the Workflows track report for TPC26"
# LangGraph agent decides which tools to call and in what order
```

### Key Questions to Explore

- How does LangGraph state management compare to our simple file-based handoffs?
- Can the agent handle partial failures (e.g., missing notes for one session) better than re-running manually?
- Does an agentic loop improve report quality through iterative refinement?
- What's the overhead of LangGraph vs. the benefit for a pipeline this size?

---

## Data Flow (Reference)

```
tpc25.org/sessions/ ──scrape──→ conference.json
                                      │
Google Drive folders ──collect──→ track_inputs/
                                      │
                              ┌───assemble───┐
                              │              │
                        track_bundle_1.json ... track_bundle_8.json
                              │              │
                        ┌──generate──┐  ┌──generate──┐
                        │            │  │            │
                  draft_1.md    draft_2.md  ...  draft_8.md
                        │            │
                  ┌──check──┐  ┌──check──┐
                  │         │  │         │
            report_1.md  report_2.md  ...  report_8.md
                  │
            (human review)
```

---

## Data Model

### Conference Structure (from website)

```json
{
  "conference": {
    "id": "tpc25",
    "name": "TPC25",
    "website": "https://tpc25.org"
  },
  "tracks": [
    {
      "id": "workflows",
      "name": "Workflows",
      "room": "Main Plenary",
      "sessions": [
        {
          "id": "dwarf-1",
          "title": "DWARF: Keynote and Systems Software for Agents",
          "slot": "2025-07-30T16:00",
          "duration_minutes": 90,
          "leaders": [
            {"name": "Ian Foster", "affiliation": "Argonne National Laboratory"}
          ],
          "lightning_talks": [
            {
              "title": "Academy: Empowering Scientific Workflows with Federated Agents",
              "authors": [{"name": "Kyle Chard", "affiliation": "University of Chicago"}],
              "abstract": "..."
            }
          ]
        }
      ]
    }
  ]
}
```

### Track Bundle (assembled per track, fed to LLM)

```json
{
  "track": {"id": "workflows", "name": "Workflows"},
  "sessions": [
    {
      "id": "dwarf-1",
      "title": "DWARF: Keynote and Systems Software for Agents",
      "slot": "2025-07-30T16:00",
      "leaders": ["Ian Foster (ANL)", "Neeraj Kumar (PNNL)"],
      "lightning_talks": ["... from website ..."],
      "attendees": ["... from Google Sheet ..."],
      "notes": "... from Google Doc ..."
    }
  ],
  "sources": ["tpc25.org/sessions/", "Drive: Workflows/Session1_Notes", "..."]
}
```

---

## Team Roles

| Role | Focus |
|------|-------|
| **LangGraph Lead** | Graph design, state schema, node/edge wiring |
| **Tools Lead** | Wrapping existing functions as LangGraph tools |
| **LLM/Prompt Lead** | Agent prompt, tool descriptions, output quality |
| **Domain Expert** | Review outputs, validate quality against baseline |
