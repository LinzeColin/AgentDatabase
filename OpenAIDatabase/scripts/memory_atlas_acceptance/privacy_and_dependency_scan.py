from __future__ import annotations

"""v0.0.0.32 T06 — privacy exposure (AC-010) and zero-model dependency (AC-014).

Both are asserted about the *serving* path: the modules that build, store and
hand out the live snapshot, plus whatever is currently published. Nothing here
reaches the network; it reads files and reports what it found.
"""

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
SERVING_MODULES = [
    "OpenAIDatabase/scripts/memory_atlas_private/live_snapshot_adapter.py",
    "OpenAIDatabase/scripts/memory_atlas_private/live_snapshot_store.py",
    "OpenAIDatabase/scripts/memory_atlas_private/api_live_snapshot.py",
    "OpenAIDatabase/scripts/memory_atlas_private/api_server.py",
    "OpenAIDatabase/scripts/memory_atlas_private/visual_analytics.py",
    "OpenAIDatabase/scripts/memory_atlas_private/benchmark_comparator.py",
    "OpenAIDatabase/scripts/memory_atlas_private/status_projection.py",
]

# A field carrying any of these names is raw material, a location or a secret,
# and must never appear in something the browser receives.
FORBIDDEN_KEYS = {
    "object_key", "objects", "sha256", "readback_sha256", "source_root", "relative_path",
    "materialized_path", "payload", "cookie", "secret", "token", "raw_content", "prompt",
    "authorization", "password", "api_key", "access_key", "private_key",
}
FORBIDDEN_VALUE_PATTERNS = [
    ("r2_object_prefix", re.compile(r"primary-objects/|private-agentdatabase/")),
    ("absolute_private_path", re.compile(r"/srv/linze|/Users/[^/\s]+/\.codex|\$HOME")),
    ("bare_sha256", re.compile(r"\b[0-9a-f]{64}\b")),
    ("bearer_or_key", re.compile(r"(?i)\b(bearer\s+[A-Za-z0-9._-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})")),
]

# Any import of one of these means the serving path could spend model tokens.
MODEL_MODULES = {
    "openai", "anthropic", "cohere", "google.generativeai", "vertexai", "transformers",
    "sentence_transformers", "torch", "tensorflow", "llama_cpp", "tiktoken", "litellm",
    "langchain", "llama_index", "ollama", "huggingface_hub", "onnxruntime",
}
MODEL_CALL_HINTS = re.compile(
    r"(?i)\b(embeddings?\.create|chat\.completions|messages\.create|generate_content|\.encode_batch|model\.predict)\b"
)


# The release identity is deliberately published: the browser cross-checks it
# against the API headers, and it is the digest of the deployed public bundle,
# not of a private captured object. Exact paths only — never a prefix or a key
# name, so a digest appearing anywhere else is still a finding.
ALLOWED_DIGEST_PATHS = {"$.release.artifact_digest"}


def _walk(value: Any, path: str = "$"):
    """Yields (where, key, child) for every node. List elements are yielded too:
    a leak inside `truth.limitations[0]` is still a leak."""
    if isinstance(value, dict):
        for key, child in value.items():
            where = f"{path}.{key}"
            yield where, str(key), child
            yield from _walk(child, where)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            where = f"{path}[{index}]"
            yield where, "", child
            yield from _walk(child, where)


def scan_payload(payload: Any, label: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for where, key, child in _walk(payload):
        # `privacy.object_keys_included` declares the contract; it is not a leak.
        if key in FORBIDDEN_KEYS and not key.endswith("_included"):
            findings.append({"artifact": label, "kind": "forbidden_key", "where": where})
        if isinstance(child, str):
            for name, pattern in FORBIDDEN_VALUE_PATTERNS:
                if name == "bare_sha256" and where in ALLOWED_DIGEST_PATHS:
                    continue
                if pattern.search(child):
                    findings.append({"artifact": label, "kind": name, "where": where})
    return findings


def scan_imports(paths: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for relative in paths:
        source = (REPO / relative).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                root = name.split(".")[0]
                if root in MODEL_MODULES or name in MODEL_MODULES:
                    findings.append({"artifact": relative, "kind": "model_import", "where": name})
        for match in MODEL_CALL_HINTS.finditer(source):
            findings.append({"artifact": relative, "kind": "model_call", "where": match.group(0)})
    return findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    findings: list[dict[str, Any]] = []
    scanned: list[str] = []
    for path in args.snapshot:
        scanned.append(str(path))
        findings.extend(scan_payload(json.loads(Path(path).read_text(encoding="utf-8")), path.name))
    dependency = scan_imports(SERVING_MODULES)

    report = {
        "schema_version": "memory_atlas.privacy_dependency_scan.v1",
        "verdict": "PASS" if not findings and not dependency else "FAIL",
        "scanned_payloads": scanned,
        "scanned_modules": SERVING_MODULES,
        "privacy_findings": findings,
        "model_dependency_findings": dependency,
        "forbidden_key_count": len(FORBIDDEN_KEYS),
        "forbidden_value_pattern_count": len(FORBIDDEN_VALUE_PATTERNS),
        "model_module_count": len(MODEL_MODULES),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['verdict']} — {len(findings)} privacy, {len(dependency)} model-dependency findings")
    raise SystemExit(0 if report["verdict"] == "PASS" else 2)


if __name__ == "__main__":
    main()
