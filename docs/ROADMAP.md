# MagicEditor — Roadmap detalhado (pesquisa competitiva + plano)

**Atualizado:** 2026-07-17  
**Fontes:** Notepad++, Windows Notepad, Sublime Text, Adobe Brackets / Phoenix Code, VS Code, WordPad (legado), práticas de mercado 2024–2026.

Este documento inventaria funcionalidades e vantagens dos editores do “tipo MagicEditor”, cruza com o estado atual do produto e define fases de entrega com critérios de aceite.

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
| Temas | Styles Configurator | Claro/escuro | Excelente | Bom | Excelente | 6 temas QSS |
| i18n UI | Sim | SO | Limitado | Sim | Excelente | pt/en/es |
| Macros | Sim | Não | Snippets | Extensões | Extensões | Não |
| Compare files | Plugin | Não | Diff packages | Não | Diff nativo | Não |
| Hex / binário | Sim | Não | Packages | Não | Extensão | Não |
| Minimap | Não | Não | **Sim** | Não | Sim | Não |
| Command palette | Não | Não | **Ctrl+Shift+P** | Limitado | **Ctrl+Shift+P** | Não (só Quick Open) |
| Session restore | Sim | Sim | Sim | Sim | Excelente | Sim (+ drafts) |
| Leveza / RAM | **Muito leve** | Mínimo | Leve | Médio | Pesado | Médio-leve |
| Impressão limpa | Razoável | Simples | Limitado | Limitado | Extensão | **Forte** (clean print) |

**Diferenciais já do MagicEditor:** piece table + mmap + virtual viewport; impressão/PDF “clean”; Luminous Void + GPU/transparência; drafts de Untitled; i18n JSON.

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

**Vantagem N++:** leveza + macros + coluna + ecossistema de plugins Windows-first.

### 2.2 Windows Notepad (moderno)

- Abas simples, sessão de tabs  
- Auto-save rascunhos  
- Dark mode, status bar  
- Busca básica, zoom  
- **Vantagem:** zero fricção, instantâneo, zero config  

### 2.3 Sublime Text 2/3/4

- **Multi-cursor** (Ctrl+D, Alt+F3, Ctrl+click, coluna)  
- **Command Palette** (Ctrl+Shift+P)  
- **Goto Anything** (Ctrl+P) — arquivos + @símbolos + :linha  
- Minimap com viewport highlight  
- Split panes / layouts  
- Project / workspace  
- Snippets, macros, Vintage mode  
- Incremental find, “Expand selection to scope”  
- Package Control ecosystem  
- **Vantagem:** velocidade de edição multi-cursor + palette + goto unificado  

### 2.4 Brackets → Phoenix Code

- **Live Preview** HTML/CSS no browser com sync  
- Inline editors (editar CSS no contexto do HTML)  
- Extract / quick edit  
- Foco web design  
- **Vantagem:** feedback visual imediato para front-end  

### 2.5 VS Code (referência “moderno”)

- IntelliSense, LSP, debug, Git, terminal  
- Multi-cursor, palette, quick open, settings UI  
- Extensions marketplace  
- Diff editor, merge, timeline  
- **Vantagem:** plataforma completa — MagicEditor **não** compete como IDE, e sim como editor leve + huge files  

### 2.6 WordPad / editores ricos (referência negativa)

- Formatação rich-text (fora de escopo código)  
- MagicEditor permanece **plain text / code-first**  

---

## 3. Gap analysis — MagicEditor vs meta

| Feature | Prioridade | Status | Nota |
|---------|------------|--------|------|
| Duplo clique barra → nova aba | P0 | 🔧 corrigir | Evento no QTabBar |
| Ícones toolbar/menu modernos | P0 | 🔧 upgrade | Stroke + peso visual |
| Diálogos (Sobre, mensagens) premium | P0 | 🔧 redesign | Dialog custom + QSS |
| Multi-cursor / column mode | P1 | Stretch | Sublime/N++ killer feature |
| Command palette | P1 | Falta | Ctrl+Shift+P (preview usa isso — realocar) |
| Minimap | P2 | Falta | Sublime/VS Code |
| Operações de linha (sort, join, delete blank) | P1 | Parcial | Tem duplicate |
| Tabs↔spaces / trim trailing | P1 | Falta | N++ blank ops |
| Comentário toggle | P1 | Falta | Por linguagem |
| Brace match highlight | P1 | Falta | |
| Auto-complete palavras do doc | P2 | Falta | |
| Compare two files | P2 | Falta | |
| Function/symbol list | P2 | Outline MD só | Expandir para código |
| Macros | P3 | Falta | |
| Hex editor | P3 | Falta | |
| Split editor panes | P2 | Falta | |
| Reload from disk / external change | P1 | Falta | |
| Open folder in explorer / copy path | P1 | Falta | |
| Autosave interval | P2 | Falta | |
| Settings UI mais completa | P1 | Parcial | Só GPU/opacity |
| Plugin API | P3 | Fora MVP | |
| Telemetria | — | Não | Privacy by default |

---

## 4. Roadmap por fases

### Fase A — Polish diário (atual / imediato) ✅ em curso
**Objetivo:** sensação de produto acabado.

| ID | Item | Aceite |
|----|------|--------|
| A1 | Duplo clique na **tab bar** cria Untitled | Clique na área vazia ou corner → novo doc |
| A2 | Ícones Lucide densos, HiDPI, contraste por tema | Toolbar 20px legível; menus 16px |
| A3 | Diálogo **Sobre** custom (logo, versão, links) | Não é QMessageBox genérico |
| A4 | QSS de `QMessageBox` / `QDialog` densos | Botões com padding, cantos, tipografia |
| A5 | Roadmap + STATUS sincronizados | docs/ROADMAP.md |

### Fase B — Edição poderosa (próxima)
| ID | Item | Inspiração |
|----|------|------------|
| B1 | Column selection (Alt+drag) | N++ |
| B2 | Multi-cursor básico (Ctrl+D add next, Esc clear) | Sublime |
| B3 | Line ops: move up/down, sort, join, delete blank | N++ |
| B4 | Toggle comment | Todos |
| B5 | Trim trailing whitespace + tabs↔spaces | N++ |
| B6 | Matching braces / tags highlight | N++ / ST |

### Fase C — Navegação moderna
| ID | Item | Inspiração |
|----|------|------------|
| C1 | Command Palette (mover Preview de Ctrl+Shift+P) | ST / VS Code |
| C2 | Goto Anything unificado (arquivo + :linha + #heading) | ST |
| C3 | Minimap | ST / VS Code |
| C4 | Symbol list (funções) por linguagem | N++ Function List |
| C5 | Reload if changed on disk | Todos |

### Fase D — Workspace & produtividade
| ID | Item |
|----|------|
| D1 | Open containing folder / Copy path / Reveal |
| D2 | Autosave + backup interval |
| D3 | File compare (side-by-side) |
| D4 | Split view (2 editores) |
| D5 | Settings page completa (font size, tab width, wrap default) |
| D6 | Export theme / import |

### Fase E — Diferenciação MagicEditor
| ID | Item |
|----|------|
| E1 | Huge-file search progress UI + cancel |
| E2 | MagicCloud sync real (hoje placeholder status) |
| E3 | Live HTML preview no browser (Brackets-style) opcional |
| E4 | Performance dashboard (lines, mmap, GPU) |
| E5 | Portable mode (config ao lado do exe) |

### Fase F — Qualidade / release
| ID | Item |
|----|------|
| F1 | Code review (me-review) + checklist |
| F2 | Merge `feature/editor-mvp` → `main` |
| F3 | Tag v0.2.0 + changelog |
| F4 | Installer opcional (Inno/NSIS) |

---

## 5. Nova rodada de design (Design Sprint)

### 5.1 Princípios (reforço)
1. **Void canvas, glass chrome** — Luminous Void como default  
2. **Ícones com peso óptico igual** — stroke ~1.75–2.0 @24px, never hairline  
3. **Diálogos = cards**, não caixas Windows genéricas  
4. **Densidade 5/10** — menus compactos, abas com ar no close  
5. **Acento ≤10%** — #FFD700 só em ativo/foco  

### 5.2 Ícones (especificação)
- Grid 24×24, padding 2px  
- Cap/join round  
- Export pixmap @1x e @2x com devicePixelRatio  
- Hover: +12% lightness; active toolbar: accent opcional  
- Conjunto mínimo: file, edit, clipboard, search, view, format, help  

### 5.3 Diálogos
- **Sobre:** header com monograma “M”, versão, build, créditos, botão OK  
- **Mensagens:** título + corpo + botões alinhados à direita, min-width botão 88  
- **Settings:** já existe — unificar padding 16, group titles accent  

### 5.4 Tab bar UX
- Duplo clique vazio → novo  
- Meio clique → fechar  
- Close button 18×18 com margem 6px  
- Scroll buttons estilizados  

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
| Fechar aba | Ctrl+W | Universal |

---

## 7. Critérios de “MVP diário pronto”

- [x] Huge files sem travar  
- [x] Temas + i18n  
- [x] Session + drafts  
- [x] Clipboard + find/replace  
- [ ] Tab bar double-click confiável  
- [ ] Ícones e diálogos “premium”  
- [ ] Column ou multi-cursor mínimo  
- [ ] Palette ou Goto unificado  
- [ ] Review + main  

---

## 8. Referências rápidas

- Notepad++ features / plugins: community + user manual  
- Sublime multi-cursor & palette: docs e práticas ST3/4  
- Brackets Live Preview → Phoenix Code  
- VS Code vs N++ comparativos 2025 (terminal, Git, macros)  

---

*Próxima implementação imediata deste documento: Fase A (A1–A5) + início Fase B conforme capacidade.*
