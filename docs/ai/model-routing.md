# Model Routing — MagicEditor

**Goal:** long, high-quality coding stretches at **lower token cost** by matching *reasoning effort* (or model tier) to the *phase* of work.

Host primary mapping is **Grok Build** (`/effort`, roles, subagents). Equivalents for Claude/Cursor are listed below.

## Tiers

| Tier ID | Effort (Grok) | When to use | Not for |
|---------|---------------|-------------|---------|
| **HIGH** | `xhigh` if available, else `high` | Planning, architecture, ambiguous design, adversarial **review** | Running pytest, renaming symbols, formatting |
| **MEDIUM** | `medium` | Implementing features, multi-file code, refactors with clear plan | Greenfield architecture without a plan; pure test runs |
| **LOW** | `low` | Tests, lint/format, mechanical fixes, file moves, status updates, small exec | Security review, core data-structure design |

**Rule of thumb:** if the task is *decide what/why*, use HIGH. If *write the code*, use MEDIUM. If *check it ran*, use LOW.

## Pipeline (default for any non-trivial feature)

```
PLAN (HIGH) → BUILD (MEDIUM) → VERIFY (LOW) → REVIEW (HIGH)
     ↓              ↓               ↓              ↓
  me-plan       me-build       me-verify      me-review
  read-only      write+run       execute       read-only*
```

\* Reviewer may write review notes only (`docs/` or `.memory/`), not production code.

### Phase contracts

#### 1. PLAN — HIGH (`xhigh`/`high`)
- Inputs: user goal, `docs/magiceditor-architecture.md`, `docs/STATUS.md`, scoped `AGENTS.md`
- Outputs: short plan (files to touch, tests, risks, non-goals)
- Tools: read/search; **no product code edits**
- Stop if blocked on a product decision → ask user

#### 2. BUILD — MEDIUM
- Inputs: approved/implicit plan
- Outputs: code + minimal docs only if required
- Follow `docs/ai/coding-standards.md`; keep modules ≤300 LOC
- Do **not** re-plan architecture unless build reveals a hard conflict

#### 3. VERIFY — LOW
- Inputs: list of changed paths
- Commands: file-scoped ruff/pytest (see root `AGENTS.md`)
- Outputs: pass/fail + log snippet; fix only trivial breakages (import typos). Larger failures → escalate to MEDIUM

#### 4. REVIEW — HIGH
- Inputs: diff / changed files, plan, test results
- Outputs: findings (bugs, SRP violations, huge-file policy, security)
- No drive-by refactors; open issues only

## Grok Build wiring

### Session effort (single agent)

```text
/effort xhigh   # or high — planning / review turns
/effort medium  # implementation turns
/effort low     # test/lint/mechanical turns
```

Also: `/model Reasoning X high` when selecting model+effort together.

### Project roles (spawn / resolve)

| Role | Effort | Capability | Purpose |
|------|--------|------------|---------|
| `me-plan` | xhigh | read-only | Architecture & plans |
| `me-build` | medium | all | Implementation |
| `me-verify` | low | execute (+ read) | Tests & lint |
| `me-review` | high | read-only | Code review |

Defined under `.grok/roles/` and mirrored in `.grok/config.toml`.

### Spawn guidance (parent agent)

When using `spawn_subagent`:

| Task class | `subagent_type` / role | `capability_mode` | Effort |
|------------|------------------------|-------------------|--------|
| Plan / design | `plan` or `me-plan` | `read-only` | HIGH |
| Implement | `general-purpose` or `me-build` | `all` | MEDIUM |
| Run tests / lint | `me-verify` | `execute` | LOW |
| Review | `me-review` | `read-only` | HIGH |
| Explore only | `explore` | `read-only` | LOW–MEDIUM |

**Cost caps**
- Prefer **one** HIGH plan per feature, not per file
- Prefer **one** HIGH review at the end of a coherent unit of work
- Batch VERIFY (all touched tests in one LOW pass)
- Do not nest HIGH subagents under HIGH parents
- Max spawn depth: 2

## Cross-host equivalents

| Tier | Grok | Claude Code | Cursor / generic |
|------|------|-------------|------------------|
| HIGH | effort `xhigh`/`high` | Opus / strongest | strongest available |
| MEDIUM | effort `medium` | Sonnet | default coding model |
| LOW | effort `low` | Haiku | fast/light model |

## Orchestrator checklist (every multi-step task)

1. [ ] Classify phase → set tier **before** heavy tool use  
2. [ ] Load only routed context (`AGENTS.md` table)  
3. [ ] PLAN if design is ambiguous or multi-module  
4. [ ] BUILD on medium  
5. [ ] VERIFY on low with file-scoped commands  
6. [ ] REVIEW on high before “done” / commit of large units  
7. [ ] Log phase + tier in session notes if useful (`.memory/inbox.md`)

## Anti-patterns

- Coding a new core algorithm on LOW  
- Running full-repo pytest on HIGH  
- Re-reading the entire architecture doc on every MEDIUM turn  
- Spawning parallel HIGH reviewers for the same diff  
- Using HIGH for “fix the typo / rename the variable”

## Related files

- Machine-readable: `docs/ai/model-routing.json`
- Roles: `.grok/roles/me-*.toml`
- Agents: `.grok/agents/me-*.md`
- Personas: `.grok/personas/me-*.toml`
- Always-on rule: `.grok/rules/model-routing.md`
