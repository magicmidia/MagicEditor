# Reusable Patterns

## Pure core, thin UI
- Buffer math and I/O policy in `core/` / `services/`
- Widgets emit signals and call service methods only

## Huge file open path
1. Stat size → if >50MB use mmap source else memory source  
2. Build piece table over source  
3. Build line index lazily or incrementally  
4. Bind viewport to line/offset queries  

## Live i18n
- `TranslatorManager.language_changed` → each widget `retranslate_ui()`

## Theme switch
- Load QSS from `resources/themes/<name>.qss` → `app.setStyleSheet`  
- Syntax palette separate from chrome QSS when needed  

## Worker search
- `QThread` or `QObject` + `moveToThread`  
- Cancel token; emit match batches; never touch widgets from worker (signals only)
