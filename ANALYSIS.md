# TPC Workshop Reporter: Architecture Analysis & Simplified Plan

## 1. Executive Summary

After reviewing the existing project documents, the TPC25 website structure, and the clarified requirements, this document recommends a **significant simplification** of the Workshop Reporter system. The key changes are:

1. **Drop LangGraph** for the hackathon MVP. Use a simple Python pipeline with clean function boundaries. The agentic layer comes from LLM tool-use, not a state machine framework.
2. **Restructure around tracks** (not individual sessions). TPC25 had 6 parallel tracks with 5 time slots each. TPC26 will have 8 tracks. We produce **one report per track**.
3. **Define a clear JSON data model** for the conference structure.
4. **Simplify the input pipeline**: website scraping for lightning talks + Google Drive for notes/attendees.
5. **Replace the QA framework** with a single hallucination-check LLM pass.
6. **Target: 8 draft reports**, each reviewed by the track organizer.

---

## 2. Understanding the Conference Structure

### TPC25 (What We're Testing Against)

From the TPC25 website, the breakout structure is:

- **6 parallel tracks** (themes: Workflows, Initiatives, Life Sciences, Evaluation, Scale & Services, Applications)
- **5 time slots** (Wed 14:00, Wed 16:00, Thu 8:30, Thu 11:00, Thu 14:00)
- **30 total session slots** (6 tracks × 5 slots)
- Each track contains **1–5 mini-workshops** (some span multiple slots, some are single-slot BOFs)
- Each 90-minute session has **4–6 lightning talks** followed by group discussion
- ~120 lightning talks total across all sessions

Example: The **Workflows** track (Main Plenary room) contains:
- **DWARF** (3 sessions: Wed 16:00, Thu 8:30, Thu 11:00) — a multi-session working group
- **BOF: LLMs for Living Docs** (1 session: Thu 14:00) — a single-session BOF

### TPC26 (What We're Building For)

- **8 parallel tracks**, 5 time slots → 40 session slots
- Similar structure: each track has 1–5 mini-workshops
- We produce **one draft report per track** (8 reports total)

### Data Model

The key insight is a **three-level hierarchy**:

```
Conference (e.g., TPC25)
  └── Track (e.g., "Workflows", room: Main Plenary)
        └── Session Slot (e.g., Wed 16:00)
              └── Lightning Talks (4-6 per slot)
              └── Attendees (per slot)
              └── Notes/Transcript (per slot)
```

The **track** is the unit of reporting. Within each track, we need to know which lightning talks belong to which session slot, and we may have separate notes and attendees lists for each slot.

---

## 3. Recommended Architecture

### Why Not LangGraph (For the MVP)

LangGraph solves problems we don't have yet:

| LangGraph Feature | Do We Need It? |
|---|---|
| State persistence/checkpointing | No — 8 reports, run takes minutes |
| Conditional routing | No — pipeline is linear |
| Human-in-the-loop gates | No — humans review final drafts |
| Parallel node execution | No — sequential is fine for 8 tracks |
| Retry/error recovery | No — just re-run |

LangGraph adds learning overhead for the hackathon team without proportional benefit. The team's time is better spent on data quality and prompt engineering.

**What about the agentic vision?** The path to "tell the agent to make me a report" runs through **LLM tool-use** (the LLM decides what functions to call), not through a predetermined state graph. The simple pipeline we build now becomes the set of tools the agent calls later. LangGraph can be added as a wrapper in Phase 2 if needed.

### Recommended Pipeline

```
scrape_website(url) → conference.json
                              ↓
collect_google_drive(folder_id) → track_inputs/
                              ↓
for each track:
    assemble_track_data(conference.json, track_inputs/) → track_bundle.json
                              ↓
    generate_report(track_bundle.json, prompt) → draft_report.md
                              ↓
    check_hallucinations(draft_report.md, track_bundle.json) → flagged_report.md
                              ↓
output: 8 flagged draft reports for human review
```

Each step is a **standalone Python function** that reads files and writes files. No framework, no state machine. Any function can be re-run independently.

### Why This Is Still "Agentic"

The agentic version (Phase 2) looks like this:

```python
# The human says:
"Generate the TPC26 Workflows track report. 
 The website is tpc26.org, and the Google Drive folder is [URL]."

# The LLM (with tool-use) decides to:
1. Call scrape_website("tpc26.org") 
2. Call collect_google_drive(folder_url)
3. Call assemble_track_data("Workflows")
4. Call generate_report(...)
5. Call check_hallucinations(...)
6. Return the draft
```

The tools are the same functions. The "agent" is the LLM deciding what order to call them and handling errors. This is simpler, more flexible, and more hackathon-friendly than a LangGraph state machine.

---

## 4. Data Model (JSON)

### Conference Structure (`conference.json`)

This is scraped from the website and represents the full conference structure:

```json
{
  "conference": {
    "id": "tpc25",
    "name": "TPC25 Annual Meeting",
    "dates": "2025-07-28 to 2025-07-31",
    "location": "San Jose, California",
    "website": "https://tpc25.org"
  },
  "tracks": [
    {
      "id": "workflows",
      "name": "Workflows",
      "room": "Main Plenary",
      "description": "...",
      "sessions": [
        {
          "id": "dwarf-1",
          "title": "DWARF: Keynote and Systems Software for Agents",
          "parent_workshop": "Data Workflows, Agents, and Reasoning Frameworks (DWARF)",
          "slot": "2025-07-30T16:00",
          "duration_minutes": 90,
          "leaders": [
            {"name": "Ian Foster", "affiliation": "Argonne National Laboratory and University of Chicago"},
            {"name": "Neeraj Kumar", "affiliation": "Pacific Northwest National Laboratory"}
          ],
          "description": "This multi-session track explores...",
          "lightning_talks": [
            {
              "title": "A Case Study of the System Software/Middleware Needs for Agents",
              "authors": [
                {"name": "Ian Foster", "affiliation": "University of Chicago and Argonne National Laboratory"}
              ],
              "abstract": "..."
            }
          ]
        },
        {
          "id": "dwarf-2",
          "title": "DWARF: Scalable Scientific Data/Scientific Data for AI",
          "parent_workshop": "Data Workflows, Agents, and Reasoning Frameworks (DWARF)",
          "slot": "2025-07-31T08:30",
          "duration_minutes": 90,
          "leaders": [],
          "description": "",
          "lightning_talks": []
        }
      ]
    }
  ]
}
```

### Track Input Bundle (`track_bundle.json`)

This is assembled per-track before report generation, combining website data with Google Drive materials:

```json
{
  "track": {
    "id": "workflows",
    "name": "Workflows",
    "room": "Main Plenary"
  },
  "sessions": [
    {
      "id": "dwarf-1",
      "title": "DWARF: Keynote and Systems Software for Agents",
      "slot": "2025-07-30T16:00",
      "leaders": ["Ian Foster", "Neeraj Kumar"],
      "lightning_talks": [
        {
          "title": "...",
          "authors": "Ian Foster (University of Chicago and Argonne National Laboratory)",
          "abstract": "..."
        }
      ],
      "attendees": [
        {"name": "Jane Doe", "organization": "ORNL"}
      ],
      "notes": "Full text of session notes or transcript..."
    }
  ],
  "sources": {
    "website_url": "https://tpc25.org/sessions/",
    "google_drive_folder": "https://drive.google.com/...",
    "files_used": [
      "Workflows_Session1_Attendees.gsheet",
      "Workflows_Session1_Notes.gdoc"
    ]
  }
}
```

---

## 5. Google Drive Structure

### Recommended Folder Layout

```
TPC25 Track Reports/
  ├── Workflows/
  │   ├── Session1_Attendees    (Google Sheet)
  │   ├── Session1_Notes        (Google Doc)
  │   ├── Session2_Attendees    (Google Sheet)
  │   ├── Session2_Notes        (Google Doc)
  │   └── ...
  ├── Initiatives/
  │   ├── Session1_Attendees    (Google Sheet)
  │   └── ...
  └── ... (one folder per track)
```

### Google Sheet Format (Attendees)

Simple two-column format:

| Name | Organization |
|------|-------------|
| Ian Foster | Argonne National Laboratory |
| Neeraj Kumar | Pacific Northwest National Laboratory |

### Google Doc Format (Notes)

Free-form text. Scribes write whatever they capture. The LLM handles the structure. We should provide a lightweight template suggesting:
- Key discussion points
- Questions raised
- Action items / outcomes
- Notable quotes or positions

But we don't enforce structure — the LLM is good at working with messy notes.

---

## 6. Revised Master Prompt

The existing `tpc25_master_prompt.yaml` is solid but needs updating for the track-level reporting structure. Key changes:

1. **Track-level framing**: The report covers an entire track (multiple sessions), not a single session.
2. **Session-by-session structure within the report**: Each session slot gets its own subsection.
3. **Clearer appendix handling**: Attendees and lightning talks are organized by session within the track.
4. **Lighter tone on data validation**: Since we're assembling the data programmatically, the "DATA VALIDATION FAILED" pattern is less necessary — the code handles missing data before the LLM sees it.

See the updated prompt in the companion `tpc_master_prompt_v2.yaml` file.

---

## 7. Hallucination Check (Replaces QA Framework)

Instead of a formal QA scoring system with scorecards and review queues, we do a single verification pass:

```python
def check_hallucinations(draft: str, source_bundle: dict) -> dict:
    """
    Ask a second LLM call to compare the draft against source data.
    Returns a list of flagged passages with explanations.
    """
    prompt = f"""
    Compare this draft report against the source data provided.
    
    Flag any claims in the draft that:
    1. Mention people, talks, or organizations NOT in the source data
    2. Attribute statements to specific people without source support
    3. Include specific numbers, dates, or facts not in the sources
    4. Describe discussion outcomes not supported by the notes
    
    For each flag, quote the problematic passage and explain why.
    If the draft is clean, say "No issues found."
    
    SOURCE DATA:
    {json.dumps(source_bundle, indent=2)}
    
    DRAFT REPORT:
    {draft}
    """
    # Returns structured flags for human review
```

This is lightweight, effective, and doesn't require a framework. The output is a simple list of flags appended to the draft as reviewer notes.

---

## 8. Implementation Plan (Simplified)

### What to Build (in order)

#### Step 1: Website Scraper (`scraper.py`) — 3-4 hours
- Parse the TPC sessions page HTML
- Extract track → session → lightning talk hierarchy
- Output `conference.json`
- **Test**: Run on tpc25.org, verify all 6 tracks and ~120 lightning talks captured

#### Step 2: Google Drive Collector (`gdrive.py`) — 2-3 hours
- Read Google Sheets (attendees) and Google Docs (notes) from a shared folder
- Use Google Sheets/Docs export APIs (CSV and plain text)
- Organize by track and session
- **Test**: Create a sample folder with one track's data, verify extraction

#### Step 3: Data Assembler (`assembler.py`) — 1-2 hours
- Merge `conference.json` with Google Drive materials
- Produce one `track_bundle.json` per track
- Handle missing data gracefully (notes not provided, etc.)
- **Test**: Assemble one complete track bundle

#### Step 4: Report Generator (`generator.py`) — 2-3 hours
- Load track bundle + master prompt
- Call LLM API (OpenAI or NIM)
- For large tracks (many lightning talks), may need to split across multiple calls
- Output draft Markdown
- **Test**: Generate one track report, review quality

#### Step 5: Hallucination Checker (`checker.py`) — 1-2 hours
- Second LLM pass comparing draft against sources
- Append flags as reviewer comments
- **Test**: Intentionally add a fake name, verify it's caught

#### Step 6: CLI & Orchestration (`cli.py`) — 1-2 hours
- `tpc_reporter scrape --url https://tpc25.org/sessions/`
- `tpc_reporter collect --drive-folder <URL>`
- `tpc_reporter generate --track workflows`
- `tpc_reporter generate-all`
- **Test**: End-to-end on one track

### Total Estimated Effort: 12-18 hours of focused work

This is achievable in a 2-3 day hackathon with 4-6 people.

---

## 9. What Changed from the Original Plan

| Original Plan | New Plan | Why |
|---|---|---|
| LangGraph workflow with 5 nodes | Simple Python functions | Less overhead, same result |
| Per-session reports (30 reports) | Per-track reports (8 reports) | Tractable for human review |
| QA scorecard + review queue framework | Single hallucination-check LLM pass | Simpler, equally effective |
| Fuzzy session matching with confidence scores | Direct JSON data model | Website scraping gives us the structure |
| File-based artifact matching | Google Drive API | Structured input, no guessing |
| PPTX/DOCX text extraction | Mostly unnecessary | Lightning talks come from website, notes from Google Docs |
| 6 different schemas (event, artifact, match, report, etc.) | 2 JSON structures (conference.json, track_bundle.json) | Less code, less confusion |
| Configurable LLM endpoints (NIM, OpenAI, tunnels) | Just use OpenAI API (or compatible) | Keep it simple for hackathon |
| Multi-phase timeline (4 sprints) | Build sequentially, test as you go | More realistic for a hackathon |

---

## 10. What Stays the Same

- **Anti-hallucination discipline**: The master prompt's strict rules about never fabricating data remain critical.
- **Hybrid approach**: Python handles structured data (attendees tables, talk lists), LLM handles narrative (discussion summary, outcomes).
- **Human-in-the-loop**: The final reports are drafts for human review, not finished products.
- **"Sources Used" list**: Every report lists where its data came from.

---

## 11. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| TPC25 website structure changes for TPC26 | High | Scraper is modular; adapt HTML parsing |
| Lightning talk abstracts are very long, exceed context window | Medium | Chunk by session; use summarization for appendix if needed |
| Google Drive API auth is painful | Medium | Fall back to manual CSV/text export |
| Notes quality varies wildly between scribes | High | Prompt handles "notes not provided" gracefully |
| LLM hallucinates despite anti-hallucination prompt | Medium | Second-pass hallucination check catches most issues |

---

## 12. Phase 2: Making It Agentic

After the hackathon MVP works, the agentic layer is straightforward:

1. **Wrap each pipeline step as an LLM tool** (function calling)
2. **Create an orchestrator prompt** that tells the LLM what tools are available
3. **The user says**: "Generate the Workflows track report for TPC26. Website: tpc26.org, Drive folder: [URL]"
4. **The LLM decides**: scrape → collect → assemble → generate → check
5. **If something fails** (e.g., Drive auth), the LLM can ask the user for help

This is where LangGraph *might* add value — as a framework for managing the tool-calling loop with error recovery. But by that point, you'll have working tools and real experience with the pipeline, making the LangGraph integration much more informed.

---

## 13. Recommendations for the Organizer

1. **Make tpc25.org/sessions scrapable** or export the session data as JSON. The HTML structure is workable but fragile.
2. **Create the Google Drive template folder now** with one track's sample data, so the team can test during the hackathon.
3. **Recruit one scribe per session slot** (up to 5 per track) and give them the lightweight notes template.
4. **Plan for ~$5-15 in OpenAI API costs** for generating and checking 8 track reports (GPT-4o-mini).
5. **Brief track organizers** that they'll receive draft reports for review — set expectations that these are AI drafts, not final products.
