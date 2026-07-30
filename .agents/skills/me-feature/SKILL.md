---
name: me-feature
description: >
  End-to-end MagicEditor feature pipeline PLAN→BUILD→VERIFY→REVIEW with cost-aware model routing.
  Use when starting a non-trivial feature, multi-file change, or user says /feature or "implement feature".
  Triggers: new feature, roadmap item, multi-file, plan then build, me-plan, me-build.
---

# MagicEditor — Feature Pipeline

Follow `docs/ai/model-routing.md`. Do not skip phase contracts.

## 1. PLAN (HIGH / me-plan)
- Read `docs/STATUS.md`, scoped `AGENTS.md`, only needed architecture slices
- Output: goal, non-goals, ordered steps, critical files, verify commands, risks
- **No product code edits**

## 2. BUILD (MEDIUM / me-build)
- Implement plan only; extract modules if touching oversized files (`main_window.py`, `virtual_editor.py`)
- TDD for `core/`; thin UI for `ui/`
- Skills: `me-core` and/or `me-ui` as applicable

## 3. VERIFY (LOW / me-verify-loop)
- File-scoped ruff + pytest
- Escalate real failures back to BUILD

## 4. REVIEW (HIGH / me-review)
- Layering, huge-file policy, module size, missing tests
- Findings only — no drive-by refactors

## Routing table
| Phase | Effort | Agent |
|-------|--------|-------|
| PLAN | xhigh/high | me-plan |
| BUILD | medium | me-build |
| VERIFY | low | me-verify |
| REVIEW | high | me-review |

## Caps
- One HIGH plan + one HIGH review per feature unit
- Max spawn depth 2; no nested HIGH
- Update `.memory/decisions.md` or `patterns.md` only for durable ADRs/patterns
- Status handoff: note done items in `docs/STATUS.md` when phase completes for the user
