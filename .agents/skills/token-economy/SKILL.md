---
name: token-economy
description: Use to optimize token usage, manage context windows efficiently, prune history, compress data, and avoid reading large files repeatedly. Essential for long conversations or when handling large codebases.
---

# Token Economy & Context Optimization Skill

This skill provides strategies and guidelines for maintaining a clean context window, reducing latency, and keeping token costs to a minimum while maintaining maximum intelligence and correctness.

## 1. Context Hygiene & Lazy Loading
- **Load Only What You Need**: Strictly follow the file-scoped command and context routing table in `AGENTS.md`. Never read a whole directory or broad module unless strictly necessary.
- **Do Not Re-Read Files**: Avoid calling `view_file` on the same file multiple times in the same conversation session. Trust your memory of the file's content unless it has been modified.
- **Avoid Massive File Dumps**: For files larger than 10MB (or logs with thousands of lines), do not read the entire file. Use targeted `grep_search` or read specific line ranges (`StartLine` and `EndLine`).

## 2. Model Routing & Phase Alignment
- **Set Esforço (Effort) Properly**: Follow the model routing protocol (`PLAN → BUILD → VERIFY → REVIEW`).
  - Use **LOW** effort (Vite/Ruff/tests) for simple lookups, linting, formatting, or test executions.
  - Use **MEDIUM** effort for building features based on a plan.
  - Reserve **HIGH** or **XHIGH** effort only for complex architectural planning and critical quality reviews.
- **Limit Spawn Depth**: When invoking subagents, keep the spawn depth strictly under 2, and avoid nested HIGH effort subagents.

## 3. Command Output Compression
- **Noisy Terminals**: When running tests or commands that produce long outputs (e.g., git logs, pip updates), limit the output. For example:
  - Use `git log -n 5` instead of `git log`.
  - Filter test output to show only failures (e.g., `pytest -q` or targeted test node runs).
- **Trimming Stack Traces**: Do not copy-paste hundreds of lines of stack traces. Focus on the file path, line number, exception type, and the exact failing assertion.

## 4. Reusable Project Memory (`.memory/`)
- **Avoid Architecture Re-Reading**: Instead of reading the entire `magiceditor-architecture.md` file repeatedly, refer to `.memory/decisions.md` (ADRs) and `.memory/patterns.md`.
- **Update Memory Promptly**: When a key architectural decision is made or a complex pattern is successfully solved, document it briefly in `.memory/decisions.md` or `.memory/patterns.md` so future runs don't need to re-derive it from scratch.

## 5. Subagent Efficiency
- **Sparse Prompts**: When launching a subagent, keep the prompt concise and actionable.
- **Targeted Workspace**: Prefer inheriting workspaces (`inherit`) to avoid storage overhead and redundant indexing unless isolation is strictly required (use `share` or `branch` carefully).
- **Communication Focus**: Use `send_message` strictly for status updates, instructions, and results. Do not exchange conversational fluff.
