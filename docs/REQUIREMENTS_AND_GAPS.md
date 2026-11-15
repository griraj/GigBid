# Assignment interpretation and honest compliance ledger

The **16-page AI-4016 Assignment II PDF** is the authority. The starter kit was inspected only to determine what was supplied; no starter source or layout was copied. Because the assignment itself prescribes `agent/`, `rag/`, `mcp_servers/`, `apps/`, `evals/`, etc., those public paths were retained.

| Rubric | Implemented and verified | Still required for full marks |
|---|---|---|
| A — MCP (20) | Three official-SDK FastMCP servers, named read/write tools, dry-run default, SQLite idempotency/audit local port | Agent-to-tool MCP invocation (graph currently uses Python port), HTTP bearer authentication and tool annotations, rate limiter, in-memory MCP tests, Inspector captures, real GigSim contract mapping, encrypted OAuth Upwork adapter, authorized third-party GitHub MCP, tool-granularity study (40 tasks) |
| B — RAG (20) | Deterministic ingestion fixtures, six lexical variants, precision-oriented structured evidence selection, claim removal, measured Recall@5/MRR/nDCG@10 script | Actual licensed Kaggle or supplied persona corpus, open neural embeddings, vector DB, cross-encoder reranker, calibrated judge, claim-rate study, classmate blind review, 30-item calibration, ablations, GigSim outcome evaluation, pricing metrics |
| C — LangGraph (25) | Two real StateGraph graphs, parallel fanout, typed objects, bounded critique, interrupts, local durable SQLite checkpoints if driver present, deterministic write key, integration tests | Postgres checkpointer, LangGraph Store memory promotion, real LLM agents and baseline comparisons (50 jobs), checkpoint replay UI, worker recovery and step/token budgets, official `Send` fanout, injection resistance beyond regex-based detection |
| D — Interface (15) | React + TypeScript, responsive UI, sign-in mock, inbox, details/evidence, approval editor, pipeline overview, messages, analytics and settings | Proper multi-user auth, connected account setup/portfolio upload, real ranked list, true Kanban state, persisted pending thread browser after refresh, genuine streaming during execution (current SSE replays node states after completion), Playwright 5-test suite, generated OpenAPI client |
| E — Production (10) | Runnable local API and Vite build, integration tests, audit records, guarded local sends | Docker Compose all services, worker/Redis, Postgres, neural vector store, tracing backend, CI eval gates, public host and reviewer credentials, OAuth encryption, comprehensive PII redaction, tenancy |
| Portfolio/report (10) | README, architecture and data explanation, this ledger, reproducible micro-eval | <=10-page research PDF based on real dev data, 1200–1800-word published article, public MCP package, demo video/GIF, trace links, 10 failure analyses, change-request comparison, signature extension evaluation |

## Data licensing and provenance

- **Actually used:** the synthetic fixtures authored in `data/synthetic.py`. Their contents and miniature labels are openly inspectable. Neither the starter code nor the starter sample JSON was copied.
- **Not downloaded:** six user-proposed Kaggle datasets. They may not be redistributable under identical terms; licensing must be checked on each dataset page before downloading, joining, or committing data. Never call these fixtures “Kaggle results.”
- **Not provided in the uploaded archive:** claimed instructor GigSim executable service and its 200-jobs-per-persona labelled development set. The archive includes two example job records and thin mock stubs, not the simulator or full corpus.
- **Limitations:** tiny sample, optimistic metrics, biased relevance annotations, local simulated approval outcomes not replies or hires, no neural semantic generalization.

## Priorities to close the gap

1. Obtain the instructor's actual GigSim base URL/auth docs, complete persona corpora, gold development labels and 2 November policy change request. Validate adapter calls before attempting real outcomes.
2. Implement genuine MCP client boundaries (per-agent allowlists) and OAuth Upwork integration through official MCP only. Build safe HTTP auth and audit redaction.
3. Bring up Postgres/Redis/vector DB/Ollama in Compose, add checkpoint persistence, distributed jobs and schedule; run reset/restart test.
4. Replace lexical fallback with CPU embedding, implement actual neural rerank and V8 corrective graph, and compare at least two open LLMs by reproducible runs.
5. Make full Playwright suite, CI gates, genuine SSE, upload/onboarding/tenancy, memory inspection, and measured all-rubric evaluations.
6. Write PDF report only after actual experiments, publish app/MCP server/article/video and record public traces.

## Assignment submission timing

The supplied specification states a deadline of **12 November 2026 at 11:59 PM PKT**. This build was made on 14 November 2026; do not claim an on-time submission or an eligible commit without checking with the instructor.
