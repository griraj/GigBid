# Assignment compliance: verified scope and external gates

Reviewed against the AI-4016 assignment PDF and GitHub `main` at commit
`8788445` (2026-11-15). This is an engineering checklist, **not** a claim of
full rubric compliance. Commit IDs and result artifacts must remain truthful.

The next phase added opt-in account sessions, owner-scoped run/memory access,
an Arq/Postgres queue path, GitHub OAuth token encryption, document uploads,
and a generated OpenAPI TypeScript client. See `docs/PHASE3_IMPLEMENTATION.md`
for precise limitations and activation instructions.

Phase 4 subsequently added per-user local marketplace ledgers, portfolio MCP
search routing, conservative run-budget guards, scheduled scouting, and a
LangGraph Store-backed memory implementation. Its verification and external
dependencies are documented in `docs/PHASE4_IMPLEMENTATION.md`.

## Implemented in this worktree (not yet deployed)

- An authenticated, read-only `GET /runs/{thread_id}/history` endpoint exposes
  up to 100 actual LangGraph checkpoint metadata records. It does **not**
  replay external writes; a safe replay engine still needs to be designed.
- `POST /runs/{thread_id}/regenerate-paragraph` provides a conservative
  evidence-cited replacement suggestion while a proposal awaits approval.
  It does not mutate the checkpoint or spend Connects. The same original
  approval/verification guard still applies before any submission.
- The proposal studio now offers this controlled regeneration action.

## Critical local work that remains

1. **Identity and isolation.** Complete tenant scoping through marketplace,
   MCP subprocesses, account-specific RAG and persistent database operations.
   The new opt-in user auth scopes private API resources but does not yet
   isolate the shared synthetic marketplace or Connects balance.
2. **Durable execution.** Integrate the new Arq + Postgres queue path in a
   real Compose run, and add scheduled scouting, Postgres long-term store,
   tenant-scoped queue deduplication, crash
   recovery and safe checkpoint replay. Bound steps, tokens, latency and costs;
   route overruns to a visible dead-letter status. A SQLite fallback exists
   but is not a production substitute on Render's ephemeral free tier.
3. **User onboarding.** Uploaded text documents are now stored per-user,
   but still need incremental private RAG indexing, GitHub repository content,
   account-specific budgets and preferences. The OpenAPI client is generated;
   remaining handwritten request paths still need migration.
4. **Infrastructure and traces.** Compose the complete worker, Redis,
   Postgres, MCP, Ollama, API and frontend stack. Configure real hosted traces,
   correlated IDs, redaction, service health and secrets; verify public links.
5. **Model/retrieval evaluation.** Run real neural V3 cross-encoder weights,
   ablation, calibrated judge against 30 human ratings, 40-task tool choice
   comparison, and 50 labelled-job agent architecture comparison. Save raw
   predictions, prompts, timing, configurations and computed metrics. The
   existing V3 neural code can load a `CrossEncoder` if its weights are present;
   lexical V3 is **not** cross-encoder evaluation.

## Dependencies that code alone cannot satisfy

- Instructor-supplied GigSim URL, verified API schema/credentials, labelled
  persona corpora, ~200-job/persona dev set and the actual November 2 policy
  update. Ask the instructor/course platform; do not invent them.
- Explicit Upwork and GitHub account OAuth authorization and any required
  provider app registration. Do not automate login, scrape or store credentials
  in Git. Official remote MCP connections need live authorized tests.
- Blind human proposal panel, 30 independent judge labels and GigSim
  reply/hire outcomes. These are measurements involving people or external
  services and must not be fabricated.
- Host ownership and paid infrastructure choices where a free service cannot
  support persistent Postgres/Redis/tracing. The Render free app is a demo,
  not evidence of a complete production deployment.

## Suggested verification order

Tenant auth and query scoping -> production databases and worker -> OAuth
integration -> datasets/GigSim -> controlled studies -> hosted traces and
replay -> full CI/browser tests -> R&D report refresh -> instructor submission.

The original PDF states November 12, 2026 as its deadline. A later extension
cannot be inferred from the code: obtain a written confirmation from the instructor.
