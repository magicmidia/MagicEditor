# Model routing (always on)

Follow `docs/ai/model-routing.md` and `docs/ai/model-routing.json`.

| Phase | Effort | Agent/role |
|-------|--------|------------|
| Plan | `xhigh` or `high` | `me-plan` |
| Build | `medium` | `me-build` |
| Verify | `low` | `me-verify` |
| Review | `high` | `me-review` |

Before heavy work: classify the phase and match the tier.  
Do not use HIGH for pytest/lint. Do not design core algorithms on LOW.  
Single-agent sessions: use `/effort <level>` when switching phases.
