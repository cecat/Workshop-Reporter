# TPC-Session-Reporter Reference Materials

This directory contains valuable components from the earlier TPC-Session-Reporter prototype that have been tested and should be incorporated into Workshop-Reporter.

## What's Preserved

### 1. Master Prompt (`config/prompts/tpc25_master_prompt.yaml`)
**Status**: Tested and working
**Purpose**: LLM prompt for generating session report summaries

This prompt has been carefully tuned and tested with real TPC25 data. Key features:
- Clear process instructions for the LLM
- Strong constraints (VERBATIM abstracts, NO summarization)
- Structured output format (Introduction, Discussion, Outcomes, Appendices)
- Error handling instructions
- Specific completeness requirements

**Integration**: Use this as the template for the `SummarizeAgent` in Academy implementation.

### 2. Configuration Reference (`config/prompts/tpc25_config_reference.yml`)
**Status**: Working configuration
**Purpose**: Model settings and data source URLs

Contains:
- OpenAI model configuration (gpt-4o-2024-11-20)
- Data source URLs (Google Sheets for lightning talks, TPC25 sessions page)
- System message for LLM

**Integration**: Merge with new event configuration YAMLs.

### 3. Original Implementation (`generate_report.py`)
**Status**: Incomplete but contains valuable logic
**Purpose**: Reference for data pipeline and matching algorithms

Key functions to extract and reuse:

#### Session Matching Logic
```python
def session_matches(target_group, session_label):
    """Flexible matching: exact, acronym, partial, word overlap"""
```
- **Use in**: `MatchAgent` for linking artifacts to sessions
- **Tested**: Works for "DWARF" → "Data, Workflows, Agents, and Reasoning Frameworks (DWARF)"

#### Data Download Pipeline
```python
def download_to_input(url, filename):
def download_all_sources(config, args):
```
- **Use in**: `ProgramIngestAgent` and `DriveIndexAgent`
- **Features**: Google Sheets/Docs URL conversion, browser headers, error handling

#### Appendix Generation
```python
def generate_attendees_appendix():
def generate_lightning_talks_appendix(filtered_talks):
```
- **Use in**: `PublishAgent`
- **Pattern**: Python generates structured data (tables), LLM generates prose
- **Important**: Keep this separation of concerns

#### HTML Parsing
```python
def extract_session_details(session_acronym, html_content=None):
```
- **Use in**: `ProgramIngestAgent`
- **Note**: BeautifulSoup-based, somewhat fragile, but works for TPC25 format

## Integration Strategy

### For Academy Implementation

1. **Prompt → SummarizeAgent Action**
   ```python
   class SummarizeAgent(Agent):
       @action
       async def generate_summary(self, session_id: str, artifacts: List[Artifact]):
           prompt = load_prompt("config/prompts/tpc25_master_prompt.yaml")
           # Use existing tested prompt with session data
   ```

2. **Session Matching → MatchAgent**
   ```python
   class MatchAgent(Agent):
       @action
       async def match_artifacts(self, sessions: List[Session], artifacts: List[Artifact]):
           # Reuse session_matches() logic for confidence scoring
   ```

3. **Appendix Generation → PublishAgent**
   ```python
   class PublishAgent(Agent):
       @action
       async def assemble_report(self, session: Session, summary: str, artifacts: List[Artifact]):
           # Use generate_attendees_appendix() and generate_lightning_talks_appendix()
           # Pattern: Python for structured data, LLM for narrative
   ```

## What Was Missing in TPC-Session-Reporter

The prototype never completed the LLM integration. The code:
1. ✅ Downloaded and filtered data
2. ✅ Generated appendices
3. ❌ Never called the LLM with the master prompt
4. ❌ Never filled in the `<!-- AI_CONTENT_PLACEHOLDER -->`

Workshop-Reporter completes this by:
- Wiring the master prompt into `SummarizeAgent`
- Adding multi-session orchestration
- Adding QA checks and review workflows
- Scaling with Academy's async agent architecture

## Testing Notes

The following sessions were tested with TPC-Session-Reporter:
- **MAPE** (Model Architecture and Performance Evaluation) - 13 lightning talks
- **DWARF** (Data, Workflows, Agents, and Reasoning Frameworks) - 16 lightning talks

Test data is preserved in TPC-Session-Reporter repo at:
- `_INPUT/lightning_talks.csv` (111KB)
- `_INPUT/The Trillion Parameter Consortium | Sessions.html` (427KB)
- `_INPUT/attendees.csv` (sample)

## Key Lessons

1. **Hybrid Python + LLM approach works best**
   - Python: Data filtering, structured output (tables, lists)
   - LLM: Narrative summaries, synthesis, discussion

2. **Session matching needs flexibility**
   - Exact matching is insufficient
   - Acronym extraction is critical for TPC data
   - Fuzzy/partial matching catches edge cases

3. **Graceful degradation is important**
   - "Attendees list not available" vs. crashing
   - Proceed without notes if missing
   - Clear error messages when data is incomplete

4. **Google Sheets/Docs require URL conversion**
   - Sharing URLs → Export URLs
   - Handle both formats transparently

## Next Steps

When implementing Academy-based Workshop-Reporter:
1. Start by integrating the master prompt into `SummarizeAgent`
2. Port session matching logic to `MatchAgent`
3. Reuse appendix generation in `PublishAgent`
4. Test with existing TPC25 data before hackathon
5. Expand to multi-session orchestration during hackathon
