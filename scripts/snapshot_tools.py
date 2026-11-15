"""Reviewed MCP schema snapshot. Regenerate only for intentional contract changes."""
import json
from pathlib import Path


def schemas():
    from mcp_servers.marketplace.server import mcp as marketplace
    from mcp_servers.portfolio.server import mcp as portfolio
    from mcp_servers.workspace.server import mcp as workspace
    return {name:{tool.name:{'parameters':tool.parameters,'annotations':tool.annotations.model_dump(mode='json')}
        for tool in server._tool_manager.list_tools()} for name,server in
        [('marketplace',marketplace),('portfolio',portfolio),('workspace',workspace)]}


if __name__=='__main__':
    path=Path(__file__).resolve().parents[1]/'tests/contract/tool_schema_snapshot.json'
    path.write_text(json.dumps(schemas(),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('Saved reviewed MCP tool schemas to '+str(path))
