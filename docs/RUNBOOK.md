# Operator runbook

Run `make dev` from project root and `npm run dev` from `apps/web`. Test with `make test`, evaluate with `make eval`, and compile Python with `make lint`. The local marketplace is seeded in Python. Reset a stuck demonstration by stopping services and moving the SQLite database files **after ensuring no useful local records need retaining**.

If `langgraph-checkpoint-sqlite` is installed, interrupts persist in `checkpoints.sqlite`, but the in-browser thread index currently does not; keep the `/runs/{thread_id}` URL/id to resume through the API. Without this package, an in-memory saver is used and a restart loses approvals. Authentication is demo-only and must never be deployed publicly unchanged.

If GigSim becomes unavailable, external reads raise `MarketplaceUnavailable`; the API returns 503 for the job list. The external API paths are provisional and require instructor validation. Live Upwork mode fails closed. No background scheduler currently runs; do not claim a production interval, cost, latency or uptime target.
