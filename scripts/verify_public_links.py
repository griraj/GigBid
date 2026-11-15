"""Verify submission landing pages without cookies or reviewer credentials."""
import json,time
from datetime import datetime,timezone
from pathlib import Path
import httpx

if __name__=='__main__':
    with httpx.Client(timeout=120,follow_redirects=True) as client:
        repository=client.get('https://api.github.com/repos/griraj/GigBid')
        repository.raise_for_status()
        attempts=[]
        for attempt in range(3):
            website=client.get('https://gigbid-ti71.onrender.com/')
            attempts.append(website.status_code)
            if website.status_code==200:break
            if attempt<2:time.sleep(2)
        health=client.get('https://gigbid-ti71.onrender.com/api/health')
        health.raise_for_status()
        writeup=client.get('https://gigbid-ti71.onrender.com/writeup')
        portfolio=client.get('https://api.github.com/repos/griraj/GigBid/contents/mcp_servers/portfolio/README.md')
        result={'checked_at':datetime.now(timezone.utc).isoformat(),
            'repository':{'url':'https://github.com/griraj/GigBid','public':not repository.json()['private']},
            'application':{'url':'https://gigbid-ti71.onrender.com/','landing_status':website.status_code,'landing_attempts':attempts,'health':health.json()},
            'technical_writeup':{'url':'https://gigbid-ti71.onrender.com/writeup','status':writeup.status_code,
                'article_present':'<h1>Perfect retrieval' in writeup.text},
            'portfolio_mcp':{'url':'https://github.com/griraj/GigBid/tree/main/mcp_servers/portfolio',
                'readme_status':portfolio.status_code,'distribution':'Public source and documented Docker installation, not PyPI'},
            'method':'Unauthenticated HTTP; no private reviewer credential stored'}
    Path('evals/results/public_links.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
