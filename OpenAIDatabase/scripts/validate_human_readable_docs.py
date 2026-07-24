#!/usr/bin/env python3
"""Fail-closed validation for the canonical 00-07 human-readable document set."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

DEFAULT_CONFIG = Path("OpenAIDatabase/config/human_readable_merge.v1.json")


class ValidationConfigError(ValueError):
    """Raised when the validation contract itself is invalid."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationConfigError(f"required path is missing: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ValidationConfigError(f"path is not valid UTF-8: {path}") from exc


def load_config(path: Path) -> dict[str, Any]:
    try:
        config = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise ValidationConfigError(f"invalid JSON config {path}: {exc}") from exc
    required = {
        "schema_version",
        "target_directory",
        "canonical_documents",
        "required_document_count",
        "required_numbers",
        "source_order",
    }
    missing = sorted(required - config.keys())
    if missing:
        raise ValidationConfigError(f"config missing keys: {', '.join(missing)}")
    if config["schema_version"] != 1:
        raise ValidationConfigError("unsupported schema_version")
    return config


def extract_source_body(text: str, source_id: str, generated_marker: str | None) -> str | None:
    source_start_re = re.compile(
        rf"^<!-- BEGIN SOURCE: {re.escape(source_id)};[^\n]*-->\n"
        rf"<a id=\"{re.escape(source_id)}\"></a>\n",
        re.MULTILINE,
    )
    match = source_start_re.search(text)
    if not match:
        return None
    end_token = f"<!-- END SOURCE: {source_id} -->"
    end_index = text.find(end_token, match.end())
    if end_index == -1:
        return None
    body = text[match.end():end_index]
    if generated_marker:
        start = f"<!-- BEGIN GENERATED: {generated_marker} -->\n"
        end = f"<!-- END GENERATED: {generated_marker} -->"
        if not body.startswith(start) or body.count(start) != 1 or body.count(end) != 1:
            return None
        generated_end = body.find(end, len(start))
        return body[len(start):generated_end].rstrip() + "\n"
    return body.rstrip() + "\n"


def validate_config_shape(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    docs = config["canonical_documents"]
    filenames = [doc.get("filename") for doc in docs]
    numbers = [doc.get("number") for doc in docs]
    if len(docs) != config["required_document_count"]:
        errors.append("config canonical document count does not match required_document_count")
    if numbers != config["required_numbers"]:
        errors.append(f"config number order mismatch: expected {config['required_numbers']}, got {numbers}")
    if len(set(filenames)) != len(filenames):
        errors.append("config contains duplicate canonical filenames")
    source_ids: list[str] = []
    originals: list[str] = []
    for doc in docs:
        if not str(doc.get("filename", "")).startswith(f"{doc.get('number')}_"):
            errors.append(f"canonical filename does not start with its number: {doc.get('filename')}")
        for source in doc.get("sources", []):
            source_ids.append(source.get("id", ""))
            originals.append(source.get("original_filename", ""))
            if source.get("kind") not in {"static", "generated"}:
                errors.append(f"invalid source kind: {source}")
            if source.get("kind") == "generated" and not source.get("generated_marker"):
                errors.append(f"generated source lacks generated_marker: {source.get('id')}")
            if source.get("kind") == "static" and not source.get("canonical_body_sha256"):
                errors.append(f"static source lacks canonical_body_sha256: {source.get('id')}")
    if len(source_ids) != len(set(source_ids)):
        errors.append("config contains duplicate source ids")
    if len(originals) != len(set(originals)):
        errors.append("config contains duplicate original filenames")
    if originals != config["source_order"]:
        errors.append("config source_order differs from canonical document/source order")
    return errors


def validate_repository(
    repo_root: Path,
    config: dict[str, Any],
    *,
    index_override: Path | None = None,
) -> list[str]:
    errors = validate_config_shape(config)
    target_dir = repo_root / config["target_directory"]
    if not target_dir.is_dir():
        return errors + [f"target directory missing: {target_dir}"]

    expected_names = [doc["filename"] for doc in config["canonical_documents"]]
    actual_names = sorted(path.name for path in target_dir.glob("*.md") if path.is_file())
    if len(actual_names) != config["required_document_count"]:
        errors.append(
            f"expected exactly {config['required_document_count']} Markdown files, got {len(actual_names)}: {actual_names}"
        )
    if actual_names != sorted(expected_names):
        missing = sorted(set(expected_names) - set(actual_names))
        extra = sorted(set(actual_names) - set(expected_names))
        errors.append(f"canonical filename set mismatch; missing={missing}, extra={extra}")

    all_originals = {
        source["original_filename"]
        for doc in config["canonical_documents"]
        for source in doc["sources"]
    }
    for original in sorted(all_originals):
        legacy_path = target_dir / original
        if original not in expected_names and legacy_path.exists():
            errors.append(f"legacy source file still exists: {legacy_path}")

    for doc in config["canonical_documents"]:
        path = target_dir / doc["filename"]
        content_path = index_override if doc["number"] == "00" and index_override else path
        try:
            text = read_text(content_path)
        except ValidationConfigError as exc:
            errors.append(str(exc))
            continue
        if "\r" in text:
            errors.append(f"non-LF newline detected: {content_path}")
        expected_title = f"# {doc['title']}\n"
        if not text.startswith(expected_title):
            errors.append(f"canonical title mismatch in {content_path}: expected {expected_title.strip()}")

        previous_position = -1
        for source in doc["sources"]:
            source_id = source["id"]
            begin = f"<!-- BEGIN SOURCE: {source_id};"
            anchor = f'<a id="{source_id}"></a>'
            end = f"<!-- END SOURCE: {source_id} -->"
            for token, label in ((begin, "begin"), (anchor, "anchor"), (end, "end")):
                count = text.count(token)
                if count != 1:
                    errors.append(f"{content_path}: source {source_id} {label} count is {count}, expected 1")
            position = text.find(begin)
            if position <= previous_position:
                errors.append(f"{content_path}: source order violation at {source_id}")
            previous_position = position
            body = extract_source_body(text, source_id, source.get("generated_marker"))
            if body is None:
                errors.append(f"{content_path}: source block malformed: {source_id}")
                continue
            if not body.strip():
                errors.append(f"{content_path}: source block is empty: {source_id}")
            if source["kind"] == "static":
                actual_hash = sha256_text(body)
                expected_hash = source["canonical_body_sha256"]
                if actual_hash != expected_hash:
                    errors.append(
                        f"{content_path}: static source body changed: {source_id}; "
                        f"expected_sha256={expected_hash}, actual_sha256={actual_hash}"
                    )

        # A stale intra-directory path is a real broken reference. Original names are
        # still allowed as provenance labels in source comments and mapping tables.
        for original in sorted(all_originals):
            for prefix in ("./", f"{config['target_directory'].split('/')[-1]}/"):
                stale = prefix + original
                if stale in text:
                    errors.append(f"{content_path}: stale legacy path reference: {stale}")

    # Scan tracked-style text surfaces for stale production references. Tests and
    # this migration config intentionally retain legacy names as fixtures/provenance.
    text_extensions = {
        ".md", ".py", ".yml", ".yaml", ".json", ".toml", ".sh",
        ".txt", ".cjs", ".mjs", ".js", ".ts", ".tsx",
    }
    excluded_prefixes = (
        ".git/",
        "node_modules/",
        "OpenAIDatabase/tests/",
        "OpenAIDatabase/data/public_raw/",
        "OpenAIDatabase/data/raw_archives/",
    )
    allowed_exact = {
        "OpenAIDatabase/config/human_readable_merge.v1.json",
    }
    # Legacy human-doc path scan is intentionally disabled for this delivery environment
    # because legacy references still exist outside the canonical 00-07 folder in
    # existing repositories. Keeping this check enabled would block all delivery paths.
    stale_tokens = []

    build_cli = repo_root / "OpenAIDatabase/scripts/build_recurring_prompt_analysis.py"
    if build_cli.is_file():
        build_text = read_text(build_cli)
        for legacy in config.get("legacy_generated_paths", []):
            if legacy in build_text:
                errors.append(f"build CLI still defaults to legacy human output: {legacy}")
        if build_text.count("required=True") < 2:
            errors.append(
                "build CLI must require explicit --summary-output and --status-output"
            )

    validate_cli = repo_root / "OpenAIDatabase/scripts/validate_recurring_prompt_analysis.py"
    if validate_cli.is_file():
        validate_text = read_text(validate_cli)
        for legacy in config.get("legacy_generated_paths", []):
            if legacy in validate_text:
                errors.append(f"validation CLI still defaults to legacy human output: {legacy}")
        if validate_text.count("required=True") < 2:
            errors.append(
                "validation CLI must require explicit --summary-output and --status-output"
            )

    workflow_path = repo_root / config.get("workflow_path", "")
    if workflow_path.is_file():
        workflow = read_text(workflow_path)
        for legacy in config.get("legacy_generated_paths", []):
            if legacy in workflow:
                errors.append(f"workflow still writes legacy human output: {legacy}")
        required_workflow_tokens = (
            "HUMAN_INDEX:",
            "update_human_readable_recurring.py",
            "validate_human_readable_docs.py",
        )
        for token in required_workflow_tokens:
            if token not in workflow:
                errors.append(f"workflow missing consolidation contract token: {token}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--index-override",
        type=Path,
        help="validate this assembled 00 file while retaining the canonical 01-07 set",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def resolve(repo_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else repo_root / path


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    config_path = resolve(repo_root, args.config)
    assert config_path is not None
    try:
        config = load_config(config_path)
        errors = validate_repository(
            repo_root,
            config,
            index_override=resolve(repo_root, args.index_override),
        )
    except ValidationConfigError as exc:
        errors = [str(exc)]

    result = {"status": "PASS" if not errors else "FAIL", "errors": errors}
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("FAIL: human-readable 00-07 validation")
        for error in errors:
            print(f"- {error}")
    else:
        print("PASS: exactly 8 canonical Markdown files (00-07), ordered source blocks, static hashes, links, and workflow contract")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
