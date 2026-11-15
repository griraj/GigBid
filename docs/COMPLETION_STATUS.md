# Current completion status

This document records implemented features, validation and remaining rubric gaps.

## Implemented functionality

- Phase 3 and Phase 4 additions: invitation-based account sessions;
  account-scoped run ownership, simulator ledgers and MCP portfolio searches;
  encrypted GitHub OAuth token vault (authorization still requires credentials);
  document uploads; generated TypeScript OpenAPI client; Postgres checkpoint and
  LangGraph memory store configuration; Redis/Arq worker, scheduled searches;
  conservative execution bounds; and a non-fabricating 40-task Ollama study
  harness. See `docs/PHASE3_IMPLEMENTATION.md` and
  `docs/PHASE4_IMPLEMENTATION.md` for tested/untested boundaries.

- Shared API/MCP persistent data paths, a durable run index and reopening
  pending approvals from Pipeline after refresh.
- A real LangGraph update stream consumed by the frontend. The older GET
  events endpoint remains a completed-state replay for compatibility.
- Reviewer-token validation at sign-in; production startup refuses known demo
  tokens. This remains a single-reviewer gate, not multi-user authentication.
- Portfolio Streamable HTTP bearer protection, host/origin validation and a
  configurable per-process rate limit, with an actual initialize contract test.
- Conservative claim content checks, guarantee refusal and configured hard
  stops for detected injection/prohibited-work flags. Known misses remain.
- An hourly negotiation subgraph, floor-based walk-away drafts and a parent
  approval gate; Workspace MCP interview slots and message dry-run previews.
- Real local nomic embeddings with persistent SQLite/sqlite-vec cosine search;
  optional Chroma/cross-encoder support remains separately configurable.
- Two downloaded open language models, local inference runners and actual
  synthetic smoke/benchmark result files. Inspect truncation and sample counts
  before interpreting the model comparison.
- Redacted local trace correlation across API, MCP calls and marketplace audit
  rows; writer token/duration records when the Ollama backend is used.
- Playwright approval workflows, regression gates in CI, an actual captioned
  browser recording, a GIF and code-rendered graphs.
- A report builder within the ten-page limit, article draft, submission checklist, source
  browser test report and Render single-container deployment configuration.

## Still unfinished locally

Tenant-aware production Postgres migration for all account and application
tables, official Upwork OAuth/tool calls, independently verified live GigSim,
full user-specific indexing across all RAG backends, exact token/cost budgets,
full checkpoint replay and complete dead-letter recovery still remain work.
The extended Compose file has not been exercised with Docker in this
workspace. A local trace file is not a hosted tracing product. V3
cross-encoder weights have not been executed by the sqlite-vec backend.

## Requires external resources or account access

The actual instructor GigSim and verified API/credentials; complete labelled
persona/dev corpora; real policy update; authorized Upwork/GitHub MCP sessions;
independent judge/panel studies and simulator outcomes; hidden tests; final demo upload and verified hosted public trace links.
The public GitHub repository, Render app, published project article and Portfolio
MCP source installation page were verified without credentials. A live
authenticated synthetic test verified the deployed session-reuse speedup.

The original deadline is past and an extension is unconfirmed in the latest
clarification. Confirm eligibility with the instructor. No commit is backdated.


## Demo release verification

The final performance change passed Python/contract tests and browser approval,
editing, rejection, degraded-mode, recovery, interview and negotiation scenarios.
Exact counts and timings are in the result files. Reused MCP sessions retain
role allowlists and per-request audit trace IDs; timeout recovery and schema
snapshots are covered by tests. No reviewer credential is stored in the submission folder.

The submission folder is demo-ready, not a claim of complete rubric compliance: the unfinished
production items and independent studies listed above remain explicit.
