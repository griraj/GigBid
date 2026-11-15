# Reproduce experiments and add instructor data

## Available synthetic experiments

```bash
python -m evals.runners.compare_retrieval
python -m evals.runners.evaluate_system
python -m evals.runners.check_gates
```

These use eight authored jobs and six evidence items, not the instructor's dev
set. Only five queries have positive relevance labels. The initial adversarial
and claim behaviour is preserved in `synthetic_system_before.json`; the current
runner regenerates `synthetic_system.json`. A gate verifies decisions and the
authored claim probes, not a real GigSim reply-rate threshold.

## Real local model calls

Start Ollama and install the models with `python scripts/prepare_open_models.py`.
Model downloads consume local disk and network bandwidth. Then run:

```bash
python -m evals.runners.compare_open_models --input evals/datasets/synthetic_writer.jsonl --models qwen2.5:0.5b qwen3:0.6b
python -m evals.runners.evaluate_ollama_rag
```

The second command uses actual nomic embeddings through Ollama and cosine
distance in persistent SQLite/sqlite-vec storage. Install `.[neural-lite]`.
V3 cross-encoder evaluation still needs the separate `.[neural]` dependencies
and downloaded reranker weights; it is excluded instead of substituted.

Writer results retain raw and cleaned synthetic drafts, generated/prompt token
counts and measured latency. A verifier rejection is a heuristic observation,
not an independently judged unsupported claim. Local inference has no paid API
bill; hardware/electricity costs are not estimated. Do not compare latency runs
while another model experiment is competing for the same Ollama process.

## Instructor retrieval labels

Place authorized documents in the portfolio importer and supply independent
JSONL labels with `query`, `persona`, `requirements`, `relevant_evidence_ids`
and optionally `job_type`. Then run:

```bash
python -m evals.runners.evaluate_gold --labels path/to/dev_retrieval.jsonl --backend neural
```

Gold evidence IDs must match imported stable IDs. Never derive relevance labels
from the retriever's own predictions. Empty relevance sets are excluded from
retrieval metric averages and must be counted separately for decisions.

## Instructor system labels

Provide JSONL records with the full normalized `job`, `persona`, Boolean
`expected_bid`, Boolean `expected_scam`, `relevant_evidence_ids` and optional
`fair_price_band` array. Configure the verified marketplace adapter and run:

```bash
python -m evals.runners.evaluate_dev --labels path/to/dev_system.jsonl
```

This executes graph decisions and safe previews only. It never resumes approval
or spends Connects. Prices are scored only where a price and a labelled band
both exist; the denominator is reported. Watch counts as non-bid. Reply/hire
rates require a separately authorised fixed-set run against the real GigSim
service and its outcome events. The actual service contract is missing, so no
fake outcome runner or fabricated response is included.

## Studies that remain unperformed

The 40-task tool granularity experiment; 50-job ReAct/supervisor/handwritten
comparison; independent ablations; 30-item judge calibration; blind human
panel; real policy-change measurement and hidden-test run remain outstanding.
They are not replaced by the small regression fixtures.
