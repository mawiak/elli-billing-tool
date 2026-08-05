from pathlib import Path

import pytest
from elli_client import InvalidOAuthState, ReauthenticationRequired, TokenRefreshError, TokenResponse

from elli_billing_tool.auth.auth_service import AuthenticationService
from elli_billing_tool.auth.callback_ipc import forward_callback, session_path


class Store:
    def __init__(self, token=None): self.token, self.saved, self.cleared = token, [], False
    def load_refresh_token(self): return self.token
    def save_tokens(self, tokens, previous_refresh_token=None):
        self.saved.append((tokens.refresh_token or previous_refresh_token, previous_refresh_token))
        self.token = tokens.refresh_token or previous_refresh_token
    def clear(self): self.token, self.cleared = None, True
    def has_credentials(self): return bool(self.token)


class Client:
    def __init__(self, refresh_result=None, refresh_error=None, invalid_state=False):
        self.refresh_result, self.refresh_error = refresh_result, refresh_error
        self.invalid_state, self.tokens, self.closed = invalid_state, None, False
        self.authorization = type("Authorization", (), {"authorization_url": "https://safe.example/login"})()
    def refresh(self, token):
        if self.refresh_error: raise self.refresh_error
        return self.refresh_result
    def create_authorization(self): return self.authorization
    def exchange_callback(self, callback, authorization):
        if self.invalid_state: raise InvalidOAuthState("state mismatch")
        return TokenResponse(access_token="access", refresh_token="new-refresh")
    def set_tokens(self, tokens): self.tokens = tokens
    def close(self): self.closed = True


def test_valid_refresh_avoids_browser_and_saves_rotation():
    client = Client(TokenResponse(access_token="a", refresh_token="rotated"))
    store = Store("old")
    service = AuthenticationService(store, lambda: client, browser_open=lambda _: pytest.fail("browser opened"))
    assert service.get_authenticated_client() is client
    assert store.token == "rotated"


def test_refresh_without_rotation_preserves_previous():
    client, store = Client(TokenResponse(access_token="a")), Store("old")
    service = AuthenticationService(store, lambda: client)
    assert service.get_authenticated_client() is client
    assert store.token == "old"


def test_temporary_refresh_error_does_not_clear_token():
    client, store = Client(refresh_error=TokenRefreshError("network")), Store("keep")
    with pytest.raises(TokenRefreshError):
        AuthenticationService(store, lambda: client).get_authenticated_client()
    assert store.token == "keep" and not store.cleared


def test_reauthentication_clears_then_runs_browser_login(tmp_path):
    refresh_client = Client(refresh_error=ReauthenticationRequired("expired"))
    login_client, store = Client(), Store("old")
    clients = iter([refresh_client, login_client])
    service = AuthenticationService(
        store, lambda: next(clients),
        browser_open=lambda _: (forward_callback("safe-callback", session_path(tmp_path)) or True),
        handler_setup=lambda: None, data_directory=tmp_path, timeout=1,
    )
    assert service.get_authenticated_client() is login_client
    assert store.cleared and store.token == "new-refresh"
    assert not session_path(tmp_path).exists()


def test_no_refresh_token_callback_success_and_cleanup(tmp_path):
    client, store = Client(), Store()
    service = AuthenticationService(
        store, lambda: client,
        browser_open=lambda _: (forward_callback("safe-callback", session_path(tmp_path)) or True),
        handler_setup=lambda: None, data_directory=tmp_path, timeout=1,
    )
    assert service.get_authenticated_client() is client
    assert client.tokens.access_token == "access"
    assert not session_path(tmp_path).exists()


def test_invalid_state_saves_nothing_and_cleans_up(tmp_path):
    client, store = Client(invalid_state=True), Store()
    service = AuthenticationService(
        store, lambda: client,
        browser_open=lambda _: (forward_callback("safe-callback", session_path(tmp_path)) or True),
        handler_setup=lambda: None, data_directory=tmp_path, timeout=1,
    )
    with pytest.raises(InvalidOAuthState): service.interactive_login()
    assert not store.saved and not session_path(tmp_path).exists()
