# Phase 4: remaining production foundations and research harness

This document differentiates **executed checks** from code paths that still
require external services. No simulator result, judge rating, human response,
OAuth authorization or hosted trace is fabricated.

## Implemented

- **Tenant-scoped local marketplace:** Each authenticated multi-user account
  gets an independent SQLite simulator database for Connects, messages, audit
  and idempotency keys. MCP subprocess sessions receive the tenant ID through
  server-created environment parameters, not from a client-submitted argument.
  The existing reviewer mode keeps its original database.
- **Tenant-scoped portfolio MCP:** In multi-user mode, uploaded documents are
  included only in their owner's MCP evidence searches. The index refreshes
  when a new upload is saved, even during a persistent server session.
  Uploaded claims are marked `unverified`; the proposal verifier still refuses
  unsupported assertions. Authored public synthetic evidence is a shared demo
  fixture, not another user's confidential corpus.
- **LangGraph memory store:** `GIGBID_MEMORY_DATABASE_URL` selects
  `PostgresStore`; SQLite memory remains a dev fallback. Style signals are
  promoted only after repeated approved edits, outcomes only when the source is
  explicitly `marketplace_verified`. Storage namespaces include the user ID.
- **Scheduling:** Saved searches are per-user, cannot run more frequently than
  every 4 hours, and record seen job IDs. An hourly Arq cron task enqueues
  new analyses. Only the bid graph's interrupt gate can approve an external
  write; scheduled scouting never submits proposals or messages.
- **Execution budget safeguards:** An initial conservative input-length
  estimate can divert oversized jobs to `needs_attention`. API/worker graph
  invocations now set LangGraph's `recursion_limit` from `max_steps`; caught
  errors are recorded as attention states without persisting exception text.
  Exact model-token accounting and cost budgets remain future work.
- **Research runner:** `evals/runners/tool_study.py` defines 40 authored,
  schema-validated tasks and three tool-description inventories. It uses a
  real configured Ollama model and saves every prediction, tool selection,
  argument match, timing, and token count. The script does **not** simulate
  model answers or produce a results file when Ollama is unavailable.
- **Compose:** Adds a protected internal Portfolio HTTP MCP service and an
  optional Ollama service (`--profile local-model`). Instructor GigSim is not
  bundled because its actual service and contract have not been provided.

## How to run the tool experiment

With Ollama running and a model already pulled:

```bash
python -m evals.runners.tool_study --model qwen3:0.6b --limit 40
```

This makes 120 actual local model requests (40 tasks x 3 catalogs) and may
take substantial time on an 8 GB laptop. A quick dry connectivity probe is
possible with `--limit 1` but does not count as the required 40-task study.
Results, if successfully produced, go to
`evals/results/tool_study_ollama.json`. The task set is **authored synthetic**,
not a supplied instructor set. Coarse tools have a different answer space, so
the experiment reports that comparability limitation.

## Real Compose test procedure

1. Set `GIGBID_API_TOKEN`, `GIGBID_MCP_BEARER`, and
   `GIGBID_POSTGRES_PASSWORD` to independently generated private values in
   your local `.env` file. Keep `.env` out of Git.
2. Run `docker compose -f infra/docker-compose.yml --env-file .env up --build`.
   Optionally add `--profile local-model` to start Ollama; model weights need
   to be pulled separately and locally.
3. Verify API health, create two invited accounts in multi-user mode, upload
   different portfolio documents, send dry-run marketplace calls, and confirm
   separate databases, MCP evidence sets, Connects and saved searches.
4. Queue an analysis, kill the API while the graph awaits approval, restart,
   approve once and verify the marketplace ledger has exactly one write.

These Compose checks were **not** executed in this workspace because Docker,
running Postgres, Redis and OAuth/GigSim credentials were unavailable.

## Still needed for full assignment compliance

- Production Postgres migration for **all** identity, OAuth, upload, search
  and run-index metadata (only checkpoints and promoted memory are backed by
  Postgres in the current Compose design).
- Official Upwork OAuth 2.1 handshake and live tool mapping verified against
  the actual third-party server. A protected GitHub token handshake exists,
  but repo ingestion still requires the official GitHub MCP tool connection.
- Verified instructor GigSim contract and service URL, provided labelled
  personas/dev jobs, and actual November 2 policy update.
- Full 50-job single-agent/ReAct, supervisor and hand-built graph comparison;
  independent cross-encoder execution; retrieval ablation; 30-label calibrated
  judge; blind human review; fixed-set simulator reply/hire outcomes.
- Real hosted trace URLs, per-node accurate costs, full replay from arbitrary
  checkpoints, comprehensive dead-letter recovery, complete live-mode safety
  verification, and external publication/submission links.

Do not describe this phase as complete rubric compliance or cite synthetic
smoke scores as independently labelled GigSim results.
