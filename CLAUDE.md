# MagicEditor — Claude / multi-host entry

Follow **`AGENTS.md`** as the single source of agent instructions.

## Model routing (mandatory)
See `docs/ai/model-routing.md`.

| Phase | Grok effort | Claude equiv |
|-------|-------------|--------------|
| Plan / Review | `xhigh` / `high` | Opus / strongest |
| Build | `medium` | Sonnet |
| Verify / mechanical | `low` | Haiku |

Token hygiene: hierarchical routing in `AGENTS.md` — load only scoped files.  
Optional RTK: global `@RTK.md` if available.  
Skills: `.agents/skills/` · catalog `docs/ai/skills-and-tools.md` (load selectively).  
Host/MCP setup: `docs/ai/ai-setup.md`.  
Claude local: `.claude/settings.json` + `.claude/CLAUDE.md`.
