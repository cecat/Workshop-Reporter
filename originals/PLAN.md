# Implementation Plan: Workshop Agent

## Overview

We will implement a goal-driven agent that performs autonomous document matching against predefined session lists. The system will work with local files and maintain memory, reason about its state, and dynamically choose next steps using LLM calls.

To the extent possible we will vibe code to attempt to get a basic working system in place within 30 hours during the [TPC25](https://tpc25.org) Hackathon.

For the *big picture* objectives, see [README.md](./README.md)

---

## Technical Requirements

- **Language**: Python 3.9+
- **LLM API**: OpenAI GPT-4 or Anthropic Claude
- **Key Libraries**: 
  - `pandas` (CSV/data handling)
  - `openai` or `anthropic` (LLM API)
  - `python-docx` (Word document parsing)
  - `fuzzywuzzy` (string similarity)
  - `pathlib` (file operations)

---

## Phases and Tasks

### Phase 0: Environment Setup
- [ ] Set up conda environment with required packages
- [ ] Configure LLM API keys and test connectivity
- [ ] Create sample session list JSON file
- [ ] Create sample document folder with test files
- [ ] Verify all file parsing works with sample data

### Phase 1: Input Processing
- [ ] Load predefined session list from JSON file
- [ ] Scan local documents folder and inventory all files
- [ ] Parse lightning talks CSV file (if provided)
- [ ] Initialize agent memory state (sessions list, documents list, match records, outstanding questions)

### Phase 2: Document Content Extraction
- [ ] Extract text content from various file types (.doc, .docx, .txt, .csv)
- [ ] Normalize filenames for easier comparison (lowercase, remove punctuation)
- [ ] Generate document summaries using LLM
- [ ] Store document metadata and content snippets

### Phase 3: Session-Document Matching
- [ ] Implement fuzzy string matching for session names against filenames
- [ ] Use LLM to extract key themes from session descriptions
- [ ] Compare document content against session themes using LLM
- [ ] Generate confidence scores for each potential match
- [ ] Flag low-confidence matches for human review

### Phase 4: Agent Loop and Planning
- [ ] Create a stateful agent loop: observe → reason → act
- [ ] Use LLM to select the next best tool ("match_documents", "ask_user", "refine_match")
- [ ] Define tools: load_sessions, extract_content, match_docs, ask_user, output_report

### Phase 5: Validation and Quality Control
- [ ] Implement confidence scoring for matches
- [ ] Validate that all sessions have corresponding documents
- [ ] Flag orphaned documents (no session match)
- [ ] Create human review queue for ambiguous cases

### Phase 6: Output and User Feedback
- [ ] Generate final structured JSON report linking sessions to files
- [ ] Output unmatched sessions and orphaned files
- [ ] Create summary statistics (match rate, confidence distribution)
- [ ] Optionally prompt user for unresolved items

---

## Division of Labor

- **File I/O & Parsing**: Local document loading, content extraction, JSON/CSV handling
- **LLM Integration**: Prompt templates for content analysis and matching decisions
- **Matching Logic**: String similarity, semantic comparison, confidence scoring
- **Agent Framework**: Memory management, planning loop, tool execution
- **Output & Reporting**: JSON report generation, human review interfaces

---

## Error Handling Strategy

- **File Access Issues**: Graceful handling of missing/corrupted files
- **LLM API Failures**: Retry logic with exponential backoff, fallback to simpler string matching
- **Parsing Errors**: Skip problematic files but log for manual review
- **Low Confidence Matches**: Queue for human review rather than auto-assign

---

## Testing Approach

- **Unit Tests**: Individual file parsers, string matching functions
- **Integration Tests**: End-to-end with sample TPC25 data
- **Validation**: Manual review of match quality on known good examples
- **Performance**: Measure processing time for realistic document volumes

---

## Stretch Goals

### Advanced Features
- Use LangGraph or CrewAI for more sophisticated planning
- Add vector embeddings for semantic matching via FAISS or similar
- Build a simple Streamlit or CLI UI for interactive review
- Support for additional file formats (PDF, PowerPoint)

### API Integration (Original Vision)
- Accept workshop URLs and scrape session data dynamically
- Google Drive API integration for live folder access
- Google Sheets API for lightning talk data
- Real-time web scraping with crawler detection avoidance

### Production Features
- Database storage for session and document metadata
- Web interface for batch processing multiple workshops
- Export to various formats (Excel, PDF reports)
- Integration with conference management systems

