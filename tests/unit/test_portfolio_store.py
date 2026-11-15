from data.portfolio_store import PortfolioStore


def test_portfolio_uploads_are_private(tmp_path):
    store=PortfolioStore(tmp_path/'portfolio.sqlite')
    item=store.add('alice','case.md','An evidence-backed case study.')
    assert store.list('bob')==[]
    assert store.list('alice')[0]['id']==item['id']
    assert not store.delete('bob',item['id'])
    assert store.delete('alice',item['id'])
    assert store.list('alice')==[]
