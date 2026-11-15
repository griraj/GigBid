from pathlib import Path
from data.ingest import normalize,merge_exports,load_jobs
from rag.ingest_portfolio import chunk,ingest_directory,load_portfolio

def test_normalize_rejects_empty_and_sanitizes():
    assert normalize({'title':'Bad','description':'short'},'mock') is None
    item=normalize({'Job Title':'Build model','Description':'<div>Need accurate sklearn reporting and Python data pipelines</div>',
                    'Skills':'Python, SQL, python','Budget':'$1,250'},'mock')
    assert item['max_budget']==1250
    assert item['skills']==['python','sql']
    assert '<div>' not in item['description']
    assert item['provenance']['kind']=='real_export'

def test_dedup_and_provenance(tmp_path):
    row='title,description,skills,budget\nBuild report,Please build a dashboard with SQL and good documentation,"SQL,Python",400\n'
    a=tmp_path/'a.csv';b=tmp_path/'b.csv'
    a.write_text(row);b.write_text(row)
    output=tmp_path/'jobs.jsonl'
    result=merge_exports([(a,'source-a'),(b,'source-b')],output)
    assert result['unique_jobs']==1
    assert result['duplicate_rows']==1
    assert load_jobs(output)[0]['provenance']['sources']==['source-a','source-b']

def test_portfolio_chunks_and_source(tmp_path):
    source=tmp_path/'portfolio';source.mkdir()
    (source/'case.md').write_text('Completed a reproducible model with verified CSV data and analysis. '*20)
    output=tmp_path/'portfolio.jsonl'
    result=ingest_directory(source,'ai',output)
    assert result['chunks']>=1
    item=load_portfolio(output)[0]
    assert item['outcome']=='unverified'
    assert item['source']=='user-upload: case.md'
