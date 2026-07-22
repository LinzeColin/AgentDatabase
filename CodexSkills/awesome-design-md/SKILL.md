---
name: awesome-design-md
description: Use when Codex needs brand-specific DESIGN.md reference material for UI generation, redesign, product visual direction, design-language matching, or frontend styling inspired by a known product or company such as Apple, Airbnb, Stripe, Vercel, Linear, Notion, Shopify, NVIDIA, Tesla, Uber, or similar entries from VoltAgent/awesome-design-md.
---

# Awesome Design MD

Use the bundled `references/source/design-md/` directory as a local library of brand and product `DESIGN.md` files.

## Workflow

1. Identify the requested brand, product, or visual reference.
2. Search locally first:
   - List available slugs with `find references/source/design-md -maxdepth 1 -type d`.
   - Search by name with `rg -i "<brand|product>" references/source/README.md references/source/design-md`.
3. Read only the relevant files:
   - `references/source/design-md/<slug>/README.md` for the short description.
   - `references/source/design-md/<slug>/DESIGN.md` for design rules, tokens, layout patterns, typography, colors, and component guidance.
4. Apply the selected design language to the current task while respecting the user's app context, existing design system, and accessibility constraints.

## Constraints

- Do not load the whole repository into context.
- Do not claim the bundled design files are current; they are a local snapshot from `VoltAgent/awesome-design-md`.
- If the user asks for the latest brand guidance or official design-system truth, verify from the official source before relying on the snapshot.
- Treat these references as inspiration unless the user explicitly requests faithful emulation.
