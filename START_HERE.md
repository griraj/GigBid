# GigBid: start here and record your demo

## Public links

- App: https://gigbid-ti71.onrender.com/
- Repository: https://github.com/griraj/GigBid
- Technical write-up: https://gigbid-ti71.onrender.com/writeup
- Portfolio MCP installation: https://github.com/griraj/GigBid/tree/main/mcp_servers/portfolio

Enter your reviewer token privately in the app. It is deliberately absent from
this submission folder. Keep it out of the recording and use only the private Classroom
comment to share it with the instructor.

## Add your narration to the new demo

The new `docs/demo/GigBid_Silent_Demo.mp4` is a real three-minute browser
capture of the local application and backend using synthetic marketplace data.
Read `docs/demo/GigBid_Narration_Script.md` while watching it, then supply your
audio for synchronization. The video intentionally has no audio yet.
Its source recording and measured scene timeline are in `docs/demo/`.

## Record another take if needed

1. Open the app, sign in before recording, and allow any Render cold start to
   finish. Use the AI persona from Settings.
2. **0:00-0:20:** introduce the app and identify the marketplace records as synthetic.
3. **0:20-1:15:** Job inbox -> churn prediction job -> inspect evidence and price
   -> edit the draft -> approve -> show submitted status.
4. **1:15-1:45:** show the unpaid sample and banking verification jobs being
   skipped; point to scam and injected-instruction flags.
5. **1:45-2:20:** Messages -> enter an interview request -> show calendar slots
   -> approve the reply. Demonstrate a $15/hour offer and the rate-floor response
   if time allows; a proposed counteroffer is not an achieved client outcome.
6. **2:20-2:45:** open a new pending draft, refresh, then reopen it in Pipeline.
   Refresh recovery works while the free instance stays running; it does not
   survive Render restarting or spinning down.
7. **2:45-3:00:** show the results files or technical article and the public repo.
   Mention the measured MCP startup fix and the limited synthetic evaluation.

Use OBS, Windows screen recording, or another recorder. Upload the resulting
video, check access while signed out, and add that URL to your final submission.
`docs/demo/GigBid_Reference_Demo.webm` is an earlier scripted reference recording;
the newly captured, narration-ready file is `docs/demo/GigBid_Silent_Demo.mp4`.

## Run this project locally

Requirements: Python 3.11+ (deployment targets 3.12), Node 20+.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test,neural-lite]" langgraph-checkpoint-sqlite
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd apps/web
npm.cmd ci
npm.cmd run dev
```

Open http://localhost:5173 and use the local-only `demo-reviewer-token`.
This development token does not grant access to the public deployment.
The default synthetic template/lexical demo runs without downloading models.
See README.md for real Ollama generation/embeddings and evaluation instructions.

## Submission files in this folder

- `docs/GigBid_RnD_Report.pdf`: current ten-page R&D report.
- `docs/TECHNICAL_WRITEUP.md`: source of the published technical article.
- `docs/SUBMISSION_CHECKLIST.md`: the final links and upload checklist.
- `docs/test-reports/playwright/index.html`: readable browser test report.
- `evals/results/`: recorded test, retrieval, model and performance evidence.
- `docs/demo/GigBid_Reference_Demo.webm`: earlier scripted reference video.
- `docs/demo/GigBid_Silent_Demo.mp4`: new capture, waiting for your narration.
- `docs/demo/GigBid_Narration_Script.md`: easy spoken script with scene times.
- `submission.json`: verified public links and the pending final demo URL.

Runnable source, configuration and tests stay in their existing assignment
folders. Git history is preserved. Development dependencies and runtime
outputs are ignored by Git; the recorder uses `tmp/`. No ZIP is generated.
Use the commands above to restore dependencies when setting up a fresh copy.

The actual GigSim service/dev labels, policy update, external OAuth authorizations
and independent outcome studies are unavailable. Additional production gaps are
listed in `docs/COMPLETION_STATUS.md`; this demo is not represented as full
rubric compliance. Do not invent the missing measurements.
