"""User-provided portfolio documents -> attributable evidence JSONL.

Documents are only evidence of their *contents*, not independently verified
employment achievements. The UI must never elevate them into verified claims.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path

SUPPORTED={'.md','.txt','.pdf'}

def extract(path:Path)->str:
    if path.suffix.lower()=='.pdf':
        from pypdf import PdfReader
        return '\n'.join(page.extract_text() or '' for page in PdfReader(str(path)).pages)
    return path.read_text(encoding='utf-8',errors='replace')

def chunk(text:str,max_words=170,overlap=25)->list[str]:
    words=re.sub(r'\s+',' ',text).strip().split(' ')
    if words==['']:return []
    stride=max_words-overlap
    return [' '.join(words[i:i+max_words]) for i in range(0,len(words),stride) if len(words[i:i+max_words])>=12]

def ingest_directory(directory:Path,persona:str,output:Path)->dict:
    if persona not in ('ai','web','analytics'):raise ValueError('Unknown persona')
    if not directory.is_dir():raise NotADirectoryError(directory)
    docs=[];count=0
    for path in sorted(directory.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED:continue
        count+=1
        content=extract(path)
        for position,part in enumerate(chunk(content)):
            identifier=hashlib.sha256((persona+str(path.resolve())+str(position)).encode()).hexdigest()[:20]
            docs.append({'id':'portfolio-'+identifier,'persona':persona,'type':'portfolio_document',
                'title':path.stem,'text':part,'skills':[], 'project':path.stem,
                'source':'user-upload: '+path.name,'date':datetime.now(timezone.utc).date().isoformat(),
                'outcome':'unverified','provenance':{'kind':'user_uploaded','file':path.name,'chunk':position}})
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=output.with_suffix(output.suffix+'.tmp')
    with temp.open('w',encoding='utf-8') as stream:
        for doc in docs:stream.write(json.dumps(doc,ensure_ascii=False)+'\n')
    temp.replace(output)
    return {'documents':count,'chunks':len(docs),'persona':persona,'output':str(output)}

def load_portfolio(path:Path|None=None)->list[dict]:
    path=path or Path(__file__).resolve().parents[1]/'data/processed/portfolio.jsonl'
    if not path.exists():return []
    with path.open(encoding='utf-8') as stream:return [json.loads(line) for line in stream if line.strip()]

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--persona',required=True,choices=['ai','web','analytics'])
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data/processed/portfolio.jsonl')
    args=parser.parse_args()
    print(json.dumps(ingest_directory(args.directory,args.persona,args.output),indent=2))
