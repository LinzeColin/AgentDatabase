#!/usr/bin/env python3
"""DSH skin factory: four images in, one installable skin package out.

Reverse-engineered from the four skins already installed on this machine
(dsh-arknights is the cleanest model). A skin is a DSH bundle whose browser
half prepends two layers to <body> — a full-bleed backdrop and a character
stage — scopes every rule under one body attribute, and tears all of it back
out on dispose.

Two decisions that differ from the shipped skins, both paid for in measurement
today (2026-08-19, see ~/.dsh/AGENTS.md 8.8):

*   **No animation, ever.** Deep Whale keeps ten `infinite` CSS animations on
    screen; the compositor then never idles and repaints the whole window every
    frame, at a cost proportional to window pixels — measured 111% CPU idle on
    the 4K TV versus 0.9% with no skin. Generated skins are static art only.
*   **The settings row is pinned.** Deep Whale reserves a fixed block for its
    companion art without accounting for other plugins' footer cards, which
    pushes the settings button past the bottom edge with no way to scroll to
    it. Every generated skin ships the sticky rule that prevents that.

Art contract (what the generator expects in `art/<id>/`):

    bg-light.<ext>    full-bleed background, bright scene
    bg-dark.<ext>     full-bleed background, night scene (optional: reuses light)
    char-left.png     transparent-background character cutout (optional)
    char-right.png    transparent-background character cutout (optional)

Usage:
    python3 build_skin.py --id ganyu --name 甘雨 --accent '#7fd6e8' \\
        --tagline '璃月月海亭' --art art/ganyu --out out
    python3 build_skin.py --manifest characters.json --art art --out out
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environment guard
    sys.exit("Pillow is required: python3 -m pip install Pillow")

# Backgrounds are full-bleed behind a 4K-wide window; characters are cut-outs
# that only ever occupy a side gutter, so they need far less width. Both are
# re-encoded to WebP because every byte lands in a base64 data: URI inside the
# client bundle, which the shell parses on every boot.
BACKGROUND_MAX = (2560, 1440)
CHARACTER_MAX = (900, 1600)
BACKGROUND_QUALITY = 82
CHARACTER_QUALITY = 88

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class Skin:
    """One character's skin definition."""

    id: str
    name: str
    accent: str
    tagline: str
    name_en: str = ""
    description: str = ""
    author: str = ""
    series: str = ""


def encode(path: Path, box: tuple[int, int], quality: int, *, keep_alpha: bool) -> str:
    """Re-encode one image to a WebP data: URI.

    @param path - source image.
    @param box - maximum (width, height); aspect ratio is preserved.
    @param quality - WebP quality.
    @param keep_alpha - keep transparency (characters) or flatten (backgrounds).
    @returns a `data:image/webp;base64,...` string.
    """
    with Image.open(path) as source:
        image = source.convert("RGBA" if keep_alpha else "RGB")
        image.thumbnail(box, Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, "WEBP", quality=quality, method=6)
    return "data:image/webp;base64," + base64.b64encode(buffer.getvalue()).decode()


def find(art_dir: Path, stem: str) -> Path | None:
    """First image in `art_dir` whose stem matches, in preference order."""
    for suffix in (".png", ".webp", ".jpg", ".jpeg"):
        candidate = art_dir / f"{stem}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def client_js(skin: Skin, art: dict[str, str]) -> str:
    """Render the browser half.

    Emitted as plain JS rather than built from TypeScript: the shipped skins
    need tsdown plus the whole @deepseek-ai workspace to build, which makes
    batch production a build-system problem instead of a templating one.
    """
    scope = f"data-dsh-skin-{skin.id}"
    dataset_key = "dshSkin" + "".join(part.capitalize() for part in skin.id.split("-"))
    owner = f"dsh-skin-{skin.id}"

    layers = []
    if "char_left" in art:
        layers.append(("left", art["char_left"]))
    if "char_right" in art:
        layers.append(("right", art["char_right"]))

    css = f"""
body[{scope}] {{
  --skin-bg: url("{art['bg_light']}");
  --skin-scrim: rgba(255,255,255,.55);
  --skin-accent: {skin.accent};
}}
body[{scope}][data-ds-dark-theme] {{
  --skin-bg: url("{art['bg_dark']}");
  --skin-scrim: rgba(6,12,28,.58);
}}
body[{scope}] [data-skin-owner="{owner}"][data-skin-chrome="backdrop"] {{
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: var(--skin-scrim), var(--skin-bg);
  background-size: cover, cover;
  background-position: center, center;
}}
body[{scope}] [data-skin-owner="{owner}"][data-skin-chrome="stage"] {{
  position: fixed; inset: 0; z-index: 1; pointer-events: none; overflow: hidden;
}}
body[{scope}] [data-skin-character] {{
  position: absolute; bottom: 0; height: min(92vh, 1100px);
  width: auto; object-fit: contain; user-select: none;
}}
body[{scope}] [data-skin-character="left"] {{ left: max(0px, var(--skin-sidebar-width, 280px) - 40px); }}
body[{scope}] [data-skin-character="right"] {{ right: 0; }}
/* The chat surface floats above both layers. */
body[{scope}] #root {{ position: relative; z-index: 2; }}
/* Panels get a translucent ground so the art reads through without eating text. */
body[{scope}] [data-pane="sidebar"],
body[{scope}] [class*="sidebarCol"] {{ background: var(--skin-scrim) !important; backdrop-filter: blur(6px); }}
/* Other plugins add footer cards the skin cannot predict; without this the
   settings row is pushed past the bottom edge and cannot be scrolled to. */
body[{scope}] [data-slot="sidebar.settings"] {{ position: sticky !important; bottom: 0 !important; z-index: 3 !important; }}
""".strip()

    image_lines = "\n".join(
        f'      stage.append(image({json.dumps(src)}, {json.dumps(role)}));' for role, src in layers
    )
    stage_block = (
        f"""    const stage = own(document.createElement('div'), 'stage');
{image_lines}
      body.prepend(stage);
      nodes.add(stage);
"""
        if layers
        else "    // no character layers for this skin\n"
    )

    return f"""window.__ModuleLoader__.load({{
\tid: {json.dumps('dsh-skin-' + skin.id)},
\tfactory: (require) => {{
\t\tvar module = {{ exports: {{}} }};
\t\tvar exports = module.exports;
\t\tObject.defineProperty(exports, Symbol.toStringTag, {{ value: 'Module' }});

\t\t/**
\t\t * {skin.name} — generated by skin-factory. Presentation only.
\t\t *
\t\t * Static art, zero animation: a running CSS animation keeps the
\t\t * compositor out of idle and repaints the window every frame, which on a
\t\t * large external display costs more than a full core.
\t\t */
\t\tconst OWNER = {json.dumps(owner)};
\t\tconst TITLE = {json.dumps(skin.name + ' · DeepSeek Harness')};
\t\tconst CSS = {json.dumps(css)};
\t\tconst SIDEBAR = ":is([data-pane='sidebar'], [class*='sidebarCol'])";

\t\t/** Tag a node as ours so teardown can find it again. */
\t\tfunction own(element, chrome) {{
\t\t\telement.dataset.skinOwner = OWNER;
\t\t\telement.dataset.skinChrome = chrome;
\t\t\telement.setAttribute('aria-hidden', 'true');
\t\t\treturn element;
\t\t}}

\t\t/** One character layer. */
\t\tfunction image(src, role) {{
\t\t\tconst node = own(document.createElement('img'), 'character');
\t\t\tnode.src = src;
\t\t\tnode.alt = '';
\t\t\tnode.draggable = false;
\t\t\tnode.dataset.skinCharacter = role;
\t\t\treturn node;
\t\t}}

\t\t/** Required services: none — this half only paints. */
\t\tconst inject = [];

\t\t/**
\t\t * Mount the skin and hand back its teardown.
\t\t * @param ctx - cordis context (client half).
\t\t */
\t\tfunction apply(ctx) {{
\t\t\tctx.effect(() => {{
\t\t\t\tconst body = document.body;
\t\t\t\tconst previousTitle = document.title;
\t\t\t\tconst nodes = new Set();

\t\t\t\tconst style = own(document.createElement('style'), 'style');
\t\t\t\tstyle.textContent = CSS;
\t\t\t\tdocument.head.append(style);
\t\t\t\tnodes.add(style);

\t\t\t\tconst backdrop = own(document.createElement('div'), 'backdrop');
\t\t\t\tbody.prepend(backdrop);
\t\t\t\tnodes.add(backdrop);

{stage_block}
\t\t\t\t// Track the sidebar width so the left character never slides under it.
\t\t\t\tlet observed;
\t\t\t\tconst resize = typeof ResizeObserver === 'undefined' ? undefined : new ResizeObserver((entries) => {{
\t\t\t\t\tconst entry = entries.at(-1);
\t\t\t\t\tif (entry !== undefined) body.style.setProperty('--skin-sidebar-width', Math.round(entry.contentRect.width) + 'px');
\t\t\t\t}});
\t\t\t\tconst track = () => {{
\t\t\t\t\tconst sidebar = document.querySelector(SIDEBAR);
\t\t\t\t\tif (sidebar === null) return;
\t\t\t\t\tbody.style.setProperty('--skin-sidebar-width', Math.round(sidebar.getBoundingClientRect().width) + 'px');
\t\t\t\t\tif (resize !== undefined && observed !== sidebar) {{
\t\t\t\t\t\tif (observed !== undefined) resize.unobserve(observed);
\t\t\t\t\t\tobserved = sidebar;
\t\t\t\t\t\tresize.observe(sidebar);
\t\t\t\t\t}}
\t\t\t\t}};
\t\t\t\tconst structure = new MutationObserver(track);
\t\t\t\tstructure.observe(body, {{ childList: true, subtree: true }});

\t\t\t\tbody.dataset.{dataset_key} = '';
\t\t\t\tdocument.title = TITLE;
\t\t\t\ttrack();

\t\t\t\treturn () => {{
\t\t\t\t\tstructure.disconnect();
\t\t\t\t\tresize?.disconnect();
\t\t\t\t\tfor (const node of nodes) node.remove();
\t\t\t\t\tdelete body.dataset.{dataset_key};
\t\t\t\t\tbody.style.removeProperty('--skin-sidebar-width');
\t\t\t\t\tif (document.title === TITLE) document.title = previousTitle;
\t\t\t\t}};
\t\t\t}}, {json.dumps(owner + ': presentation layer')});
\t\t}}

\t\texports.apply = apply;
\t\texports.inject = inject;
\t\treturn module.exports;
\t}}
}});
"""


def build(skin: Skin, art_dir: Path, out_dir: Path) -> Path:
    """Assemble one installable skin package.

    @param skin - the character definition.
    @param art_dir - directory holding this character's source images.
    @param out_dir - where the package directory is written.
    @returns the package directory.
    """
    if not ID_RE.match(skin.id):
        raise ValueError(f"id {skin.id!r} must be lowercase alphanumeric with dashes")

    bg_light = find(art_dir, "bg-light")
    if bg_light is None:
        raise FileNotFoundError(f"{art_dir}/bg-light.(png|webp|jpg) is required")
    bg_dark = find(art_dir, "bg-dark") or bg_light

    art = {
        "bg_light": encode(bg_light, BACKGROUND_MAX, BACKGROUND_QUALITY, keep_alpha=False),
        "bg_dark": encode(bg_dark, BACKGROUND_MAX, BACKGROUND_QUALITY, keep_alpha=False),
    }
    for key, stem in (("char_left", "char-left"), ("char_right", "char-right")):
        source = find(art_dir, stem)
        if source is not None:
            art[key] = encode(source, CHARACTER_MAX, CHARACTER_QUALITY, keep_alpha=True)

    package = f"dsh-skin-{skin.id}"
    root = out_dir / package
    if root.exists():
        shutil.rmtree(root)
    (root / "lib").mkdir(parents=True)
    (root / "preview").mkdir()

    (root / "lib" / "client.js").write_text(client_js(skin, art), encoding="utf-8")
    (root / "lib" / "index.js").write_text(
        "/** Host half of a browser-only skin: the loader row needs a plugin, "
        "and all the work happens in lib/client.js. */\n"
        f"const name = {json.dumps('ui-skin-' + skin.id)}\n"
        "const inject = []\n"
        "function apply() {}\n"
        "export { apply, inject, name }\n",
        encoding="utf-8",
    )
    (root / "cordis.patch.yml").write_text(
        "# Mounts this skin's loader row. Mutual exclusion between skins is\n"
        "# managed by the skin center's `disabled` rows in ~/.dsh/cordis.patch.yml.\n"
        "- insert:\n"
        f"    - id: ui-skin-{skin.id}\n"
        f"      name: {package}\n",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        json.dumps(
            {
                "name": package,
                "version": "0.1.0",
                "private": True,
                "description": f"{skin.name} — non-commercial fan skin for DeepSeek Harness",
                "type": "module",
                "main": "lib/index.js",
                "exports": {
                    ".": "./lib/index.js",
                    "./client": "./lib/client.js",
                    "./skin.json": "./skin.json",
                    "./package.json": "./package.json",
                },
                "dsh": {
                    "bundle": {"patch": "./cordis.patch.yml"},
                    "client": {"inject": [], "platform": "web"},
                },
                "license": "CC-BY-NC-4.0",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "skin.json").write_text(
        json.dumps(
            {
                "id": skin.id,
                "name": skin.name,
                "nameEn": skin.name_en or skin.id,
                "author": skin.author or "local",
                "tagline": skin.tagline,
                "description": skin.description
                or f"{skin.name} 同人皮肤，仅供个人非商业使用。静态美术，无常驻动画。",
                "tags": ["anime", "fan-art", "static"] + ([skin.series] if skin.series else []),
                "accent": skin.accent,
                "bodyAttr": f"data-dsh-skin-{skin.id}",
                "package": package,
                "wiring": {"id": f"ui-skin-{skin.id}", "bundleWired": True},
                "order": 9,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "NOTICE").write_text(
        f"{skin.name} fan skin.\n\n"
        "Character designs are the property of their respective rights holders.\n"
        "This package is unofficial fan work for personal, non-commercial use only.\n"
        "Do not redistribute or sell.\n",
        encoding="utf-8",
    )
    shutil.copyfile(bg_light, root / "preview" / ("cover" + bg_light.suffix))

    size = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
    print(f"  ✓ {package:<28} {size / 1024 / 1024:5.1f} MB  ({len(art)} 张图)")
    return root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="JSON array of skin definitions for batch mode")
    parser.add_argument("--id")
    parser.add_argument("--name")
    parser.add_argument("--accent", default="#c5a468")
    parser.add_argument("--tagline", default="")
    parser.add_argument("--series", default="")
    parser.add_argument("--art", type=Path, required=True, help="art dir (single) or art root (batch)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    if args.manifest is not None:
        entries = json.loads(args.manifest.read_text(encoding="utf-8"))
        print(f"批量构建 {len(entries)} 张皮肤：")
        built = 0
        for entry in entries:
            skin = Skin(**{k: v for k, v in entry.items() if k in Skin.__dataclass_fields__})
            art_dir = args.art / skin.id
            if not art_dir.is_dir():
                print(f"  ✗ {skin.id:<28} 缺素材目录 {art_dir}")
                continue
            try:
                build(skin, art_dir, args.out)
                built += 1
            except (FileNotFoundError, ValueError) as error:
                print(f"  ✗ {skin.id:<28} {error}")
        print(f"完成 {built}/{len(entries)}")
        return

    if args.id is None or args.name is None:
        parser.error("single mode needs --id and --name (or use --manifest)")
    build(Skin(id=args.id, name=args.name, accent=args.accent, tagline=args.tagline, series=args.series),
          args.art, args.out)


if __name__ == "__main__":
    main()
