---
name: me-theme
description: >
  MagicEditor QSS themes, design tokens, and chrome polish for the desktop editor.
  Use when editing resources/themes/*.qss, themes manager, About dialog polish, or visual hierarchy.
  Triggers: QSS, theme, dark mode, Luminous Void, design taste, contrast, scrollbar, monokai.
---

# MagicEditor — Themes & Visual System

## Load also
- Project skill `design-taste` for anti-slop visual rules
- Architecture theme sections in `docs/magiceditor-architecture.md` when inventing a new theme

## Rules
- Themes live as **QSS files** under `resources/themes/`
- Register/switch via `src/magiceditor/themes/manager.py` without restart
- Prefer curated palettes over pure black (`#000`) and neon primaries
- Interactive states required: hover, pressed, focus, disabled, selected
- Contrast ≥ 4.5:1 for body text; muted labels still readable
- Desktop motion: 100–200ms max; never block the GUI thread

## New theme checklist
1. Copy closest existing QSS as base
2. Define surfaces: window, panel, tab, input, menu, scrollbar, selection
3. Align syntax colors if theme implies a palette (may be separate)
4. Test in light/dark OS settings if applicable
5. Add i18n name key if shown in Settings

## Anti-slop
- No generic purple gradients, Inter-everywhere web aesthetics forced onto desktop
- No glassmorphism that kills text contrast
- Prefer editor-native density (Notepad++/Sublime class), not dashboard SaaS cards
