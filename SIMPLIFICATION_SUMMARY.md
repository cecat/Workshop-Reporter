# Workshop-Reporter: Academy Removal & LangGraph Adoption
**Date**: January 28, 2026  
**Status**: Documentation simplified, Academy removed, LangGraph adopted

---

## What Happened

After consulting with Academy developers, we determined that Academy is **architecturally mismatched** for Workshop-Reporter. The evaluation (see `archive/academy-exploration/academy_compatibility_evaluation.md`) showed:

| Factor | Workshop-Reporter | Academy |
|--------|-------------------|---------|
| Scale | Single organization, local files | Federated multi-institution |
| Infrastructure | Simple Python + LLM API | HPC clusters, experimental equipment |
| Data flow | Small document batches | High-throughput scientific datasets |
| Coordination | Linear pipeline | Complex cross-site orchestration |

**Verdict**: Academy is designed for federated scientific computing (HPC coordination, lab instruments, multi-site research). We're building a **document processing pipeline**. Academy would add massive complexity with zero benefit.

---

## What We Did

### 1. Archived Academy Documentation
Moved to `archive/academy-exploration/`:
- `PLAN-academy.md` - Comprehensive Academy-based plan
- `RECONCILIATION_SUMMARY.md` - Initial Academy integration work
- `workshop-reporter-academy-strategy.md` - Full Academy vision
- `academy_compatibility_evaluation.md` - Evaluation from Academy team
- `PLAN-workflow-original.md` - Original workflow plan

### 2. Updated README.md
**Changed**:
- Removed all Academy references
- Changed description to "workflow-based reporting system using LangGraph"
- Updated Strategy section: LangGraph workflow orchestration
- Updated Architecture: LangGraph nodes instead of Academy agents
- Updated Repository Layout: Simpler `tpc_reporter/` structure
- Updated Quickstart: LangGraph installation instead of Academy
- Updated Run commands: Simple CLI instead of orchestrator service

**Preserved**:
- "Built on Prior Work" section (TPC-Session-Reporter components)
- Tested prompt, matching logic, data pipeline references
- Hybrid Python + LLM approach

### 3. Created New PLAN.md
**Key features**:
- LangGraph workflow with 6 nodes (ingest, match, summarize, evaluate, publish, review_gate)
- Strategy: Complete TPC-Session-Reporter prototype first, then refactor into LangGraph
- Pre-hackathon prep includes finishing the prototype (~50 lines of LLM code)
- Simpler timeline: No Academy learning curve
- Clear examples of LangGraph state graph

**Structure**:
- Executive Summary with LangGraph rationale
- Architecture: LangGraph workflow diagram and state definition
- Timeline (March 31 - April 16)
- Team roles (4-8 people, no Academy expertise needed)
- Pre-hackathon prep (~8-10 hours)
- Task breakdown for all phases
- LangGraph example code in appendix

---

## Architecture Comparison

### Before (Academy)
```
OrchestratorAgent (@timer loop)
  ↓ (async messages via exchange)
ProgramIngestAgent → DriveIndexAgent → DocExtractAgent → MatchAgent → SummarizeAgent → EvaluatorAgent → PublishAgent
```
- Complex: Async agents, message bus, handles, control loops
- Deployment: ThreadExchange (dev) or RedisExchange (production)
- Learning curve: High (Academy framework patterns)
- Complexity: High for no benefit

### After (LangGraph)
```
[START] → ingest_node → match_node → summarize_node → evaluate_node → publish_node → [END]
                 ↓ (low confidence)         ↓ (QA flags)
            review_gate                 review_gate
```
- Simple: Python functions, state passing
- Deployment: Single process with checkpointing
- Learning curve: Low (just StateGraph API)
- Complexity: Appropriate for the problem

---

## What Stayed the Same

✅ **Tested components from TPC-Session-Reporter**:
- Tested LLM prompt (`config/prompts/tpc25_master_prompt.yaml`)
- Session matching logic (acronym, keyword, fuzzy)
- Appendix generation (Python for tables, LLM for narrative)
- Data pipeline (Google Sheets/Docs, HTML parsing)

✅ **Core workflow phases**:
- INGEST → MATCH → SUMMARIZE → EVALUATE → PUBLISH

✅ **Human-in-the-loop**:
- Review gates for low-confidence decisions
- Resume capability after edits

✅ **Hackathon timeline**:
- March 31 - April 16
- 4-8 person team
- 3-day in-person hackathon

---

## Key Benefits of LangGraph Over Academy

### 1. **Right Tool for the Job**
- ✅ Purpose-built for LLM workflows
- ✅ Common pattern: document processing pipelines
- ✅ Wide adoption in LLM space
- ❌ Academy: Built for federated HPC scientific computing

### 2. **Simplicity**
- ✅ Simple Python API (nodes are functions)
- ✅ State is just a TypedDict
- ✅ No distributed systems complexity
- ❌ Academy: Agents, exchanges, launchers, handles, control loops

### 3. **Learning Curve**
- ✅ 1-2 hours to understand LangGraph basics
- ✅ Good documentation and examples
- ✅ Team can focus on domain logic
- ❌ Academy: Days to learn framework, specialized expertise needed

### 4. **Deployment**
- ✅ Single Python process
- ✅ Checkpointing to disk (built-in)
- ✅ No external dependencies (Redis, etc.)
- ❌ Academy: Complex deployment options, infrastructure overhead

### 5. **Maintenance**
- ✅ Standard Python code
- ✅ Easy to debug and test
- ✅ Low dependency footprint
- ❌ Academy: Framework-specific patterns, harder to maintain

---

## Migration Path

### Phase 1: Complete TPC-Session-Reporter (Pre-Hackathon)
**Status**: Prototype is 70% done  
**Remaining work**: ~50 lines to wire LLM call
```python
# Add this to generate_report.py:
def generate_ai_content(session_info, filtered_talks, notes, master_prompt):
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a technical report writer."},
            {"role": "user", "content": master_prompt.format(...)}
        ]
    )
    return response.choices[0].message.content
```

**Test**: Run on MAPE session, verify complete report

### Phase 2: Refactor into LangGraph (April 1-7)
**Extract functions**:
- `ingest_node`: Session parsing + text extraction
- `match_node`: Session matching (reuse `session_matches()`)
- `summarize_node`: LLM call + appendix generation
- `evaluate_node`: QA checks
- `publish_node`: Report assembly

**Create workflow**:
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(WorkflowState)
workflow.add_node("ingest", ingest_node)
workflow.add_node("match", match_node)
workflow.add_node("summarize", summarize_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("publish", publish_node)

workflow.add_edge("ingest", "match")
workflow.add_conditional_edges("match", should_review_matches, {
    "review": "review_gate",
    "continue": "summarize"
})
# ... etc

app = workflow.compile()
```

### Phase 3: Multi-Session + Polish (April 8-16)
- Loop over all sessions in `summarize_node`
- Add QA checks in `evaluate_node`
- Add review gates (conditional edges)
- Test on full TPC25 data
- Documentation and demo

---

## Updated Dependencies

### Removed
- ❌ `academy-agents`
- ❌ `redis` (for RedisExchange)

### Added
- ✅ `langgraph >= 0.1`
- ✅ `langchain >= 0.1`
- ✅ `langchain-openai >= 0.1`

### Kept
- ✅ `pydantic >= 2.0`
- ✅ `python-docx >= 1.0`
- ✅ `python-pptx >= 0.6.21`
- ✅ `pyyaml >= 6.0`
- ✅ `beautifulsoup4 >= 4.12`
- ✅ `requests >= 2.31`

---

## Team Impact

### Before (Academy)
**Required**:
- Academy framework experts
- Understanding of federated systems
- Knowledge of agents, exchanges, launchers
- Distributed systems experience helpful

**Risk**: Team might spend more time learning Academy than building the system

### After (LangGraph)
**Required**:
- Python proficiency
- Some LLM experience helpful
- Basic understanding of state machines

**Risk**: Minimal, team can focus on domain logic

---

## Success Metrics (Unchanged)

### MVP (Must Have)
- ✅ Works on real TPC25 data (all sessions)
- ✅ Accurate summaries using tested prompt
- ✅ Full meeting report generated
- ✅ QA catches issues
- ✅ Review workflow usable
- ✅ Documentation clear
- ✅ Tests pass

### Stretch Goals
- Embedding-based matching
- Streamlit review UI
- Cost tracking
- Parallel processing

---

## Files Changed

### Created
- `PLAN.md` - New simplified plan with LangGraph
- `SIMPLIFICATION_SUMMARY.md` - This document
- `archive/academy-exploration/` - Archived Academy work

### Modified
- `README.md` - Removed Academy, added LangGraph
  - Strategy section: LangGraph workflow orchestration
  - Architecture section: LangGraph nodes
  - Repository layout: Simpler structure
  - Quickstart: LangGraph installation
  - Run commands: Simple CLI

### Archived
- `archive/academy-exploration/PLAN-academy.md`
- `archive/academy-exploration/RECONCILIATION_SUMMARY.md`
- `archive/academy-exploration/workshop-reporter-academy-strategy.md`
- `archive/academy-exploration/academy_compatibility_evaluation.md`
- `archive/academy-exploration/PLAN-workflow-original.md`

### Unchanged
- `pre_hackathon_setup.md` - TODO: Update with LangGraph instructions
- `config/prompts/tpc25_master_prompt.yaml` - Tested prompt preserved
- `reference/tpc-session-reporter/` - Prototype code preserved

---

## Next Steps

### Immediate
1. ✅ **Done**: Remove Academy, adopt LangGraph in documentation
2. ⏳ **TODO**: Update `pre_hackathon_setup.md` with LangGraph setup
3. ⏳ **TODO**: Create LangGraph architecture diagram (optional)

### Pre-Hackathon (By March 28)
1. ⏳ Complete TPC-Session-Reporter LLM integration (~2-3 hours)
2. ⏳ Test on MAPE, DWARF sessions
3. ⏳ Prepare TPC25 dataset (3-4 hours)
4. ⏳ Install LangGraph and test hello-world
5. ⏳ Create repository structure
6. ⏳ Port key functions to tools/ (1-2 hours)
7. ⏳ Create test fixtures

### Hackathon
- April 1-6: Complete prototype, port to LangGraph structure
- April 7: Refactor into LangGraph workflow
- April 8-13: Multi-session, QA, polish
- April 14-16: Full TPC25 data, demo

---

## Lessons Learned

### 1. **Evaluate Frameworks Early**
We spent significant time on Academy before realizing it was wrong. Earlier consultation with Academy team would have saved work.

### 2. **Match Tool to Problem**
Academy is excellent for its intended use case (federated scientific computing). For document processing, it's overkill. LangGraph is purpose-built for LLM workflows.

### 3. **Preserve What Works**
We kept the valuable tested components (prompt, matching logic, data pipeline) throughout the architecture changes.

### 4. **Simplicity is Valuable**
The simpler LangGraph approach is easier to understand, build, test, and maintain. Complexity should match problem complexity.

### 5. **Complete What You Started**
TPC-Session-Reporter was 70% done. Completing it first gives us a working baseline to refactor from, rather than building from scratch.

---

## Conclusion

**Academy removal was the right decision.** The evaluation clearly showed it's designed for a different problem domain. LangGraph provides everything we need (workflow orchestration, checkpointing, conditional edges) without the complexity overhead.

**The plan is now simpler and more achievable**:
1. Complete TPC-Session-Reporter prototype (pre-hackathon)
2. Refactor into LangGraph workflow (April 1-7)
3. Multi-session + quality (April 8-16)

**Key insight**: We had the right intuition with TPC-Session-Reporter's simple approach. LangGraph gives us just enough structure without overengineering.

**Risk level**: Low → Lower  
**Complexity**: High (Academy) → Appropriate (LangGraph)  
**Time to working MVP**: Extended (with Academy) → Realistic (with LangGraph)

We're now well-positioned for a successful 3-day hackathon.
