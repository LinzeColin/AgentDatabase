---
name: html-anything
description: "Use when converting notes, Markdown, structured data, reports, cards, decks, posters, dashboards, resumes, or social posts into polished single-file HTML artifacts, or when selecting from the html-anything template/skill catalog as design reference."
---

# HTML Anything

Use this skill as a global wrapper around the upstream `nexu-io/html-anything`
repository.

## When To Use

- Build a polished HTML artifact from Markdown, prose notes, CSV/JSON/table data, or rough content.
- Choose an HTML template direction for decks, reports, magazine pages, posters, Xiaohongshu cards, X/Twitter cards, dashboards, web prototypes, resumes, or Hyperframes-style video frames.
- Inspect or reuse the upstream template skill catalog under `references/html-anything/next/src/lib/templates/skills/`.
- Run or modify the upstream HTML Anything app only when the user explicitly asks for the local app, CLI, or repository behavior.

## Reference Loading

Start with:

- `references/source.md` for pinned upstream source information.
- `references/html-anything/README.md` for product behavior, quickstart, supported agents, export targets, and the template catalog.
- `references/html-anything/next/src/lib/templates/skills/` for concrete template skills and examples.
- `references/html-anything/docs/screenshots/` when visual comparison is useful.

Load only the specific template folder needed for the requested surface. Do not read
the full template catalog unless the user asks for an inventory or comparison.

## Execution Rules

- Default to producing a standalone, user-facing HTML artifact when the user asks for an output, not merely describing the upstream app.
- If the request is a deck or slide workflow and `$frontend-slides` or `$guizang-ppt-skill` is a closer execution fit, use those skills for generation and use this skill as template/design reference.
- If the user asks to run the app, follow the upstream quickstart from `references/html-anything/README.md`.
- Do not require an API key by default; upstream HTML Anything is designed to reuse local coding-agent CLI sessions.
