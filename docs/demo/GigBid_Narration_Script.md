# GigBid narration for the silent demo

Record in a quiet room. Speak naturally while watching the video. The times
below identify the corresponding scenes; brief pauses between sentences are
fine. You can send one audio file or one file per section. Do not read the
headings or timestamps aloud. No background music is needed.

## 0:00–0:15 — Introduction

Hello, this is GigBid, my freelance bidding assistant. It checks jobs, finds
portfolio evidence, and prepares proposals and replies. This demo uses
synthetic jobs and clients. Every send needs human approval.

## 0:15–0:50 — Job analysis

I will open this churn prediction job. GigBid checks the job requirements,
client risk, and portfolio match. LangGraph runs the analysis steps, and MCP
tools provide the information.

Here, we can see the recommendation and risk score. This evidence map connects
the required skills to portfolio examples. GigBid also suggests a price and
shows the Connects cost.

## 0:50–1:15 — Review and approve

The proposal includes references to portfolio evidence. I can review and edit
it before approval. I will add a note about the delivery schedule.

After approval, the proposal is submitted to the local simulator. Idempotency
keys prevent duplicate submissions and repeated Connects charges.

## 1:15–1:45 — Safety checks

This job asks for unpaid work, a deposit, and off-platform contact. GigBid flags
these risks and recommends skipping it.

The next job contains an instruction pretending to be a system message.
GigBid treats job descriptions as untrusted content. This recognised injection
is flagged, and the job is skipped.

## 1:45–2:20 — Interview reply

Now I will simulate a client asking for an interview. The conversation workflow
prepares a reply and gets available interview slots through the Workspace MCP
server.

The reply waits for approval. I can review it before sending. Once I approve,
the local simulator records the message.

## 2:20–2:40 — Negotiation

GigBid also helps with negotiation. This offer is below the configured minimum
rate. The workflow suggests a counteroffer and a walk-away response. It remains
a draft until I approve it.

## 2:40–3:00 — Closing

The repository contains the code, tests, report, and measured evaluation
results. One finding was that outcome-based boosting reduced ranking quality
on our small synthetic dataset.

GigBid combines evidence-based drafting, risk checks, and human approval in one
application. Thank you.

## Recording and editing notes

The video shows the actual local application and backend using the synthetic
marketplace, followed by the public repository and published technical
write-up. It does not demonstrate official Upwork authorization or verified
instructor GigSim outcomes. Login credentials are excluded from the capture.

The original browser capture is `GigBid_Silent_Demo.webm`; the shareable export
is `GigBid_Silent_Demo.mp4`. `GigBid_Demo_Timeline.json` contains the measured
browser cue times; the export removes the initial 2.5 seconds of loading and trims the
redundant closing hold. Scene times above are approximate. The MP4 intentionally
has no audio stream. Keep your natural
speaking speed; we can adjust the picture cuts to your audio afterward.
