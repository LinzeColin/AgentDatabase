---
name: beautiful-html-templates
description: Reference-only visual template library for HTML slides and presentation aesthetics. Use when Codex needs to choose or compare deck styles, map a presentation brief to a visual direction, or support guizang-ppt-skill/frontend-slides with template inspiration. Not the primary execution skill for building decks; prefer guizang-ppt-skill or frontend-slides for generation.
---

# Beautiful HTML Templates

Use this as a reference library, not as the main deck generator.

## Non-Blocking Style Choice

Do not ask the user to choose a style unless they explicitly want to pick. Read `references/style-selection-matrix.md`, infer the most suitable template family, and proceed with a default. State the selected style and assumptions in the final response.

## Reference Loading

- Start with `references/style-selection-matrix.md`.
- For template inventory, read `references/beautiful-html-templates/index.json`.
- Open only the selected template folder under `references/beautiful-html-templates/templates/<slug>/`.
- Use screenshots under `references/beautiful-html-templates/screenshots/` only when visual comparison is needed.

## Execution Routing

For actual slide generation, use `$frontend-slides` for fixed-stage HTML slides or `$guizang-ppt-skill` for magazine/Swiss-style web PPT. Use this skill to supply aesthetic direction, template candidates, and avoidable style mistakes.
