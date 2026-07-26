from __future__ import annotations

import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .io import canonical_json, load_json, read_frontmatter, sha256_bytes, sha256_file, utc_now, write_json
from .process import run_bounded, run_bounded_to_file

SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
QUALIFYING_EVIDENCE = {"github-pulled-static", "product-live", "artifact-bundle-live"}
GITHUB_EVIDENCE = {"github-pulled-static"}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".py", ".sh", ".js", ".ts", ".html", ".css"}
SHOWCASE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".pdf", ".html"}
LICENSE_NAMES = {"LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "NOTICE", "NOTICE.md"}


def validate_slug(slug: str) -> str:
    slug = slug.strip()
    if not SLUG_RE.fullmatch(slug) or ".." in slug or slug.startswith("-") or "/-" in slug:
        raise ValueError("invalid GitHub owner/repository slug: %s" % slug)
    return slug


def _safe_git_env(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    # Build an allowlisted environment rather than inheriting GIT_CONFIG_COUNT,
    # credential helpers, trace hooks, alternate object stores, or executable paths.
    passthrough = (
        "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
        "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "no_proxy",
        "SSL_CERT_FILE", "SSL_CERT_DIR", "CURL_CA_BUNDLE",
    )
    safe_env = {key: os.environ[key] for key in passthrough if key in os.environ}
    isolated_home = Path(tempfile.gettempdir()) / "teleiosis-git-home"
    isolated_home.mkdir(parents=True, exist_ok=True)
    try:
        isolated_home.chmod(0o700)
    except OSError:
        pass
    safe_env.update({
        "HOME": str(isolated_home),
        "XDG_CONFIG_HOME": str(isolated_home / "xdg"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "echo",
        "SSH_ASKPASS": "echo",
        "GIT_ALLOW_PROTOCOL": "https",
        "GIT_LFS_SKIP_SMUDGE": "1",
        "LC_ALL": "C",
        "LANG": "C",
    })
    if extra:
        forbidden = [key for key in extra if key.startswith("GIT_CONFIG_") or key in {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_EXEC_PATH", "GIT_TEMPLATE_DIR", "GIT_SSH_COMMAND", "GIT_PROXY_COMMAND"}]
        if forbidden:
            raise ValueError("unsafe Git environment override(s): %s" % sorted(forbidden))
        safe_env.update(extra)
    return safe_env


def _run(command: Sequence[str], cwd: Optional[Path] = None, timeout: int = 180, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    result = run_bounded(
        command, cwd=cwd, timeout_seconds=timeout, env=_safe_git_env(env),
        max_output_bytes=2 * 1024 * 1024,
    )
    stderr = result["stderr"]
    if result["timed_out"]:
        stderr = (stderr + "\ncommand timed out after %s seconds" % timeout).strip()
    return subprocess.CompletedProcess(list(command), result["returncode"], result["stdout"], stderr)


def extract_target_terms(target: Path, limit: int = 16) -> List[str]:
    target = target.resolve()
    parts: List[str] = []
    skill = target / "SKILL.md"
    if skill.is_file():
        try:
            frontmatter, body = read_frontmatter(skill)
            parts.extend([str(frontmatter.get("name", "")), str(frontmatter.get("description", "")), body[:8000]])
        except Exception:
            parts.append(skill.read_text(encoding="utf-8", errors="replace")[:10000])
    for name in ("README.md", "README.txt"):
        path = target / name
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8", errors="replace")[:10000])
            break
    text = " ".join(parts).lower()
    candidates = re.findall(r"[a-z][a-z0-9-]{2,}|[\u4e00-\u9fff]{2,8}", text)
    stop = {"skill", "agent", "with", "from", "that", "this", "when", "use", "using", "the", "and", "for", "existing", "white", "box", "iteration", "teleiosis", "一个", "进行", "必须", "可以", "不得", "以及", "当前"}
    ordered: List[str] = []
    seen = set()
    for term in candidates:
        normalized = term.strip("-_")
        if len(normalized) < 3 or normalized in stop or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
        if len(ordered) >= limit:
            break
    return ordered


def build_queries(target: Path, explicit: Optional[Iterable[str]] = None) -> List[str]:
    if explicit:
        queries = [str(item).strip() for item in explicit if str(item).strip()]
        return list(dict.fromkeys(queries))[:12]
    terms = extract_target_terms(target)
    core = terms[:5] or ["agent skill optimizer"]
    phrases = [
        " ".join(core[:3]) + " skill",
        "agent skill optimization evaluation",
        "self evolving agent skills",
        "agent skill creator benchmark",
        "prompt optimizer agent workflow",
        "agent skill security evaluator",
    ]
    return list(dict.fromkeys(phrases))[:10]


def github_search(query: str, token: str = "", per_page: int = 20, timeout: int = 30, max_response_bytes: int = 5 * 1024 * 1024) -> Dict[str, Any]:
    if isinstance(per_page, bool) or not isinstance(per_page, int) or not 1 <= per_page <= 100:
        raise ValueError("per_page must be between 1 and 100")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 60:
        raise ValueError("GitHub search timeout must be between 1 and 60 seconds")
    if isinstance(max_response_bytes, bool) or not isinstance(max_response_bytes, int) or not 1024 <= max_response_bytes <= 20 * 1024 * 1024:
        raise ValueError("max_response_bytes must be between 1 KiB and 20 MiB")
    url = "https://api.github.com/search/repositories?q=%s&sort=updated&order=desc&per_page=%d" % (urllib.parse.quote(query), per_page)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "teleiosis-white-box-iteration-skill/0.0.0.1"}
    if token:
        headers["Authorization"] = "Bearer %s" % token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(max_response_bytes + 1)
            if len(raw) > max_response_bytes:
                raise ValueError("GitHub search response exceeds resource policy")
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("items", []), list):
                raise ValueError("GitHub search returned an unexpected payload")
            return {
                "status": "PASS",
                "query": query,
                "url": url,
                "captured_at": utc_now(),
                "etag": response.headers.get("ETag"),
                "rate_remaining": response.headers.get("X-RateLimit-Remaining"),
                "items": payload.get("items", []),
            }
    except Exception as exc:
        return {"status": "BLOCKED", "query": query, "url": url, "captured_at": utc_now(), "error": type(exc).__name__ + ": " + str(exc), "items": []}


def _git_tree_preflight(repo: Path, commit: str, max_files: int, max_bytes: int, timeout: int) -> Dict[str, int]:
    completed = _run(["git", "ls-tree", "-r", "-l", commit], cwd=repo, timeout=timeout)
    if completed.returncode != 0:
        raise ValueError("git tree preflight failed: %s" % completed.stderr.strip())
    files = 0
    bytes_total = 0
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        files += 1
        prefix = line.split("\t", 1)[0]
        fields = prefix.split()
        if len(fields) >= 4 and fields[3].isdigit():
            bytes_total += int(fields[3])
        if files > max_files:
            raise ValueError("repository exceeds max file count")
        if bytes_total > max_bytes:
            raise ValueError("repository exceeds max bytes")
    return {"files": files, "bytes": bytes_total}


def _normalized_tar_name(name: str) -> str:
    if not name or "\x00" in name or "\\" in name:
        raise ValueError("unsafe tar path: %r" % name)
    normalized = unicodedata.normalize("NFC", name.rstrip("/"))
    path = Path(normalized)
    if path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise ValueError("unsafe tar path: %s" % name)
    if path.parts and (":" in path.parts[0] or path.parts[0].strip() != path.parts[0]):
        raise ValueError("unsafe tar path: %s" % name)
    return path.as_posix()


def _extract_tar_archive(archive: tarfile.TarFile, destination: Path, max_files: int, max_bytes: int) -> Dict[str, int]:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    count = 0
    total = 0
    seen = set()
    seen_casefold = set()
    members = archive.getmembers()
    if len(members) > max_files * 2:
        raise ValueError("repository archive exceeds member-count policy")
    for member in members:
        identity = _normalized_tar_name(member.name)
        folded = identity.casefold()
        if identity in seen:
            raise ValueError("duplicate tar path: %s" % member.name)
        if folded in seen_casefold:
            raise ValueError("case-colliding tar path: %s" % member.name)
        seen.add(identity)
        seen_casefold.add(folded)
        if member.issym() or member.islnk() or member.isdev() or member.isfifo():
            raise ValueError("links/devices/fifos are not allowed in repository archive")
        if member.isdir():
            continue
        if not member.isfile():
            raise ValueError("unsupported tar member type: %s" % member.name)
        count += 1
        total += int(member.size)
        if count > max_files or total > max_bytes:
            raise ValueError("repository archive exceeds resource policy")
        target = (destination / Path(identity)).resolve()
        if destination != target and destination not in target.parents:
            raise ValueError("tar member escapes destination")
        target.parent.mkdir(parents=True, exist_ok=True)
        source = archive.extractfile(member)
        if source is None:
            raise ValueError("unable to read tar member")
        with target.open("wb") as sink:
            shutil.copyfileobj(source, sink, length=1024 * 1024)
        target.chmod(0o644)
    return {"files": count, "bytes": total}


def _safe_extract_tar_bytes(data: bytes, destination: Path, max_files: int, max_bytes: int) -> Dict[str, int]:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
        return _extract_tar_archive(archive, destination, max_files, max_bytes)


def _safe_extract_tar_path(path: Path, destination: Path, max_files: int, max_bytes: int) -> Dict[str, int]:
    path = path.resolve()
    if not path.is_file():
        raise ValueError("repository archive file is missing")
    with tarfile.open(name=str(path), mode="r:*") as archive:
        return _extract_tar_archive(archive, destination, max_files, max_bytes)


def pull_github_repository(slug: str, destination: Path, timeout: int = 180, max_files: int = 12000, max_bytes: int = 250 * 1024 * 1024) -> Dict[str, Any]:
    slug = validate_slug(slug)
    destination = destination.resolve()
    if destination.exists():
        shutil.rmtree(str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    quarantine = destination.parent / (".%s-quarantine" % destination.name)
    if quarantine.exists():
        shutil.rmtree(str(quarantine))
    empty_hooks = destination.parent / ".empty-hooks"
    empty_hooks.mkdir(parents=True, exist_ok=True)
    command = [
        "git", "-c", "protocol.ext.allow=never", "-c", "protocol.file.allow=never",
        "-c", "core.hooksPath=%s" % empty_hooks,
        "clone", "--depth", "1", "--filter=blob:none", "--no-checkout",
        "https://github.com/%s.git" % slug, str(quarantine),
    ]
    completed = _run(command, timeout=timeout)
    if completed.returncode != 0:
        return {
            "status": "PULL_BLOCKED", "slug": slug, "captured_at": utc_now(),
            "command": command, "error": completed.stderr.strip() or completed.stdout.strip(),
            "third_party_code_executed": False,
        }
    try:
        _run(["git", "config", "core.hooksPath", str(empty_hooks)], cwd=quarantine, timeout=30)
        head = _run(["git", "rev-parse", "HEAD"], cwd=quarantine, timeout=30)
        if head.returncode != 0 or not COMMIT_RE.fullmatch(head.stdout.strip()):
            raise ValueError("unable to resolve exact commit")
        commit = head.stdout.strip()
        preflight = _git_tree_preflight(quarantine, commit, max_files, max_bytes, timeout)
        # Stream the binary archive to disk. The tree preflight bounds expected
        # uncompressed bytes, while the command runner prevents RAM log growth.
        archive_path = quarantine.parent / (quarantine.name + ".archive.tar")
        archive_budget = max_bytes + max_files * 1024 + 4 * 1024 * 1024
        binary = run_bounded_to_file(
            ["git", "archive", "--format=tar", commit], archive_path, cwd=quarantine,
            timeout_seconds=timeout, env=_safe_git_env(), max_output_bytes=archive_budget,
        )
        if binary["returncode"] != 0 or binary["timed_out"] or binary["output_limit_exceeded"]:
            raise ValueError("git archive failed: %s" % binary.get("stderr", ""))
        extracted = _safe_extract_tar_path(archive_path, destination, max_files, max_bytes)
        archive_path.unlink(missing_ok=True)
        return {
            "status": "PASS", "slug": slug, "source_url": "https://github.com/%s" % slug,
            "resolved_commit": commit, "captured_at": utc_now(), "preflight": preflight,
            "extracted": extracted, "path": str(destination), "third_party_code_executed": False,
            "submodules_initialized": False, "hooks_executed": False,
        }
    except Exception as exc:
        if destination.exists():
            shutil.rmtree(str(destination))
        return {"status": "PULL_FAILED", "slug": slug, "captured_at": utc_now(), "error": type(exc).__name__ + ": " + str(exc), "third_party_code_executed": False}
    finally:
        archive_path = quarantine.parent / (quarantine.name + ".archive.tar")
        archive_path.unlink(missing_ok=True)
        shutil.rmtree(str(quarantine), ignore_errors=True)


def _walk_repository(root: Path, max_files: int = 12000, max_bytes: int = 250 * 1024 * 1024, max_depth: int = 40) -> Tuple[List[Path], int]:
    root = root.resolve()
    files: List[Path] = []
    total = 0
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if len(relative.parts) > max_depth:
            raise ValueError("repository path depth exceeds policy")
        if any(part in {".git", "node_modules", ".venv", "__pycache__"} for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError("repository symlink rejected: %s" % relative)
        if not path.is_file():
            continue
        files.append(path)
        total += path.stat().st_size
        if len(files) > max_files or total > max_bytes:
            raise ValueError("repository exceeds static inspection resource policy")
    return files, total


def inspect_repository(root: Path, source_slug: str = "", resolved_commit: str = "") -> Dict[str, Any]:
    root = root.resolve()
    files, total = _walk_repository(root)
    rels = [path.relative_to(root).as_posix() for path in files]
    skill_files = [rel for rel in rels if rel == "SKILL.md" or rel.endswith("/SKILL.md")]
    readmes = [rel for rel in rels if Path(rel).name.lower().startswith("readme")]
    licenses = [rel for rel in rels if Path(rel).name in LICENSE_NAMES]
    workflows = [rel for rel in rels if rel.startswith(".github/workflows/")]
    tests = [rel for rel in rels if "test" in Path(rel).name.lower() or "tests" in Path(rel).parts]
    scripts = [rel for rel in rels if "scripts" in Path(rel).parts or "tools" in Path(rel).parts]
    artifacts = [
        rel for rel in rels
        if Path(rel).suffix.lower() in SHOWCASE_SUFFIXES.union({".json", ".jsonl", ".csv", ".tsv"})
        and any(token in rel.lower() for token in ("showcase", "demo", "result", "report", "artifact", "screenshot", "eval", "output"))
    ]
    skill_metrics: List[Dict[str, Any]] = []
    for rel in skill_files[:100]:
        path = root / rel
        oversized = path.stat().st_size > 2 * 1024 * 1024
        frontmatter_valid = False
        name = None
        description = None
        if not oversized:
            try:
                fm, _ = read_frontmatter(path)
                frontmatter_valid = True
                name = fm.get("name")
                description = fm.get("description")
            except Exception:
                pass
        skill_metrics.append({
            "path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size,
            "lines": None if oversized else len(path.read_text(encoding="utf-8", errors="replace").splitlines()),
            "frontmatter_valid": frontmatter_valid, "name": name,
            "description_chars": len(str(description or "")), "oversized": oversized,
        })
    return {
        "captured_at": utc_now(), "evaluation_mode": "static-untrusted-no-exec",
        "source_slug": source_slug or None, "source_url": "https://github.com/%s" % source_slug if source_slug else None,
        "resolved_commit": resolved_commit or None, "third_party_code_executed": False,
        "inventory": {
            "file_count": len(files), "byte_count": total, "skill_files": skill_metrics,
            "readme_files": readmes[:100], "license_files": licenses[:50], "workflow_files": workflows[:100],
            "test_file_count": len(tests), "script_file_count": len(scripts), "artifact_files": artifacts[:200],
        },
        "signals": {
            "has_skill": bool(skill_files), "has_readme": bool(readmes), "has_license": bool(licenses),
            "has_ci": bool(workflows), "has_tests": bool(tests), "has_scripts": bool(scripts),
            "has_observable_artifacts": bool(artifacts),
        },
    }


def classify_peer(target_terms: List[str], metadata: Dict[str, Any], inspection: Optional[Dict[str, Any]]) -> Tuple[str, float, List[str]]:
    text = " ".join(str(metadata.get(key, "")) for key in ("name", "description", "topics", "full_name", "slug")).lower().replace("-", " ")
    overlap = sum(1 for term in target_terms if term.lower() in text)
    signals = (inspection or {}).get("signals", {})
    evidence: List[str] = []
    if signals.get("has_skill"):
        evidence.append("contains Agent Skill package")
    if overlap:
        evidence.append("target-term-overlap=%d" % overlap)
    if signals.get("has_skill") and any(token in text for token in ("evol", "optimiz", "refin", "darwin", "luban")):
        return "direct", min(0.98, 0.70 + overlap * 0.04), evidence
    if signals.get("has_skill") or any(token in text for token in ("skill creator", "skill registry", "skill publish", "agent skills")):
        return "craft", min(0.95, 0.60 + overlap * 0.04), evidence
    return "indirect", min(0.90, 0.50 + overlap * 0.04), evidence


def qualify_peer(row: Dict[str, Any]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    category = row.get("category")
    if category not in {"direct", "indirect", "craft"}:
        reasons.append("invalid category")
    mode = row.get("evidence_mode")
    if mode not in QUALIFYING_EVIDENCE:
        reasons.append("evidence mode is discovery-only")
    if not row.get("source_url") or not row.get("captured_at"):
        reasons.append("missing provenance")
    if not row.get("license_status"):
        reasons.append("missing license status")
    if mode == "github-pulled-static":
        try:
            validate_slug(str(row.get("slug", "")))
        except ValueError:
            reasons.append("invalid GitHub slug")
        if not COMMIT_RE.fullmatch(str(row.get("resolved_commit", ""))):
            reasons.append("missing exact commit")
        inspection = row.get("inspection")
        if not isinstance(inspection, dict) or inspection.get("third_party_code_executed") is not False:
            reasons.append("missing static no-exec inspection")
    elif mode in {"product-live", "artifact-bundle-live"}:
        if not row.get("observed_artifacts"):
            reasons.append("missing observed live artifacts")
        if not row.get("reproduction_or_observation"):
            reasons.append("missing observation procedure")
    if row.get("third_party_code_executed") not in {False, None}:
        reasons.append("third-party code execution was not isolated/approved")
    return not reasons, reasons


def select_peers(rows: List[Dict[str, Any]], minimum: int = 5, min_remote_github: int = 1) -> Dict[str, Any]:
    eligible: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    for row in rows:
        passed, reasons = qualify_peer(row)
        if passed:
            eligible.append(row)
        else:
            excluded.append({"peer_id": row.get("peer_id") or row.get("slug") or row.get("source_url"), "reasons": reasons})
    eligible.sort(key=lambda item: (-float(item.get("relevance_score", 0)), str(item.get("peer_id") or item.get("slug") or item.get("source_url"))))
    selected: List[Dict[str, Any]] = []
    for category, required in (("direct", 2), ("indirect", 1), ("craft", 1)):
        selected.extend([row for row in eligible if row.get("category") == category][:required])
    used = {str(row.get("peer_id") or row.get("slug") or row.get("source_url")) for row in selected}
    for row in eligible:
        identity = str(row.get("peer_id") or row.get("slug") or row.get("source_url"))
        if len(selected) >= minimum:
            break
        if identity not in used:
            selected.append(row)
            used.add(identity)
    counts = {category: sum(1 for row in selected if row.get("category") == category) for category in ("direct", "indirect", "craft")}
    github_count = sum(1 for row in selected if row.get("evidence_mode") == "github-pulled-static")
    errors: List[str] = []
    if len(selected) < minimum:
        errors.append("at least %d qualifying peers required" % minimum)
    if counts["direct"] < 2 or counts["indirect"] < 1 or counts["craft"] < 1:
        errors.append("peer category coverage is incomplete")
    if github_count < min_remote_github:
        errors.append("at least %d auto-pulled GitHub peer(s) required" % min_remote_github)
    return {
        "status": "PASS" if not errors else "BLOCKED",
        "selected_peer_ids": [str(row.get("peer_id") or row.get("slug") or row.get("source_url")) for row in selected],
        "counts": counts, "github_pulled_count": github_count,
        "eligible_count": len(eligible), "excluded": excluded, "errors": errors,
    }


def _license_status(inspection: Dict[str, Any]) -> str:
    return "observed-license-file" if inspection.get("signals", {}).get("has_license") else "unknown-no-license-file-observed"


def build_competitor_dataset(
    target: Path,
    workspace: Path,
    seeds: Iterable[str],
    explicit_queries: Optional[Iterable[str]] = None,
    token: str = "",
    max_candidates: int = 20,
    timeout: int = 180,
    offline: bool = False,
    local_repositories: Optional[Iterable[Tuple[str, Path, str]]] = None,
    supplementary_records: Optional[Iterable[Dict[str, Any]]] = None,
    min_remote_github: int = 1,
) -> Dict[str, Any]:
    if isinstance(max_candidates, bool) or not isinstance(max_candidates, int) or not 1 <= max_candidates <= 100:
        raise ValueError("max_candidates must be between 1 and 100")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 5 <= timeout <= 600:
        raise ValueError("timeout must be between 5 and 600 seconds")
    if isinstance(min_remote_github, bool) or not isinstance(min_remote_github, int) or not 0 <= min_remote_github <= 5:
        raise ValueError("min_remote_github must be between 0 and 5")
    seeds = list(seeds)
    if len(seeds) > 100:
        raise ValueError("at most 100 explicit peer seeds are allowed")
    target = target.resolve()
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    repositories_dir = workspace / "repositories"
    repositories_dir.mkdir(parents=True, exist_ok=True)
    queries = build_queries(target, explicit_queries)
    target_terms = extract_target_terms(target)
    metadata_pool: Dict[str, Dict[str, Any]] = {}
    source_events: List[Dict[str, Any]] = []
    for seed in seeds:
        slug = validate_slug(seed)
        metadata_pool[slug] = {"full_name": slug, "name": slug.split("/", 1)[1], "description": "explicit seed", "stargazers_count": 0, "seed": True}
    if not offline:
        for query in queries:
            result = github_search(query, token=token, per_page=min(50, max_candidates), timeout=min(timeout, 45))
            source_events.append({key: result.get(key) for key in ("status", "query", "url", "captured_at", "etag", "rate_remaining", "error") if result.get(key) is not None})
            for item in result.get("items", []):
                slug = item.get("full_name")
                if not slug:
                    continue
                try:
                    validate_slug(slug)
                except ValueError:
                    continue
                current = metadata_pool.get(slug)
                if current is None or int(item.get("stargazers_count", 0) or 0) > int(current.get("stargazers_count", 0) or 0):
                    metadata_pool[slug] = item
    ranked = sorted(metadata_pool.values(), key=lambda item: (-int(item.get("stargazers_count", 0) or 0), str(item.get("full_name", "")).lower()))[:max_candidates]
    rows: List[Dict[str, Any]] = []
    for metadata in ranked:
        slug = validate_slug(str(metadata["full_name"]))
        destination = repositories_dir / slug.replace("/", "__")
        pull = pull_github_repository(slug, destination, timeout=timeout)
        if pull.get("status") == "PASS":
            inspection = inspect_repository(destination, source_slug=slug, resolved_commit=str(pull["resolved_commit"]))
            category, score, evidence = classify_peer(target_terms, metadata, inspection)
            row = {
                "schema_version": "2.0", "peer_id": "github:%s@%s" % (slug, pull["resolved_commit"]),
                "peer_kind": "open-source-repository", "slug": slug, "source_url": "https://github.com/%s" % slug,
                "category": category, "relevance_score": score, "classification_evidence": evidence,
                "evidence_mode": "github-pulled-static", "resolved_commit": pull["resolved_commit"],
                "captured_at": pull["captured_at"], "license_status": _license_status(inspection),
                "inspection": inspection, "artifact_inventory": inspection["inventory"].get("artifact_files", []),
                "third_party_code_executed": False, "pull_status": "PASS",
            }
        else:
            category, score, evidence = classify_peer(target_terms, metadata, None)
            row = {
                "schema_version": "2.0", "peer_id": "github:%s@unresolved" % slug,
                "peer_kind": "open-source-repository", "slug": slug, "source_url": "https://github.com/%s" % slug,
                "category": category, "relevance_score": score, "classification_evidence": evidence,
                "evidence_mode": "web-metadata", "resolved_commit": None, "captured_at": pull.get("captured_at", utc_now()),
                "license_status": "unknown-not-pulled", "inspection": None, "artifact_inventory": [],
                "third_party_code_executed": False, "pull_status": pull.get("status"), "pull_error": pull.get("error"),
            }
        rows.append(row)
    for slug, path, category in local_repositories or []:
        slug = validate_slug(slug)
        completed = _run(["git", "rev-parse", "HEAD"], cwd=path, timeout=30)
        commit = completed.stdout.strip() if completed.returncode == 0 else ""
        inspection = inspect_repository(path, source_slug=slug, resolved_commit=commit)
        rows.append({
            "schema_version": "2.0", "peer_id": "fixture:%s@%s" % (slug, commit or "unresolved"),
            "peer_kind": "local-test-fixture", "slug": slug, "source_url": "file://%s" % path.resolve(),
            "category": category, "relevance_score": 0.5, "classification_evidence": ["caller supplied local repository"],
            "evidence_mode": "local-git-fixture", "resolved_commit": commit or None, "captured_at": utc_now(),
            "license_status": _license_status(inspection), "inspection": inspection,
            "artifact_inventory": inspection["inventory"].get("artifact_files", []), "third_party_code_executed": False,
            "production_eligible": False,
        })
    rows.extend(dict(item) for item in (supplementary_records or []))
    rows.sort(key=lambda item: str(item.get("peer_id") or item.get("source_url")))
    dataset = workspace / "competitor-dataset.jsonl"
    with dataset.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    selection = select_peers(rows, minimum=5, min_remote_github=min_remote_github)
    write_json(workspace / "peer-selection.json", selection)
    manifest = {
        "schema_version": "2.0", "generated_at": utc_now(), "target": str(target),
        "queries": queries, "dataset_file": dataset.name, "dataset_sha256": sha256_file(dataset),
        "row_count": len(rows), "selection_status": selection["status"], "selection_file": "peer-selection.json",
        "source_events": source_events,
        "policy": {
            "minimum_peers": 5, "category_minimums": {"direct": 2, "indirect": 1, "craft": 1},
            "minimum_remote_github_pulls": min_remote_github, "third_party_default": "static-no-exec",
            "local_fixtures_never_count_for_production": True,
        },
    }
    manifest["manifest_sha256"] = sha256_bytes(canonical_json(manifest))
    write_json(workspace / "dataset-manifest.json", manifest)
    matrix_lines = ["# Competitor Matrix", "", "| Peer | Category | Evidence | Commit | License | Artifacts | Qualifies |", "|---|---|---|---|---|---:|---:|"]
    for row in rows:
        passed, _ = qualify_peer(row)
        matrix_lines.append("| %s | %s | %s | %s | %s | %d | %s |" % (
            row.get("slug") or row.get("peer_id"), row.get("category"), row.get("evidence_mode"),
            str(row.get("resolved_commit") or "-")[:12], row.get("license_status"), len(row.get("artifact_inventory", [])),
            "yes" if passed else "no",
        ))
    (workspace / "competitor-matrix.md").write_text("\n".join(matrix_lines) + "\n", encoding="utf-8")
    return {"status": selection["status"], "manifest": manifest, "selection": selection, "dataset": str(dataset)}


def load_supplementary_records(path: Optional[Path]) -> List[Dict[str, Any]]:
    if path is None:
        return []
    rows: List[Dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            rows.append(json.loads(raw))
    return rows
