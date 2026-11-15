from cryptography.fernet import Fernet
from apps.api.auth.oauth import OAuthVault


def test_encrypted_oauth_tokens_tenant_scoped_and_state_single_use(tmp_path):
    path=tmp_path/'oauth.sqlite'
    vault=OAuthVault(path,Fernet.generate_key())
    state=vault.begin('alice','github')
    assert vault.consume(state,'github')=='alice'
    assert vault.consume(state,'github') is None
    vault.save('alice','github','test-secret-oauth-token')
    assert vault.load('alice','github')=='test-secret-oauth-token'
    assert vault.load('bob','github') is None
    assert b'test-secret-oauth-token' not in path.read_bytes()
    assert vault.connected('bob')==[]
    assert vault.disconnect('alice','github')
    assert vault.load('alice','github') is None
