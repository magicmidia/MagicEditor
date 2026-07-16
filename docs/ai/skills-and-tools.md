# Skills, MCPs & Plugins — MagicEditor

Use this catalog when starting a task. Load **only** the skills that match the current work (token hygiene).

## Model routing first
Before picking skills, pick **phase/effort**: `docs/ai/model-routing.md`.

| Phase | Effort | Skills OK to load |
|-------|--------|-------------------|
| PLAN (HIGH) | xhigh/high | `brainstorming`, `writing-plans`, `architecture*` |
| BUILD (MEDIUM) | medium | `test-driven-development`, `python-pro`, `clean-code` |
| VERIFY (LOW) | low | `lint-and-validate`, `verification-before-completion` (run cmds) |
| REVIEW (HIGH) | high | `requesting-code-review`, `find-bugs`, `code-review-checklist` |

Grok agents/roles: `me-plan`, `me-build`, `me-verify`, `me-review` under `.grok/`.

## Always-on mindset
| Concern | Prefer |
|---------|--------|
| Isolation | `using-git-worktrees` for feature branches under `.worktrees/` |
| Spec before code | PLAN (HIGH) → `writing-plans` → BUILD (MEDIUM) |
| Core correctness | `test-driven-development` on BUILD; VERIFY on LOW |
| Token cost | Model routing + `AGENTS.md` file routing + `.memory/`; no full architecture re-read |
| Code quality | REVIEW on HIGH; `clean-code` on BUILD |
| Anti-bloat | `moyu`, `andrej-karpathy`, `code-simplifier` |

## Superpowers / delivery loop
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
| `impeccable` | UI polish, hierarchy, empty states, settings |
| `ui-ux-designer` | Layout/IA for main window, docks, toolbars |
| `product-design` | Design tokens, visual system for QSS themes |
| `accessibility-compliance-accessibility-audit` | Keyboard, contrast, focus order |
| `motion-design` | Subtle transitions only (prefer snappy desktop feel) |
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
| Hierarchical routing (`AGENTS.md`) | Every session — load scoped files only |
| `.memory/*` | Persist decisions/patterns; don't re-derive |
| `recursive-context-pruning-token-budgeting` | Long sessions, bloated context |
| `context-optimization` / `filesystem-context` | Offload large dumps to files |
| RTK (global `@RTK.md`) | Compress noisy CLI output when installed |
| `zipai-optimizer` | Dense intermediate notes |
| `graphify` | Only on `/graphify` — knowledge graph of repo |

## Security / quality gates
| Skill | When |
|-------|------|
| `security-audit` / `007` | File I/O, path traversal, untrusted paths |
| `code-review-checklist` | Pre-merge |
| `find-bugs` | Branch audit |
| `vibe-code-auditor` | After large AI-generated chunks |

## Recommended MCPs (optional)
Install only if the agent host supports them; do not hard-require.

| MCP | Use |
|-----|-----|
| **filesystem** (scoped to repo) | Safe file ops within project root |
| **git** / GitHub | Branches, PRs, reviews |
| **memory** / mesh-memory | Cross-session project memory (if not using `.memory/`) |
| **sequential-thinking** | Hard architecture trade-offs (piece table vs rope) |
| **context7** / docs MCP | Fresh PyQt6 / Qt docs without web scrape noise |

Project-local suggestion file: `.mcp.example.json` (copy to host-specific config; never commit secrets).

## Plugins / host config
| Host | Suggested |
|------|-----------|
| Claude Code | Project `CLAUDE.md` + skills above; worktrees; hooks for ruff if desired |
| Cursor | `.cursor/rules/magiceditor.mdc` (points at `AGENTS.md`) |
| Grok / Codex | Root `AGENTS.md` as primary |
| VS Code | Python + Ruff extension; pytest; Qt offscreen for CI |

## Anti-patterns
- Loading 10+ skills “just in case”
- Pasting full architecture into every prompt (route instead)
- UI skills for pure `core/` algorithms
- Implementing features without reading the matching scoped `AGENTS.md`
