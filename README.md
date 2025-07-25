# Workshop Session Intelligence Agent

This project builds an AI-powered agent that, given a URL for a scientific workshop and a shared Google Drive folder, can autonomously:
- Parse the workshop website to identify sessions and metadata.
- Extract key details: session titles, leaders, individual talks, and abstracts.
- Examine documents in a shared Google Drive folder and infer which file corresponds to which session.
- Match files to sessions using best-fit similarity based on title and content.
- Flag mismatches or gaps and optionally prompt a human user for input.
- Output a structured report of session metadata and associated documents.

## Motivation

Workshops and conferences often produce valuable information that is poorly organized across websites, emails, and shared drives. This project creates a generalizable agent that can extract and organize this information with minimal manual effort.

## Team Scope

This project is designed for 4–5 developers over a 1–3 day hackathon. Contributors can focus on:
- LLM prompting and tool design
- Web scraping and parsing
- Google Drive access and file analysis
- Agent architecture and planning loop
- Logging and human-in-the-loop interaction

See `PLAN.md` for technical design and implementation steps.
