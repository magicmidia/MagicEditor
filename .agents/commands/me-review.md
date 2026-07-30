---
description: HIGH-tier review of current MagicEditor changes
---

Act as **me-review** (HIGH effort, prefer read-only).

Check only the current diff / listed files for:
- `core/` purity (no Qt)
- thin UI / no I/O policy in paint handlers
- huge-file rules (mmap, virtual viewport, visible syntax)
- module size smells (>400 LOC)
- missing tests

Output: Blockers / Majors / Minors / Nits / Verdict.
