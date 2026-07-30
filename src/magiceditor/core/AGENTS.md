# core/ — pure engine

- **No PyQt6** (enforce in review)
- Piece table / rope, mmap file source, Boyer–Moore search, line index
- Unit-test everything here without a display
- Hot paths: prefer clear algorithms + benchmarks later; avoid premature abstraction
- Skill: `me-core` · TDD under `tests/core/`
