"""High-level browser OAuth authentication orchestration."""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import Callable

from elli_client import ElliAPIClient, ReauthenticationRequired

from .callback_ipc import (
    CALLBACK_TIMEOUT_SECONDS,
    CallbackError,
    create_ipc_session,
    create_listener,
    receive_callback,
    session_path,
    write_session,
)
from .platform_handler import ensure_callback_handler
from .token_store import TokenStore


class BrowserOpenError(CallbackError):
    pass


class AuthenticationService:
    def __init__(
        self,
        token_store: TokenStore | None = None,
        client_factory: Callable[[], ElliAPIClient] = ElliAPIClient,
        browser_open: Callable[[str], bool] = webbrowser.open,
        handler_setup: Callable[[], None] = ensure_callback_handler,
        data_directory: Path | None = None,
        timeout: float = CALLBACK_TIMEOUT_SECONDS,
    ):
        self.token_store = token_store or TokenStore()
        self.client_factory = client_factory
        self.browser_open = browser_open
        self.handler_setup = handler_setup
        self.data_directory = data_directory
        self.timeout = timeout

    def get_authenticated_client(self) -> ElliAPIClient:
        refresh_token = self.token_store.load_refresh_token()
        if refresh_token:
            client = self.client_factory()
            try:
                tokens = client.refresh(refresh_token)
                self.token_store.save_tokens(tokens, previous_refresh_token=refresh_token)
                client.set_tokens(tokens)
                return client
            except ReauthenticationRequired:
                client.close()
                self.token_store.clear()
            except Exception:
                client.close()
                raise
        return self.interactive_login()

    def interactive_login(self) -> ElliAPIClient:
        self.handler_setup()
        listener = create_listener()
        ipc_session = create_ipc_session(listener)
        current_session_path = session_path(self.data_directory)
        write_session(current_session_path, ipc_session)
        client = self.client_factory()
        try:
            authorization = client.create_authorization()
            print("Die Elli-Anmeldung wird im Standardbrowser geöffnet.\n")
            print("Bitte melde dich dort mit deinem Elli-Konto an und bestätige")
            print("gegebenenfalls die Cloudflare-Prüfung.\n")
            print("Dieses Fenster bitte geöffnet lassen.")
            if not self.browser_open(authorization.authorization_url):
                raise BrowserOpenError("Der Standardbrowser konnte nicht automatisch geöffnet werden. Bitte prüfe die Systemeinstellungen für den Standardbrowser.")
            callback_url = receive_callback(listener, ipc_session.secret, self.timeout)
            tokens = client.exchange_callback(callback_url, authorization)
            self.token_store.save_tokens(tokens)
            client.set_tokens(tokens)
            print("\nElli-Anmeldung erfolgreich.\nDie Abrechnung wird erstellt.")
            return client
        except Exception:
            client.close()
            raise
        finally:
            listener.close()
            current_session_path.unlink(missing_ok=True)

    def logout(self) -> None:
        self.token_store.clear()
