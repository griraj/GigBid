from fastapi.testclient import TestClient
from apps.api.main import app


client=TestClient(app)
HEADERS={'Authorization':'Bearer demo-reviewer-token'}


def test_authenticated_portfolio_upload_and_delete():
    assert client.post('/portfolio/upload',files={'file':('case.md',b'Portfolio example')}).status_code==401
    response=client.post('/portfolio/upload',headers=HEADERS,
        files={'file':('case.md',b'Portfolio example')})
    assert response.status_code==201,response.text
    item=response.json()
    assert item['source']=='user_uploaded'
    assert any(e['id']==item['id'] for e in client.get('/portfolio',headers=HEADERS).json())
    assert client.delete(f"/portfolio/upload/{item['id']}",headers=HEADERS).status_code==200


def test_rejects_executables_and_large_uploads():
    assert client.post('/portfolio/upload',headers=HEADERS,
        files={'file':('unsafe.exe',b'run')}).status_code==415
    assert client.post('/portfolio/upload',headers=HEADERS,
        files={'file':('huge.txt',b'x'*500001)}).status_code==413
