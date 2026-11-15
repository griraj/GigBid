# Phase 3: identity, durability, OAuth and API contract

These are **incremental capabilities**, not a statement that all Assignment 2
requirements are complete. Tests run against development SQLite and mocks;
the production Postgres/Redis/OAuth stacks require real credentials and an
integration run. The existing Render Free container remains a reviewer demo.

## Multi-user mode (opt in)

Set `GIGBID_AUTH_MODE=multi`, `GIGBID_SIGNUP_INVITE=<private random value>`
and persistent `GIGBID_DATA_DIR`. The sign-in screen switches to invited
email/password accounts. Passwords use salted scrypt; sessions are random
bearer tokens stored only as SHA-256 hashes, expire after 24 hours and can
be revoked. The API restricts run listing, checkpoint history, approvals,
conversations, and style/outcome memory to the owning user. Existing reviewer
mode is kept for deployment migration. Never distribute the invitation secret.

**Limits:** This is not complete production tenant isolation. The current
simulated marketplace, Connects balance, persona evidence, MCP subprocesses and
index are still shared across tenants. The accounts, run index and uploaded
portfolio still use SQLite; deploy production Postgres tables and tenant-bound
MCP context before enabling multi-user accounts on a public host. A second
login does not imply every backend adapter has been made tenant-safe.

## Docker + background jobs

`infra/docker-compose.yml` now provisions Postgres 16, Redis 7, API,
Arq worker and frontend. Set both `GIGBID_POSTGRES_PASSWORD` and
`GIGBID_API_TOKEN` privately before running:

```bash
docker compose -f infra/docker-compose.yml --env-file .env up --build
```

When `GIGBID_REDIS_URL` and `GIGBID_CHECKPOINT_DATABASE_URL` are configured,
the UI submits analyses through `POST /runs/queue`. The worker runs the bid
graph with a shared Postgres checkpointer, which pauses before submission;
the UI polls the saved graph state. `GET /health` reports `queue_enabled`.
The preexisting synchronous API route remains for the free single-container
demo. Worker scheduling for saved searches, cross-process idempotent queues,
dead-letter handling, token budgets and complete disaster recovery are not yet
implemented. On a single Render Free service Redis/Postgres will not appear
automatically; keep queue configuration unset there.

## GitHub OAuth (opt in)

Create a GitHub OAuth app whose callback is
`https://YOUR_DOMAIN/api/auth/github/callback`. Configure:

- `GIGBID_GITHUB_OAUTH_CLIENT_ID`
- `GIGBID_GITHUB_OAUTH_CLIENT_SECRET` (server secret; never put in Vite)
- `GIGBID_PUBLIC_BASE_URL=https://YOUR_DOMAIN`
- `GIGBID_OAUTH_ENCRYPTION_KEY` (persistent Fernet key; rotate with migration)

Generate the encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

`POST /auth/github/start` returns an authorization URL and stores a one-use,
10-minute state challenge bound to the user. GitHub's callback exchanges the
code on the server; the token is encrypted at rest and never returned to the
browser. Disconnect removes the saved token locally. Current requested scope
is `read:user` to avoid unnecessary repository access. Token refresh/revoke
at the provider, repository ingestion through the GitHub MCP server, and
official Upwork OAuth remain separate work requiring authorization. The real
GitHub exchange has **not** been exercised with a user account.

## Portfolio document storage

`POST /portfolio/upload` accepts UTF-8 TXT/MD and text-extractable PDFs,
limited to 500 KB / 50 PDF pages. Filenames are not used as disk paths.
Uploads are associated with the authenticated user and can be listed/deleted
from Settings. They remain separate from authored demo evidence. Per-tenant
RAG indexing, chunk metadata, GitHub ingestion and complete onboarding still
need implementation before claiming B1 compliance.

## Generated API client

```bash
make api-client
```

The first command exports the actual FastAPI OpenAPI document to
`apps/web/src/lib/api/openapi.json`. `openapi-typescript` generates
`schema.d.ts`, and `openapi-fetch` supplies the typed client. Health-check
bootstrap already uses it; legacy handwritten requests can be migrated
incrementally. CI should later assert generated code is up to date.

## Hosted traces and evaluations

Use LangSmith only after configuring a private LangSmith account/project and
`LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT=gigbid`.
Native LangGraph spans can then be forwarded through its tracing integration.
This has not been independently validated or linked to full MCP audit events.
The specified 40-task, 50-job and cross-encoder studies still need their
labelled inputs, independent comparison baselines and real execution.
