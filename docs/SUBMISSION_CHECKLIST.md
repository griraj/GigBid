# Final submission and recording checklist

## Prepared and verified

- Public app: https://gigbid-ti71.onrender.com/
- Public repository: https://github.com/griraj/GigBid
- Published article: https://gigbid-ti71.onrender.com/writeup
- Portfolio MCP source/Docker installation: https://github.com/griraj/GigBid/tree/main/mcp_servers/portfolio
- Actual authenticated hosted before/after performance checks, public-link checks,
  Python tests and browser workflow tests are recorded in evals/results/.
- The current report is docs/GigBid_RnD_Report.pdf. The source is in this folder;
  the browser test report is docs/test-reports/playwright/index.html.
- START_HERE.md gives extraction instructions and a three-minute recording plan.

## Your remaining submission steps

1. Record your own final three-minute demonstration using START_HERE.md. Sign in
   before recording and keep the private reviewer token out of the video.
2. Upload the recording and verify that the instructor can open it while signed
   out. Replace the null demo URL in submission.json with that real link.
3. Review the report's measured findings and explicitly stated limitations.
4. Submit the PDF and verified app, repository, demo, MCP and article links
   together. Attach the ZIP if requested.
5. Put the reviewer login token directly in a private GCR comment, never in the
   repository, ZIP, public document, recording or public issue.
6. Confirm the applicable deadline with the instructor. The supplied original
   deadline was 12 November 2026 at 11:59 PM PKT; an extension is unconfirmed.

## Limits that must remain explicit

Render Free sleeps when idle and resets SQLite data on restart, redeploy or
spin-down. Refresh recovery within a running instance is verified; hosted
restart durability is not supplied by this free storage configuration.

The operational instructor GigSim, full labelled dev/persona corpora and real
2 November policy update were absent from the starter archive. Existing files
are illustrative examples, not a verified running service. Do not invent its
API responses, reply/hire rates or hidden-test results.

Full multi-user tenancy, encrypted OAuth, Redis scheduling/worker infrastructure,
Postgres Store memory, all required independent studies and hosted tracing
remain documented in docs/COMPLETION_STATUS.md. A demo-ready folder is not a
claim that these rubric requirements have been completed.

The included earlier scripted recording is a reference. Record the current
application yourself and upload that final video.
