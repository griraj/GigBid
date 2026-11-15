from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.api.publication import article


def test_public_article_is_readable_html():
    app=FastAPI();app.add_api_route('/writeup',article)
    response=TestClient(app).get('/writeup')
    assert response.status_code==200
    assert '<h1>' in response.text
    assert 'application/json' not in response.headers['content-type']
    assert 'GigBid engineering notes' in response.text
