# X5: draft-only negotiation coach

`agent/graphs/negotiation_graph.py` is an executable subgraph with offer
assessment and counteroffer drafting. It accepts explicit hourly amounts,
compares them with the configured floor and produces a walk-away condition
and proposed reply. Fixed project budgets without hourly context trigger a
clarification rather than being misread as an hourly rate.

The parent conversation graph classifies negotiation, invokes the subgraph and
interrupts before sending the suggested reply. It does not agree to a contract
or accept an offer automatically. Reviewer-edited replies are checked again.

Actual local probes are retained under `negotiation_probes` in
`evals/results/synthetic_system.json`. Unit tests cover below-floor, acceptable,
missing-rate and fixed-budget cases. These are synthetic policy checks, not
negotiated client outcomes. The required GigSim achieved-rate versus offered-rate
evaluation remains unavailable without the actual simulator and its contract.
