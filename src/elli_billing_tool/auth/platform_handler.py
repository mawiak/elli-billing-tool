"""Operating-system registration for the Elli custom URL scheme."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .callback_ipc import CallbackError

REGISTRY_KEY = r"Software\Classes\com.elli.ios.emsp"
MACOS_BUNDLE_ID = "de.mawiak.elli-billing-tool.oauth-callback"


def windows_open_command(executable: str) -> str:
    if '"' in executable:
        raise CallbackError("Der Programmpfad enthält ein nicht unterstütztes Anführungszeichen.")
    return f'"{executable}" oauth-callback "%1"'


def _read_windows_handler() -> str | None:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\shell\open\command") as key:
            return str(winreg.QueryValueEx(key, None)[0])
    except FileNotFoundError:
        return None


def register_windows_handler(executable: str | None = None) -> None:
    if sys.platform != "win32":
        raise CallbackError("Windows-Protokollregistrierung ist nur unter Windows verfügbar.")
    import winreg
    executable = executable or sys.executable
    desired, current = windows_open_command(str(Path(executable).resolve())), _read_windows_handler()
    if current == desired:
        return
    if current is not None:
        raise CallbackError("com.elli.ios.emsp ist bereits durch eine andere Anwendung registriert. Die Registrierung wurde nicht überschrieben.")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY) as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "URL:Elli Billing Tool OAuth callback")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\DefaultIcon") as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, str(Path(executable).resolve()))
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\shell\open\command") as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, desired)


def macos_helper_path(executable: str | None = None) -> Path:
    binary = Path(executable or sys.executable).resolve()
    return binary.parent / "Elli Login Callback.app"


def register_macos_helper(helper: Path | None = None, runner=subprocess.run) -> None:
    helper = helper or macos_helper_path()
    if not helper.is_dir():
        raise CallbackError("Elli Login Callback.app fehlt neben der ausführbaren Datei.")
    lsregister = Path("/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister")
    try:
        runner([str(lsregister), "-f", str(helper)], check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CallbackError("Der macOS-Callback-Helper konnte nicht bei Launch Services registriert werden.") from exc


def ensure_callback_handler() -> None:
    if sys.platform == "darwin":
        register_macos_helper()
    elif sys.platform == "win32":
        register_windows_handler()
    else:
        raise CallbackError("Der automatische Elli-Callback wird nur unter macOS und Windows unterstützt.")
