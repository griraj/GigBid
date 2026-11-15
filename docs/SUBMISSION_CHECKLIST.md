# Single-submission checklist

The original specification deadline is 12 November 2026, 11:59 PM PKT. The
latest clarification says an extension is not confirmed. Confirm the applicable
deadline directly with the instructor; do not backdate commits.

## Prepared locally

- R&D PDF builder: `python scripts/build_report.py`; generated file under `output/pdf/`.
- Source ZIP builder: `python scripts/package_submission.py`; archive and checksum under `output/submission/`.
- Publication draft: `docs/TECHNICAL_WRITEUP.md` (verify the final word count).
- Actual-screen recording plan: `docs/DEMO_SCRIPT.md`.
- Installable Portfolio MCP instructions: `mcp_servers/portfolio/README.md`.
- Render single-container blueprint, persistent paths and private token requirement.
- Synthetic retrieval/system experiments and before/after safety probes.
- Python, MCP contract and Playwright test definitions and local reports.

## Must be completed and verified before submission

- Deploy the complete backend/frontend, set a private reviewer token and confirm
  persistence through a restart. Keep the service live until grades are released.
- Push the reviewed final source to the public repository and verify it while
  signed out. The configured remote is `https://github.com/griraj/GigBid`;
  current public accessibility and inclusion of local edits are not assumed.
- Record and upload the three-minute actual application demo; verify access.
- Publish the article to your selected platform and record its public URL.
- Verify that the public repository's Portfolio MCP Docker/source instructions
  install from a clean checkout, or publish a package separately.
- Obtain instructor resources and run the missing studies. Keep unperformed
  measurements marked unavailable in the report.
- Confirm the final report is at most ten pages and review its limitations.
- Attach the PDF, all required verified links, and the ZIP if requested, together.

## Private Classroom comment

Enter the real deployment login details directly in the private GCR comment.
Do not put credentials into this document, the manifest, the ZIP, a video, the
public repository or a public issue. For the current single-reviewer token UI,
describe it as a reviewer access token rather than inventing an email/password.

## Missing instructor evidence

The executable GigSim, verified contract/credentials, full labelled persona/dev
corpora and real 2 November policy update were not provided. The starter's
localhost URL and token are placeholders. Do not infer reply/hire rates from
local submissions. The 40-task tool study, 50-job orchestration comparison,
judge calibration, blind panel and hidden-test results remain outstanding.
