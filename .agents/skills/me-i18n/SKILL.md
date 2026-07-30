---
name: me-i18n
description: >
  MagicEditor localization: TranslatorManager, locales JSON, retranslate_ui.
  Use when adding UI strings, new languages, or fixing hard-coded labels.
  Triggers: i18n, locale, pt_BR, en_US, es_ES, translation, retranslate.
---

# MagicEditor — i18n

## Rules
- User-visible strings → translator keys, not long-term hard-coded PT/EN in widgets
- Locale files: `locales/<lang>.json` only for string catalogs
- Live switch: `TranslatorManager.language_changed` → each surface `retranslate_ui()`
- Supported today: `pt_BR`, `en_US`, `es_ES` — add a new JSON + register when expanding

## Process
1. Add keys to **all** locale files in the same change
2. Wire `tr("key")` / project helper in the widget
3. Ensure dialogs rebuilt or retranslated on language change
4. Smoke: switch language in Settings without restart
