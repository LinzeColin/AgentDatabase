#!/usr/bin/env python3
"""Build a self-contained, no-JavaScript acceptance evidence gallery.

Usage:
    python3 make_gallery.py pairs.csv gallery.html

v2 CSV header:
    id,label,reference,actual,status,severity,note

For v1 compatibility, rows without a header are accepted as:
    label,reference,actual

Image paths must be relative to the CSV directory and stay inside it after
symlink resolution. PNG, JPEG, GIF and WebP are accepted and embedded as data
URLs. SVG and remote URLs are rejected to keep the artifact inert.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


class GalleryError(ValueError):
    """Raised for unsafe or invalid gallery input."""


@dataclass(frozen=True)
class EvidenceImage:
    data_url: str
    sha256: str
    size_bytes: int
    source: str


@dataclass(frozen=True)
class GalleryRow:
    test_id: str
    label: str
    reference: str
    actual: str
    status: str
    severity: str
    note: str


ALLOWED_STATUSES = {
    "PLANNED",
    "RUNNING",
    "PASS",
    "FAIL",
    "BLOCKED",
    "NOT_RUN",
    "NOT_APPLICABLE",
    "WAIVED",
    "UNKNOWN",
}
MAX_DEFAULT_IMAGE_BYTES = 15 * 1024 * 1024


def _detect_mime(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _inside(child: Path, root: Path) -> bool:
    try:
        child.relative_to(root)
        return True
    except ValueError:
        return False


def load_image(raw_path: str, root: Path, max_bytes: int) -> Optional[EvidenceImage]:
    raw_path = raw_path.strip()
    if not raw_path:
        return None
    if "\x00" in raw_path or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", raw_path):
        raise GalleryError(f"remote/schemed image path is forbidden: {raw_path!r}")
    relative = Path(raw_path)
    if relative.is_absolute():
        raise GalleryError(f"absolute image path is forbidden: {raw_path!r}")

    resolved = (root / relative).resolve()
    if not _inside(resolved, root):
        raise GalleryError(f"image path escapes gallery root: {raw_path!r}")
    if not resolved.is_file():
        raise GalleryError(f"image not found: {raw_path!r}")
    size = resolved.stat().st_size
    if size > max_bytes:
        raise GalleryError(f"image exceeds limit ({size} > {max_bytes} bytes): {raw_path!r}")
    data = resolved.read_bytes()
    mime = _detect_mime(data)
    if mime is None:
        raise GalleryError(f"unsupported or invalid raster image: {raw_path!r}")
    encoded = base64.b64encode(data).decode("ascii")
    return EvidenceImage(
        data_url=f"data:{mime};base64,{encoded}",
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=size,
        source=raw_path,
    )


def _clean_rows(reader: Iterable[list[str]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        if row[0].lstrip().startswith("#"):
            continue
        rows.append([cell.strip() for cell in row])
    return rows


def read_rows(csv_path: Path) -> list[GalleryRow]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = _clean_rows(csv.reader(handle))
    if not rows:
        raise GalleryError("pairs CSV has no evidence rows")

    header = [cell.lower() for cell in rows[0]]
    has_header = "label" in header and ("actual" in header or "implementation" in header)
    parsed: list[GalleryRow] = []
    if has_header:
        index = {name: pos for pos, name in enumerate(header)}

        def get(row: list[str], *names: str) -> str:
            for name in names:
                pos = index.get(name)
                if pos is not None and pos < len(row):
                    return row[pos]
            return ""

        for number, row in enumerate(rows[1:], 1):
            label = get(row, "label")
            if not label:
                raise GalleryError(f"row {number + 1} has an empty label")
            status = (get(row, "status") or "UNKNOWN").upper()
            if status not in ALLOWED_STATUSES:
                raise GalleryError(f"row {number + 1} has invalid status: {status!r}")
            parsed.append(
                GalleryRow(
                    test_id=get(row, "id") or f"E-{number:03d}",
                    label=label,
                    reference=get(row, "reference", "ref"),
                    actual=get(row, "actual", "implementation", "impl"),
                    status=status,
                    severity=get(row, "severity").upper(),
                    note=get(row, "note"),
                )
            )
    else:
        for number, row in enumerate(rows, 1):
            padded = (row + ["", ""])[:3]
            if not padded[0]:
                raise GalleryError(f"row {number} has an empty label")
            parsed.append(
                GalleryRow(
                    test_id=f"E-{number:03d}",
                    label=padded[0],
                    reference=padded[1],
                    actual=padded[2],
                    status="UNKNOWN",
                    severity="",
                    note="Imported from v1 three-column format",
                )
            )
    if not parsed:
        raise GalleryError("pairs CSV contains a header but no evidence rows")
    return parsed


def _figure(image: Optional[EvidenceImage], caption: str, alt: str) -> str:
    if image is None:
        return (
            '<figure class="empty"><div class="placeholder">无图像</div>'
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    metadata = f"SHA-256 {image.sha256[:16]}… · {image.size_bytes} bytes"
    return (
        "<figure>"
        f'<img src="{image.data_url}" alt="{html.escape(alt, quote=True)}">'
        f"<figcaption>{html.escape(caption)}<small>{html.escape(metadata)}</small></figcaption>"
        "</figure>"
    )


def build_html(rows: list[GalleryRow], root: Path, max_bytes: int) -> str:
    cards: list[str] = []
    for row in rows:
        reference = load_image(row.reference, root, max_bytes)
        actual = load_image(row.actual, root, max_bytes)
        status_class = row.status.lower().replace("_", "-")
        severity = f'<span class="severity">{html.escape(row.severity)}</span>' if row.severity else ""
        cards.append(
            '<section class="card">'
            '<header>'
            f'<span class="test-id">{html.escape(row.test_id)}</span>'
            f"<h2>{html.escape(row.label)}</h2>"
            f'<span class="status {html.escape(status_class)}">{html.escape(row.status)}</span>{severity}'
            "</header>"
            '<div class="pair">'
            + _figure(reference, "基准", f"{row.label} 基准图")
            + _figure(actual, "实际", f"{row.label} 实际图")
            + "</div>"
            f'<p class="note">{html.escape(row.note) if row.note else "无补充说明"}</p>'
            '<p class="judge">Owner 仲裁：☐ 接受　☐ 打回（L0/L1/L2）　☐ 升级讨论</p>'
            "</section>"
        )

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Verifier 验收证据画廊</title>
<style>
:root{{--bg:#0b1020;--panel:#141b2d;--text:#edf2ff;--muted:#aeb9d2;--line:#2c3855;--accent:#88aaff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,sans-serif}}
main{{max-width:1400px;margin:auto;padding:28px}} .intro{{color:var(--muted);max-width:900px}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px;margin:20px 0}}
header{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}} h1{{font-size:24px}} h2{{font-size:17px;margin:0;flex:1}}
.test-id,.status,.severity{{border:1px solid var(--line);border-radius:999px;padding:3px 9px;font-size:12px}}
.status.pass{{background:#123c2d}} .status.fail{{background:#5a1f28}} .status.blocked,.status.not-run{{background:#5a4517}}
.pair{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:14px}}
figure{{margin:0;min-width:0}} img,.placeholder{{width:100%;min-height:180px;max-height:70vh;object-fit:contain;background:#070a12;border:1px solid var(--line);border-radius:8px}}
.placeholder{{display:grid;place-items:center;color:var(--muted)}} figcaption{{text-align:center;color:var(--muted);margin-top:5px}}
figcaption small{{display:block;font-size:11px}} .note{{white-space:pre-wrap}} .judge{{color:#f4cf7a;border-top:1px solid var(--line);padding-top:10px}}
@media(max-width:760px){{main{{padding:14px}}.pair{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>Verifier 验收证据画廊</h1>
<p class="intro">共 {len(rows)} 项。图像已内嵌，状态仍以 TEST_MATRIX、原始结果和 VERDICT 为准；画廊不能单独证明验收通过。</p>
{''.join(cards)}
</main></body></html>"""


def generate_gallery(csv_path: Path, output_path: Path, max_bytes: int) -> int:
    csv_path = csv_path.resolve()
    if not csv_path.is_file():
        raise GalleryError(f"pairs CSV not found: {csv_path}")
    root = csv_path.parent.resolve()
    rows = read_rows(csv_path)
    document = build_html(rows, root, max_bytes)
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", dir=str(output_path.parent), text=True
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(document)
        os.replace(temporary_name, output_path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return len(rows)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs_csv", type=Path)
    parser.add_argument("output_html", type=Path)
    parser.add_argument("--max-image-mb", type=float, default=15.0)
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    if args.max_image_mb <= 0:
        print("error: --max-image-mb must be positive", file=sys.stderr)
        return 2
    try:
        count = generate_gallery(
            args.pairs_csv, args.output_html, int(args.max_image_mb * 1024 * 1024)
        )
    except (GalleryError, OSError, UnicodeError, csv.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"done: {args.output_html} ({count} items, self-contained)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
