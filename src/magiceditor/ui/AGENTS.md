# ui/ — Qt presentation

- Thin widgets: no piece-table math, no mmap policy
- `main_window.py` composes; `tab_manager.py` owns tab chrome; `text_editor.py` owns viewport
- Use signals for cross-widget events
- pytest-qt + offscreen for automated UI tests
