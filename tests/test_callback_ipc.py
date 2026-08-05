import json
import os
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest

from elli_billing_tool.auth.callback_ipc import (
    MAX_IPC_PAYLOAD_BYTES, CallbackError, InvalidIPCSecret, PayloadTooLarge,
    create_ipc_session, create_listener, load_session, receive_callback,
    session_path, write_session,
)


def _send(port, payload):
    with socket.create_connection(("127.0.0.1", port), timeout=1) as connection:
        connection.sendall(payload)
        connection.shutdown(socket.SHUT_WR)


def test_listener_is_random_loopback_and_single_use():
    first, second = create_listener(), create_listener()
    assert first.getsockname()[0] == "127.0.0.1"
    assert first.getsockname()[1] != second.getsockname()[1]
    second.close()
    session = create_ipc_session(first)
    assert len(session.secret) >= 43
    payload = json.dumps({"secret": session.secret, "callback_url": "safe"}).encode()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(receive_callback, first, session.secret, 1)
        _send(session.port, payload)
        assert future.result() == "safe"
    assert first.fileno() == -1


def test_wrong_secret_and_large_payload_are_rejected():
    listener = create_listener()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(receive_callback, listener, "expected", 1)
        _send(listener.getsockname()[1], b'{"secret":"wrong","callback_url":"safe"}')
        with pytest.raises(InvalidIPCSecret): future.result()
    listener = create_listener()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(receive_callback, listener, "expected", 1)
        _send(listener.getsockname()[1], b"x" * (MAX_IPC_PAYLOAD_BYTES + 1))
        with pytest.raises(PayloadTooLarge): future.result()


def test_timeout_and_expired_session_cleanup_contract(tmp_path):
    listener = create_listener()
    with pytest.raises(CallbackError, match="fünf Minuten"):
        receive_callback(listener, "expected", .01)
    path = session_path(tmp_path)
    session = create_ipc_session(create_listener())
    expired = type(session)(session.port, session.secret, session.created_at - timedelta(minutes=6), os.getpid())
    write_session(path, expired)
    with pytest.raises(CallbackError): load_session(path)
    if os.name != "nt": assert path.stat().st_mode & 0o777 == 0o600
