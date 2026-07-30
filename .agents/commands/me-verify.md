---
description: Run MagicEditor VERIFY loop (file-scoped ruff + pytest)
---

Run the project skill **me-verify-loop** at LOW effort.

1. Detect changed files from git status.
2. File-scoped `uv run ruff check` / `ruff format` / targeted pytest.
3. UI tests: `QT_QPA_PLATFORM=offscreen` on Windows PowerShell.
4. Report VERIFY PASS/FAIL with escalate yes/no.
