#!/usr/bin/env python3
"""Audit the bounded, owner-readable Memory Atlas document plane."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


EXPECTED_FILES = {
    "快速开始.md",
    "系统使用.md",
    "功能工作流.md",
    "同步备份.md",
    "模型参数.md",
    "版本路线图.md",
    "维护故障.md",
}
MOJIBAKE_MARKERS = ("\ufffd", "锟斤拷", "烫烫烫", "屯屯屯")
INLINE_LINK_RE = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
REFERENCE_DEFINITION_RE = re.compile(r"(?m)^[ \t]{0,3}\[([^\]\n]+)\]:[ \t]*(<[^>\n]+>|\S+)")
REFERENCE_USE_RE = re.compile(r"!?\[([^\]\n]+)\](?:\[([^\]\n]*)\])?")
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")


def normalize_reference_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def markdown_link_targets(text: str) -> list[str]:
    """Return inline and reference-style Markdown targets, including images."""

    targets = [match.group(1) for match in INLINE_LINK_RE.finditer(text)]
    definitions = {
        normalize_reference_label(match.group(1)): match.group(2)
        for match in REFERENCE_DEFINITION_RE.finditer(text)
    }
    for match in REFERENCE_USE_RE.finditer(text):
        if match.end() < len(text) and text[match.end()] == "(":
            continue
        explicit_label = match.group(2)
        label = explicit_label if explicit_label else match.group(1)
        target = definitions.get(normalize_reference_label(label))
        if target is not None:
            targets.append(target)
    return targets


def classify_local_link(raw_target: str, *, source_path: Path, human_root: Path) -> tuple[str, str] | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    target = unquote(target)
    parsed = urlsplit(target)
    if parsed.scheme in {"http", "https", "mailto"}:
        return None
    if parsed.scheme or parsed.netloc:
        return ("unsupported", raw_target)
    if not parsed.path:
        return None

    candidate = Path(parsed.path)
    resolved = candidate.resolve() if candidate.is_absolute() else (source_path.parent / candidate).resolve()
    try:
        resolved.relative_to(human_root)
    except ValueError:
        return ("outside", raw_target)
    if not resolved.exists():
        return ("broken", raw_target)
    return None


def audit(database_dir: Path) -> dict[str, object]:
    human_dir = database_dir / "人类可读"
    errors: list[str] = []
    file_reports: list[dict[str, object]] = []

    if not human_dir.is_dir():
        return {"status": "FAIL", "human_dir": str(human_dir), "errors": ["人类可读目录不存在"]}

    human_root = human_dir.resolve()
    direct_files = sorted(path for path in human_dir.iterdir() if path.is_file())
    direct_names = {path.name for path in direct_files}
    nested_files = sorted(path for path in human_dir.rglob("*") if path.is_file() and path.parent != human_dir)
    nested_dirs = sorted(path for path in human_dir.rglob("*") if path.is_dir())

    if direct_names != EXPECTED_FILES:
        errors.append(
            "核心文件集合不一致："
            f"缺少={sorted(EXPECTED_FILES - direct_names)}，多出={sorted(direct_names - EXPECTED_FILES)}"
        )
    if len(direct_files) > 7:
        errors.append(f"核心文件超过 7 个：{len(direct_files)}")
    if nested_files or nested_dirs:
        errors.append(
            "人类目录必须保持浅层："
            f"nested_files={[str(path.relative_to(human_dir)) for path in nested_files]}，"
            f"nested_dirs={[str(path.relative_to(human_dir)) for path in nested_dirs]}"
        )

    for path in direct_files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{path.name} 不是有效 UTF-8：{exc}")
            continue

        chinese_chars = len(CHINESE_RE.findall(text))
        markdown_links = markdown_link_targets(text)
        local_link_errors: list[str] = []
        outside_link_errors: list[str] = []
        unsupported_link_errors: list[str] = []
        for raw_target in markdown_links:
            classification = classify_local_link(raw_target, source_path=path, human_root=human_root)
            if classification is None:
                continue
            kind, _ = classification
            if kind == "broken":
                local_link_errors.append(raw_target)
            elif kind == "outside":
                outside_link_errors.append(raw_target)
            else:
                unsupported_link_errors.append(raw_target)

        if not text.startswith("# "):
            errors.append(f"{path.name} 缺少一级中文标题")
        if "## 结论" not in text or "## 操作" not in text:
            errors.append(f"{path.name} 必须直接提供“结论”和“操作”")
        if chinese_chars < 250:
            errors.append(f"{path.name} 中文说明不足：{chinese_chars} 字")
        if any(marker in text for marker in MOJIBAKE_MARKERS):
            errors.append(f"{path.name} 命中乱码标记")
        if "Machine-readable boundary summary" in text:
            errors.append(f"{path.name} 包含旧机器边界摘要")
        if len(markdown_links) > 8:
            errors.append(f"{path.name} 链接过多，疑似链接索引：{len(markdown_links)}")
        if local_link_errors:
            errors.append(f"{path.name} 存在断链：{local_link_errors}")
        if outside_link_errors:
            errors.append(f"{path.name} 存在人类目录外链接：{outside_link_errors}")
        if unsupported_link_errors:
            errors.append(f"{path.name} 存在不支持的链接协议：{unsupported_link_errors}")

        file_reports.append(
            {
                "file": path.name,
                "lines": text.count("\n"),
                "chinese_chars": chinese_chars,
                "markdown_links": len(markdown_links),
                "broken_local_links": local_link_errors,
                "outside_human_dir_links": outside_link_errors,
                "unsupported_links": unsupported_link_errors,
            }
        )

    return {
        "status": "PASS" if not errors else "FAIL",
        "human_dir": str(human_dir),
        "file_count": len(direct_files),
        "nested_file_count": len(nested_files),
        "files": file_reports,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="OpenAIDatabase directory; defaults to the script parent project.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit(args.database_dir.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
