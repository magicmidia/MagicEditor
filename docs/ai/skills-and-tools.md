# Skills, MCPs & Plugins — MagicEditor

Use this catalog when starting a task. Load **only** the skills that match the current work (token hygiene).

Setup for hosts/MCP: **`docs/ai/ai-setup.md`**.

## Model routing first
Before picking skills, pick **phase/effort**: `docs/ai/model-routing.md`.

| Phase | Effort | Skills OK to load |
|-------|--------|-------------------|
| PLAN (HIGH) | xhigh/high | `me-feature`, `brainstorming`, `writing-plans`, `architecture*` |
| BUILD (MEDIUM) | medium | `me-core`, `me-ui`, `me-theme`, `me-i18n`, `test-driven-development`, `python-pro` |
| VERIFY (LOW) | low | `me-verify-loop`, `lint-and-validate` |
| REVIEW (HIGH) | high | `me-review` command, `find-bugs`, `code-review-checklist` |

Grok agents/roles: `me-plan`, `me-build`, `me-verify`, `me-review` under `.grok/`.

## Project-local skills (`.agents/skills/`)

| Skill | When |
|-------|------|
| **`me-feature`** | Non-trivial feature; full PLAN→BUILD→VERIFY→REVIEW |
| **`me-core`** | `core/`: piece table, mmap, line index, search, encoding |
| **`me-ui`** | `ui/`: thin widgets, virtual viewport, dialogs, pytest-qt |
| **`me-theme`** | QSS themes, chrome polish |
| **`me-i18n`** | Locales, `retranslate_ui`, new strings |
| **`me-verify-loop`** | File-scoped ruff/pytest / delivery check |
| **`design-taste`** | Anti-slop visual system (pairs with me-theme) |
| **`superpowers`** | Hard architecture, deep debug, multi-agent discipline |
| **`token-economy`** | Context hygiene, long sessions |

Slash commands (`.agents/commands/`): `/me-feature`, `/me-verify`, `/me-review`.

## Always-on mindset
| Concern | Prefer |
|---------|--------|
| Isolation | `using-git-worktrees` under `.worktrees/` |
| Spec before code | PLAN (HIGH) → `me-feature` / `writing-plans` → BUILD |
| Core correctness | `me-core` + TDD; VERIFY on LOW |
| Token cost | Model routing + AGENTS file routing + `.memory/` |
| Code quality | REVIEW on HIGH; extract from god-files |
| Anti-bloat | `moyu`, `andrej-karpathy`, `code-simplifier` |

## Superpowers / delivery loop (global skills)
| Skill | When |
|-------|------|
| `brainstorming` | New feature/UX before coding |
| `writing-plans` / `executing-plans` | Multi-step implementation |
| `subagent-driven-development` | Parallelizable independent tasks |
| `test-driven-development` | Any `core/` or pure logic |
| `systematic-debugging` | Failures / flaky UI |
| `verification-before-completion` | Before claiming done |
| `finishing-a-development-branch` | Merge/PR/cleanup worktree |
| `using-git-worktrees` | Isolated workspace |
| `dispatching-parallel-agents` | 2+ independent workstreams |

## Design / UX (desktop editor)
| Skill | When |
|-------|------|
| `me-theme` + `design-taste` | First choice for MagicEditor chrome |
| `impeccable` | Hierarchy, empty states, settings polish |
| `ui-ux-designer` | Layout/IA for main window, docks, toolbars |
| `product-design` | Design tokens / visual system |
| `accessibility-compliance-accessibility-audit` | Keyboard, contrast, focus order |
| `motion-design` | Subtle transitions only (snappy desktop) |
| `baseline-ui` | Spacing/type consistency checks |

## Engineering (this stack)
| Skill | When |
|-------|------|
| `python-pro` / `python-patterns` | Idiomatic Python 3.12+ |
| `python-testing-patterns` | pytest / fixtures / mocking |
| `clean-code` / `uncle-bob-craft` | SRP, short modules |
| `architecture-decision-records` | ADR into `.memory/decisions.md` |
| `performance-profiling` | Viewport, mmap, search bottlenecks |
| `complexity-cuts` / `lemmaly` | Hot paths (piece table, Boyer–Moore) |
| `debugger` | Crash/hang investigation |
| `lint-and-validate` | After every code change |

## Token / context economy
| Skill / tool | When |
|--------------|------|
| Hierarchical routing (`AGENTS.md`) | Every session — scoped files only |
| `.memory/*` | Persist decisions/patterns |
| `token-economy` (project) | Long sessions |
| `recursive-context-pruning-token-budgeting` | Bloated context |
| `context-optimization` / `filesystem-context` | Offload large dumps |
| RTK (global `@RTK.md`) | Compress noisy CLI when installed |
| `graphify` | Only on `/graphify` |

## Security / quality gates
| Skill | When |
|-------|------|
| `security-audit` / `007` | File I/O, path traversal, untrusted paths |
| `code-review-checklist` | Pre-merge |
| `find-bugs` | Branch audit |
| `vibe-code-auditor` | After large AI-generated chunks |

## Recommended MCPs (optional)
Do not hard-require. Examples: `.mcp.example.json`, `.grok/mcp.example.toml`.

| MCP | Use |
|-----|-----|
| **filesystem** (repo-scoped) | Safe file ops within project root |
| **git** | Branches, status, log helpers |
| **context7** | Fresh PyQt6 / Qt / pytest docs |
| **sequential-thinking** | PLAN trade-offs (piece table vs rope, etc.) |
| **github** | PRs/issues (token via env only) |
| **memory** | Cross-session; prefer `.memory/` for ADRs |

## Plugins / host config
| Host | Suggested |
|------|-----------|
| Grok | `.grok/config.toml` + roles; skills from `.agents/skills/` |
| Claude Code | `CLAUDE.md` + `.claude/settings.json`; skills catalog |
| Cursor | `.cursor/rules/magiceditor.mdc` |
| VS Code / Copilot | `.github/copilot-instructions.md` + Ruff/Python |
| CI | `.github/workflows/ci.yml` (ruff + core tests) |

## Anti-patterns
- Loading 10+ skills “just in case”
- Pasting full architecture into every prompt (route instead)
- UI skills for pure `core/` algorithms
- Implementing features without reading the matching scoped `AGENTS.md`
- Growing `main_window.py` / `virtual_editor.py` past SRP limits
