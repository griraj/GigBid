# Deploy the single-container review build

The repository includes `render.yaml` and `infra/docker/Dockerfile.deploy`.
The app is deployed at https://gigbid-ti71.onrender.com/ and its public
write-up is at https://gigbid-ti71.onrender.com/writeup. Current verification
and authenticated timing records live in evals/results/.
The candidate uses a single reviewer token and synthetic local marketplace.

## Render

1. Push the reviewed source to your own public GitHub repository.
2. Sign in to Render and create a Blueprint from that repository. The Blueprint
   selects the Free web service plan and does not attach a persistent disk.
3. The Blueprint builds the frontend and Python API into one container. The API
   runs beneath `/api`; the frontend uses the same origin. The health endpoint
   is `/api/health` and SQLite files live beneath `/app/local_data`.
4. Render generates `GIGBID_API_TOKEN`. Retrieve it privately from service
   settings and enter it in the app. Never copy it into Git, a video or the
   public submission manifest.
5. Test an opportunity and approve it during the same running session. Check
   that only one local marketplace write is recorded and Connects are deducted
   once. A browser refresh can reopen saved approvals while this instance runs;
   restarting or spinning down the service resets its local state.
6. Record the real public URL only after these checks. Allow for a cold start
   when opening an idle service, and check availability before review.

Free services spin down after 15 minutes without inbound traffic and take about
a minute to wake up. SQLite databases, pending approvals, messages, memory and
local traces are lost when the service restarts, redeploys or spins down. This
free demo does not satisfy restart-durable approvals or continuously live
deployment requirements. Persistent storage needs a separate storage integration
or a paid service with a disk.
[Free service limitations](https://render.com/docs/free),
[Persistent disk documentation](https://render.com/docs/disks),
[Docker deployment](https://render.com/docs/docker),
[Blueprint specification](https://render.com/docs/blueprint-spec).

The Blueprint defaults to lexical/template mode so it does not silently depend
on an inaccessible laptop. To deploy the open-model profile, configure a
reachable Ollama/open-model endpoint, a model actually installed there, and the
neural backend dependencies. `localhost:11434` on Render refers to the container,
not your Windows laptop. This part is not yet a verified hosted open profile.

## Docker locally

Set a private `GIGBID_API_TOKEN` in your shell, then run:

```bash
docker compose -f infra/docker-compose.yml up --build
```

Open port 5173. The Nginx service proxies `/api/` to the private API container.
The API has a health check and both services have restart policies. Docker was
unavailable in the working environment, so the container build itself still
needs verification. The full prescribed worker/Postgres/Redis/model stack is
not represented as completed by this two-service demo.

## Portfolio MCP HTTP

Set a separate private `GIGBID_MCP_BEARER`; configure the deployment hostname
in `GIGBID_MCP_ALLOWED_HOSTS` and permitted browser origins in
`GIGBID_MCP_ALLOWED_ORIGINS`. Start `uvicorn mcp_servers.http:app` on a
TLS-terminated host. Follow `mcp_servers/portfolio/README.md`. The standard
source/Docker stdio installation does not require hosting an HTTP endpoint.

## Tracing

`X-Trace-ID` correlates API requests with redacted local MCP call records in
`GIGBID_DATA_DIR/traces.jsonl` and marketplace audit rows. This local record is
not a public trace from a hosted tracing product. LangGraph can use configured
LangSmith tracing via its standard environment variables; authorise a real
account, verify traces, review redaction and then publish the required links.
Model/provider credentials must never enter these logs or public artifacts.


## MCP performance fix

The default `GIGBID_MCP_PERSISTENT=1` reuses an official ClientSession for
each server instead of starting a subprocess for every call. Separate owner
tasks keep each session's context lifetime valid. Timeouts do not replay writes.
Trace IDs use per-call MCP metadata instead of a process-level cached value.
Set the variable to `0` only to reproduce the fresh-session benchmark.
The free deployment limits BLAS threads to avoid oversubscribing its CPU.

Cold tool startup remains visible on the first analysis after a deploy or
spin-down. Repeat actions reuse warm sessions. Do not compare the local
benchmark numbers directly with hosted HTTP measurements.
