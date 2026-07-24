#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from registry_core import default_registry_root, validate_registry, write_index

START = "<!-- PERSONA-REGISTRY:START -->"
END = "<!-- PERSONA-REGISTRY:END -->"


def atomic_write_text(path: Path, text: str) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def compact(values: Any, limit: int = 2) -> str:
    if not isinstance(values, list):
        return ""
    cleaned = [str(value).replace("|", "\\|").strip() for value in values if str(value).strip()]
    return "；".join(cleaned[:limit])


def registry_block(index: dict[str, Any], *, route_view: bool) -> str:
    products = index.get("products", [])
    if not products:
        return (
            f"{START}\n"
            "当前登记：**0 个人物**。路由时必须返回 `insufficient_roster`，不得虚构候选。\n"
            f"{END}"
        )
    lines = [START]
    if route_view:
        lines.extend(
            [
                f"当前唯一登记：**{len(products)} 个人物**。",
                "",
                "| 人物 | 唯一身份 | 版本 | 场景 | 关键能力 | 准备度 |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in products:
            lines.append(
                "| {name} | `{category}` | `{version}` | {scenarios} | {capabilities} | `{readiness}` |".format(
                    name=str(item.get("canonical_name", "")).replace("|", "\\|"),
                    category=str(item.get("registration_category", "")).replace("|", "\\|"),
                    version=str(item.get("latest_product_version", "")).replace("|", "\\|"),
                    scenarios=compact(item.get("application_scenarios")),
                    capabilities=compact(item.get("key_capabilities")),
                    readiness=str(item.get("readiness", "")),
                )
            )
    else:
        lines.extend(
            [
                "",
                "| 人物 | 唯一身份 | 版本 | 选入原因 | 最值得蒸馏的特点 | 对用户的利益/帮助 | 应用场景 | 关键能力 | 完整 ZIP |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for item in products:
            artifact = str(item.get("latest_artifact", ""))
            lines.append(
                "| {name} | `{category}` | `{version}` | {reason} | {traits} | {value} | {scenarios} | {capabilities} | [ZIP]({artifact}) |".format(
                    name=str(item.get("canonical_name", "")).replace("|", "\\|"),
                    category=str(item.get("registration_category", "")).replace("|", "\\|"),
                    version=str(item.get("latest_product_version", "")).replace("|", "\\|"),
                    reason=compact(item.get("selection_reasons")),
                    traits=compact(item.get("distillation_traits")),
                    value=compact(item.get("user_value")),
                    scenarios=compact(item.get("application_scenarios")),
                    capabilities=compact(item.get("key_capabilities")),
                    artifact=artifact,
                )
            )
    lines.append(END)
    return "\n".join(lines)


def replace_block(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    start = text.find(START)
    end = text.find(END)
    if start < 0 or end < start:
        raise ValueError(f"registry markers missing or reversed: {path}")
    end += len(END)
    atomic_write_text(path, text[:start] + block + text[end:])


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild persona team index and human registry tables.")
    parser.add_argument("--registry-root", type=Path, default=default_registry_root())
    args = parser.parse_args()
    root = args.registry_root.expanduser().resolve()
    index = write_index(root)
    replace_block(root / "README.md", registry_block(index, route_view=False))
    replace_block(root / "CANONICAL-ROOT-ROUTE.md", registry_block(index, route_view=True))
    validation = validate_registry(root)
    print(
        json.dumps(
            {
                "products": len(index["products"]),
                "index": str(root / "team-index.json"),
                "readme": str(root / "README.md"),
                "route": str(root / "CANONICAL-ROOT-ROUTE.md"),
                "validation": validation,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if validation["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
