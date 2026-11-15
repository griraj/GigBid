# Priority 1 — Data, real embeddings, RAG, and open-model proposal writing

This release extends the previous GigBid. **Synthetic mode still works without downloads.**
Neural inference and the open model writer are opt-in: activation fails clearly
when models cannot be loaded. Do not report synthetic fixture scores as Kaggle
or instructor development-set measurements.

## 1. Install on Windows

The previous console used Python 3.14. Because large ML dependencies have
version-specific binary support, **Python 3.12 in a separate virtual environment
is recommended** for this stage. Keep the existing installation untouched.

```powershell
cd C:\Users\mohit\Downloads\GigBid
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e ".[test,neural]" langgraph-checkpoint-sqlite
.\.venv\Scripts\python.exe -m pytest -q
```

Install Ollama separately using its official installer, then obtain the model
declared in `agent/config.yaml` (currently `qwen3:4b`):

```powershell
ollama pull qwen3:4b
```

The first neural startup downloads `sentence-transformers/all-MiniLM-L6-v2`
from the official model host. The V3 reranker additionally downloads
`cross-encoder/ms-marco-MiniLM-L-6-v2`. Internet access is needed for initial
downloads; the models then run locally on CPU. Do not set the neural option
unless enough RAM and disk space are available.

```powershell
$env:GIGBID_RAG_BACKEND = 'neural'
$env:GIGBID_LLM_BACKEND = 'ollama'
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

To revert safely, set `GIGBID_RAG_BACKEND=lexical` and
`GIGBID_LLM_BACKEND=template`. `/health` reports the chosen retrieval backend.

## 2. Add actual Kaggle CSV exports

Download datasets manually through the authorized Kaggle UI/API. Read and
retain the actual dataset page's license, provenance and attribution; don't
re-publish source records without permission. The ingestion script does **not**
scrape any site. You can combine multiple exports in a single command:

```powershell
.\.venv\Scripts\python.exe -m data.ingest `
  --input "C:\data\upwork_50k.csv" --source "asaniczka/upwork-job-postings-dataset-2024-50k-records" `
  --input "C:\data\upwork_60k.csv" --source "ahmedmyalo/upwork-freelance-jobs-60k"
```

Files are processed to `data/processed/jobs.jsonl`: whitespace/HTML cleanup,
column aliases, numeric budget parsing, skill normalization, content-hash
deduplication, provenance merging and source counts. The exact CSV schema
should be checked before treating any column as meaningful. Processed records
are local and git-ignored. Restart the API to see newly imported jobs.

**Important:** Kaggle job posts are research-only in the local simulator. GigBid
shows their source and may analyze them, but never sends a synthetic proposal
to a real scraped/archived job listing. The actual GigSim adapter still needs
the instructor's API contract.

## 3. Add a real portfolio

You may ingest your own PDF CV, Markdown case studies, and text documents:

```powershell
.\.venv\Scripts\python.exe -m rag.ingest_portfolio --directory "C:\data\my_portfolio" --persona ai
```

The importer extracts PDF text, splits documents into overlapping passages,
creates stable IDs, and records file-level attribution. The records are tagged
`user_uploaded` and `unverified` until achievements are corroborated.
Restart the API to reindex. For multiple personas, supply a separate output
file or merge the generated JSONL files after checking unique IDs.

## 4. Five retrieval variants and one corrective mode

| ID | Operational implementation |
|---|---|
| V0 | Neural vector similarity (in neural mode); TF-IDF in lexical mode |
| V1 | Requirement decomposition and merged retrieval |
| V2 | Neural + BM25/TF-IDF reciprocal rank fusion |
| V3 | Open cross-encoder re-ranking of top candidates |
| V4 | Outcome-aware priority adjustment |
| V8 | Weak-result fallback query; **not yet a full LangGraph corrective subgraph** |

Chroma provides a locally persistent vector collection. IDs and content hashes
enable incremental upserts and deletion of stale chunks.

## 5. Evaluate honestly

`make eval` regenerates only the tiny synthetic fixture benchmark. For a
research-grade comparison, create a JSONL file with independently labelled
relevant evidence IDs, for example:

```json
{"query":"Need a Python churn model", "persona":"ai", "requirements":["python","classification"], "job_type":"machine_learning", "relevant_evidence_ids":["e1"]}
```

Run:

```powershell
.\.venv\Scripts\python.exe -m evals.runners.evaluate_gold --labels "C:\data\dev_gold.jsonl" --backend neural
```

This records Precision@5, Recall@5, MRR, nDCG@10, p95 retrieval latency and
results by persona/job type. Label sets should come from instructor dev labels
or blind human relevance annotation, never the model's own retrieved answers.

## 6. What is still unverified / incomplete

- This build environment could not install the neural runtime because the
  available package cache volume was full. Real neural model loading and
  cross-encoder scores therefore **have not been executed** here.
- No Kaggle CSV files were actually supplied or ingested during this turn;
  the pipeline is ready to consume authorized exports.
- Ollama proposal generation is functional through its HTTP API path when
  installed and configured, but no live model invocation was run here.
- Claim checks enforce citation presence and numeric evidence checks, not
  semantic entailment or a calibrated judge; human review remains mandatory.
- Open model A/B studies, 30-item judge calibration, realistic proposals and
  actual GigSim replies/hire rates still require real data and model runs.
- V8 needs a full LangGraph corrective retrieval loop, not just fallback.
