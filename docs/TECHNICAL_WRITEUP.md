# Perfect retrieval was the least useful result in my freelancer copilot

Experimental scope: authored synthetic development data and local model runs. These are not instructor data or real marketplace outcomes.

I started GigBid with a practical question: can an assistant help a freelancer
choose better opportunities without inventing experience or taking control of
the account? The intended product brings together job analysis, portfolio
retrieval, risk screening, proposal drafting and approved client replies. A
React interface lets a reviewer inspect evidence and decide what happens next.
FastAPI connects that interface to handwritten LangGraph workflows and three
MCP servers. The interesting engineering work was deciding what evidence could
justify a decision, and what an apparently successful result actually meant.

My most surprising result was initially reassuring. Every retrieval variant
achieved perfect Recall@5. That included a plain TF-IDF baseline, requirement
decomposition, hybrid lexical fusion, lexical reranking, outcome weighting and
a corrective retrieval loop. It looked as though the retrieval problem had
been solved before I needed an embedding model. Looking at the data made that
interpretation collapse. The fixture contained six evidence items split across
three personas. Only five jobs had positive evidence labels. Once retrieval
was restricted to the correct persona, there were too few eligible items for
Recall@5 to be a demanding test.

The experiment still told me something useful, but its lesson concerned the
measurement rather than a superior retrieval architecture. A metric can be
implemented correctly and still be almost uninformative for the decision I
want to make. In this case, retrieving the relevant document somewhere among
a handful of candidates did not establish that the first document was useful,
that a proposal was truthful, or that a client would reply. Perfect recall
could coexist with bad ranking and unsupported writing.

## When an apparently helpful signal made ranking worse

Outcome weighting produced a more informative negative result. Its MRR fell
from 1.0 to 0.9, and nDCG@10 fell from 1.0 to 0.9262 on the same fixture. These
values come from `evals/results/synthetic_retrieval.json`; the runner regenerates
them from the authored jobs and evidence. They are not statistically persuasive
estimates of real marketplace performance. They do show a concrete failure mode:
rewarding evidence because its associated proposal won can move it above an
item that better matches the current requirement.

A won proposal answers a historical question: something about that application
worked for that opportunity. It does not automatically answer the new question:
does this item prove the freelancer can deliver this particular requirement?
Client preferences, budget, timing and competition may have influenced the
earlier outcome. Even a perfectly observed historical outcome cannot replace
relevance. In a small corpus, an aggressive boost can dominate the weaker
retrieval score and make the problem especially visible.

I kept the outcome-aware variant as an experiment instead of presenting it as
an improvement. The development default remains configurable hybrid lexical
retrieval, but the fixture does not justify claiming that it beats the simple
baseline. A separate backend has now executed real nomic embeddings through Ollama and
persisted them with SQLite/sqlite-vec. It showed the same recall saturation.
Optional SentenceTransformer/Chroma and cross-encoder paths remain separate;
independent labels are needed before a defensible neural shipping choice.
Calling the fallback dense neural retrieval would hide the actual experiment.

## A citation can be correct while the claim is false

The next failure was more directly relevant to safety. The original verifier
checked whether an experience claim cited an existing evidence ID and whether
its numeric assertions appeared in that evidence. This rejected uncited
experience, unknown citations and invented percentages. It also accepted a
sentence about building a lunar rover when that sentence cited the churn
modelling case study. The citation existed; the relationship between the claim
and the source did not.

I saved the original probe results before changing the gate. The revised
version compares substantive claim vocabulary with the cited item's title and
text, rejects explicit guarantees and refuses achievement claims grounded only
in unverified uploaded material. The same authored probes are then executed
again. Their before and after outputs are retained in
`synthetic_system_before.json` and `synthetic_system.json`, so the improvement
can be inspected instead of inferred from a screenshot or a selected example.

This remains a conservative lexical check. It can reject a valid paraphrase,
and a false statement that shares enough words with its source may still pass.
I do not call its output semantic entailment. The important correction was to
stop treating a valid identifier as proof of a supported statement. A proper
evaluation would use independently labelled claims, distinguish partial support
from full support, and test the verifier after a real model has generated drafts.

## Detection and permission are separate boundaries

The risk probes exposed another distinction. A trusted synthetic client could
submit a job containing an explicit instruction to ignore earlier guidance.
The risk node detected the phrase, but one flag alone did not cross the numeric
skip threshold. The job therefore continued to drafting. Detection had worked;
the decision policy had not translated that detection into the expected stop.

The fix was a configurable hard-block list. Recognised prompt-injection and
prohibited-work flags now force skip independently of the aggregate client
risk score. That is a policy decision I can explain and change without
rewiring the graph. It is not a claim that regular expressions solve injection.
The adversarial probes still include paraphrased, encoded and authority-spoofing
requests that the screening rules miss. Those misses stay in the result file.

Across the executed probes, no proposal was sent without approval. That result
comes from a different mechanism: the graph interrupts before a write and
requires an explicit resume decision. The current template writer also does
not interpret arbitrary text as instructions. Consequently, these results do
not establish an attack success rate for a model-backed writer. They establish
that the tested paths retained their human approval boundary, despite known
screening weaknesses. That narrower conclusion is still useful.

## Tool startup dominated the wait

The deployed template/lexical path took about 68 seconds to analyse a job and
12 seconds to approve it in an authenticated synthetic check. The workflow
launched a new MCP subprocess and initialised the protocol for every tool call.
That overhead repeated for individual skill searches, balance reads and writes.
I replaced it with one reusable session per server, with bounded timeouts,
per-call trace metadata and no automatic replay of writes. A local controlled
comparison reduced repeat analysis from about 28 seconds to 0.18 seconds, and
approval from about 6.6 seconds to 0.06 seconds. Those local timings are not
hosted results; the first call still pays process startup. The raw measurements
are in `mcp_performance.json` and `live_performance_before.json`.

## Persistence was a product feature hiding in deployment configuration

Another issue appeared outside the agents. The original container mounted a
persistent directory, while parts of the application wrote SQLite files
elsewhere. MCP subprocesses also replaced the configured marketplace path with
a repository-relative path. A volume in the deployment file could therefore
create the appearance of persistence while checkpoints or writes remained
outside it. The application and its tools needed to agree on the same paths.

I introduced shared path resolution and a durable run index. The Pipeline view
now lists saved graph runs and can reopen an interrupted approval after a page
refresh. The deployment candidate serves the frontend and API from one origin
and mounts the actual data directory. This is a single-reviewer implementation,
not multi-user account isolation. A public host still needs a real persistent
disk, a private token and a restart demonstration before I can claim durable
hosted approvals. A successful local build cannot stand in for that evidence.

## What the small open models actually wrote

I also executed Qwen2.5 0.5B and Qwen3 0.6B on the five positive synthetic jobs.
Their raw outputs, actual token counts and completion reasons are retained in
`open_model_comparison.json`. Some outputs were truncated, and several copied
job descriptions or evidence lists rather than writing a useful proposal.
Faster generation and fewer verifier rejections did not establish better
proposal quality. The experiment is exploratory, not a calibrated model ranking.
An earlier capped smoke run remains separate so its incomplete outputs cannot
be mistaken for full proposal results. That failure led to structured opening,
plan, question and evidence-ID fields. The application assembles the factual
sentences from selected portfolio items and verifies the resulting draft.
Uncited experience introductions are removed, and truncated drafts are blocked.

## What I would measure before making stronger claims

The next valuable experiment requires the missing instructor development set,
not more optimistic scores on the authored fixture. I would hold the job set
constant, compare the required dense baseline with decomposition, hybrid search
and reranking, and report relevance metrics by persona and job type. Claim
verification should have an independently labelled test set. Proposal quality
needs a calibrated judge and blind human comparisons. Simulator reply and hire
rates must come from the actual simulator, not from heuristics labelled as
client behaviour.

The same discipline applies to orchestration. Two handwritten graphs and
parallel branches demonstrate an implementation; they do not prove that the
design beats one ReAct agent or a prebuilt supervisor. That comparison needs
matched tasks, real model calls, token counts, latency and the same approval
policy. Local template timings exclude inference, HTTP and MCP startup, so I
report that scope next to the numbers. Unknown outcomes remain unavailable.

GigBid's strongest finding so far is that useful engineering evidence often
comes from disappointing a convenient story. Perfect recall revealed an easy
test. Outcome weighting reduced ranking quality. Valid citations concealed an
unsupported claim. A detected injection still reached drafting. Each result
changed a specific decision or implementation boundary. The project becomes
more credible when those failures remain visible, reproducible and connected
to the next experiment.

Evidence: `evals/results/synthetic_retrieval.json`,
`evals/results/synthetic_system_before.json`,
`evals/results/synthetic_system.json`; implementation in `rag/verify.py`,
`agent/graphs/`, `agent/paths.py` and `apps/api/main.py`.
