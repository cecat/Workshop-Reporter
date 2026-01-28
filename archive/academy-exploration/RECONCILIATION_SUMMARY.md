# Workshop-Reporter: Reconciliation Summary
**Date**: January 28, 2026  
**Status**: Planning documents updated to incorporate Academy + TPC-Session-Reporter components

---

## What Was Accomplished

### 1. Preserved Valuable Assets from TPC-Session-Reporter
**Location**: `reference/tpc-session-reporter/` and `config/prompts/`

Copied and documented:
- ✅ **Tested LLM prompt** (`config/prompts/tpc25_master_prompt.yaml`)
  - Carefully tuned for TPC25 session reports
  - Includes strong constraints (VERBATIM abstracts, NO summarization)
  - Structured output format (Introduction, Discussion, Outcomes, Appendices)

- ✅ **Working logic** from `generate_report.py`
  - Session matching algorithm (`session_matches()`) - flexible acronym/keyword/fuzzy matching
  - Data download pipeline with Google Sheets/Docs URL conversion
  - Appendix generation (Python for tables, LLM for narrative)
  - HTML parsing for TPC25 format

- ✅ **Configuration reference** (`config/prompts/tpc25_config_reference.yml`)
  - Model settings (gpt-4o-2024-11-20)
  - Data source URLs

**Created**: `reference/tpc-session-reporter/README.md` documenting what to preserve and how to integrate

### 2. Updated README.md
**Major changes**:
- ✅ Described as "cooperative multi-agent system built on Academy"
- ✅ Added "Built on Prior Work" section citing TPC-Session-Reporter
- ✅ Updated Strategy section to describe Academy architecture
- ✅ Updated Architecture to describe Academy agents with `@action` and `@timer`
- ✅ Updated Repository Layout to `src/workshop_reporter/` structure
- ✅ Updated Quickstart with Academy installation
- ✅ Updated run commands for orchestrator pattern
- ✅ Updated post-hackathon phases (2: Production, 3: Scale-Out, 4: Advanced)

### 3. Created Comprehensive PLAN.md
**New reconciled plan** (saved original as `PLAN.md.original`):

**Key sections**:
- ✅ Executive Summary stating Academy-based with preserved TPC-Session-Reporter components
- ✅ Detailed Academy agent specifications (OrchestratorAgent, ProgramIngestAgent, etc.)
- ✅ Communication patterns (ThreadExchange for dev, RedisExchange for production)
- ✅ Deployment modes (local, single-host, federated)
- ✅ Complete timeline (March 31 - April 16)
- ✅ Team roles (4-8 people, Academy experts + Python devs)
- ✅ Pre-hackathon prep for organizer (Charlie):
  - Install Academy framework
  - Create repository structure
  - Port key functions from TPC-Session-Reporter to tools
  - Create schemas adapted for Academy
  - Prepare TPC25 dataset
  - Create test fixtures

- ✅ Task breakdown for April 1-6 (Priority 1: 6 issues, Priority 2: 3 issues)
- ✅ April 7 remote sprint plan (goal: orchestrator dispatching tasks to agents)
- ✅ April 8-13 tasks (LLM integration, QA, review workflow)
- ✅ April 14-16 in-person hackathon plan (integration, quality, demo)
- ✅ Success metrics and risk mitigation
- ✅ Comparison with original plan and Academy strategy doc

---

## What Still Needs To Be Done

### Remaining Documentation Updates

#### 1. Update `pre_hackathon_setup.md`
**Status**: Not yet started  
**Tasks**:
- Add Academy installation section
- Update schemas to show Academy integration patterns
- Add Academy hello-world test
- Update dependency list to include `academy-agents`
- Add Redis setup for production deployment

#### 2. Create Agent Specifications
**Status**: Not yet started  
**Tasks**:
- Create detailed specs for each agent in `docs/agents/`
  - OrchestratorAgent.md
  - ProgramIngestAgent.md
  - DriveIndexAgent.md
  - DocExtractAgent.md
  - MatchAgent.md
  - SummarizeAgent.md
  - EvaluatorAgent.md
  - PublishAgent.md

- Each spec should include:
  - Purpose and responsibilities
  - Actions with signatures
  - Control loops (if any)
  - Dependencies on other agents
  - Integration with TPC-Session-Reporter logic
  - Testing strategy

### Pre-Hackathon Implementation Work

Based on PLAN.md Section 3, Charlie needs to:

#### Critical (Must Complete by March 28)
- [ ] **Prepare TPC25 Dataset** (4-6 hours)
  - Download session roster, lightning talks, attendee list
  - Organize into `data/tpc25/`
  - Convert any PDFs

- [ ] **Install Academy Framework** (30 min)
  - Create conda environment
  - Install academy-agents
  - Test hello-world example

- [ ] **Create Repository Structure** (30 min)
  - Create `src/workshop_reporter/{agents,schemas,tools}/`
  - Create test fixtures directory
  - Create docs directory

- [ ] **Create Schemas** (1 hour)
  - `src/workshop_reporter/schemas/job_spec.py`
  - `src/workshop_reporter/schemas/canonical_model.py`
  - `src/workshop_reporter/schemas/match_graph.py`
  - `src/workshop_reporter/schemas/report.py`

- [ ] **Port Key Functions to Tools** (2 hours)
  - `src/workshop_reporter/tools/session_matching.py`
  - `src/workshop_reporter/tools/web_fetch.py`

- [ ] **Create Test Fixture** (1-2 hours)
  - `tests/fixtures/tpc24_mini/` with MAPE and DWARF sessions

- [ ] **Set Up Communication** (30 min)
  - Slack/Discord server
  - GitHub issues enabled
  - Zoom links

- [ ] **Test Setup End-to-End** (1 hour)
  - Verify Academy installation
  - Test schema imports
  - Verify fixtures and TPC25 data

**Total time**: ~10-12 hours

---

## Key Design Decisions Made

### 1. Academy-Based Architecture (Not Simple Workflow)
**Decision**: Use Academy's agent middleware with async messaging  
**Rationale**: 
- More scalable and resilient than sequential pipeline
- Supports future federated deployment
- Team includes Academy system developers
- Better separation of concerns

**Tradeoff**: More complex than original workflow plan, but more powerful

### 2. Preserve TPC-Session-Reporter Components
**Decision**: Reuse tested prompt, session matching, appendix generation  
**Rationale**:
- Prompt is proven with real TPC25 data
- Session matching handles TPC's complex naming (acronyms, keywords)
- Appendix generation works well (Python for structure, LLM for narrative)

**Tradeoff**: Some refactoring needed, but avoids reinventing

### 3. MVP Scope: Local/Single-Host Only
**Decision**: No federated deployment, no embeddings, no real-time Drive monitoring in MVP  
**Rationale**:
- 3-day hackathon is aggressive timeline
- Need working end-to-end pipeline first
- Can add advanced features post-hackathon

**Tradeoff**: Less ambitious, but achievable

### 4. Hybrid Python + LLM Approach
**Decision**: Python generates structured data (tables, lists), LLM generates narrative  
**Rationale**:
- Proven pattern from TPC-Session-Reporter
- More reliable than asking LLM to format tables
- Cheaper (less LLM usage)

**Tradeoff**: More code, but better quality

---

## How This Differs from Original Plans

### vs. Original Plan (README/PLAN/pre_hackathon_setup)
| Aspect | Original | Reconciled |
|--------|----------|------------|
| Architecture | Sequential workflow pipeline | Academy multi-agent system |
| Execution | One-shot CLI commands | Continuously running orchestrator |
| Communication | Direct function calls | Async messaging via exchange |
| Deployment | Single process | Distributed (ThreadExchange or RedisExchange) |
| Complexity | Lower | Higher, but more scalable |

### vs. workshop-reporter-academy-strategy.md
| Aspect | Strategy Doc | Reconciled MVP |
|--------|--------------|----------------|
| Scope | Full vision with federated deployment | Local/single-host only |
| Matching | Semantic embeddings | Rule-based from TPC-Session-Reporter |
| Drive Integration | Real-time monitoring | Pre-downloaded or fetch-at-start |
| Timeline | Open-ended | 3-day hackathon focused |

### What Was Preserved
✅ Tested prompt  
✅ Session matching logic  
✅ Appendix generation patterns  
✅ Data pipeline (Google Sheets/Docs handling)  
✅ Hybrid Python + LLM approach  

---

## Next Steps

### Immediate (Before Starting Pre-Hackathon Prep)

1. **Review this summary** and the updated README/PLAN
2. **Decide if Academy approach is right** for your team
   - Do you have Academy experts on the team?
   - Is 3 days enough time to learn Academy + build system?
   - Alternative: Simpler workflow pipeline (original plan) as MVP, Academy as Phase 2

3. **Update remaining docs** (pre_hackathon_setup.md, agent specs)

### Pre-Hackathon (By March 28)

Follow PLAN.md Section 3 checklist (~10-12 hours of work):
- Prepare TPC25 dataset
- Install Academy framework
- Create repository structure
- Implement schemas and tools
- Create test fixtures
- Test end-to-end

### Hackathon Timeline

- **March 31**: Kickoff (Academy crash course for team)
- **April 1-6**: Async work (core infrastructure)
- **April 7**: Remote sprint (orchestrator + agents wired up)
- **April 8-13**: Async work (LLM integration, QA)
- **April 14-16**: In-person hackathon (multi-session, quality, demo)

---

## Questions to Resolve

### 1. Team Composition
- Who are the Academy system developers?
- What's their experience level with Academy framework?
- Do they need to be onboarded, or are they already experts?

### 2. Timeline Feasibility
- Is March 31 kickoff realistic? (It's 2 months away)
- Can pre-hackathon prep be completed by March 28?
- Is 3 days enough for Academy-based system?

### 3. Fallback Plan
If Academy proves too complex:
- **Option A**: Simplify to original workflow pipeline for MVP, Academy for Phase 2
- **Option B**: Extend hackathon timeline
- **Option C**: Reduce scope (single session only)

### 4. Testing Strategy
- How to test Academy agents locally before hackathon?
- Who validates that agents work correctly?
- What's the acceptance criteria for "done"?

---

## Files Changed

### Created
- `reference/tpc-session-reporter/README.md` - Integration guide
- `config/prompts/tpc25_master_prompt.yaml` - Tested prompt (copied)
- `config/prompts/tpc25_config_reference.yml` - Config reference (copied)
- `reference/tpc-session-reporter/generate_report.py` - Reference implementation (copied)
- `PLAN.md` - Comprehensive reconciled plan
- `RECONCILIATION_SUMMARY.md` - This document

### Modified
- `README.md` - Updated for Academy architecture
- `PLAN.md.original` - Renamed from original PLAN.md

### Not Yet Modified
- `pre_hackathon_setup.md` - Needs Academy setup instructions
- `workshop-reporter-academy-strategy.md` - Can leave as architectural vision doc

---

## Recommendations

### Recommendation 1: Validate Academy Approach
**Before proceeding with pre-hackathon prep**, test Academy framework yourself:
1. Install academy-agents
2. Run hello-world example from PLAN.md
3. Create a simple 2-agent system (submitter + worker)
4. Verify it works on your machine

**Why**: Academy may have installation issues, version conflicts, or API changes. Better to discover now than at kickoff.

### Recommendation 2: Start with Simpler Hybrid Approach
Consider a **phased Academy adoption**:

**Phase 1 (Hackathon MVP)**: 
- Simple workflow orchestrator (not Academy)
- Reuse TPC-Session-Reporter logic directly
- Get working end-to-end for multiple sessions

**Phase 2 (Post-Hackathon)**:
- Migrate to Academy agents
- Add async capabilities
- Add advanced features

**Why**: Lower risk, team can focus on domain logic rather than learning Academy

### Recommendation 3: Create Minimal Test First
Before full pre-hackathon prep, create **one working agent**:
- Implement `ProgramIngestAgent` in Academy
- Test with real TPC25 HTML
- Verify Academy patterns work

**Why**: Validates architecture early, identifies issues before team commits time

---

## Success Criteria

### Documentation Complete
- ✅ README describes Academy system with preserved components
- ✅ PLAN provides detailed roadmap with Academy agent specs
- ⏳ pre_hackathon_setup has Academy installation guide
- ⏳ Agent specifications created

### Pre-Hackathon Prep Complete
- ⏳ TPC25 dataset organized
- ⏳ Academy installed and tested
- ⏳ Repository structure created
- ⏳ Schemas implemented
- ⏳ Tools ported from TPC-Session-Reporter
- ⏳ Test fixtures created
- ⏳ End-to-end test passes

### Hackathon MVP Delivered
- ⏳ Works on real TPC25 data (all sessions)
- ⏳ Accurate summaries using tested prompt
- ⏳ Full meeting report generated
- ⏳ QA catches issues
- ⏳ Review workflow usable
- ⏳ Documentation complete

---

## Conclusion

You now have a **reconciled plan** that:
1. ✅ Adopts Academy multi-agent architecture
2. ✅ Preserves tested components from TPC-Session-Reporter
3. ✅ Provides realistic 3-day hackathon roadmap
4. ✅ Includes detailed pre-hackathon prep checklist

**Key decision point**: Validate Academy approach before investing in pre-hackathon prep. The framework may be more complex than needed for MVP.

**Recommended next action**: Install Academy and run hello-world example from PLAN.md Section 3B to confirm it works on your machine.
