# Light-mode reach audit (AC-007 / AC-008)

`light` is the first-use default, so the original ten views have to be readable in
it, not merely reachable. The taskpack CSS ships a compatibility layer covering
the shell chrome only, with an explicit instruction to extend it from a real
browser audit. This is that audit.

Method: drive the built preview through all thirteen routes in light mode and
record, per element, (a) its own background colour composited over white and
(b) its text colour. Anything that still paints a near-black surface, or light
text where the surface is now light, is a gap.

| Pass | Dark surfaces still painting near-black | Light-on-light text |
|---|---|---|
| Taskpack CSS as shipped | 64 class signatures | 32 |
| After the extension | 9 | 7 |

## What the residue is — and why it stays

All nine remaining dark surfaces are intentional:

- `.galaxy-scene`, `.galaxy-webgl-canvas`, `.data-guide-canvas`,
  `.memory-river-canvas`, `.semantic-bubble-canvas`, `.obsidian-scene-shell`,
  and the two `svg` visualisation canvases — the dark backdrop **is** the
  starfield/graph rendering. Lightening them would destroy the visualisation.
- `.map-legend i` colour swatches — those pixels are data, not chrome.
- `.active` at `rgb(0,127,156)` — the theme accent behind a selected control,
  carrying white text.

The seven light-on-light residues are the white labels sitting on that solid
accent fill (correct), plus four elements across two views.

## Why the token approach was not available

`MemoryAtlas/src/styles.css` is 215 KB and defines no colour tokens: the palette
is hard-coded (`#f4f1e8` base text, `#d9d4ca` / `#cfc8bd` muted, `rgba(9,10,13,·)`
panels). There is no variable to re-point, and editing `styles.css` would not be
additive. The extension therefore does two things inside
`.app-shell[data-memory-atlas-mode="light"]` only:

1. names the surfaces the audit found and gives them a light panel/inset colour;
2. re-anchors text to `color: inherit` inside the two shell containers so every
   original component picks up `--ma31-text`, then re-asserts the visualisation
   canvases, accent controls and `.positive` / `.negative` semantics.

Data visualisations paint with SVG `fill`/`stroke` attributes rather than
`color`, so their marks are untouched by step 2.

Dark mode is unchanged, and `<html>` now follows the selected mode so the page
behind the shell no longer shows a black gutter under the light layout.
