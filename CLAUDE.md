# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TPC Workshop Reporter is a Python pipeline that generates draft markdown reports for TPC conference tracks. It scrapes conference websites, collects notes/attendees from Google Drive, assembles data into track bundles (JSON), generates reports via LLMs (OpenAI or NVIDIA NIM), and verifies them for hallucinations with a second LLM pass.

## Commands

```bash
# Install (editable, with all extras)
pip install -e ".[all]"

# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_generator.py -v

# Format
black .

# Lint
ruff check .
```

CI runs tests on Python 3.10–3.12 and enforces Black formatting + Ruff linting.

## Architecture

**Pipeline flow:**
```
Website scrape / Google Drive downloads
        ↓
  assemble_track_bundle() → track_bundle.json
        ↓
  generate_report() → draft.md       (LLM pass 1: generation)
        ↓
  check_report() → checked.md        (LLM pass 2: hallucination flags)
```

**Data hierarchy:** Conference → Track → Session → Lightning Talks + Attendees + Notes. One report is generated per track.

**Key modules in `tpc_reporter/`:**

| Module | Role |
|--------|------|
| `cli.py` | Click CLI entry point (`tpc-reporter` command) with subcommands: `fetch-and-assemble`, `assemble`, `generate`, `check`, `run`, `generate-all` |
| `config_loader.py` | Loads `configuration.yaml` + `secrets.yaml`; searches upward from module directory |
| `llm_client.py` | `LLMClient` abstracts OpenAI and NIM SSH endpoints behind a unified interface |
| `generator.py` | Loads prompt templates from `prompts/`, formats track bundle, calls LLM |
| `checker.py` | Second-pass verification; outputs `[FLAG: ...]` annotations in markdown |
| `assembler.py` | Builds track bundle JSON from CSVs and text files; CSV column mapping is config-driven |
| `gdrive.py` | Downloads Google Sheets (as CSV) and Docs via Google Drive API |
| `scraper.py` | Scrapes conference website HTML for structure (tracks, sessions, speakers) |

**Config files (project root):**
- `configuration.yaml` — LLM endpoints, data source URLs, CSV schema mappings, app settings
- `secrets.yaml` — API keys (gitignored; see `secrets.yaml.template`)
- `prompts/` — YAML prompt templates for generator and checker

**Conventions:**
- Config and prompt files are auto-discovered by searching upward from the module directory
- Result types use dataclasses (`AssemblyResult`, `VerificationResult`, `ScrapeResult`)
- All file I/O uses `pathlib.Path`
- CSV column mappings are configurable via `csv_schema` in `configuration.yaml` (columns can be referenced by name or index)

## Code Style

- **Black** with 88-char line length, Python 3.10+ target
- **Ruff** rules: E, F, W, I, UP (ignores E501, E402)
- Python 3.10+ features are used (union types with `|`, `from __future__ import annotations`)
