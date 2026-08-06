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


def test_macos_build_always_seals_complete_bundle():
    script = Path("packaging/macos/build_callback_helper.sh").read_text(encoding="utf-8")
    assert 'codesign --force --deep --sign - "$APP_DIR"' in script


def test_macos_launcher_removes_conflicts_and_registers_helper_before_login():
    launcher = Path("run.sh").read_text(encoding="utf-8")
    cleanup = launcher.index('"$LSREGISTER" -u "$registered_helper"')
    registration = launcher.index('"$LSREGISTER" -f "$CALLBACK_HELPER"')
    direct_commands = launcher.index('case "${1:-}" in')
    assert cleanup < registration < direct_commands


def test_missing_macos_helper_is_clear(tmp_path):
    with pytest.raises(CallbackError, match="fehlt"):
        register_macos_helper(tmp_path / "missing")
