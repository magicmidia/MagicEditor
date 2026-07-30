---
name: design-taste
description: Use when designing, polishing, auditing, or refactoring user interfaces, themes, layouts, or stylesheets. Applies "Taste" and "Impeccable" design principles to avoid AI design slop (like generic gradients, overused fonts, poor contrast, and default cards) and creates premium, modern, accessible, and responsive visual systems.
---

# Design & Taste (Impeccable UI) Skill

This skill guides the design, visual hierarchy, styling (QSS/CSS), typography, and user experience of interfaces, focusing on desktop (PyQt6) and web layouts. Use these guidelines to deliver premium, state-of-the-art designs that delight the user.

## 1. Visual Aesthetics & Themes (Anti-AI Slop)
- **Harmonious Palettes**: Avoid harsh default colors (pure red, pure blue, saturated primary colors). Use carefully curated color systems (e.g., tailored HSL/OKLCH color ramps).
- **Premium Dark Mode**: For dark themes, do not use pure black (`#000000`). Use deep, rich grays/blues (e.g., `#0f1115`, `#181a20`) with subtle glassmorphism or border styling.
- **Elevation and Contrast**: Body text must maintain a contrast ratio of at least 4.5:1 against the background. Muted labels or placeholders must be readable, not faded out.
- **Borders & Shadows**: Use extremely subtle borders (e.g., 1px solid with 5% to 10% opacity of the text color) and smooth box-shadows (multi-layered or soft blurs) instead of single hard borders.

## 2. Desktop UI Excellence (PyQt6 / QSS specific)
- **Design Tokens**: Do not hardcode colors in widget styles. Always reference shared stylesheet variables (e.g., `@primary`, `@background`, `@foreground`) or QSS variables if supported.
- **Dynamic States**: Every interactive element (buttons, tabs, menu items) MUST have clear, beautiful styling for:
  - `:hover` (subtle brightness change or background tint)
  - `:pressed` (slight inset look or color shift)
  - `:focus` (distinct focus outline or color bar, essential for keyboard navigation)
  - `:disabled` (clean, readable opacity shift, never looking completely broken)
- **Viewport Snappiness**: Keep layouts fluid. Use `QSplitter` for resizable panels, and ensure proper `minimumSize` and `maximumSize` constraints are set so widgets don't collapse or overlap awkwardly.
- **Scroll Areas**: Ensure `QScrollArea` components have clean, modern scrollbar designs, avoiding default thick OS scrollbars where possible.

## 3. Typography & Hierarchy
- **System / Google Fonts**: Avoid default browser/system font families. Favor modern typography (e.g., Inter, Outfit, Roboto, or JetBrains Mono for code viewports).
- **Scale Consistency**: Establish a clear typography hierarchy (e.g., 12px for small details, 14px for body, 16px for UI headers, 20px-24px for page titles).
- **Readability Rules**:
  - Keep line length for readable text constrained (e.g., maximum 65–75 characters per line).
  - Use appropriate `line-height` (typically `1.4` to `1.6` for body text) to let the copy breathe.
  - Set `text-wrap: balance` for headings and `text-wrap: pretty` for descriptions.

## 4. Spacing & Rhythm
- **Grid Discipline**: Align all elements to a consistent 4px or 8px grid system. Margins and paddings should utilize standard values (e.g., 4px, 8px, 12px, 16px, 24px, 32px).
- **Content Breathing Room**: Give panels, sidebars, and dialogue boxes generous padding. A cramped UI immediately looks cheap and unprofessional.
- **Structured Sections**: Use clear horizontal/vertical lines, card grids, or subtle background changes to separate unrelated features, avoiding nested cards or excessive borders.

## 5. Micro-Animations & Snappiness
- **Snappy Motion**: Desktop apps should feel fast and alive. Use quick, subtle transitions (100ms - 200ms) for hovers and state changes.
- **Animation Constraints**: Use `QPropertyAnimation` or similar logic carefully. Animations should never block the main GUI thread.
- **Reduced Motion**: Always respect system preferences for reduced motion. Allow animations to be toggled off or fall back to instant transitions.

## 6. Empty States, Loading, and Error Recovery
- **Polished Empty States**: Never leave a blank panel. When there's no data (e.g., no files open, empty search results), display:
  - A beautiful, subtle illustration or icon.
  - A friendly, short heading explaining the empty state.
  - A clear call-to-action (CTA) button to help the user get started.
- **Graceful Loading**: Show subtle loaders, progress bars, or skeletons when fetching data or rendering large files.
- **Error States**: Display error messages in context with clear, actionable advice on how to fix them, styled in soft warning colors (e.g., muted amber or red-orange).
