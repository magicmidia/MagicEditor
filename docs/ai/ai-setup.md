# AI-assisted development setup — MagicEditor

Single source of agent behavior: root **`AGENTS.md`**.  
Cost control: **`docs/ai/model-routing.md`**.  
Skill catalog: **`docs/ai/skills-and-tools.md`**.

## Layout (what lives where)

```
AGENTS.md / CLAUDE.md          # host entry (keep short)
docs/ai/                       # long catalogs + this setup guide
.memory/                       # ADRs, patterns, inbox, audit log
.agents/skills/                # project skills (all hosts)
.agents/commands/              # slash commands (/me-feature, …)
.grok/                         # Grok roles, agents, rules, config
.cursor/rules/                 # Cursor always-on rules
.claude/                       # Claude Code settings + project memory
.mcp.example.json              # MCP for Cursor/Claude/VS Code
.grok/mcp.example.toml         # MCP for Grok Build
.github/copilot-instructions.md
```

## Hosts

| Host | Entry | Skills | MCP |
|------|-------|--------|-----|
| **Grok Build** | `AGENTS.md` + `.grok/` | `.agents/skills/` (auto) | copy `.grok/mcp.example.toml` → `~/.grok/config.toml` |
| **Claude Code** | `CLAUDE.md` + `.claude/` | `.agents/skills/` if scanned; else symlink/copy | `.mcp.example.json` → Claude MCP config |
| **Cursor** | `.cursor/rules/magiceditor.mdc` | project skills if enabled | Cursor MCP settings from example JSON |
| **GitHub Copilot** | `.github/copilot-instructions.md` | n/a | n/a |
| **Codex / other** | `AGENTS.md` | `.agents/skills/` when supported | optional |

## Project skills (load selectively)

| Skill | When |
|-------|------|
| `me-feature` | Non-trivial feature (full pipeline) |
| `me-core` | `core/` / piece table / mmap / search |
| `me-ui` | PyQt6 thin UI / viewport / dialogs |
| `me-theme` | QSS / visual polish |
| `me-i18n` | Locales / retranslate |
| `me-verify-loop` | Lint + tests after changes |
| `design-taste` | Premium UI anti-slop |
| `superpowers` | Hard architecture / debugging |
| `token-economy` | Long sessions / context hygiene |

Slash (Grok): `/me-feature`, `/me-verify`, `/me-review`.

## Agents / roles (Grok)

| Role | Phase | Effort | Mode |
|------|-------|--------|------|
| `me-plan` | PLAN | xhigh | read-only |
| `me-build` | BUILD | medium | all |
| `me-verify` | VERIFY | low | execute |
| `me-review` | REVIEW | high | read-only |

Defined under `.grok/agents/`, `.grok/roles/`, `.grok/personas/`.

## MCP (optional)

Install only what you use. Prefer **no secrets in repo**.

Recommended:

1. **filesystem** (repo-scoped)
2. **git**
3. **context7** — PyQt6 / pytest docs
4. **sequential-thinking** — PLAN trade-offs
5. **github** — only if shipping PRs via agent (token in env)
6. **memory** — optional; project truth stays in `.memory/`

JSON hosts: copy from `.mcp.example.json`.  
Grok: copy sections from `.grok/mcp.example.toml`.  
First `npx` cold start may need `startup_timeout_sec = 120` or `MCP_TIMEOUT=120000`.

## Session checklist

1. Classify phase → set effort / spawn role
2. Read root `AGENTS.md` → route table → **only** scoped files
3. Load 0–2 skills matching the work (not the whole catalog)
4. Prefer `.memory/decisions.md` + `patterns.md` over re-reading full architecture
5. VERIFY file-scoped before “done”
6. Durable decisions → ADR in `.memory/decisions.md`

## Anti-patterns

- Loading 10+ skills “just in case”
- HIGH effort for pytest/ruff
- Growing `main_window.py` / `virtual_editor.py` instead of extracting modules
- Committing `.mcp.json` with tokens or `dist/*.exe`
