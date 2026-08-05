import os

from elli_client import TokenResponse
from elli_billing_tool.auth.token_store import TokenStore


class MemoryKeyring:
    def __init__(self): self.value = None
    def get_password(self, service, account): return self.value
    def set_password(self, service, account, value): self.value = value
    def delete_password(self, service, account): self.value = None


def test_keyring_roundtrip_rotation_and_clear(tmp_path):
    backend = MemoryKeyring()
    store = TokenStore(backend, tmp_path / "fallback.json")
    assert not store.has_credentials()
    store.save_tokens(TokenResponse(access_token="a", refresh_token="r1"))
    assert store.load_refresh_token() == "r1"
    store.save_tokens(TokenResponse(access_token="b"), previous_refresh_token="r1")
    assert store.load_refresh_token() == "r1"
    store.clear()
    assert not store.has_credentials()


def test_explicit_fallback_is_atomic_private(tmp_path):
    class Broken:
        def get_password(self, *args): raise RuntimeError()
        def set_password(self, *args): raise RuntimeError()
        def delete_password(self, *args): raise RuntimeError()
    path = tmp_path / "private" / "refresh.json"
    store = TokenStore(Broken(), path, allow_fallback=True)
    store.save_tokens(TokenResponse(access_token="a", refresh_token="secret"))
    assert store.load_refresh_token() == "secret"
    assert not list(path.parent.glob("*.tmp"))
    if os.name != "nt": assert path.stat().st_mode & 0o777 == 0o600
