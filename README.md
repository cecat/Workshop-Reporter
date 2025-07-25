# Workshop Reporter

This project builds an agentic system that can autonomously organize workshop data by:
- Taking a predefined list of workshop sessions with metadata
- Examining local documents and inferring which file corresponds to which session
- Matching files to sessions using best-fit similarity based on title and content
- Flagging mismatches or gaps and optionally prompting a human user for input
- Outputting a structured report of session metadata and associated documents

The initial system targets breakout sessions from the [TPC25](https://tpc25.org) conference, working with these simplified inputs:

## Input Data Sources

1. **Session List** (JSON file): Pre-defined list of sessions with:
   - Session name/acronym
   - Session leaders
   - Brief description or theme
   - Expected file patterns

2. **Local Documents Folder**: Contains downloaded files with patterns like:
   - `SessionName.csv` - 2-column CSV collection of {name, institution}
   - `SessionName.doc/.txt` - Session discussion notes

3. **Lightning Talks Data** (CSV file): Downloaded spreadsheet with:
   - Author, title, abstract, assigned session

## Example Output

The system generates a structured report like:
```json
{
  "session_name": "Machine Learning Applications",
  "leaders": ["Dr. Smith", "Prof. Johnson"],
  "matched_files": {
    "participants": "ML_Apps.csv",
    "notes": "MachineLearning_Apps.doc"
  },
  "lightning_talks": ["Talk 1", "Talk 2"],
  "confidence_score": 0.95
}
```
## Motivation

Workshops and conferences often produce valuable information that is poorly organized across
websites, emails, and shared drives. This project creates a generalizable agent that
can extract and organize this information with minimal manual effort.

## Technical Architecture

```
workshop-reporter/
├── agent/          # Core agent loop and planning
├── extractors/     # Document parsing and content extraction
├── matchers/       # Session-document matching logic
├── outputs/        # Report generation
├── config/         # Configuration and sample data
└── tests/          # Sample test data
```

## Team Scope

This project is designed for 4–5 developers over a 1–3 day hackathon. Contributors can focus on:
- LLM prompting and tool design for content extraction
- Local file parsing and content analysis
- Similarity matching algorithms (string + semantic)
- Agent architecture and planning loop
- Report generation and user interaction

## Success Metrics

- 80%+ accuracy in session-document matching
- All sessions have at least one matched document
- Clear confidence scores for manual review of low-confidence matches
- Structured output ready for further processing

See [PLAN.md](./PLAN.md) for technical design and implementation steps.
