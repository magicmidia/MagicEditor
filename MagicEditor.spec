# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — one-file windowed EXE.
# Prefer:  build.bat  or  powershell -ExecutionPolicy Bypass -File scripts/build.ps1
# Output:  MagicEditor.exe at repo root (build.ps1 --distpath .)

from pathlib import Path

block_cipher = None
root = Path(SPECPATH)
_app_icon = root / "resources" / "icons" / "app" / "magiceditor.ico"

# K10: onefile skips qtawesome/spellchecker datas (lazy at runtime; embedded lexicon).
# Daily onedir collects them — see MagicEditor-onedir.spec.
_qta_datas: list = []
_spell_datas: list = []

a = Analysis(
    [str(root / "src" / "magiceditor" / "__main__.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[
        (str(root / "locales"), "locales"),
        (str(root / "resources"), "resources"),
        *_qta_datas,
        *_spell_datas,
    ],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtPrintSupport",
        "PyQt6.QtSvg",
        "PyQt6.QtNetwork",
        "markdown",
        "magiceditor.ui.single_instance",
        "qtawesome",
        "qtawesome.iconic_font",
        "magiceditor",
        "magiceditor.app",
        "magiceditor.ui.main_window",
        "magiceditor.ui.syntax_highlighter",
        "magiceditor.ui.icons",
        "magiceditor.core.syntax",
        "spellchecker",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt6.QtWebEngine",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtBluetooth",
        "PyQt6.QtNetworkAuth",
        "PyQt6.QtNfc",
        "PyQt6.QtTest",
        "tkinter",
        "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MagicEditor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # K10/L12: no UPX; prefer onedir for daily cold-start (see COLLECT below)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_app_icon) if _app_icon.is_file() else None,
)
