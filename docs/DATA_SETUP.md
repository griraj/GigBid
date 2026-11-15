# Data and model setup

The default template/lexical demonstration uses clearly labelled synthetic
fixtures. Downloaded datasets are optional research inputs, not instructor data.
Use README.md to create `.venv` and install the base dependencies first.

## Import authorised job exports

Check each dataset's licence, attribution and redistribution terms before use.
Download through the authorised provider UI/API; this project does not scrape.
Multiple CSV exports can be normalised and deduplicated together:

```powershell
.\.venv\Scripts\python.exe -m data.ingest `
  --input "C:\data\jobs_a.csv" --source "dataset-owner/dataset-a" `
  --input "C:\data\jobs_b.csv" --source "dataset-owner/dataset-b"
```

The importer normalises whitespace, column aliases, budgets and skills, merges
provenance and writes ignored `data/processed/jobs.jsonl`. Imported real job
exports are research-only in the local simulator; they cannot receive external
submissions through the synthetic marketplace.

## Import a portfolio

```powershell
.\.venv\Scripts\python.exe -m rag.ingest_portfolio --directory "C:\data\portfolio" --persona ai
```

PDF, Markdown and text imports retain source attribution and stable chunk IDs.
Uploaded claims remain unverified. Restart the API after import to rebuild its
portfolio index and start fresh tool-server sessions. For multiple personas,
use separate output files and merge deliberately without duplicate IDs.

## Local models and vector storage

Run `python scripts/prepare_open_models.py` with Ollama running to obtain the
explicitly named small models. Set `GIGBID_LLM_BACKEND=ollama` and
`GIGBID_RAG_BACKEND=ollama-vector` for real generation and nomic embeddings in
SQLite/sqlite-vec. `GIGBID_MCP_TIMEOUT=120` permits slower cold model loads.
Model weights stay in Ollama's own storage and are not submission files.

The optional `.[neural]` extra enables SentenceTransformer/Chroma retrieval and
cross-encoder reranking. Install its weights before selecting the neural path.
V8 uses the bounded corrective LangGraph; it is not simply a fallback string.

Use docs/EVALUATION.md for independent relevance labels, system labels and the
exact experiment commands. Never replace missing instructor outcomes with
synthetic reply/hire scores.
