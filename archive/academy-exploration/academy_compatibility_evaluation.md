Analysis: Workshop-Reporter vs. Academy

  Workshop-Reporter Summary

  A multi-agent Python system for generating structured summary reports from workshop/conference materials for the Trillion Parameter Consortium (TPC). It:
  - Ingests session rosters, meeting notes, slides, and documents (local files)
  - Outputs per-session summaries, comprehensive reports, and QA scorecards
  - Uses a linear pipeline of specialized agents: Director → Ingestion → Artifact Collector → Matcher → Summarizer → Evaluator → Publisher
  - Operates on pre-downloaded, locally organized materials

  Academy Summary

  Middleware for deploying autonomous agents across federated research ecosystems. Designed for:
  - Cross-institutional HPC systems, experimental facilities, and data repositories
  - High-throughput scientific data streaming
  - Autonomous experimentation with lab instruments
  - Multi-site research coordination

  Verdict: Not a good fit
  ┌────────────────┬──────────────────────────────────┬──────────────────────────────────────┐
  │     Factor     │     Workshop-Reporter Needs      │           Academy Provides           │
  ├────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
  │ Scale          │ Single organization, local files │ Federated multi-institution          │
  ├────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
  │ Infrastructure │ Simple Python + LLM API          │ HPC clusters, experimental equipment │
  ├────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
  │ Data flow      │ Small document batches           │ High-throughput scientific datasets  │
  ├────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
  │ Coordination   │ Linear agent pipeline            │ Complex cross-site orchestration     │
  ├────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
  │ Resources      │ Local filesystem                 │ Heterogeneous distributed systems    │
  └────────────────┴──────────────────────────────────┴──────────────────────────────────────┘
  Key reasons against using Academy:

  1. Architectural mismatch: Workshop-Reporter is a straightforward document processing pipeline. Academy is designed for federated scientific computing across institutions—this adds significant complexity with no benefit.
  2. Overkill infrastructure: Academy's features (HPC integration, experimental instrument control, cross-site coordination) are irrelevant for processing meeting notes and slides.
  3. Simpler alternatives exist: For Workshop-Reporter's needs, frameworks like LangGraph, CrewAI, or even a custom Pydantic-based workflow would be more appropriate and maintainable.

  Academy would make sense if TPC needed to coordinate meeting analysis across multiple institutions with shared HPC resources and automated lab equipment integration—but that's not what this proposal describes.
