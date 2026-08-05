"""Single-use loopback IPC used by the native OAuth callback handler."""

from __future__ import annotations

import hmac
import json
import os
import secrets
import socket
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

SESSION_FILENAME = "oauth-session.json"
SESSION_MAX_AGE = timedelta(minutes=5)
CALLBACK_TIMEOUT_SECONDS = 300.0
MAX_IPC_PAYLOAD_BYTES = 16 * 1024


class CallbackError(Exception):
    """Safe, user-facing callback infrastructure error."""


class SessionExpired(CallbackError):
    pass


class InvalidIPCSecret(CallbackError):
    pass


class PayloadTooLarge(CallbackError):
    pass


@dataclass(frozen=True)
class IPCSession:
    port: int
    secret: str
    created_at: datetime
    pid: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "port": self.port,
            "secret": self.secret,
            "created_at": self.created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "pid": self.pid,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "IPCSession":
        try:
            created_at = datetime.fromisoformat(str(value["created_at"]).replace("Z", "+00:00"))
            port, pid, secret = int(value["port"]), int(value["pid"]), str(value["secret"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CallbackError("Die Callback-Sitzungsdatei ist ungültig.") from exc
        if created_at.tzinfo is None or not 1 <= port <= 65535 or pid <= 0 or len(secret) < 43:
            raise CallbackError("Die Callback-Sitzungsdatei ist ungültig.")
        return cls(port, secret, created_at, pid)


def app_data_directory(platform_name: str | None = None, environ: Mapping[str, str] | None = None) -> Path:
    platform_name, environ = platform_name or os.sys.platform, environ or os.environ
    if platform_name == "darwin":
        return Path(environ.get("HOME", str(Path.home()))) / "Library" / "Application Support" / "Elli Billing Tool"
    if platform_name == "win32":
        local = environ.get("LOCALAPPDATA")
        if not local:
            raise CallbackError("LOCALAPPDATA ist nicht gesetzt.")
        return Path(local) / "Elli Billing Tool"
    return Path(environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "elli-billing-tool"


def session_path(data_directory: Path | None = None) -> Path:
    return (data_directory or app_data_directory()) / SESSION_FILENAME


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        path.parent.chmod(0o700)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as temporary:
            temporary_name = temporary.name
            if os.name != "nt":
                os.chmod(temporary_name, 0o600)
            json.dump(value, temporary, separators=(",", ":"), sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
        if os.name != "nt":
            path.chmod(0o600)
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


def write_session(path: Path, session: IPCSession) -> None:
    atomic_write_json(path, session.to_dict())


def load_session(path: Path, now: datetime | None = None) -> IPCSession:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CallbackError("Keine gültige aktive Anmeldung gefunden.") from exc
    if not isinstance(value, dict):
        raise CallbackError("Die Callback-Sitzungsdatei ist ungültig.")
    session = IPCSession.from_dict(value)
    age = (now or datetime.now(timezone.utc)) - session.created_at.astimezone(timezone.utc)
    if age < timedelta(seconds=-30) or age > SESSION_MAX_AGE:
        raise SessionExpired("Die Callback-Sitzung ist abgelaufen.")
    return session


def create_listener() -> socket.socket:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    return listener


def create_ipc_session(listener: socket.socket) -> IPCSession:
    host, port = listener.getsockname()
    if host != "127.0.0.1":
        raise CallbackError("IPC-Listener ist nicht an Loopback gebunden.")
    return IPCSession(port, secrets.token_urlsafe(32), datetime.now(timezone.utc), os.getpid())


def _read_limited(connection: socket.socket) -> bytes:
    chunks, total = [], 0
    while True:
        chunk = connection.recv(min(4096, MAX_IPC_PAYLOAD_BYTES + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > MAX_IPC_PAYLOAD_BYTES:
            raise PayloadTooLarge("Callback-Payload ist zu groß.")
    return b"".join(chunks)


def receive_callback(listener: socket.socket, expected_secret: str, timeout: float) -> str:
    listener.settimeout(timeout)
    try:
        connection, address = listener.accept()
    except TimeoutError as exc:
        raise CallbackError("Die Elli-Anmeldung wurde nicht innerhalb von fünf Minuten abgeschlossen. Bitte starte den Vorgang erneut.") from exc
    finally:
        listener.close()
    if address[0] != "127.0.0.1":
        connection.close()
        raise CallbackError("Nicht-lokale Callback-Verbindung abgelehnt.")
    with connection:
        connection.settimeout(5.0)
        raw = _read_limited(connection)
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CallbackError("Callback-Payload ist ungültig.") from exc
    if not isinstance(payload, dict):
        raise CallbackError("Callback-Payload ist ungültig.")
    secret, callback_url = payload.get("secret"), payload.get("callback_url")
    if not isinstance(secret, str) or not hmac.compare_digest(secret, expected_secret):
        raise InvalidIPCSecret("Callback-Secret ist ungültig.")
    if not isinstance(callback_url, str) or len(callback_url.encode("utf-8")) > MAX_IPC_PAYLOAD_BYTES:
        raise CallbackError("Callback-URL ist ungültig.")
    return callback_url


def forward_callback(callback_url: str, path: Path | None = None) -> None:
    session = load_session(path or session_path())
    payload = json.dumps({"secret": session.secret, "callback_url": callback_url}, separators=(",", ":")).encode()
    if len(payload) > MAX_IPC_PAYLOAD_BYTES:
        raise PayloadTooLarge("Callback-Payload ist zu groß.")
    try:
        with socket.create_connection(("127.0.0.1", session.port), timeout=5.0) as connection:
            connection.sendall(payload)
            connection.shutdown(socket.SHUT_WR)
    except OSError as exc:
        raise CallbackError("Callback konnte nicht an den wartenden Prozess zugestellt werden.") from exc
