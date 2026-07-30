# Architecture Decision Records

Format: short ADR. Newest first.

## ADR-0001 — Hybrid core + PyQt6 UI (2026-07-16)
**Status:** Accepted  
**Context:** Need Notepad++-class huge-file performance and modern UI.  
**Decision:** Pure Python `core/` (piece table + mmap + search) isolated from PyQt6 `ui/`. Virtual viewport paints visible lines only.  
**Consequences:** UI can be swapped/tested independently; agents must never put Qt in `core/`.

## ADR-0002 — Agent harness layout (2026-07-16)
**Status:** Accepted  
**Context:** Multi-agent AI development; token cost and drift risk.  
**Decision:** Canonical `AGENTS.md` + hierarchical routing + `.memory/` + `docs/ai/*` for long catalogs.  
**Consequences:** Skills/MCP lists live outside AGENTS.md; keep root under ~100 lines.

## ADR-0003 — Three-tier model routing (2026-07-16)
**Status:** Accepted  
**Context:** Long coding sessions burn high-effort tokens on tests and mechanical work.  
**Decision:** Phase pipeline PLAN→BUILD→VERIFY→REVIEW mapped to effort `xhigh|high` / `medium` / `low` / `high`, with Grok roles/agents `me-plan|me-build|me-verify|me-review`.  
**Consequences:** Parent agents must classify phase before heavy work; VERIFY never uses HIGH; core design never uses LOW. See `docs/ai/model-routing.md`.

## ADR-0004 — Expanded AI harness (2026-07-30)
**Status:** Accepted  
**Context:** Multi-host agents needed domain skills, MCP examples, and package-scoped AGENTS without bloating root `AGENTS.md`.  
**Decision:** Canonical skills/commands under `.agents/`; host adapters in `.grok/`, `.claude/`, `.cursor/`, `.github/copilot-instructions.md`; setup guide `docs/ai/ai-setup.md`; MCP via `.mcp.example.json` + `.grok/mcp.example.toml` (no secrets). Domain skills: `me-core`, `me-ui`, `me-theme`, `me-i18n`, `me-feature`, `me-verify-loop`.  
**Consequences:** Agents load skills selectively; new packages get a short `AGENTS.md`; MCP remains opt-in per developer machine.
