# MagicEditor

Editor de texto e código para o desktop (Python 3.12+, PyQt6). A viewport mostra só o trecho visível, o texto fica numa piece table e arquivos grandes são lidos com mmap, sem carregar o arquivo inteiro na memória.

**Versão:** 0.9.8 ([Semantic Versioning](docs/VERSIONING.md)). O rótulo BETA na interface é o canal da versão, não faz parte do número.

[Novidades](docs/CHANGELOG.md) · [Documentação](docs/README.md) · [Arquitetura](docs/magiceditor-architecture.md) · [Releases](https://github.com/magicmidia/MagicEditor/releases)

## O que o editor faz

- Abas, sessão e recuperação do texto não salvo se o processo cair (o arquivo no disco não é sobrescrito)
- Pré-visualização de Markdown, com impressão dessa visualização
- Hashes do arquivo ativo: MD5, SHA-1, SHA-256, SHA-384, SHA-512 e BLAKE2b
- Temas, três idiomas (pt_BR, en_US, es_ES) e corretor ortográfico
- Busca no arquivo e na pasta, impressão e PDF do código-fonte

A lista completa de cada versão está em [docs/CHANGELOG.md](docs/CHANGELOG.md) e, dentro do programa, em **Ajuda → Novidades**.

## Instalar no Windows

O instalador publicado fica em [Releases](https://github.com/magicmidia/MagicEditor/releases): `MagicEditor-<versão>-win64-setup.exe`.

Para gerar o pacote nesta máquina:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Inno
```

Os binários saem em `dist/` e não entram no git. Detalhes em [docs/BUILD.md](docs/BUILD.md).

## Rodar a partir do código

```powershell
uv sync --all-extras
uv run magiceditor
```

Testes e lint: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Mapa do repositório

| Caminho | Função |
|---------|--------|
| `src/magiceditor/core/` | Buffer, índice de linhas e busca. Sem PyQt |
| `src/magiceditor/ui/` | Janela, abas e viewport |
| `src/magiceditor/services/` | Sessão, impressão, recuperação |
| `src/magiceditor/preview/` | Markdown e HTML |
| `src/magiceditor/themes/` | Temas |
| `src/magiceditor/i18n/` | Tradução em tempo real |
| `locales/` | `pt_BR.json`, `en_US.json`, `es_ES.json` |
| `resources/themes/` | Folhas QSS |
| `docs/` | Documentação. Índice em [docs/README.md](docs/README.md) |
| `.github/workflows/` | Testes em cada push e instalador a cada tag `vX.Y.Z` |

## Versão e entrega

Uma versão é `MAJOR.MINOR.PATCH`. Os três lugares que precisam concordar são `src/magiceditor/version.py`, `pyproject.toml` e o instalador Inno. O procedimento de bump, tag e release está em [docs/VERSIONING.md](docs/VERSIONING.md).

## Licença

[MIT](LICENSE). Ícones Qlementine em `resources/icons/qlementine/` têm a licença própria daquela pasta.
