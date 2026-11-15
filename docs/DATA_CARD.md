# Data card

All records currently shipped are original **synthetic** demonstrations, defined in `data/synthetic.py`. There are 8 jobs, 3 client histories, 6 evidence items, 3 personas and eight manually assigned benchmark labels. `evals/results/synthetic_retrieval.json` is produced by executing the evaluation. The corpus does not include any Upwork or Kaggle record. No actual client messages, identifiable personal information or payment data were imported.

Each evidence record includes stable ID, persona, type, title, text, skills, project, source, date and outcome. Relevance annotations are illustrative, with no adjudicator. Small sample sizes and result saturation prevent meaningful external validity.

Candidate external sources provided by the user: asaniczka Upwork postings 2024 50k, asaniczka all jobs on Upwork 200k+, ahmedmyalo Upwork jobs 60k, asaniczka freelance contracts 1.3m, sarveshchhetri freelancer success/earnings/churn, adityammantri trial-1. **No licenses have been verified, so none are incorporated.** Download and retain source attribution and license evidence before use.


## Completion-pass model provenance

Actual local runs used `nomic-embed-text`, `qwen2.5:0.5b` and `qwen3:0.6b`
from the Ollama model library. Weights are stored by the user's Ollama service,
not committed or included in the submission folder. The Qwen model pages identify the
selected small variants as Apache 2.0; consult each model's own terms before
redistribution. The embedding model has its own model card and licence.

- https://ollama.com/library/qwen2.5:0.5b
- https://ollama.com/library/qwen3:0.6b
- https://ollama.com/library/nomic-embed-text

The real embedding experiment uses the same authored evidence corpus as the
lexical micro-evaluation. Downloading a real model does not turn synthetic data
into real marketplace evidence. Final retrieval timings clear the query cache
before each variant; the earlier warm-cache run remains a separate result file.
