# services/ — policy & I/O

- Document open/save, settings, print/PDF, folder search, graphics helpers
- May import `core` + stdlib; **no paint/event handlers**
- Huge-file open policy lives here (size gate → mmap vs memory), not in widgets
- Workers for long search: cancel token + signal batches; UI only consumes results
- Keep modules focused: `document.py`, `document_io.py`, `settings.py`, `print_engine.py`, `folder_search.py`
