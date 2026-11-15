from agent.graphs.negotiation_graph import build_negotiation_graph


def test_below_floor_counteroffer_never_accepts_low_rate():
    result=build_negotiation_graph().invoke({'incoming':'Our rate is $15 per hour','floor':22.0})
    assert result['walk_away'] is True
    assert result['recommendation']==22
    assert '$22' in result['suggestion']


def test_acceptable_offer_and_missing_offer():
    graph=build_negotiation_graph()
    result=graph.invoke({'incoming':'The rate is 35 per hour','floor':22.0})
    assert result['walk_away'] is False
    assert result['recommendation']==35
    unknown=graph.invoke({'incoming':'Can we discuss your rate?','floor':22.0})
    assert unknown['recommendation'] is None


def test_amount_without_hourly_context_is_not_assumed_hourly():
    result=build_negotiation_graph().invoke({'incoming':'Our entire project budget is $500','floor':22.0})
    assert result['offered'] is None
