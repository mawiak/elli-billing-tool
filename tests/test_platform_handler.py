import plistlib
from pathlib import Path

import pytest

from elli_billing_tool.auth.callback_ipc import CallbackError
from elli_billing_tool.auth.platform_handler import register_macos_helper, windows_open_command


def test_windows_command_quotes_unicode_and_spaces():
    assert windows_open_command(r"C:\Program Files\Älli\elli-billing-tool.exe") == (
        '"C:\\Program Files\\Älli\\elli-billing-tool.exe" oauth-callback "%1"'
    )


def test_macos_plist_and_registration(tmp_path):
    with Path("packaging/macos/Info.plist").open("rb") as source:
        plist = plistlib.load(source)
    assert plist["LSUIElement"] is True
    assert plist["CFBundleURLTypes"][0]["CFBundleURLSchemes"] == ["com.elli.ios.emsp"]
    helper = tmp_path / "Elli Login Callback.app"
    helper.mkdir()
    calls = []
    register_macos_helper(helper, runner=lambda args, **kwargs: calls.append((args, kwargs)))
    assert calls[0][0][1:] == ["-f", str(helper)]


def test_missing_macos_helper_is_clear(tmp_path):
    with pytest.raises(CallbackError, match="fehlt"):
        register_macos_helper(tmp_path / "missing")
