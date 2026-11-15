# Combined Priority 1 + Priority 2 release

## Verified in this release

- Twenty-three automated tests pass, including an actual MCP Python SDK
  `ClientSession` ↔ marketplace server call over stdio.
- LangGraph bid graph runs Analyst, Risk and Fit through `Send` fan-out.
  The risk and fit nodes use MCP tools rather than importing the server
  functions. The pricing node reads the balance through MCP; approved sends
  and proposal submissions go through MCP with deterministic idempotency keys.
- Two interrupt-based LangGraph graphs remain usable: bidding and client
  conversation. SQLite checkpoints survive backend restarts when the optional
  SQLite saver is installed. PostgresSaver is configurable with
  `GIGBID_CHECKPOINT_DATABASE_URL` and optional `.[postgres]` dependencies.
- Three official-SDK servers have defined MCP tool annotations and constrained
  write schemas. Contract tests check names, constraints and read/write hints.
- Role allowlists limit which agent may call each MCP tool. Timeouts fail
  closed. Every marketplace write retains a unique idempotency key and a
  PII-masked append-only audit record in the local development adapter.
- The RAG V8 mode is now a genuine bounded LangGraph corrective loop with
  evidence coverage checks, one re-query and refusal on inadequate evidence.
  The lexical and optional neural paths both support this loop.
- Memory uses explicit rules: two approved edits with the same style signal
  are required before promoting it. Outcome records require a trusted
  `marketplace_verified` source. Settings lets the user view and delete
  promoted records. The development memory store is SQLite, not LangGraph
  Postgres Store.
- Authorized CSV merges, PDF/Markdown portfolio ingestion, persistent
  Chroma-backed neural embeddings, open cross-encoder reranking, Ollama writer,
  gold-label retrieval scoring, and a two-open-model comparison runner are
  implemented as opt-in code paths. The small synthetic baseline is still the
  only executed retrieval benchmark.
- Optional third-party GitHub MCP and official Upwork MCP transport
  configuration is available through `agent/remote_mcp.py` and fails closed
  without authorization.

## What *cannot* be claimed as done

1. **Upwork OAuth:** the official provider currently says arbitrary custom
   hosted app callback URLs may not be accepted. The transport configuration
   is not an OAuth flow; no live Upwork session was connected. No scraper or
   session-cookie workaround was used.
2. **GitHub:** server discovery is configured, but a user-scoped, read-only
   GitHub token and Docker are needed for actual connections.
3. **Marketplace:** the instructor GigSim executable, real schemas, client
   replies/hire outcomes, and hidden test remain unavailable. The REST
   adapter endpoints are provisional.
4. **Datasets and models:** no Kaggle CSVs, original persona corpora or real
   neural weights were supplied to this environment. We did not invent
   labels, token counts, latency comparisons or outcome scores.
5. **Full production:** Redis workers, hosted authenticated MCP servers,
   tenant-scoped OAuth tokens, LangGraph Postgres Store, reconnect UI after
   restart, calibrated LLM judge, and all required 40/50-job ablations remain.

## Quick Windows activation

Recommended separate Python 3.12 virtual environment:

```powershell
cd C:\Users\mohit\Downloads\GigBid
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test,neural,postgres]" langgraph-checkpoint-sqlite
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

Set `GIGBID_TOOL_BACKEND=mcp` (the default). Keep the frontend command in
another PowerShell window: `npm.cmd run dev` from `apps\web`.

To enable local models after installing Ollama and its configured model:

```powershell
$env:GIGBID_RAG_BACKEND='neural'
$env:GIGBID_LLM_BACKEND='ollama'
$env:GIGBID_TOOL_BACKEND='mcp'
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

The neural model runs inside the Portfolio MCP subprocess, so initial model
loading can be slow; memory/CPU usage should be measured before deployment.
For complete data import and evaluation instructions see
`docs/PRIORITY1_SETUP.md`.
