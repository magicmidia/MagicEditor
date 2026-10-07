# MagicEditor

Editor de texto e código para o desktop. Python 3.12+ e PyQt6. O buffer é uma piece table em bytes, a tela pinta só as linhas visíveis e arquivos acima de 5 MiB são lidos com mmap.

**Versão no código:** 0.9.9 ([Semantic Versioning](docs/VERSIONING.md)). O rótulo BETA na interface é o canal de lançamento e não entra no número da versão.

[Novidades](docs/CHANGELOG.md) · [Documentação](docs/README.md) · [Arquitetura](docs/magiceditor-architecture.md) · [Desenvolvimento](docs/DEVELOPMENT.md) · [Empacotar](docs/BUILD.md) · [Releases](https://github.com/magicmidia/MagicEditor/releases)

O instalador publicado em Releases é o da tag `vX.Y.Z` daquele release. O que ainda não foi etiquetado fica em [docs/CHANGELOG.md](docs/CHANGELOG.md), na seção Unreleased, e também em **Ajuda → Novidades**.

## O que o editor faz

### Arquivos e edição

- Abas, sessão, arquivos recentes, favoritos e vários cursores (Ctrl+D, Alt+F3, Ctrl+clique).
- Seleção em coluna (Alt+arrastar), quebra de linha, guia de indentação, fechar parênteses e realce da ocorrência sob o cursor.
- Operações de linha: duplicar, mover, comentar, aparar, converter tabulação, ordenar, inverter e remover duplicadas.
- Correspondência de chaves e salto com Ctrl+M.
- Codificações e fim de linha. O texto inválido para a codificação do documento aparece como U+FFFD e o Backspace apaga o trecho de bytes inteiro que o codec rejeitou.
- Atalho de data e hora, transformações de texto (maiúsculas, Base64, URL) e estatísticas do documento, com teto em arquivos enormes.

### Arquivos grandes

| Limite | Comportamento |
|--------|----------------|
| Acima de 5 MiB | Leitura com mmap. A interface entra no modo de arquivo grande. |
| Acima de 20 MiB | O destaque de sintaxe é desligado. A tela continua pintando só o trecho visível. |
| Texto completo | Operações que precisam do documento inteiro como texto param em 2 MiB. |
| Busca na pasta | Ignora arquivo maior que 8 MiB, binário e diretórios de ferramenta (`.git`, `node_modules`, `.venv`, `dist`, `build`). |

A extensão escolhe a linguagem em `resources/syntax/extensions.json`. O destaque cobre linguagens comuns de código e marcação (Python, JavaScript, TypeScript, HTML, CSS, JSON, Markdown, C, C++, C#, Java, Go, Rust, SQL, shell, YAML e a família listada nesse mapa). Acima de 20 MiB esse destaque fica desligado.

### Busca, workspace e navegação

- Localizar e substituir no arquivo, com expressões regulares.
- Localizar na pasta, com cancelamento e progresso.
- Abrir rápido, paleta de comandos (Ctrl+Shift+P), ir para linha e símbolos.
- Minimapa, comparar arquivos e dividir a vista.
- Filtrar linhas para uma aba nova e uma lente de log que conta e navega por severidade.
- Recarregar (F5), revelar no explorador e copiar o caminho.

Padrões de busca do usuário recusam grupos quantificados que contêm outro quantificador, como `(a+)+`. A proteção é uma heurística: padrões caros de outra forma ainda podem existir. Não há limite de tempo na engine de expressões regulares.

### Markdown, impressão e hashes

- Pré-visualização de Markdown e de HTML dentro do programa. A folha de estilo do tema é aplicada como estilo do documento, então o CSS do editor não aparece como texto no meio da página.
- A mesma visualização de Markdown pode ser impressa à parte do código-fonte.
- Impressão e PDF do código-fonte.
- Hashes do arquivo ativo, em fluxo e sem carregar o arquivo inteiro: MD5, SHA-1, SHA-256, SHA-384, SHA-512 e BLAKE2b.

Abrir o HTML no navegador do sistema é outra ação. O programa avisa que os scripts da página vão executar lá.

### Aparência, idioma e sessão

- Temas em QSS, assistente de primeiro uso (idioma e tema) e exportar ou importar tema.
- Interface em português (`pt_BR`), inglês (`en_US`) e espanhol (`es_ES`).
- Corretor ortográfico nesses três idiomas, com dicionário do usuário e sugestões empacotadas.
- Configurações de fonte, tabulação, quebra de linha, espaçamento, margem direita, zoom com Ctrl+roda e salvamento automático (desligado por padrão).
- Recuperação de queda: o texto das abas não salvas vai para um arquivo de recuperação e volta na próxima abertura. O arquivo original no disco permanece como estava. Arquivos grandes não recebem esse texto de volta. Há no máximo 24 rascunhos, cada um com até 400 000 caracteres.

O editor trabalha na máquina local. A barra de status indica **Local only**. Não há telemetria.

## Segurança do que o programa abre

- A pré-visualização reescreve o HTML com uma lista de tags permitidas. Atributos são escapados. Links `javascript:`, URLs que começam com `//` ou `\\`, e um esquema escondido numa entidade HTML são descartados. Imagens remotas não são pedidas.
- A pré-visualização e a impressão do Markdown não carregam recurso remoto nem arquivo local pelo documento Qt. O CSS do tema entra pela folha de estilo padrão.
- Localizar na pasta e Abrir rápido não seguem link de diretório. Um arquivo cujo destino real fica fora da pasta aberta é ignorado. Link físico (hard link) para fora da pasta não é distinguível por esse teste. Abrir um pipe ou um dispositivo pelo diálogo de arquivo ainda pode bloquear a leitura; isso fica no mesmo usuário da máquina.
- O arquivo de recuperação é trocado por um temporário de nome único (`mkstemp`), para um `recovery.json.tmp` plantado como link não ser aberto para escrita.
- Uma segunda instância fala com a janela já aberta por um socket local do mesmo usuário (`QLocalServer`). Esse canal pede para abrir caminhos; ele não escuta na rede.

## Instalar no Windows

O pacote publicado é `MagicEditor-<versão>-win64-setup.exe`, em [Releases](https://github.com/magicmidia/MagicEditor/releases).

Para gerar o executável e o instalador nesta máquina:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Inno
```

Os binários saem em `dist/` e não entram no git. Outras saídas (`-Exe`, `-Portable`, `-Msi`, `-All`) estão em [docs/BUILD.md](docs/BUILD.md). O Windows é a plataforma empacotada. O código-fonte roda onde houver Python 3.12 e PyQt6.

Log do programa instalado: `%LOCALAPPDATA%\MagicEditor\MagicEditor.log`.

## Desenvolvimento

```powershell
uv sync --all-extras
uv run magiceditor
```

| Tarefa | Comando |
|--------|---------|
| Lint de um arquivo | `uv run ruff check caminho/arquivo.py` |
| Formatar um arquivo | `uv run ruff format caminho/arquivo.py` |
| Teste de um arquivo | `uv run pytest tests/caminho/test_x.py -q` |
| Interface sem tela | `$env:QT_QPA_PLATFORM = "offscreen"` antes do pytest |

O dia a dia está em [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md). O núcleo em `src/magiceditor/core/` não importa PyQt6.

## Mapa do repositório

| Caminho | Função |
|---------|--------|
| `src/magiceditor/core/` | Piece table, índice de linhas, busca, codificação, sintaxe e hashes. Sem Qt |
| `src/magiceditor/ui/` | Janela, abas, viewport e diálogos |
| `src/magiceditor/services/` | Sessão, disco, impressão, recuperação e escopo de pasta |
| `src/magiceditor/preview/` | Markdown e HTML, com o filtro de marcação |
| `src/magiceditor/themes/` | Carga e troca de temas |
| `src/magiceditor/i18n/` | Tradução em tempo de execução |
| `locales/` | `pt_BR.json`, `en_US.json`, `es_ES.json` |
| `resources/themes/` | Folhas QSS |
| `resources/syntax/extensions.json` | Extensão de arquivo para linguagem |
| `docs/` | Índice em [docs/README.md](docs/README.md) |
| `.github/workflows/` | Testes em cada push e pacote Windows a cada tag `vX.Y.Z` |

## Versão

Uma versão é `MAJOR.MINOR.PATCH`. Antes de 1.0.0, uma versão menor pode incluir mudança incompatível. Estes três lugares precisam concordar:

- `src/magiceditor/version.py` (`VERSION`)
- `pyproject.toml`
- `MyAppVersion` no instalador Inno

O procedimento de bump, tag e release está em [docs/VERSIONING.md](docs/VERSIONING.md).

## Licença

[MIT](LICENSE). Os ícones Qlementine em `resources/icons/qlementine/` seguem a licença daquela pasta.
