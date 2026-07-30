---
name: superpowers
description: Use when tackling complex architectural designs, debugging deep system crashes, performing comprehensive code refactoring, or applying advanced chain-of-thought engineering workflows. Supercharges the agent with deep analytical logic, systematic problem solving, and advanced self-correction loops.
---

# Superpowers Skill

This skill supercharges the agent with advanced engineering workflows, rigorous logical reasoning, and systemic discipline. Use these guidelines when executing difficult tasks, designing core logic, or investigating complex bugs.

## 1. Architectural Planning & Spec-First Design
- **No Rushing to Code**: Before touching any code in a medium/high-effort task, outline the architecture, data flow, and interfaces.
- **Trace the Boundaries**: Ensure clear separation of concerns (e.g., separating core logic from UI layers, ensuring UI is thin, and business rules remain in `core/`).
- **Define Contracts**: Explicitly list function signatures, input/output types, and data structures before implementing them.

## 2. Test-Driven Development (TDD) Mindset
- **Write Tests First**: For core components and pure logic, write failing unit tests first.
- **Verify Coverage**: Run pytest and verify that edge cases (null values, boundary sizes, unexpected types) are fully covered.
- **Isolate Qt**: Keep tests for `core/` pure and runnable without a display or Qt dependencies. Use headless testing (`QT_QPA_PLATFORM=offscreen`) only when validating UI layers.

## 3. Systematic Debugging Protocol
When hit with a bug, crash, or failing test:
1. **Hypothesis Formulation**: State 2-3 logical hypotheses of what could be causing the issue.
2. **Isolate & Test**: Write a minimal test or run a target command to verify or discard each hypothesis one by one.
3. **Root Cause Analysis**: Address the core underlying issue instead of adding quick "patches" or "if" guards that clutter the codebase.
4. **Regression Prevention**: Add a test that explicitly triggers the previously failing scenario to ensure it never returns.

## 4. Multi-Agent Delegation & Task Splitting
- **Divide and Conquer**: Split large projects into independent, modular sub-tasks.
- **Subagent Routing**: Spawn specialized subagents (e.g., `research` or `self`) to execute independent research or validation tasks in parallel.
- **Context Isolation**: Pass only the necessary files and context to subagents to conserve tokens and prevent clutter.
- **Handoff Quality**: Write extremely clear, actionable, and precise prompts for subagents.

## 5. Verification Checklist (Before Delivery)
Always run the following verification steps before claiming a task is done:
- **Linting**: Run `uv run ruff check path/to/file.py` and fix any errors.
- **Formatting**: Run `uv run ruff format path/to/file.py`.
- **Type Checking**: Run `uv run mypy path/to/file.py` and ensure zero type errors in the modified files.
- **Test Suite**: Run the unit tests related to your changes to ensure no regression.
