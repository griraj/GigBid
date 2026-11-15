# Data card

All records currently shipped are original **synthetic** demonstrations, defined in `data/synthetic.py`. There are 8 jobs, 3 client histories, 6 evidence items, 3 personas and eight manually assigned benchmark labels. `evals/results/synthetic_retrieval.json` is produced by executing the evaluation. The corpus does not include any Upwork or Kaggle record. No actual client messages, identifiable personal information or payment data were imported.

Each evidence record includes stable ID, persona, type, title, text, skills, project, source, date and outcome. Relevance annotations are illustrative, with no adjudicator. Small sample sizes and result saturation prevent meaningful external validity.

Candidate external sources provided by the user: asaniczka Upwork postings 2024 50k, asaniczka all jobs on Upwork 200k+, ahmedmyalo Upwork jobs 60k, asaniczka freelance contracts 1.3m, sarveshchhetri freelancer success/earnings/churn, adityammantri trial-1. **No licenses have been verified, so none are incorporated.** Download and retain source attribution and license evidence before use.
