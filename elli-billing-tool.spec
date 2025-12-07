# -*- mode: python ; coding: utf-8 -*-

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
        'elli_client',
        'elli_client.config',
        'elli_client.service',
        'elli_client.auth',
        'elli_client.models',
    ],
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
