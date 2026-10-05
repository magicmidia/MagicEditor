## O que muda

<!-- Uma frase sobre o comportamento que o usuário vê. -->

## Checklist

- [ ] `docs/CHANGELOG.md` tem uma entrada em `## [Unreleased]` ou na versão que este PR entrega
- [ ] Se a versão mudou: `version.py`, `pyproject.toml` e `MyAppVersion` continuam iguais (`uv run python scripts/check_release_version.py`)
- [ ] Testes do módulo alterado passaram
- [ ] Sem binários (`dist/`, `.exe`, `.msi`, `.zip`)
