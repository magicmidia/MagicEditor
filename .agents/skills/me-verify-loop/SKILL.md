---
name: me-verify-loop
description: >
  MagicEditor VERIFY phase: file-scoped ruff, format, pytest, packaging check.
  Use after code changes, before claiming done, or when user runs /verify or /me-verify.
  Triggers: verify, lint, pytest, check work, before commit, delivery.
effort: low
---

# MagicEditor — VERIFY Loop (LOW effort)

## Caps
- Effort **low** only. No architecture redesign.
- Trivial fixes OK (import, format, typo). Logic failures → escalate to BUILD (medium).

## Steps
1. List changed paths (`git status` / user list)
2. Map paths → tests:
   - `src/magiceditor/core/**` → `tests/core/`
   - `services/**` → `tests/services/`
   - `ui/**` → `tests/ui/` (+ offscreen)
3. Run file-scoped commands:

```bash
uv run ruff check <paths>
uv run ruff format <paths>
uv run pytest tests/<area>/test_<related>.py -q
```

Windows UI:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
uv run pytest tests/ui -q
```

4. Optional delivery package (when user asks for shippable build):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe
```

Never commit `dist/` binaries.

## Report format
```
VERIFY: PASS|FAIL
Commands:
- ...
Failures:
- ...
Escalate: yes|no — reason
```
