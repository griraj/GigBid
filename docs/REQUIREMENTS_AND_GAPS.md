# Assignment interpretation and honest compliance ledger

The **16-page AI-4016 Assignment II PDF** is the authority. The starter kit was inspected only to determine what was supplied; no starter source or layout was copied. Because the assignment itself prescribes `agent/`, `rag/`, `mcp_servers/`, `apps/`, `evals/`, etc., those public paths were retained.

| Rubric | Implemented and verified | Still required for full marks |
|---|---|---|
| A — MCP (20) | Three official-SDK FastMCP servers, schema annotations, scoped tool calls through MCP ClientSession, dry-run default, SQLite idempotency/audit local port, role allowlists and transport roundtrip tests | HTTP bearer authentication and per-user rate limiter, Inspector captures, real GigSim contract mapping, encrypted OAuth Upwork adapter and approved callback, authorized third-party GitHub MCP session, tool-granularity study (40 tasks) |
| B — RAG (20) | Deterministic fixtures; authorized CSV normalization/merge, PDF/Markdown portfolio import, optional SentenceTransformer + Chroma index, configurable rerank, V8 bounded corrective graph, stronger citation checks, gold-label metric runner and open-model comparison runner; lexical micro-eval run | Actually run downloaded neural weights and external labelled corpora; real Kaggle and supplied persona corpora, calibrated judge, unsupported-claim rate study, classmate blind review, 30-item calibration, ablations, GigSim outcome evaluation, pricing metrics |
| C — LangGraph (25) | Two real StateGraph graphs, official `Send` parallel fanout, typed objects, bounded critique, interrupts, SQLite checkpoints and optional PostgresSaver, deterministic write keys, MCP transport, rule-gated SQLite memory and viewer, integration tests | LangGraph Postgres Store memory promotion, real LLM comparisons (50 jobs), checkpoint replay UI, worker recovery and step/token budgets, injection resistance beyond regex-based detection |
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
2. Complete OAuth Upwork integration through approved official MCP only, live GitHub token integration, HTTP MCP bearer auth and per-user limits; run tool-granularity study.
3. Bring up Postgres/Redis/vector DB/Ollama in Compose, add checkpoint persistence, distributed jobs and schedule; run reset/restart test.
4. Execute the optional CPU neural embedding and reranker models, and compare at least two open LLMs on a real labelled development set.
5. Make full Playwright suite, CI gates, genuine SSE, upload/onboarding/tenancy, memory inspection, and measured all-rubric evaluations.
6. Write PDF report only after actual experiments, publish app/MCP server/article/video and record public traces.

## Assignment submission timing

The supplied specification states a deadline of **12 November 2026 at 11:59 PM PKT**. This build was made on 14 November 2026; do not claim an on-time submission or an eligible commit without checking with the instructor.
