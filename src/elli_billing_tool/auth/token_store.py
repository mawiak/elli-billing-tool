"""Secure local refresh-token storage."""

from __future__ import annotations

import json
import os
from pathlib import Path

from elli_client import TokenResponse

from .callback_ipc import app_data_directory, atomic_write_json

SERVICE_NAME = "Elli Billing Tool"
ACCOUNT_NAME = "elli-refresh-token"
FALLBACK_ENV = "ELLI_BILLING_TOKEN_FALLBACK"


class TokenStoreError(Exception):
    pass


class TokenStore:
    def __init__(self, keyring_backend=None, fallback_path: Path | None = None, allow_fallback: bool | None = None):
        self._keyring = keyring_backend
        self.fallback_path = fallback_path or app_data_directory() / "refresh-token.json"
        self.allow_fallback = (os.environ.get(FALLBACK_ENV) == "file") if allow_fallback is None else allow_fallback

    def _backend(self):
        if self._keyring is not None:
            return self._keyring
        try:
            import keyring
            return keyring
        except ImportError as exc:
            raise TokenStoreError("Der sichere Betriebssystem-Schlüsselspeicher ist nicht verfügbar.") from exc

    def _fallback_load(self) -> str | None:
        try:
            value = json.loads(self.fallback_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as exc:
            raise TokenStoreError("Der lokale Token-Fallback konnte nicht gelesen werden.") from exc
        token = value.get("refresh_token") if isinstance(value, dict) else None
        return token if isinstance(token, str) and token else None

    def load_refresh_token(self) -> str | None:
        try:
            return self._backend().get_password(SERVICE_NAME, ACCOUNT_NAME)
        except Exception as exc:
            if self.allow_fallback:
                return self._fallback_load()
            raise TokenStoreError("Der Betriebssystem-Schlüsselspeicher ist nicht verfügbar. Kein unsicherer Fallback wurde aktiviert.") from exc

    def save_tokens(self, tokens: TokenResponse, previous_refresh_token: str | None = None) -> None:
        refresh_token = tokens.refresh_token or previous_refresh_token
        if not refresh_token:
            raise TokenStoreError("Elli hat keinen speicherbaren Refresh-Token geliefert.")
        try:
            self._backend().set_password(SERVICE_NAME, ACCOUNT_NAME, refresh_token)
        except Exception as exc:
            if not self.allow_fallback:
                raise TokenStoreError("Der Betriebssystem-Schlüsselspeicher ist nicht verfügbar. Kein unsicherer Fallback wurde aktiviert.") from exc
            atomic_write_json(self.fallback_path, {"refresh_token": refresh_token})

    def clear(self) -> None:
        try:
            self._backend().delete_password(SERVICE_NAME, ACCOUNT_NAME)
        except Exception as exc:
            # Missing entries are backend-specific errors; verify presence before surfacing.
            try:
                if self._backend().get_password(SERVICE_NAME, ACCOUNT_NAME):
                    raise TokenStoreError("Der gespeicherte Refresh-Token konnte nicht gelöscht werden.") from exc
            except TokenStoreError:
                raise
            except Exception:
                if not self.allow_fallback:
                    raise TokenStoreError("Der Betriebssystem-Schlüsselspeicher ist nicht verfügbar.") from exc
        self.fallback_path.unlink(missing_ok=True)

    def has_credentials(self) -> bool:
        return bool(self.load_refresh_token())
