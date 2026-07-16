# MagicEditor

High-performance desktop text/code editor (Python 3.12+, PyQt6): virtual viewport, piece table, and mmap for huge files.

**Architecture (master spec):** [`docs/magiceditor-architecture.md`](docs/magiceditor-architecture.md)  
**Agent entry:** [`AGENTS.md`](AGENTS.md)  
**Dev setup:** [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)  
**Status:** [`docs/STATUS.md`](docs/STATUS.md)

## Quick start

```bash
uv sync --all-extras
uv run pytest
uv run magiceditor
```

## Layout

| Path | Role |
|------|------|
| `src/magiceditor/core/` | Pure buffer/search engine (no Qt) |
| `src/magiceditor/ui/` | Windows, tabs, viewport |
| `src/magiceditor/themes/` | Theme manager |
| `src/magiceditor/i18n/` | Live translation |
| `src/magiceditor/preview/` | MD/HTML preview |
| `src/magiceditor/services/` | Print/PDF, policies |
| `locales/` | `en_US.json`, `pt_BR.json` |
| `resources/themes/` | QSS themes |
| `docs/ai/` | Skills, MCPs, coding standards |
| `.memory/` | ADRs, patterns, agent inbox |

## AI-assisted development

- Follow `AGENTS.md` context routing (token-efficient).
- **Model routing (cost):** Plan/Review → HIGH (`xhigh`/`high`); Build → MEDIUM; Tests → LOW.  
  Details: [`docs/ai/model-routing.md`](docs/ai/model-routing.md). Grok roles: `me-plan` / `me-build` / `me-verify` / `me-review`.
- Skills/MCP catalog: `docs/ai/skills-and-tools.md`.
- Cursor rules: `.cursor/rules/magiceditor.mdc`.
- Example MCP config: `.mcp.example.json`.
