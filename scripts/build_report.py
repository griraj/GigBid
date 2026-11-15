"""Generate an evidence-backed engineering review; missing studies stay explicit."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing,String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderSVG

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'evals/results'


def build():
    retrieval=json.loads((RESULTS/'synthetic_retrieval.json').read_text())
    system=json.loads((RESULTS/'synthetic_system.json').read_text())
    before=json.loads((RESULTS/'synthetic_system_before.json').read_text())
    vectors=json.loads((RESULTS/'ollama_retrieval.json').read_text())
    models=json.loads((RESULTS/'open_model_comparison.json').read_text())
    output=ROOT/'output/pdf/GigBid_RnD_Report.pdf'
    output.parent.mkdir(parents=True,exist_ok=True)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyGig',fontName='Helvetica',fontSize=10,leading=15,spaceAfter=10))
    styles.add(ParagraphStyle(name='HeadingGig',fontName='Helvetica-Bold',fontSize=18,leading=23,spaceAfter=16,textColor=colors.HexColor('#223149')))
    story=[]
    def p(text):story.append(Paragraph(text,styles['BodyGig']))
    def page(title):
        if story:story.append(PageBreak())
        story.append(Paragraph(title,styles['HeadingGig']))
    def table(rows,widths):
        cells=[[Paragraph(escape(str(cell)),styles['BodyGig']) for cell in row] for row in rows]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0f5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#8b98a8'))]))
        story.append(t);story.append(Spacer(1,12))

    page('GigBid | Engineering Design Review')
    p('AI-4016 Assignment II | 15 November 2026 | Development evidence edition')
    p('<b>Scope.</b> This report records the implemented system and experiments actually executed. It is not evidence of full assignment compliance. The instructor GigSim executable, verified contract, gold development corpus, hidden test and 2 November policy update were unavailable. Public deployment, publication and live OAuth are not claimed.')
    p('<b>Problem.</b> Freelancers need to identify relevant opportunities, avoid risky requests, ground proposals in demonstrated work, and control every submission. The approval boundary is a product requirement: proposals, messages and Connects spending require a human decision through LangGraph interrupts.')
    p('<b>Working implementation.</b> React/TypeScript connects to FastAPI; two handwritten LangGraph workflows use typed handoffs. The bid workflow runs analysis branches in parallel. Three official-SDK MCP servers expose portfolio, marketplace and workspace capabilities. Local marketplace writes use deterministic idempotency keys and an audit table. The default demo uses lexical retrieval and a template writer; separate actual Ollama writer and embedding experiments are included below.')
    p('<b>Data.</b> The available corpus has eight authored jobs, six evidence items and three personas. Only five jobs have nonempty positive evidence labels. All are synthetic. No Kaggle data or instructor labels are represented as used. Each experiment cites JSON under evals/results/.')
    p('<b>Declared development targets.</b> Proposed acceptance targets are p95 below 120 seconds for model-backed analysis, zero unapproved sends, and no paid API calls in the local profile. These are targets, not verified production service levels. Model-backed and hidden-test latency remain unmeasured.')

    page('1 | Architecture and state discipline')
    p('<b>Bid graph.</b> Start -&gt; parallel Analyst / Risk / Fit -&gt; Decision -&gt; Pricing -&gt; Writer -&gt; Critic -&gt; Compliance -&gt; Approval interrupt -&gt; Submit. Skip and watch terminate early. Critique revisions are bounded by configuration. Approval edits are rechecked before writing. A configured hard-block flag prevents known injected or prohibited job content from proceeding to drafting.')
    p('<b>Conversation graph.</b> Liaison classifies incoming text, blocks recognised scams, prepares a reply, and interrupts before sending. Negotiation requests use a draft-only subgraph that parses an hourly offer, checks the configured floor and proposes a counteroffer or walk-away response. No negotiated outcome is inferred from a draft.')
    p('<b>Why roles exist.</b> Analyst supplies structured requirements; Risk evaluates client history and untrusted text; Fit maps requirements to evidence; Pricing proposes a budget midpoint; Writer creates a cited draft; Critic checks basic completeness; Compliance gates content; Liaison handles client communication. The current pricing rule is not an empirically fitted market estimator.')
    p('<b>Stores.</b> Job state lives in LangGraph checkpoints, a separate durable SQLite run index makes approvals discoverable after refresh, and SQLite memory promotes repeated approved edit signals or verified outcomes. A configured PostgresSaver path exists, but Postgres Store memory and multi-tenant identity isolation are unfinished. Raw tool output is not promoted into memory.')
    p('<b>Transport and UI.</b> Agent-scoped MCP allowlists separate reads and writes. Portfolio tools run over stdio or authenticated Streamable HTTP. The UI consumes live graph update events from a new streaming endpoint, shows completed nodes and resumes saved runs from Pipeline. Local JSON and SQLite evidence must not be confused with published tracing-service links.')

    page('2 | R&D A: tool design and MCP verification')
    p('<b>Hypothesis, not yet tested:</b> role-scoped tools with concrete parameter descriptions will reduce wrong-tool selection compared with one unrestricted tool collection. The assignment requires a 40-task comparison of fine tools, coarse tools and rewritten descriptions, including argument accuracy and tokens per task.')
    p('<b>Implemented surface.</b> Portfolio exposes evidence search, case study lookup, skill listing, resource templates and a screening-answer prompt. Marketplace exposes five reads and three constrained writes; write tools default to dry-run and require idempotency keys. Workspace exposes mock calendar availability, tentative holds and unsent email drafts.')
    p('<b>Executed verification.</b> Contract tests check tool names, constraints and annotations; a real official MCP ClientSession reads client history over stdio. Additional HTTP tests exercise missing-token rejection, rate limiting and the real initialize exchange. These are protocol/engineering checks; they do not establish an LLM tool-selection score.')
    p('<b>HTTP deployment scope.</b> Portfolio HTTP refuses missing and known placeholder tokens, compares bearer tokens in constant time, enforces a configurable process-local limit and validates allowed hosts/origins. It represents one reviewer identity. Marketplace and Workspace HTTP endpoints, per-user distributed limits and OAuth are not completed by this wrapper.')
    p('<b>External integration.</b> GigSim remains configurable but its route mapping is provisional until the real contract is supplied. Live Upwork mode remains unavailable without official authorization. The additional GitHub MCP transport is configurable but has no verified authorised session. No Inspector screenshot, 40-task study or live OAuth success is claimed.')

    page('3 | R&D B: retrieval experiment')
    p('<b>Hypothesis recorded for future independent data:</b> decomposition and hybrid retrieval will improve evidence coverage on multi-requirement jobs. The present authored micro-corpus is a regression fixture and cannot provide an independent confirmation of that hypothesis.')
    rows=[['Variant','Recall@5','MRR','nDCG@10','p95 ms']]
    for name,metrics in retrieval['variants'].items():
        rows.append([name,f"{metrics['recall_at_5']:.3f}",f"{metrics['mrr']:.3f}",f"{metrics['ndcg_at_10']:.3f}",f"{metrics['latency_p95_ms']:.2f}"])
    table(rows,[74,88,75,90,168])
    drawing=Drawing(495,145)
    chart=VerticalBarChart();chart.x=38;chart.y=20;chart.width=435;chart.height=100
    chart.data=[[m['mrr'] for m in retrieval['variants'].values()],
                [m['ndcg_at_10'] for m in retrieval['variants'].values()]]
    chart.categoryAxis.categoryNames=list(retrieval['variants'])
    chart.valueAxis.valueMin=0;chart.valueAxis.valueMax=1;chart.valueAxis.valueStep=.25
    chart.bars[0].fillColor=colors.HexColor('#315f89');chart.bars[1].fillColor=colors.HexColor('#a3b3c4')
    drawing.add(chart);drawing.add(String(38,132,'MRR (dark) and nDCG@10 (light); synthetic fixture only',fontSize=8))
    story.append(drawing)
    image_dir=ROOT/'docs/images';image_dir.mkdir(parents=True,exist_ok=True)
    renderSVG.drawToFile(drawing,str(image_dir/'retrieval_results.svg'))
    p('Source: evals/results/synthetic_retrieval.json, generated by python -m evals.runners.compare_retrieval. Five positive queries; six evidence items. Precision@5 uses the number of returned items when fewer than five exist. Per-persona recall and F1@5 are stored in the result file.')
    p('<b>Interpretation.</b> Recall saturates in every configuration because each persona has very few eligible items. Outcome weighting (V4) lowers MRR and nDCG on this fixture. A won proposal can describe a different project; outcome is not evidence of relevance. The V8 cold-start timing is retained rather than removed. These are lexical comparisons, not measured dense or cross-encoder benchmarks.')
    p('<b>Shipped development choice.</b> V2 remains a configurable development default; this fixture does not show it is statistically better than V0. Optional SentenceTransformer, Chroma and cross-encoder paths need actual model execution and independent labels before a neural shipping decision. No judge score, human panel, ablation on gold data, reply rate or hire rate is available.')

    page('Model-backed checks | Real local execution')
    p('<b>Dense retrieval.</b> The alternative Ollama backend generated actual nomic-embed-text vectors, persisted them in SQLite and used sqlite-vec cosine distance. The same five positive synthetic queries were evaluated. V3 is excluded because no cross-encoder weights were installed. Source: evals/results/ollama_retrieval.json.')
    rows=[['Variant','Recall@5','nDCG@10','p95 ms']]
    for name,metrics in vectors['variants'].items():
        rows.append([name,f"{metrics['recall_at_5']:.3f}",f"{metrics['ndcg_at_10']:.3f}",f"{metrics['p95_latency_ms']:.2f}"])
    table(rows,[80,105,105,205])
    p('<b>Timing protocol.</b> Query cache is cleared before each variant in the final run; index creation is excluded. The earlier warm-cache run is preserved separately and is not used as a controlled algorithm-speed comparison. Model startup and cache behaviour materially affect latency. Perfect recall still reflects the tiny corpus and does not demonstrate generalisation.')
    rows=[['Writer','Jobs','p95 seconds','Generated tokens']]
    for name,metrics in models['models'].items():rows.append([name,metrics['samples'],metrics['p95_latency_s'],metrics['generated_tokens']])
    table(rows,[170,60,115,150])
    p('<b>Writer comparison.</b> Both open models ran on five authored jobs with a maximum of 180 output tokens per call. Raw and cleaned drafts, actual generation/prompt token counts and completion reasons are retained in open_model_comparison.json. Earlier capped smoke outputs are separate. Local paid API cost was zero; hardware and electricity were not estimated.')
    p('<b>Negative result.</b> The smaller writers frequently copied job/evidence text rather than producing a polished proposal; some outputs hit the token cap. Verifier rejections are heuristic observations, not calibrated unsupported-claim rates. Neither model is established as a quality winner. Larger-model evaluation, independent labels and a calibrated judge remain necessary.')

    page('4 | Claim verification and R&D C')
    failed_before=sum(not item['correct'] for item in before['claim_probes'])
    failed_after=sum(not item['correct'] for item in system['claim_probes'])
    p(f'<b>Executed claim probes.</b> {failed_before} of {len(before["claim_probes"])} authored probes failed the original citation/number gate. After adding a conservative content-overlap check and guarantee refusal, {failed_after} of {len(system["claim_probes"])} probes failed. Sources: synthetic_system_before.json and synthetic_system.json. These are hand-authored regression probes, not a calibrated unsupported-claim benchmark.')
    p('<b>Failure that changed the implementation.</b> A claim about building a lunar rover could borrow the valid churn-project citation [e1]. The new gate checks content overlap with the cited item and rejects unverified achievement claims. This is still lexical screening, not semantic entailment; paraphrases can be wrongly rejected and semantically false statements with similar vocabulary can pass.')
    d=system['decision'];r=system['scam']
    p(f'<b>Executed graph decisions.</b> On eight authored jobs, bid F1={d["f1"]:.3f}; scam precision={r["precision"]:.3f} and recall={r["recall"]:.3f}. Measured graph p50={system["latency_p50_ms"]:.2f} ms and p95={system["latency_p95_ms"]:.2f} ms. The run uses the direct local port and template writer to isolate decision logic; MCP startup, HTTP, hosted inference and model tokens are excluded. Source: synthetic_system.json.')
    p('<b>R&D C remains open.</b> The assignment comparison of ReAct, prebuilt supervisor and handwritten graph on 50 dev jobs has not been run. Perfect scores on eight authored examples do not establish the superiority of multi-agent orchestration. A valid comparison needs the same real job set, approved action policy and measured tokens/latencies for all three configurations.')
    p('<b>Durability.</b> SQLite checkpoint and run-index paths now share the persistent data directory across API and MCP processes. The Pipeline opens saved approvals after refresh. A hosted API kill/restart demonstration, worker recovery and Postgres-backed replay remain separate acceptance checks.')

    page('5 | Change request, extension and deployment')
    p('<b>Instructor policy change.</b> The 2 November update was not supplied. No invented update, implementation time or before/after grade is reported. Existing prohibitions are used for development. block_risk_flags is configuration so known injection and prohibited-job flags can become hard stops without changing graph wiring.')
    p('<b>Signature extension X5.</b> The negotiation subgraph drafts rate-floor responses from explicit hourly offers and requires the parent conversation approval before sending. Below-floor offers produce a minimum-rate counteroffer and a walk-away condition; missing offers trigger clarification. This implements a local coaching mechanism. GigSim achieved-rate versus offered-rate evaluation remains unavailable and no client acceptance is claimed.')
    p('<b>Deployment preparation.</b> The Compose demo uses an Nginx same-origin proxy, an API health check, a required private production token, a persistent data volume and restart policies. A separate multi-stage container serves the built frontend and API under one origin. render.yaml declares a persistent disk and generated reviewer token; it has not been deployed or verified on a hosting account.')
    p('<b>Production limitations.</b> This release is a single-reviewer deployment candidate. It does not complete multi-user auth, encrypted OAuth, a Redis worker, distributed rate limiting, full-stack Postgres/vector/model Compose services, end-to-end hosted tracing or a 30-job GigSim CI gate. Do not expose private client data or describe the token gate as full account management.')
    p('<b>Browser verification.</b> Playwright scenarios cover reviewer entry, approval, rejection with a reason, edited approval, a simulated outage banner and reopening approval after refresh. The executed report is retained under apps/web/playwright-report and evals/results/playwright.json when available. Verify the final recorded status before submission.')

    page('6 | Failure analysis: observed probes')
    p('These are ten executed adversarial development probes based on one synthetic job, not ten failed instructor dev jobs. The required ten-job failure taxonomy cannot be substituted with this list. Source: synthetic_system.json; the earlier behaviour is preserved in synthetic_system_before.json.')
    rows=[['Probe','Observed result / remaining issue']]
    for item in system['adversarial_probes']:
        observation=('Screening missed the request; approval boundary still held.' if item['screening_miss'] else 'Flagged; current graph status: '+item['status']+'.')
        rows.append([item['case'],observation])
    table(rows,[132,363])
    p('<b>Fix assessed.</b> Detected risky content now forces skip through a configured flag list. Four lexical screening misses remain. All probes retained the human send boundary, but the template writer does not execute arbitrary job instructions, so this is not a model-backed attack success-rate study.')

    page('7 | Safety, reproducibility and submission status')
    p('<b>Never automate.</b> No scraping, browser-cookie marketplace access, unapproved send, fabricated portfolio achievement or fabricated client outcome. Imported real job exports remain research-only in local mode. Approval edits pass verification again; deterministic write keys protect retries. Remaining risks include lexical verification errors, subtle injections, single-user identity and unverified external route mappings.')
    p('<b>Reproduce.</b> Install the project with test dependencies and langgraph-checkpoint-sqlite. Run python -m pytest; python -m evals.runners.compare_retrieval; python -m evals.runners.evaluate_system; python -m evals.runners.check_gates. Build the web app and run npm run test:e2e. scripts/package_submission.py creates an allowlisted source ZIP with file hashes and excludes databases, environments, dependencies and generated private runtime state.')
    p('<b>Required external evidence.</b> Real instructor dev evaluation and hidden test results; simulator reply/hire rates; the 40-task tool study; 50-job orchestration comparison; larger independent open-model comparison; calibrated judge and blind panel; the real policy update; public app, traces, demo and article; official third-party authorizations. Unknown values remain unavailable, never zero-filled.')
    p('<b>Submission.</b> Attach this PDF only after reviewing its limitations and replacing pending evidence where possible. Provide the verified live app URL, public repository URL, three-minute recording, installable Portfolio MCP and published article in one Classroom submission. Put reviewer credentials only in the private Classroom comment. Hosting must remain active until grades are released. The current deadline/extension needs confirmation with the instructor.')
    p('<b>References.</b> Primary source: supplied AI-4016 GigBid specification (16 PDF pages). Code evidence: agent/graphs/, agent/mcp_client.py, mcp_servers/, rag/, apps/api/, apps/web/. Experimental evidence: evals/results/synthetic_retrieval.json, synthetic_system_before.json and synthetic_system.json. Software primary references: github.com/modelcontextprotocol/python-sdk; docs.langchain.com/oss/python/langgraph/; fastapi.tiangolo.com; playwright.dev. Package versions are recorded in the environment lock file when regenerated.')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#536276'))
        canvas.drawString(48,29,'GigBid / development evidence / synthetic data')
        canvas.drawRightString(547,29,str(doc.page))
    SimpleDocTemplate(str(output),pagesize=(595.28,841.89),leftMargin=50,rightMargin=50,topMargin=48,bottomMargin=52,
        title='GigBid R&D Engineering Review').build(story,onFirstPage=footer,onLaterPages=footer)
    print(output)


if __name__=='__main__':build()
