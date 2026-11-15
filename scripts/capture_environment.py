"""Record versions for reproducibility without credentials or machine usernames."""
import importlib.metadata
import json
import platform
from pathlib import Path
from datetime import datetime,timezone


if __name__=='__main__':
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
        'platform':platform.system(),'packages':{d.metadata['Name']:d.version for d in importlib.metadata.distributions() if d.metadata['Name']}}
    path=Path('evals/results/environment.json')
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('Recorded Python '+result['python']+' environment in '+str(path))
