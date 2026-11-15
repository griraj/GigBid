from evals.runners.tool_study import SCHEMAS,PROBES,labelled_tasks,tool_catalog


def test_forty_authored_tool_tasks_match_real_mcp_schemas():
    assert len(labelled_tasks())==40
    for server,name,arguments,_ in PROBES:
        assert name in SCHEMAS[server]
        schema=SCHEMAS[server][name]['parameters']
        assert set(arguments)<=set(schema.get('properties',{}))
        assert set(schema.get('required',[]))<=set(arguments)
    catalog,groups=tool_catalog('coarse')
    assert len(catalog)<len(tool_catalog('fine')[0])
    assert all(name in groups for name in (f'{s}.{t}' for s,t,_,_ in PROBES))
