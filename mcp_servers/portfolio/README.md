# GigBid Portfolio MCP

Read-only evidence search, case studies, demonstrated skills, portfolio resources,
and a screening-answer prompt using the official MCP Python SDK.

## Install and run from the public repository

```bash
git clone https://github.com/griraj/GigBid.git
cd GigBid
python -m venv .venv
# Activate .venv using the command for your operating system.
python -m pip install .
python -m mcp_servers.portfolio.server
```

The final command speaks MCP over stdio. Configure your host to launch the
virtual environment's absolute Python executable with arguments
`["-m", "mcp_servers.portfolio.server"]`, and set its working directory to this
checkout. Default evidence is explicitly synthetic, separated by the `ai`, `web`
and `analytics` personas. Imported portfolio text remains unverified.

## Docker distribution

```bash
docker build -f infra/docker/Dockerfile.api -t gigbid-portfolio .
docker run --rm -i gigbid-portfolio python -m mcp_servers.portfolio.server
```

This is a documented source/Docker installation route, not a claim that a package
has been uploaded to PyPI. Use a verified public release commit for reproducibility.

## Streamable HTTP

Set `GIGBID_MCP_BEARER` to a private random token, then run:

```bash
uvicorn mcp_servers.http:app --host 0.0.0.0 --port 8001
```

Connect at `https://YOUR-MCP-HOST/mcp` with an `Authorization: Bearer ...` header.
Terminate TLS at your host or reverse proxy. The process refuses an absent or
known placeholder token; the default limit is 60 authenticated requests per
minute, configurable through `GIGBID_MCP_RATE_LIMIT`. This is a single reviewer
identity and a process-local limiter; multiple replicas require a shared limiter.

## Surface and provenance

- `search_evidence(requirement, k, persona, filters)` returns source-attributed items.
- `get_case_study(id)` returns a full case study or uploaded document chunk.
- `list_skills(persona)` returns demonstrated tags for one persona.
- Resources: `portfolio://case/{id}`, `portfolio://proposal/{id}`.
- Prompt: `answer_screening_question(question)` requires evidence and abstention.

Run `python -m pytest tests/contract -q` for schema, stdio transport and HTTP tests.
Never mount private client portfolios into a public demo server.
