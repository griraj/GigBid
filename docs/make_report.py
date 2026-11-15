"""Render an honest development-stage engineering review (not a fabricated final R&D report)."""
import json
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch

root=Path(__file__).resolve().parents[1]
results=json.loads((root/'evals/results/synthetic_retrieval.json').read_text())
output=root/'docs/GigBid_Engineering_Review.pdf'
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleGig',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=22,leading=28,textColor=colors.HexColor('#252059'),spaceAfter=14))
styles.add(ParagraphStyle(name='BodyGig',parent=styles['BodyText'],fontSize=9.5,leading=15,spaceAfter=10))
styles.add(ParagraphStyle(name='HeadingGig',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=12.5,leading=17,textColor=colors.HexColor('#5646c0'),spaceBefore=14,spaceAfter=8))
story=[]
def p(s):story.append(Paragraph(s,styles['BodyGig']))
def h(s):story.append(Paragraph(s,styles['HeadingGig']))
story.append(Paragraph('GigBid: Engineering Design Review',styles['TitleGig']))
p('AI-4016 Assignment II | Development-stage report | 14 November 2026')
p('<b>Evidence statement.</b> This document describes code executed in the provided environment, not a completed 100-mark submission. The supplied archive lacked the operational GigSim service and gold development corpus. We did not fabricate outcomes, comparisons, third-party access, latency budgets, or deployment evidence.')
h('1. Problem and constraints')
p('Freelancers need to filter risky jobs, compare each requirement with defensible portfolio evidence, avoid wasting Connects, and communicate without accidental or prohibited sends. The present implementation defaults to a local synthetic marketplace so every action is inspectable. Human approval is mandatory before proposals and messages. The system has no authorized real Upwork connection.')
h('2. Original system architecture')
p('The React/TypeScript console calls a FastAPI API. A handwritten LangGraph bid graph fans out a structured Job Analyst, Risk Assessor and Fit Matcher in parallel; the merged decision routes to skip/watch or to pricing, writing, conservative citation verification, bounded critique, compliance and an interrupt-based human gate. A second LangGraph graph classifies client messages and pauses before reply. SQLite local marketplace writes use unique idempotency keys, an audit table and a dry-run preview. Three separate official MCP Python SDK servers expose portfolio, marketplace and workspace tools, although current graph nodes use the Python marketplace port directly; this is a known compliance gap.')
h('3. Synthetic data and retrieval methodology')
p('Original fixtures contain 8 jobs, 3 client histories, 6 evidence items, 3 personas and miniature relevance labels. Each item states its synthetic source. No Kaggle dataset was ingested; its license and field definitions were not verified. The retrieval experiment executes V0 TF-IDF similarity; V1 independent requirement queries; V2 BM25 and TF-IDF reciprocal-rank fusion; V3 lexical overlap reordering; V4 outcome-weighted reordering; and V8 a limited fallback query. These are CPU lexical retrieval configurations, <b>not genuine neural dense embeddings, a cross-encoder or a LangGraph self-RAG loop.</b>')
h('4. Actual experiment')
rows=[['Variant','Recall@5','MRR','nDCG@10','p95 (ms)']]
for key,r in results['variants'].items():rows.append([key,f"{r['recall_at_5']:.3f}",f"{r['mrr']:.3f}",f"{r['ndcg_at_10']:.3f}",f"{r['latency_p95_ms']:.3f}"])
t=Table(rows,colWidths=[95,95,75,85,90]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9e5ff')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#34296d')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f8fc')]),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#cec7ec'))]))
story.append(t)
p('Measured by evals/runners/compare_retrieval.py and recorded in evals/results/synthetic_retrieval.json. Only 5 of the 8 jobs have positive relevance labels, making Recall@5 saturate. V4 fell from MRR 1.0 to 0.9 and nDCG@10 1.0 to 0.9262. These values are neither statistically significant nor transferable to real postings. p95 figures are retrieval-function wall time, not full proposal or model latency.')
h('5. Guardrails and tests')
p('Proposal writer templates cite stable item IDs, and the verifier drops uncited experience assertions before criticism. An approval edit is rechecked before submission. Risk screening detects free work, off-platform solicitations and some prompt injection strings; a safer implementation would require adversarial testing and untrusted-data delimiting throughout every model prompt. Nine Python tests passed at the time of review, covering persona-scoped retrieval, grounding, proposal approval, idempotency, rejection, job injection and conversation approval. These tests do not replace the prescribed Playwright scenarios.')
h('6. Honest limitations and next research')
p('No open LLM has yet been invoked; no Kaggle data has been merged; there is no production vector DB, Redis worker, Postgres checkpoint, third-party MCP authorization, OAuth, real user account isolation, calibrated LLM judge, 40-task tool study, 50-job graph comparison, blind proposal panel, or GigSim reply/hire rate. The UI is responsive but its SSE endpoint emits completed state events, not live streamed graph execution. The external GigSim adapter is awaiting the instructor service contract. No live URL, public trace, demo video or published MCP package has been created.')
h('7. Next steps and conclusion')
p('Obtain real simulator credentials and labelled development records; implement agents calling scoped MCP tools, persistent Postgres/Redis infrastructure, genuine open embeddings and a cross-encoder; run calibrated and reproducible experiments; implement real multi-user approval, streaming and end-to-end browser tests; then publish the system and report its measured outcomes. The present build demonstrates a useful safety-oriented integrated foundation, not a completed academic evaluation.')
h('References and reproducibility')
p('Primary specification: AI-4016 R&amp;D Assignment II, GigBid, FAST-NUCES, issued 27 October 2026. Software: LangGraph (langchain-ai.github.io/langgraph), Model Context Protocol Python SDK (github.com/modelcontextprotocol/python-sdk), FastAPI (fastapi.tiangolo.com), scikit-learn (scikit-learn.org). Reproduce reported results using <font face="Courier">make test</font> and <font face="Courier">make eval</font>. See docs/DATA_CARD.md and docs/REQUIREMENTS_AND_GAPS.md.')

def footer(canvas,doc):
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#8b91a5'))
    canvas.drawString(45,32,'GIGBID  /  DEVELOPMENT REVIEW  /  SYNTHETIC DATA')
    canvas.drawRightString(550,32,f'{doc.page}')

SimpleDocTemplate(str(output),pagesize=(595.28,841.89),rightMargin=45,leftMargin=45,topMargin=47,bottomMargin=56,title='GigBid Engineering Review').build(story,onFirstPage=footer,onLaterPages=footer)
print(output)
