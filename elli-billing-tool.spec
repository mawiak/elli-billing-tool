# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ['src/elli_billing_tool/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'elli_billing_tool',
        'elli_billing_tool.cli',
        'elli_billing_tool.config',
        'elli_billing_tool.elli_service',
        'elli_billing_tool.pdf_parser',
        'elli_billing_tool.pdf_generator',
        'elli_billing_tool.mail_generator',
        'elli_billing_tool.auth',
        'elli_billing_tool.auth.auth_service',
        'elli_billing_tool.auth.callback_ipc',
        'elli_billing_tool.auth.platform_handler',
        'elli_billing_tool.auth.token_store',
        'elli_client',
        'elli_client.config',
        'elli_client.models',
        'keyring',
    ] + (
        ['keyring.backends.macOS'] if sys.platform == 'darwin' else
        ['keyring.backends.Windows', 'win32ctypes.pywin32.pywintypes', 'win32ctypes.pywin32.win32cred']
        if sys.platform == 'win32' else []
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='elli-billing-tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
