---
name: me-core
description: >
  MagicEditor pure core engine work (piece table, mmap, line index, search, encoding).
  Use when editing src/magiceditor/core/**, huge-file buffer logic, or core unit tests.
  Triggers: piece table, mmap, Boyer-Moore, line index, encoding, core/, no Qt in core.
---

# MagicEditor — Core Engine

## Non-negotiables
- **No PyQt6** (or any Qt) in `src/magiceditor/core/`
- Prefer TDD: failing test under `tests/core/` first
- Hot paths stay algorithmic and explicit; avoid premature abstraction
- Module target ≤300 LOC; split before ~400

## Layout
| Module area | Responsibility |
|-------------|----------------|
| `piece_table.py` | Edit buffer (original + add spans) |
| `mmap_source.py` | Huge-file byte source |
| `line_index.py` | Line ↔ offset mapping |
| `search.py` / `text_match.py` | Pattern search |
| `encoding.py` | Detect / convert encodings |
| `syntax/` | Language detect + rules (no paint) |

## Huge-file contract
1. Size >50MB → mmap source; never full `read()` into `str`
2. Edits only via piece table
3. Line index incremental/lazy — not full reparse every keystroke
4. Search is cancelable and batchable (UI workers live outside core)

## Process
1. Read `src/magiceditor/core/AGENTS.md` + relevant module only
2. Write/adjust `tests/core/test_*.py`
3. Implement minimal pure-Python change
4. VERIFY (LOW): `uv run ruff check <paths>`; `uv run pytest tests/core/<file> -q`

## Done criteria
- No Qt imports in core
- Tests pass without display
- Invariants asserted (spans, line maps, offsets) — not only snapshots
