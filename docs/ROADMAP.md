# MagicEditor — Roadmap de excelência (competitivo + produto premium)

**Atualizado:** 2026-08-17  
**Fontes:** Notepad++, Windows Notepad, Sublime Text, Adobe Brackets / Phoenix Code, VS Code, WordPad (legado), práticas de mercado 2024–2026, critérios de “produto de excelência” (polish, performance, distribuição).

Este documento inventaria funcionalidades e vantagens dos editores do “tipo MagicEditor”, cruza com o estado atual do produto e define **ondas de entrega** com critérios de aceite.  
**Fonte de verdade do backlog:** este arquivo. **O que está feito agora:** `docs/STATUS.md`.

---

## 0. Norte de produto (excelência)

O MagicEditor não compete como IDE completa (LSP/debug/Git full). Compete como:

1. **Editor diário premium** — sensação de app de 1ª linha (chrome, tipografia, feedback, zero “caixa genérica”).
2. **Motor de huge files** — abrir, rolar, buscar e editar logs/SQL de GB sem travar a UI.
3. **Produtividade de texto/código** — multi-cursor, palette, ortografia, line ops, session sólida.
4. **Windows-first delivery** — EXE one-file, portable ZIP e instalador MSI com associações, atalhos e first-run (idioma/tema).

**Princípios de qualidade (não negociáveis)**
| Princípio | Critério |
|-----------|----------|
| UI thin / core pure | `core/` sem PyQt6; widgets sem I/O de política |
| Huge files | Nunca `str`/`QTextDocument` completo >50MB; highlight só no range visível >20MB |
| Responsividade | Busca/I/O em worker; cancelável; status de progresso |
| Densidade & gosto | Design system `docs/DESIGN.md` + skill design-taste; sem “AI slop” |
| i18n | Toda string de UI em locales (`pt_BR` / `en_US` / `es_ES`+) |
| Módulos enxutos | Preferir ≤300 LOC; extrair antes de inflar `main_window` / `virtual_editor` |
| Release limpa | Artefatos só em `dist/` (gitignored); versionamento a partir de `pyproject.toml` |

---

## 1. Matriz competitiva (resumo)

| Área | Notepad++ | Notepad (Win) | Sublime Text | Brackets / Phoenix | VS Code | MagicEditor (hoje) |
|------|-----------|---------------|--------------|--------------------|---------|---------------------|
| Abas multi-doc | Excelente | Básico | Excelente | Bom | Excelente | Bom |
| Arquivos gigantes | Bom (streaming) | Fraco | Bom | Fraco | Médio | **Forte** (mmap + viewport) |
| Multi-cursor / coluna | Coluna nativa | Não | **Referência** | Limitado | Multi-cursor | Parcial (seleção) |
| Busca / regex | Excelente | Básica | Excelente | Boa | Excelente | Boa |
| Syntax highlight | 80+ langs | Não | Excelente | Web-first | Excelente | Bom (muitas langs) |
| Explorer lateral | Plugin | Não | Sidebar | Sim | Excelente | Sim |
| Preview MD/HTML | Plugin | Não | Plugin | **Live Preview** | Bom | Sim (split) |
| Temas | Styles Configurator | Claro/escuro | Excelente | Bom | Excelente | **10 temas QSS** |
| i18n UI | Sim | SO | Limitado | Sim | Excelente | pt/en/es |
| **Correção ortográfica** | Plugin | Básica | Packages | Limitado | Extensão / built-in | **Sim** (viewport pt/en/es) |
| Macros | Sim | Não | Snippets | Extensões | Extensões | Não |
| Compare files | Plugin | Não | Diff packages | Não | Diff nativo | **Sim** |
| Hex / binário | Sim | Não | Packages | Não | Extensão | Não |
| Minimap | Não | Não | **Sim** | Não | Sim | **Sim** |
| Command palette | Não | Não | **Ctrl+Shift+P** | Limitado | **Ctrl+Shift+P** | **Ctrl+Shift+P** |
| Session restore | Sim | Sim | Sim | Sim | Excelente | Sim (+ drafts) |
| Leveza / RAM | **Muito leve** | Mínimo | Leve | Médio | Pesado | Médio-leve |
| Impressão limpa | Razoável | Simples | Limitado | Limitado | Extensão | **Forte** (clean print) |
| Instalador + file assoc. | Excelente | SO | Bom | Bom | Excelente | MSI ProgID + Inno setup |

**Diferenciais já do MagicEditor:** piece table + mmap + virtual viewport; impressão/PDF “clean”; Luminous Void + GPU/transparência; drafts de Untitled; i18n JSON; packaging scripts (`scripts/build.ps1`).

---

## 2. Inventário por editor (detalhado)

### 2.1 Notepad++ (paridade “clássica” diária)

**Abas e janelas**
- Abas múltiplas, reordenar, fechar com meio, fechar outras/todas  
- **Duplo clique na barra de abas → novo arquivo**  
- Duplicar aba, mover para outra vista, sessão  
- Document Map (minimap-like via plugin), Doc Switcher  

**Edição**
- Column / block mode (Alt+arrastar)  
- Multi-edição aprimorada (plugins BetterMultiSelection)  
- Operações de linha: mover, duplicar, ordenar, juntar, remover vazias  
- Blank operations: trim, tabs↔spaces  
- Comentário de bloco/linha por linguagem  
- Auto-indent, auto-complete de palavra/função  
- Macros graváveis + atalhos  
- **Spell check via plugins** (DSpellCheck)

**Navegação / busca**
- Find/Replace, Find in Files, Mark, Incremental search  
- Regex PCRE, filtros de extensão  
- Go to line, bookmark (toggle/next/prev/clear)  
- Function List (símbolos)  

**Arquivo / encoding**
- Encoding convert, EOL convert, BOM  
- Reload, rename, open containing folder  
- Read-only, autosave (plugin)  
- Compare (plugin), FTP (plugin)  

**Visual**
- Line numbers, wrap, highlight matching braces  
- Zoom, fullscreen, hide menu/toolbar  
- Style Configurator (syntax colors)  

**Vantagem N++:** leveza + macros + coluna + ecossistema de plugins Windows-first + instalador maduro.

### 2.2 Windows Notepad (moderno)

- Abas simples, sessão de tabs, auto-save rascunhos  
- Dark mode, status bar, busca básica  
- Ortografia do SO em alguns contextos  
- **Vantagem:** zero fricção, instantâneo  

### 2.3 Sublime Text 2/3/4

- **Multi-cursor** (Ctrl+D, Alt+F3, Ctrl+click, coluna)  
- **Command Palette** (Ctrl+Shift+P)  
- **Goto Anything** (Ctrl+P) — arquivos + @símbolos + :linha  
- Minimap com viewport highlight  
- Split panes / layouts, Project / workspace  
- Snippets, macros, Vintage mode  
- Packages de spell check  
- **Vantagem:** velocidade de edição multi-cursor + palette + goto unificado  

### 2.4 Brackets → Phoenix Code

- **Live Preview** HTML/CSS no browser com sync  
- Inline editors, extract / quick edit  
- **Vantagem:** feedback visual imediato para front-end  

### 2.5 VS Code (referência “moderno”)

- IntelliSense, LSP, debug, Git, terminal  
- Multi-cursor, palette, quick open, settings UI  
- Spell check (built-in / Code Spell Checker)  
- Diff, merge, extensions marketplace  
- **Vantagem:** plataforma completa — MagicEditor **não** replica IDE; absorve só UX de excelência  

### 2.6 WordPad / editores ricos (referência negativa)

- Formatação rich-text (fora de escopo código)  
- MagicEditor permanece **plain text / code-first** com **ortografia em prosa** (MD/TXT), não rich-text  

---

## 3. Gap analysis — MagicEditor vs meta de excelência

| Feature | Prioridade | Status | Nota |
|---------|------------|--------|------|
| Duplo clique barra → nova aba | P0 | ✅ Feito | STATUS 2026-07-30 |
| Ícones toolbar/menu modernos | P0 | ✅ Feito | Qlementine + Material opcional |
| Diálogos (Sobre, mensagens) premium | P0 | ✅ Feito | About custom + QSS |
| Multi-cursor / column mode | P1 | ✅ Feito | Sublime/N++ killer feature |
| Command palette | P1 | ✅ Feito | Ctrl+Shift+P |
| Minimap | P2 | ✅ Feito | Sublime/VS Code |
| Operações de linha (sort, join, delete blank) | P1 | ✅ Feito | Menu Edit + atalhos |
| Tabs↔spaces / trim trailing | P1 | ✅ Feito | N++ blank ops |
| Comentário toggle | P1 | ✅ Feito | Por linguagem |
| Brace match highlight | P1 | ✅ Feito | |
| **Correção ortográfica** | **P1** | **✅ Feito** | TXT/MD; dicionários pt/en/es; ignore list |
| Auto-complete palavras do doc | P2 | ✅ Feito | opt-in |
| Compare two files | P2 | ✅ Feito | |
| Function/symbol list | P2 | ✅ Feito | symbols + outline |
| Macros | P3 | Falta | fora do recorte J–N |
| Hex editor | P3 | Falta | fora do recorte J–N |
| Split editor panes | P2 | ✅ Feito | dock snapshot |
| Reload from disk / external change | P1 | ✅ Feito | |
| Open folder in explorer / copy path | P1 | ✅ Feito | |
| Autosave interval | P2 | ✅ Feito | |
| Settings UI mais completa | P1 | ✅ Feito | fonte, tab, wrap, spell, GPU |
| First-run wizard (idioma + tema) | P1 | ✅ Feito | Instalador + 1ª execução |
| File associations / “Open with” | P1 | ✅ Feito | MSI ProgIDs + opt-in |
| Plugin API | P3 | Fora MVP | |
| Telemetria | — | Não | Privacy by default |

---

## 4. Roadmap por ondas (fases)

### Onda A — Polish diário ✅ CONCLUÍDA
**Objetivo:** sensação de produto acabado na base.

| ID | Item | Aceite | Status |
|----|------|--------|--------|
| A1 | Duplo clique na **tab bar** cria Untitled | Área vazia / corner → novo doc | ✅ |
| A2 | Ícones **Qlementine / Material** + por linguagem | Settings switch; tabs com tipo | ✅ |
| A3 | Diálogo **Sobre** custom | Monograma M, versão, links | ✅ |
| A4 | QSS de `QMessageBox` / `QDialog` densos | Botões, cantos, tipografia | ✅ |
| A5 | Roadmap + STATUS sincronizados | docs/ | ✅ (manter em cada onda) |

---

### Onda B — Edição poderosa
**Objetivo:** paridade de “mãos no teclado” com N++/Sublime.

| ID | Item | Inspiração | Aceite |
|----|------|------------|--------|
| B1 | Column selection (Alt+drag) | N++ | Retângulos de seleção; digitar em coluna |
| B2 | Multi-cursor básico (Ctrl+D, Esc clear) | Sublime | Add next match; status mostra N cursores |
| B3 | Line ops: move up/down, sort, join, delete blank | N++ | Menu Edit + atalhos; undo unitário |
| B4 | Toggle comment | Todos | `//` `#` `/* */` por `language_id` |
| B5 | Trim trailing + tabs↔spaces | N++ | Doc inteiro ou seleção; huge-file safe (chunks) |
| B6 | Matching braces / tags highlight | N++ / ST | Gutter ou underline no pair visível |

**Performance na onda:** operações de edição em piece table sem materializar o arquivo inteiro.

---

### Onda C — Navegação moderna
**Objetivo:** achar e comandar qualquer coisa em &lt;1 s de fricção.

| ID | Item | Inspiração | Aceite |
|----|------|------------|--------|
| C1 | Command Palette (mover Preview de Ctrl+Shift+P) | ST / VS Code | Fuzzy commands + i18n labels |
| C2 | Goto Anything unificado (arquivo + :linha + #heading) | ST | Um diálogo; scopes claros |
| C3 | Minimap | ST / VS Code | Só viewport; desliga em huge files se custo alto |
| C4 | Symbol list (funções) por linguagem | N++ Function List | Regex/lexer leve; não full AST |
| C5 | Reload if changed on disk | Todos | Prompt dirty/clean; watcher + botão |

---

### Onda D — Workspace & produtividade
**Objetivo:** fluxo diário de projeto sem IDE pesada.

| ID | Item | Aceite |
|----|------|--------|
| D1 | Open containing folder / Copy path / Reveal | Menu contexto aba + File |
| D2 | Autosave + backup interval | Settings; drafts já existentes complementam |
| D3 | File compare (side-by-side) | Dois buffers, scroll sync opcional |
| D4 | Split view (2 editores) | Horizontal/vertical; foco por atalho |
| D5 | Settings page completa | Fonte, tab width, wrap, theme, lang, spell, GPU |
| D6 | Export / import theme | JSON ou QSS bundle documentado |

---

### Onda E — Diferenciação MagicEditor
**Objetivo:** o que só o ME faz bem.

| ID | Item | Aceite |
|----|------|--------|
| E1 | Huge-file search progress UI + cancel | Barra + botão cancel; não bloqueia paint |
| E2 | MagicCloud sync real (hoje placeholder) | Escopo mínimo documentado ou remover placeholder |
| E3 | Live HTML preview no browser (Brackets-style) | Opcional; default continua split interno |
| E4 | Performance dashboard | Lines, mmap, GPU, mem approx; Help ou Tools |
| E5 | Portable mode (config ao lado do exe) | Detectar `portable.ini` ou pasta `config/` |

---

### Onda F — UI de excelência (polish profundo)
**Objetivo:** interface **completa, coerente e premium** — não só “funciona”.

| ID | Item | Aceite |
|----|------|--------|
| F1 | **Design tokens unificados** em todos os temas | Roles canvas/surface/border/text/muted/accent/select documentados e aplicados |
| F2 | **Empty states & first paint** | Untitled welcome sutil (sem spam); zero layout jump |
| F3 | **Focus rings, hover, active** consistentes | Teclado-first; contraste WCAG AA em textos UI |
| F4 | **Scrollbars, splitter, dock chrome** | Espessura/hover iguais; sem artefatos em glass |
| F5 | **Status bar rica** | Ln/Col, sel chars, encoding, EOL, lang, spell on/off, mmap badge se huge |
| F6 | **Toolbar configurável** | Mostrar/ocultar; ícones 18–20px ópticos iguais |
| F7 | **Settings com live preview** | Mudar tema/fonte/idioma sem reiniciar (retranslate) |
| F8 | **Onboarding first-run** | Wizard 1 tela: idioma + tema + “abrir arquivos com ME?” (só se instalado) |
| F9 | **Acessibilidade** | High-contrast opcional; atalhos listados em Help; scale UI 100/125/150 se viável |
| F10 | **Microcopy i18n** | Zero string hard-coded em menus/diálogos novos |

**Critério de “UI excelente”:** review visual com skill `design-taste` + checklist em `docs/DESIGN.md`; screenshots de Luminous Void + Clean Light.

---

### Onda G — Inteligência de texto & funcionalidades avançadas
**Objetivo:** além de código — prosa, qualidade de escrita e power-user.

#### G1 — Correção ortográfica (P1, feature âncora)

| Sub | Item | Detalhe técnico (proposta) |
|-----|------|----------------------------|
| G1.1 | Engine de dicionário | Preferir **Hunspell** (ou wrapper estável) com dicionários empacotados ou download opcional; fallback: filtro leve se engine indisponível |
| G1.2 | Escopo por linguagem | **On** default: `plaintext`, `markdown`, `restructuredtext`, commits; **Off** default: código (`python`, `js`, …) |
| G1.3 | Underline squiggle | Só no **viewport visível** (mesma disciplina do syntax highlight) |
| G1.4 | Contexto menu | Ignore word / Add to user dict / Change language |
| G1.5 | Idiomas | `pt_BR`, `en_US`, `es_ES` no mínimo; alinhados ao i18n da UI |
| G1.6 | Performance | Huge files: spell **somente range visível + margem**; nunca escanear GB inteiro |
| G1.7 | Settings | Toggle global, idioma do doc, “check while typing”, dicionário do usuário em `%AppData%` |

**Aceite G1:** em `README.md` / About: “Spell check”; testes unitários do tokenizer/word-break; pytest de ignore list; UI com indicador na status bar.

#### G2 — Demais avançados

| ID | Item | Aceite |
|----|------|--------|
| G2.1 | Word completion (doc vocabulary) | Popup discreto; opt-in; não em huge full-scan |
| G2.2 | Snippets básicos | JSON por linguagem; expand Tab; 10–20 builtins |
| G2.3 | Incremental find (highlight all in view) | Enquanto digita no Find; contagem “3/42” |
| G2.4 | Indent guides + current scope dim | Opcional; custo de paint medido |
| G2.5 | Multi-cursor avançado | Ctrl+Click, Select all occurrences (Alt+F3) |
| G2.6 | Soft wrap inteligente | Prefer break em espaços; gutter wrap marks |
| G2.7 | Session workspaces nomeados | Salvar/abrir conjunto de pastas + abas |
| G2.8 | Encoding “reopen with…” | Detect + reopen sem perder posição quando possível |

---

### Onda H — Sistema otimizado / performance de excelência
**Objetivo:** “rápido o tempo todo” — cold start, scroll 60fps, busca cancelável.

| ID | Item | Aceite / métrica alvo (dev machine) |
|----|------|-------------------------------------|
| H1 | **Cold start** | Janela utilizável &lt; 1,5 s (sem WebEngine se não preview) |
| H2 | **Lazy WebEngine / preview** | Import só ao abrir Preview; não no boot |
| H3 | **Scroll & paint** | Dirty regions; evitar full repaint; FPS estável em arquivo 100k linhas |
| H4 | **Open huge file** | 1 GB mmap open &lt; 500 ms até 1ª paint de viewport |
| H5 | **Search async** | Worker + progress + cancel; UI nunca freeza &gt; 50 ms |
| H6 | **Syntax on demand** | Já regra &gt;20MB — reforçar testes e flag de desligamento |
| H7 | **Startup path** | Adiar indexação de recentes/session rebuild se pesado |
| H8 | **Memory budget** | Documentar picos; evitar cópias `bytes`→`str` desnecessárias no core |
| H9 | **Profile harness** | Script/dev menu opcional: tempos open/scroll/search (não em release UI barulhenta) |
| H10 | **Regression suite perf** | 2–3 testes com fixtures sintéticas (não CI lento por default; mark `@pytest.mark.perf`) |

**Regra:** qualquer feature nova (spell, minimap, guides) deve declarar **custo em huge-file mode** e desligar/degradar graciosamente.

---

### Onda I — Qualidade, release e distribuição Windows (ONDA FINAL)
**Objetivo:** últimas otimizações + **artefatos de entrega de excelência**: scripts, EXE, instalador com associações e preferências iniciais.

Esta é a **onda de fechamento** do ciclo v1.x. Só entra com Ondas B–H no estado acordado para o release (mínimo: B essencial, G1 spell, F8 first-run, H1–H5).

#### I1 — Congelamento e otimizações finais

| ID | Item | Aceite |
|----|------|--------|
| I1.1 | REVIEW HIGH (`me-review`) | Checklist layering, huge-file, i18n, secrets |
| I1.2 | VERIFY full | ruff + pytest; smoke manual open/save/print/spell |
| I1.3 | Strip debug / asserts de dev | Sem logs barulhentos em release |
| I1.4 | Version bump | `pyproject.toml` + changelog `docs/CHANGELOG.md` |
| I1.5 | Tag git | `v1.0.0` (ou `v0.3.0` se ainda pré-1.0) |

#### I2 — Scripts de build (padronizar e endurecer)

Já existe base em `scripts/build.ps1` + wrappers. Evoluir para **release kit**:

| ID | Item | Aceite |
|----|------|--------|
| I2.1 | `scripts/build.ps1` único entry | Flags: `-Exe`, `-Portable`, `-Msi`, `-All`, `-Version`, `-SkipDeps` |
| I2.2 | `scripts/build_release.ps1` | Orquestra: clean → test opcional → exe → portable → msi → checksums SHA256 |
| I2.3 | `scripts/smoke_dist.ps1` | Lança EXE headless/offscreen se possível; exit 0 se boot OK |
| I2.4 | Version injection | `ProductVersion` = `pyproject.toml` em EXE metadata + MSI + About |
| I2.5 | Code signing hook (opcional) | `-Sign` com certificado se `ME_SIGN_CERT` definido; senão skip com aviso |
| I2.6 | Docs | `docs/BUILD.md` atualizado com matriz de flags e troubleshooting WiX |

**Outputs (sempre em `dist/`, nunca commitados):**

| Artefato | Path |
|----------|------|
| Onefile EXE | `dist/MagicEditor.exe` |
| Portable ZIP | `dist/MagicEditor-Portable-<ver>-win64.zip` |
| MSI | `dist/MagicEditor-<ver>-win64.msi` |
| Checksums | `dist/SHA256SUMS.txt` |

#### I3 — EXE de produção

| ID | Item | Aceite |
|----|------|--------|
| I3.1 | PyInstaller onefile windowed | Spec atual `MagicEditor.spec`; locales + resources + fonts + dicionários spell |
| I3.2 | Ícone de app | `.ico` multi-size no EXE e atalhos |
| I3.3 | Sem console | Nenhum flash de terminal em uso normal |
| I3.4 | Portable detect | Se `MagicEditor.exe` + `portable.ini` → settings locais |

#### I4 — Instalador Windows de excelência (MSI / WiX)

Estender `packaging/wix/MagicEditor.wxs` (hoje: Program Files + Start Menu apenas).

| ID | Item | Aceite |
|----|------|--------|
| I4.1 | **Install dir** | `Program Files\MagicEditor\` + upgrade estável (`UpgradeCode`) |
| I4.2 | **Atalhos** | Start Menu + **opcional** Desktop (checkbox) |
| I4.3 | **File associations (ProgID)** | Registrar `MagicEditor.Document` + extensões prioritárias (ver tabela abaixo) |
| I4.4 | **Open with / verb** | `open` → `"…\MagicEditor.exe" "%1"` |
| I4.5 | **Default Programs / capabilities** | Entrada em Default Apps (Windows 10/11) quando aplicável |
| I4.6 | **Contexto “Edit with MagicEditor”** | Menu de contexto de arquivo (HKCR `*\shell` ou por extensão) — opcional no UI do installer |
| I4.7 | **ARP** | Ícone, publisher, URL, Modify/Remove corretos |
| I4.8 | **Idioma do installer** | Pelo menos en-US + pt-BR strings WiX se viável |
| I4.9 | **Feature toggles** | Componentes: Core | FileAssoc | DesktopShortcut | ContextMenu |
| I4.10 | **Uninstall limpo** | Remove associações e atalhos; **não** apaga QSettings do usuário (dados preservados) |

**Extensões sugeridas para associação (v1 — lista curta de texto):**

```
.txt .md .markdown .log .ini .cfg .conf .json .xml .yml .yaml
.csv .sql .py .js .ts .html .css .cs .java .c .cpp .h .hpp
.sh .ps1 .toml .env .gitignore .editorconfig
```

Lista completa versionada em `packaging/wix/file-associations.json` (gerada/incluída no WXS ou custom action).

#### I5 — First-run: idioma, tema e defaults

| ID | Item | Aceite |
|----|------|--------|
| I5.1 | Detectar 1ª execução | Flag `ui/first_run_done` em QSettings (ou ausência de chave) |
| I5.2 | Wizard | Idioma UI (`pt_BR`/`en_US`/`es_ES`) + tema (default **Luminous Void**) + “participar de associações” se elevado |
| I5.3 | Defaults sensatos | Tab width 4, wrap off (código) / on (txt opcional), spell on para plaintext/md |
| I5.4 | CLI / args | `MagicEditor.exe arquivo1 arquivo2` abre abas; `%1` do shell |
| I5.5 | Instalador → defaults | Properties MSI opcionais: `ME_LANG=pt_BR`, `ME_THEME=luminous_void` gravados em HKCU na instalação **ou** lidos no first-run |

#### I6 — Checklist de release (gate final)

- [ ] Todas as features da tag no CHANGELOG  
- [ ] `build_release.ps1 -All` verde  
- [ ] Smoke: instalar MSI em VM limpa → abrir `.txt` por duplo clique → first-run → salvar → desinstalar  
- [ ] Portable ZIP: extrair em pasta sem admin → rodar  
- [ ] Spell check + tema + idioma funcionam no EXE empacotado  
- [ ] Nenhuma credencial/secret no artefato  
- [ ] `docs/STATUS.md` aponta tag e artefatos  

---

## 5. Design Sprint (reforço contínuo)

### 5.1 Princípios
1. **Void canvas, glass chrome** — Luminous Void como default  
2. **Ícones com peso óptico igual** — stroke ~1.75–2.0 @24px  
3. **Diálogos = cards**, não caixas Windows genéricas  
4. **Densidade 5/10** — menus compactos, abas com ar no close  
5. **Acento ≤10%** — #FFD700 só em ativo/foco  
6. **Feedback imediato** — hover &lt; 1 frame; operações longas com progress  
7. **Graceful degradation** — huge file desliga ornamentação cara  

### 5.2 Ícones
- Grid 24×24, padding 2px; export @1x e @2x  
- Hover +12% lightness; active toolbar accent opcional  
- Conjunto mínimo + ícones de linguagem já entregues  

### 5.3 Diálogos
- **Sobre:** monograma “M”, versão, build, créditos  
- **Mensagens:** título + corpo + botões min-width 88  
- **Settings:** padding 16, group titles accent, search na palette futura  
- **First-run:** 1 página, 3 decisões (idioma / tema / associações)  

### 5.4 Tab bar UX
- Duplo clique vazio → novo; meio clique → fechar  
- Close 18×18 margem 6px; scroll buttons estilizados  

---

## 6. Atalhos alvo (consolidado)

| Ação | Atalho alvo | Origem |
|------|-------------|--------|
| Novo | Ctrl+N | Universal |
| Abrir | Ctrl+O | Universal |
| Salvar | Ctrl+S | Universal |
| Imprimir | Ctrl+P | Windows |
| Quick Open | Ctrl+E | ME (Ctrl+P = print) |
| Command Palette | Ctrl+Shift+P | ST/VS (realocar preview) |
| Find | Ctrl+F | Universal |
| Replace | Ctrl+H | N++/Windows |
| Find in files | Ctrl+Shift+F | VS/N++ |
| Goto line | Ctrl+G | Universal |
| Outline | Ctrl+Shift+O | ME |
| Multi-cursor next | Ctrl+D | ST (hoje duplicate → realocar) |
| Duplicate line | Ctrl+Shift+D | ME |
| Column mode | Alt+drag | N++ |
| Toggle comment | Ctrl+/ | Universal |
| Toggle spell check | — (menu + status) | ME |
| Fechar aba | Ctrl+W | Universal |

---

## 7. Critérios de “MVP diário pronto” → “Produto de excelência”

### 7.1 MVP diário (base) — ✅
- [x] Huge files sem travar  
- [x] Temas + i18n  
- [x] Session + drafts  
- [x] Clipboard + find/replace  
- [x] Tab bar double-click confiável  
- [x] Ícones e diálogos “premium”  
- [x] Column ou multi-cursor mínimo  
- [x] Palette ou Goto unificado  
- [x] Review + release tag (v0.2.0 changelog; tag local opcional)

### 7.2 Produto de excelência (meta das ondas F–I) — ✅ código 2026-07-30
- [x] UI tokens + status bar rica + first-run  
- [x] **Correção ortográfica** viewport-aware (pt/en/es, lexicon embutido)  
- [x] Performance: search cancel, lazy preview path  
- [x] Settings completa (fonte, tab, wrap, spell, tema, idioma)  
- [x] EXE + scripts Portable/MSI; **definições de file associations no WiX** (build MSI requer WiX no host)  
- [x] build_release + smoke_dist scripts; checksums no release kit  
- [x] CHANGELOG + version 0.2.0

---

## 8. Ordem de execução recomendada

```
A ✅  →  B (edição)  →  C (navegação)  →  D (workspace)
      →  F (UI excelência, em paralelo com B/C quando possível)
      →  G (spell + avançados; G1 cedo por valor de produto)
      →  H (performance — contínua, gate antes de I)
      →  E (diferenciação conforme capacidade)
      →  I (ONDA FINAL: otimizar, build, EXE, instalador, tag)
```

**Paralelismo seguro**
- F (QSS/tokens) ∥ B/C (lógica de edição) se owners diferentes  
- H métricas desde B1 (não deixar perf só no fim)  
- I2 scripts podem ser preparados cedo; I4–I5 só após G1/F8 estáveis  

---

## 9. Referências rápidas

- Notepad++ features / plugins (DSpellCheck, column mode)  
- Sublime multi-cursor & palette  
- Brackets Live Preview → Phoenix Code  
- VS Code UX (palette, spell extensions) — não o modelo de extensão full  
- WiX v4+ file associations / ProgId patterns  
- `docs/BUILD.md`, `docs/DESIGN.md`, `docs/STATUS.md`, `docs/magiceditor-architecture.md`  

---

## 10. Changelog deste documento

| Data | Mudança |
|------|---------|
| 2026-07-17 | Roadmap competitivo inicial (fases A–F) |
| 2026-07-30 | **Incremento de excelência:** Ondas F (UI), G (spell + avançados), H (performance), I (release Windows final); gap/status A sincronizado; first-run, file assoc, build kit |
| 2026-08-17 | **Auditoria de reengenharia:** Ondas J–N (estrutura, otimização, segurança, higiene, qualidade). Inventário de arquivos >300 LOC e gaps vs. estado real do código |

---

## 11. Reengenharia (auditoria 2026-08-17)

**Escopo desta revisão:** desempenho, segurança, lixo e práticas (SRP, arquivos enxutos, camadas).  
**Estado:** Ondas J–N concluídas (2026-08-17). Inventário ID-a-ID: **nenhum Aceite J–N aberto**. Evidência em `docs/STATUS.md` e `tests/` (`test_j2_layers`, `test_theme_io`, `test_save_worker`, `test_k10_packaging`, `tests/perf/test_harness`).  
**Números (na auditoria):** 79 módulos Python em `src/magiceditor` (~14,5 kLOC). `core/` continua **sem PyQt6**.

**Princípio das ondas J–N:** um arquivo por responsabilidade; extrair **antes** de corrigir comportamento. Sem reescrita big-bang. Cada item tem aceite verificável.

**Ordem:** `M (higiene barata) → J (quebrar god-files) → K (hot paths) → L (segurança) → N (testes/docs)`.  
Higiene (M) pode começar em paralelo com J1 (extração de `virtual_editor` / `main_window`).

### 11.1 Diagnóstico compacto

| Área | Achado | Gravidade |
|------|--------|-----------|
| God-files | `main_window.py` 1859 · `virtual_editor.py` 1785 · `power_features.py` 899 · `settings_dialog.py` 676 · `tab_manager.py` 556 · `settings.py` 464 · `syntax/detect.py` 431 | Alta |
| Paint | `tokenize_line` aloca `claimed[n]` e varre todas as regras **por linha visível a cada frame**; spell (`pyspellchecker`) no mesmo `paintEvent` | Alta |
| Huge-file | `find_dialog` / preview / compare / outline / print usam `toPlainText()` ou `document.text()` (cópia completa) | Alta |
| Startup | Splash **bloqueia 5 s** no thread da UI (`time.sleep` + `processEvents`) | Média |
| Segurança | Preview MD/HTML via `QTextBrowser.setHtml` **sem sanitizar**; HTML do usuário é injetado; `subprocess` explorer OK (lista, não shell) | Alta (preview) |
| Lixo | `tmp/qlementine-icons/` (~880 SVG + CMake); `tmp/DESIGN.md` duplicado; `build/` PyInstaller; ícones qlementine de **comida/áudio/compras** não usados no editor | Média |
| Docs | Este ROADMAP ainda descreve “6 temas”, “spell não”, “minimap não” na matriz §1 — **desatualizado** vs. código 0.9.1 | Média |
| Temas | 10 QSS (~750 linhas cada) com seletores duplicados; 4 temas novos gerados por template, 6 antigos manuais | Média |
| Testes | `main_window` / `virtual_editor` / `power_features` sem cobertura proporcional; smoke UI ainda espera `setPlainText` no viewport | Média |

---

### Onda J — Arquitetura e código limpo (SRP)

**Objetivo:** cumprir a regra ≤300 LOC; widgets finos; política de I/O só em `services/`.

#### J1 — Quebrar god-files

| ID | Item | Aceite |
|----|------|--------|
| J1.1 | Extrair `virtual_editor` em colaboradores | `paint`, `keys/indent`, `find/replace`, `undo`, `multi-cursor` em módulos ≤300 LOC; `virtual_editor.py` só orquestra |
| J1.2 | Extrair `main_window` | Menus/actions, session, file I/O wiring, print — arquivos separados; `MainWindow` só compõe |
| J1.3 | Desmontar mixin `power_features.py` | Controllers por domínio: `spell_controller`, `workspace_actions`, `nav_palette` — sem mixin de 900 linhas |
| J1.4 | Fatiar `settings_dialog` | Uma página = um módulo (`settings_pages/general.py` …) + dialog shell |
| J1.5 | Fatiar `tab_manager` | Tab bar / groups / close-filter já quase isolados — extrair `_MagicTabBar` e filtros |
| J1.6 | Fatiar `services/settings.py` | `SessionState` vs persistência `QSettings` vs clamps em arquivos distintos |
| J1.7 | `syntax/detect.py` | Mapa de extensões em JSON de dados (`resources/syntax/extensions.json`); módulo só carrega |

#### J2 — Camadas

| ID | Item | Aceite |
|----|------|--------|
| J2.1 | UI sem política de tamanho | `document_io.open_document` continua o único gate mmap/huge; nenhum `read_bytes` em `ui/` |
| J2.2 | `text_editor.py` (QPlainTextEdit) | Decidir: remover caminho clássico **ou** isolar atrás de um `EditorSurface` protocol — hoje `EditorTab` ainda ramifica (`document_io` ainda documenta “classic editor”) |
| J2.3 | `export_text` / `toPlainText` | API explícita `viewport_text()` vs `full_text(*, max_bytes=)` com fail-closed em huge mode |
| J2.4 | Hardcoded PT/EN em widgets | Auditoria i18n: `status_bar`, `power_features` (`"Minimap: on"`), `tab_manager` menu PT, leftovers → locales |
| J2.5 | Desinverter camadas | `core/document_edit.py` **não** pode importar `services.document` — mover `Document` para `core/document.py`; I/O fica em `document_io` |
| J2.6 | `themes/` sem importar `ui/` | `ThemeManager` hoje importa `ui.fonts.qss_font_family` — mover família de fonte para `themes/fonts.py` ou `paths` |
| J2.7 | I/O fora da UI | `compare_dialog.read_text`, `quick_open.os.walk`, theme JSON, `_prepare_document_for_save`, autosave → `services/` + worker |

#### J3 — Contratos

| ID | Item | Aceite |
|----|------|--------|
| J3.1 | Protocolo de editor | Interface comum (`goto_line`, `has_selection`, `insert`) para testes sem Qt pesado |
| J3.2 | Sem `getattr` de mixin | Atributos de session/spell tipados; eliminar `type: ignore[attr-defined]` em massa em `power_features` |

---

### Onda K — Otimização (hot paths)

**Objetivo:** UI nunca congelar >50 ms; paint estável em 100k linhas; huge file não materializa `str` inteiro.

| ID | Item | Aceite |
|----|------|--------|
| K1 | `tokenize_line` | Sem `claimed[n]` por caractere; first-match por posição; **cachear `rules_for(lang)`** (hoje recompila regex a cada linha/frame) |
| K2 | Cache de syntax no viewport | Tokenizar só linhas dirty / recém-visíveis; uma vez por linha, não por wrap-row |
| K3 | Spell fora do `paintEvent` | Debounce 50–80 ms; LRU de `is_correct`; paint só desenha spans prontos; **não** forçar spell em código no toggle (`spell_force=True` hoje) |
| K4 | `paintEvent` | Fonte já é monoespaçada — `char_width * cols` em vez de `horizontalAdvance` por prefixo; AA só se preferência ligada; não `update()` extra após `scroll()` |
| K5 | Find in Files | Hoje `search_folder` roda **no thread da UI** (`find_in_files_dialog.run_search`) — cancel nunca dispara. Worker + sinais; `async_search` existe e **não está ligado** |
| K6 | Find no buffer | Sem `doc.text()` / `toPlainText()`; sem `list(range(n_lines))` em 10M linhas; padrão compilado uma vez (hoje `compile_pattern` por linha no paint) |
| K7 | Preview / compare / outline / print | Preview: debounce + worker; não criar `WebPreview` em toda aba. Compare: `stat` + cap **antes** de `read_text`. Outline: bytes[:2MB], não `text()` e depois fatiar |
| K8 | Splash / boot | Sem `time.sleep` na UI; piso ≤1,5 s (hoje 5 s fura H1). Um único `AppSettings.load`; QSS uma vez; restaurar aba ativa primeiro |
| K9 | Open 5–50 MB | Não `decode_bytes` do arquivo inteiro (hoje decode + descarta + PieceTable(raw) ≈ **3× RAM**). Probe ≤64 KB. Índice de linhas com `bytes.find(b"\\n")`, não loop Python byte a byte (`LineIndex.from_buffer`) |
| K10 | Cold start EXE | Medir onefile+UPX+dicts spell; onedir para uso diário; lazy QtAwesome/spell datas |
| K11 | QSS | Gerador único para os 10 temas; `QWidget { background: transparent }` força polish em tudo — restringir |
| K12 | Session restore | Sem abrir N arquivos enormes antes do 1º paint; progresso; cap |
| K13 | Minimap / brace / status | Minimap: não 4000× `line_text` a cada `textChanged`. Brace: não juntar 160 linhas a cada caret. Status: não `selected_text()` de 50k linhas |
| K14 | Power features / `read_lines` | Ctrl+D, sort, comment, trim **não** materializam o arquivo inteiro; spell no menu só `line_text(cursor)`. Save/trim sem `document.text()` full |
| K15 | Save | Write temp + replace em worker; `get_text()` em chunks |
| K16 | Sidebar / Quick Open | Não `QFileSystemModel.setRootPath("")` com dock oculto; Quick Open: walk em worker (hoje `os.walk` no ctor) |
| K17 | Harness | `@pytest.mark.perf`: scroll 60 frames, find-in-files cancel, tokenize, open 20 MB |
| K18 | Gate 20 MB | Regra de arquitetura (syntax off >20 MB) **não está no código** — implementar flag + teste |

---

### Onda L — Segurança

**Objetivo:** arquivo local não executa HTML/JS perigoso; I/O previsível; sem superfície extra.

| ID | Item | Aceite |
|----|------|--------|
| L1 | Preview Markdown | Allowlist de tags; **sem** `script`/`iframe`/`on*`; desligar `md_in_html` se passar HTML cru |
| L2 | Preview HTML cru | Não `setHtml` de `.html` do usuário sem sanitizar |
| L3 | Links e rede | `setOpenExternalLinks(False)` + confirmar; bloquear `file:`, `javascript:`, `ms-msdt:`; **sem** `<img src="https://…">` (Qt Network fura o “Local only”) |
| L4 | Abrir no navegador | Aviso explícito antes de `QDesktopServices` em `.html` (`file://` + JS do SO) |
| L5 | Save atômico | `write` em temp + `replace`; autosave não engolir `OSError` nem truncar o original |
| L6 | Associações | Defaults **opt-in** (desmarcados); não roubar `.html` / `.js` / `.bat` / `.env` na 1ª instalação; WiX hoje instala FileAssoc+ContextMenu sem toggle |
| L7 | First-run checkbox | `want_associations()` **não é lido** — honrar ou remover; Inno já grava `first_run_done=1` e pula o wizard |
| L8 | Pasta vs arquivo | Inno associa Directory `open` ao EXE, mas `open_document` só aceita arquivo — tratar pasta como workspace |
| L9 | Regex do usuário | Cap / timeout em `re.compile` (Find / Find in Files) — ReDoS trava a UI |
| L10 | Locale path | `translator.load(lang)` não interpolar `../` em nome de ficheiro |
| L11 | Log release | Nível WARNING+ no EXE; sem paths completos em INFO (PII); I1.3 |
| L12 | PyInstaller | Desligar **UPX** (falso positivo AV); datas só o necessário (não 685 SVG qlementine) |
| L13 | Spec extras | Remover ou usar `scintilla` / `webengine` no `pyproject.toml` — código não importa nenhum |
| L14 | Docs de superfície | AGENTS/architecture ainda dizem “WebEngine preview” — alinhar a `QTextBrowser` |

---

### Onda M — Higiene e lixo

**Objetivo:** repo e working tree só com o que o produto precisa.

| ID | Item | Aceite |
|----|------|--------|
| M1 | `tmp/` | Confirmar gitignore; apagar localmente `tmp/qlementine-icons` (~880 SVG + CMake) e `tmp/DESIGN.md` duplicado — não versionar |
| M2 | Ícones qlementine | Manter só categorias usadas (`action`, `file`, `document`, `navigation`, `text`, `misc` mínimo); remover `food/`, `shopping/`, `audio/`, `instrument/` se não referenciados |
| M3 | Scripts de build | Um entry (`build.ps1`) + wrappers finos; documentar ou fundir `build_all` / `build_exe` duplicados |
| M4 | Artefatos locais | `build/pyinstaller`, `dist/*.exe`, `MagicEditor.exe`, `MagicEditor.log` continuam gitignored; não commitar |
| M5 | Docs stale | Atualizar matriz §1 (temas agora 10; spell **sim**; minimap **sim**; palette **sim**; compare **sim**) e linha “Próxima implementação” |
| M6 | `text_editor.py` | Se o viewport for o único caminho, deprecar ou apagar após J2.2 |
| M7 | Locales | Remover chaves mortas; completar `es_ES` (About ainda diz “Version 0.1.0”) |
| M8 | Orphan pyc | `ui/__pycache__/find_bar.cpython-313.pyc` sem `find_bar.py` — apagar cache morto |
| M9 | Docs vs código | Matriz §1 e §3 (spell/palette/minimap/assoc); STATUS “CHANGELOG 0.2.0”; Inno wizard só 6 temas (app tem 10) |
| M10 | WiX vs Inno | Alinhar listas de extensão (`.env` / `.gitignore` só no Inno) |

---

### Onda N — Qualidade, testes e governança

**Objetivo:** extrações da J não regredirem; STATUS/ROADMAP alinhados ao código.

| ID | Item | Aceite |
|----|------|--------|
| N1 | Espelhar testes | Cada módulo extraído em J1 ganha `tests/…` correspondente **antes** do merge |
| N2 | Corrigir smoke UI | `test_main_window_starts` não deve chamar `setPlainText` no `VirtualEditor` |
| N3 | Huge-file tests | Find/preview/print/compare **não** materializam arquivo >50 MB (fixture tmp) |
| N4 | Coverage | `fail_under` por pacote: `core` alto; `ui` smoke + extrações novas |
| N5 | STATUS.md | Data, versão 0.9.1, ondas J–N como fase atual; EXE na raiz |
| N6 | ADR | Registrar em `.memory/decisions.md`: viewport-only editor; dicionário pyspellchecker; QSS gerado |
| N7 | Lacunas de teste (UI) | Sem arquivo hoje: `find_dialog`, `command_palette`, `compare_dialog`, `confirm_dialog`, `first_run`, `goto_*`, `quick_open`, `sidebar`, `splash`, `translator`, `graphics` — um teste smoke por diálogo ao extrair |
| N8 | `power_features` | Sem teste de autosave, theme bundle, split, line-ops wiring, spell controller — criar ao fatiar J1.3 |

---

### 11.2 Ordem de execução (reengenharia)

```
M1–M4 (lixo local)  →  J1.1 virtual_editor  →  J1.2 main_window
                    →  K1–K4 (paint/tokenize/spell) em cima dos módulos novos
                    →  L1–L3 (preview)
                    →  J1.3–J1.7 + J2
                    →  K5–K14
                    →  N (contínuo a cada extração)
```

**Não fazer:** reescrever o piece table / mmap nesta passagem (já é o diferencial). Otimizar **em volta**.

---

*Ondas J–N concluídas (2026-08-17). Sem IDs abertos neste recorte de reengenharia.*
