# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — outputs MagicEditor.exe at repository root (distpath=.)

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
root = Path(SPECPATH)

# QtAwesome ships TTF + charmaps under qtawesome/fonts/
_qta_datas = collect_data_files("qtawesome")

a = Analysis(
    [str(root / "src" / "magiceditor" / "__main__.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[
        (str(root / "locales"), "locales"),
        (str(root / "resources"), "resources"),
        *_qta_datas,
    ],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtPrintSupport",
        "PyQt6.QtSvg",
        "markdown",
        "qtawesome",
        "qtawesome.iconic_font",
        "magiceditor",
        "magiceditor.app",
        "magiceditor.ui.main_window",
        "magiceditor.ui.syntax_highlighter",
        "magiceditor.ui.icons",
        "magiceditor.core.syntax",
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
