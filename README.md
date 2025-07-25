# Workshop Reporter

This project builds an agentic system that, given a URL for a scientific workshop and a
shared Google Drive folder, can autonomously:
- Parse the workshop website to identify sessions and metadata.
- Extract key details: session titles, leaders, individual talks, and abstracts.
- Examine documents in a shared Google Drive folder and infer which file corresponds to which session.
- Match files to sessions using best-fit similarity based on title and content.
- Flag mismatches or gaps and optionally prompt a human user for input.
- Output a structured report of session metadata and associated documents.

A viable starter system would create a report from a breakout session at the 
[TPC25](tpc25.org) conference, given the following data:
1. URL for the session details (https://tpc25.org/sessions/) or a downloaded source file (in cases, like TPC25, where the server blocks crawlers).
2. URL for the Google Folder (for TPC25: https://drive.google.com/drive/folders/17q5HVSHOhVkn9yCuNlxzQwy6kRZO_TnF?usp=sharing) which will hold two files, each with filename of the session name or acronym:
    - SessionName.csv will be a 2-column CSV colleciton of {name, institution}
    - SessionName.doc will hold all session discussion notes (single file for multi-session groups)
3. URL for lightning talk data (for TPC25: https://docs.google.com/spreadsheets/d/1p6iK7sbqfjJVL1c3M4SSLpFO4O3Ez9RHUVLaG1RbcwE/edit?resourcekey=&gid=225247942#gid=225247942)
3. Name or Acronym of the breakout session.
## Motivation

Workshops and conferences often produce valuable information that is poorly organized across
websites, emails, and shared drives. This project creates a generalizable agent that
can extract and organize this information with minimal manual effort.

## Team Scope

This project is designed for 4–5 developers over a 1–3 day hackathon. Contributors can focus on:
- LLM prompting and tool design
- Web scraping and parsing
- Google Drive access and file analysis
- Agent architecture and planning loop
- Logging and human-in-the-loop interaction

See `PLAN.md` for technical design and implementation steps.
