# Architecture decisions

The bid graph analyzes a job through three independently scheduled StateGraph branches (analyst, risk, fit), merges their structured outputs, decides bid/skip/watch, prices and drafts; evidence verification precedes critique and compliance, which precedes `interrupt()`. A resumed approved state passes through exactly one idempotent marketplace write. The conversation graph analyzes untrusted client text, drafts and pauses separately before any message. The `LocalMarketplace` implementation persists writes and audit records using SQLite uniqueness constraints. Its API is mirrored by `GigSimMarketplace`; the latter needs the actual service's contract.

The retrieval algorithm is independently authored and explicitly lexical. BM25 and TF-IDF reciprocal rank fusion can be run offline; they are not a learned embedding or a cross-encoder. The default architecture is a development foundation and does not misrepresent those methods as implemented.

Known failure: bid drafts may be too generic without a local LLM; injection detection is heuristic. The human approval and unsupported-claim dropping mechanisms limit their impact, but do not guarantee safety.
