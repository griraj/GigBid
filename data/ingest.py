"""Import authorized local CSV exports; never scrape marketplaces.

Usage: python -m data.ingest --input /path/to/jobs.csv --source kaggle-dataset-slug
The original CSV remains untouched. The job export is NOT portfolio proof.
"""
from __future__ import annotations
import argparse,csv,hashlib,html,json,re
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SYNONYMS={
    'title':['title','job_title','job title','name'],
    'description':['description','job_description','job description','body','job_text'],
    'skills':['skills','required_skills','skill','tags','expertise'],
    'min_budget':['min_budget','budget_min','budget_from','min hourly rate','hourly_low'],
    'max_budget':['max_budget','budget_max','budget_to','max hourly rate','hourly_high','budget','price'],
    'id':['id','job_id','job id','url','job_url'],
    'category':['category','job_category','industry','subcategory'],
    'client_id':['client_id','client id','client'],
}

def clean_text(value:object,max_len=6000)->str:
    text=html.unescape(str(value or ''))
    text=re.sub(r'<[^>]+>',' ',text)
    return re.sub(r'\s+',' ',text).strip()[:max_len]

def value(row:dict,key:str)->str:
    lookup={k.lower().strip():v for k,v in row.items() if k}
    for alias in SYNONYMS[key]:
        if alias in lookup and lookup[alias] is not None:return clean_text(lookup[alias])
    return ''

def money(text:str)->float:
    match=re.search(r'\d[\d,]*(?:\.\d+)?',text or '')
    return float(match.group().replace(',','')) if match else 0.0

def skills(text:str)->list[str]:
    text=text.strip('[]')
    values=re.split(r'[,;|]',text)
    return list(dict.fromkeys(s.lower() for raw in values if (s:=clean_text(raw.strip(' \"\''))) and s.lower() not in ('none','nan')))[:20]

def normalize(row:dict,source:str)->dict|None:
    title=value(row,'title');description=value(row,'description')
    if not title or len(description)<30:return None
    external_id=value(row,'id')
    fingerprint=hashlib.sha256((title.lower()+'\n'+description.lower()[:1200]).encode()).hexdigest()
    maximum=money(value(row,'max_budget'));minimum=money(value(row,'min_budget'))
    if maximum and minimum>maximum:minimum,maximum=maximum,minimum
    if not minimum:minimum=maximum
    if not maximum:maximum=minimum
    return {'id':'ext-'+fingerprint[:16],'title':title[:240],'description':description,
        'skills':skills(value(row,'skills')),'min_budget':minimum,'max_budget':maximum,
        'connects':0,'client_id':'external-unverified','category':value(row,'category') or 'Uncategorized',
        'provenance':{'kind':'real_export','dataset':source,'external_id':external_id,
                      'imported_at':datetime.now(timezone.utc).isoformat(),
                      'original_license':'VERIFY_SOURCE_TERMS'},'fingerprint':fingerprint}

def ingest_csv(input_path:Path,source:str,output_path:Path,limit:int=100000)->dict:
    if not input_path.is_file():raise FileNotFoundError(input_path)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    rows={};total=0;discarded=0
    with input_path.open(encoding='utf-8-sig',newline='',errors='replace') as inp:
        reader=csv.DictReader(inp)
        for row in reader:
            total+=1
            doc=normalize(row,source)
            if not doc:discarded+=1;continue
            rows.setdefault(doc['fingerprint'],doc)
            if total>=limit:break
    # Atomic replacement avoids a partially visible index on interruption.
    temp=output_path.with_suffix(output_path.suffix+'.tmp')
    with temp.open('w',encoding='utf-8') as out:
        for doc in rows.values():out.write(json.dumps(doc,ensure_ascii=False)+'\n')
    temp.replace(output_path)
    return {'source':source,'input_rows':total,'unique_jobs':len(rows),'invalid_rows':discarded,
            'duplicate_rows':total-discarded-len(rows),'path':str(output_path)}

def merge_exports(exports:list[tuple[Path,str]],output_path:Path,limit_per_file:int=100000)->dict:
    """Merge multiple licensed exports by content hash, recording every source."""
    merged={};count=0;invalid=0
    for path,source in exports:
        if not path.is_file():raise FileNotFoundError(path)
        with path.open(encoding='utf-8-sig',newline='',errors='replace') as stream:
            for offset,row in enumerate(csv.DictReader(stream)):
                if offset>=limit_per_file:break
                count+=1;doc=normalize(row,source)
                if doc is None:invalid+=1;continue
                key=doc['fingerprint']
                if key not in merged:
                    doc['provenance']['sources']=[source]
                    merged[key]=doc
                elif source not in merged[key]['provenance']['sources']:
                    merged[key]['provenance']['sources'].append(source)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    temp=output_path.with_suffix(output_path.suffix+'.tmp')
    with temp.open('w',encoding='utf-8') as output:
        for doc in merged.values():output.write(json.dumps(doc,ensure_ascii=False)+'\n')
    temp.replace(output_path)
    return {'sources':[source for _,source in exports],'input_rows':count,
            'unique_jobs':len(merged),'invalid_rows':invalid,'duplicate_rows':count-invalid-len(merged),
            'path':str(output_path)}

def load_jobs(path:Path|None=None)->list[dict]:
    path=path or ROOT/'processed/jobs.jsonl'
    if not path.exists():return []
    with path.open(encoding='utf-8') as stream:return [json.loads(line) for line in stream if line.strip()]

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,action='append',required=True)
    parser.add_argument('--source',action='append',required=True,help='Exact dataset slug or export attribution; repeat for each input')
    parser.add_argument('--output',type=Path,default=ROOT/'processed/jobs.jsonl')
    parser.add_argument('--limit',type=int,default=100000)
    args=parser.parse_args()
    if len(args.input)!=len(args.source):parser.error('Every --input requires one matching --source')
    print(json.dumps(merge_exports(list(zip(args.input,args.source)),args.output,args.limit),indent=2))
