# -*- mode: python ; coding: utf-8 -*-
# Daily-use onedir build (K10): faster cold start than onefile; optional datas beside EXE.
#   powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Onedir

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
root = Path(SPECPATH)
_app_icon = root / "resources" / "icons" / "app" / "magiceditor.ico"

_qta_datas = collect_data_files("qtawesome")
try:
    _spell_datas = collect_data_files("spellchecker")
except Exception:
    _spell_datas = []

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
    [],
    exclude_binaries=True,
    name="MagicEditor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(_app_icon) if _app_icon.is_file() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MagicEditor",
)
