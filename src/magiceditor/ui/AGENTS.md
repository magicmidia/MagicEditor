# ui/ — Qt presentation

- Thin widgets: no piece-table math, no mmap policy
- `main_window.py` composes; `tab_manager.py` owns tab chrome; `text_editor.py` / `virtual_editor.py` own viewport
- Use signals for cross-widget events
- pytest-qt + offscreen for automated UI tests
- **Do not grow** `main_window.py` / `virtual_editor.py` further — extract helpers
- Skill: `me-ui`
