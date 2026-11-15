from fastapi.testclient import TestClient
from apps.api.main import app


client=TestClient(app)


def test_multi_mode_registration_login_tenant_boundaries(monkeypatch):
    monkeypatch.setenv('GIGBID_AUTH_MODE','multi')
    monkeypatch.setenv('GIGBID_SIGNUP_INVITE','temporary-test-invite')
    for person in ('tenant-a','tenant-b'):
        response=client.post('/auth/register',json={'email':f'{person}@example.com',
            'password':'long-example-password','invite_code':'temporary-test-invite'})
        assert response.status_code in (200,409),response.text
    a=client.post('/auth/login',json={'email':'tenant-a@example.com','password':'long-example-password'}).json()['access_token']
    b=client.post('/auth/login',json={'email':'tenant-b@example.com','password':'long-example-password'}).json()['access_token']
    ha={'Authorization':f'Bearer {a}'}
    hb={'Authorization':f'Bearer {b}'}
    assert client.get('/auth/me',headers=ha).json()['email']=='tenant-a@example.com'
    run=client.post('/runs',headers=ha,json={'job_id':'j100','persona':'ai'})
    assert run.status_code==200,run.text
    thread=run.json()['thread_id']
    assert client.get(f'/runs/{thread}',headers=hb).status_code==404
    assert client.post(f'/runs/{thread}/approval',headers=hb,json={'action':'approve'}).status_code==404
    assert not any(item['thread_id']==thread for item in client.get('/runs',headers=hb).json())
    assert client.get(f'/runs/{thread}',headers=ha).status_code==200
    client.post('/auth/logout',headers=ha)
    assert client.get('/auth/me',headers=ha).status_code==401
