"""Export the actual FastAPI OpenAPI contract for TypeScript generation."""
import json
from pathlib import Path
from apps.api.main import app


if __name__=='__main__':
    target=Path('apps/web/src/lib/api/openapi.json')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(app.openapi(),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(f'Exported {len(app.openapi()["paths"])} API paths to {target}')
