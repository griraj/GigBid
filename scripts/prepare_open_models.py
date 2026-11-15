"""Download explicitly named public models through the user's running Ollama."""
import argparse
import json
import os
import httpx


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--models',nargs='+',default=['qwen2.5:0.5b','qwen3:0.6b','nomic-embed-text'])
    args=parser.parse_args()
    endpoint=os.getenv('GIGBID_OLLAMA_URL','http://localhost:11434').rstrip('/')
    for model in args.models:
        print('Pulling '+model,flush=True)
        last=''
        with httpx.stream('POST',endpoint+'/api/pull',json={'model':model,'stream':True},timeout=900) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                record=json.loads(line)
                if record.get('error'):raise RuntimeError(record['error'])
                percent=int(100*record.get('completed',0)/max(1,record.get('total',1)))//20*20
                status=record.get('status','')+' '+str(percent)+'%'
                if status!=last:
                    print(status,flush=True);last=status
