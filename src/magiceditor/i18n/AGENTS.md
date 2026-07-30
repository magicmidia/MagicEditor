# i18n/ — live translation

- `TranslatorManager` owns language + load of `locales/*.json`
- Emit `language_changed` so widgets call `retranslate_ui()`
- Catalogs only in `locales/`; no feature logic here
- Skill: `me-i18n` when adding strings or languages
