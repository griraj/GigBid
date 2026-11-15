# Operator runbook

Use the Windows commands in README.md for the API and frontend. The working
completion environment is `.venv-current`; the supplied `.venv` referenced a
missing Python interpreter. Exact tested versions are recorded in
`evals/results/environment.json`.

## Persistence and recovery

Set `GIGBID_DATA_DIR` to a persistent writable directory. The API and MCP
subprocesses share marketplace, checkpoint, memory and run-index paths. Set
`GIGBID_DB_PATH` only for an intentional marketplace override. The Pipeline
reopens saved interrupted runs after refresh. Without the SQLite saver package,
the health endpoint reports non-durable memory fallback; do not claim recovery.

Back up SQLite files only with services stopped or a proper SQLite backup.
Do not delete useful records to reset a demonstration. The hosted restart and
exactly-once checks in DEPLOYMENT.md are required before public deployment.

## Local models

Start Ollama, install the explicit models with `scripts/prepare_open_models.py`
and enable `GIGBID_LLM_BACKEND=ollama`, `GIGBID_RAG_BACKEND=ollama-vector`.
The configured writer is a small open model. Model outputs, latency, token
counts and truncation are retained by the experiment runners. Use a larger
writer only after measuring it. Slow/cold model loads can exceed tool timeouts;
set `GIGBID_MCP_TIMEOUT` deliberately and keep unavailable-model errors visible.
Do not silently label template output as model inference.

## Degraded operation and safety

Unavailable marketplace reads produce errors; the live stream reports an
interruption and the UI displays a degraded-mode banner. Partial checkpoints
remain indexed, but automatic Redis queue recovery is unfinished. No background
scheduler currently polls external accounts. Live Upwork mode remains disabled
without official OAuth authorization. No polling interval or simulator route
contract is invented.

Production startup requires a private token and deployment needs the persistent
data mount. This release has one reviewer identity, not tenant isolation.
Keep real client data out of a public demonstration. HTTP Portfolio MCP also
requires its own bearer and explicit allowed hosts/origins.

## Traces and checks

Requests get `X-Trace-ID`; redacted MCP events and actual writer usage are
written to `GIGBID_DATA_DIR/traces.jsonl`. Marketplace audit writes carry that
correlation ID. Local files are not hosted LangSmith/Langfuse/Phoenix links.
Review trace retention and masking before using real data.

Run Python tests, frontend build, Playwright and the synthetic regression gates
before packaging. Read EVALUATION.md for supplied-label evaluation. See
SUBMISSION_CHECKLIST.md for the public deliverables that remain.
