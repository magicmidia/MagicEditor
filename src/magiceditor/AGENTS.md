# Package: magiceditor

- Entry: `__main__.py` → `app.run` → `ui.main_window.MainWindow`
- Subpackages by responsibility; import inward: ui → services → core
- Public version: `__version__` in `__init__.py`
- New feature: add module in the matching package; avoid bloating `app.py` / `main_window.py`
