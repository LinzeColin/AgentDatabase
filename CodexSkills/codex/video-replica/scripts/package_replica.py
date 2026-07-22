#!/usr/bin/env python3
"""Create one validated video-replica ZIP in the user's Downloads directory."""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


VERSION = "1.1.0"
EXCLUDED_DIRS = {".git", "__MACOSX", "__pycache__"}
EXCLUDED_FILES = {".DS_Store"}
SENSITIVE_EXACT = {
    ".env",
    ".npmrc",
    ".pypirc",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
    "service-account.json",
}
SENSITIVE_SUFFIXES = {".jks", ".key", ".p12", ".pem", ".pfx"}


class PackageError(RuntimeError):
    """Raised when a fail-closed packaging gate is not satisfied."""


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_stream(handle):
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def safe_name(value):
    cleaned = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._-")
    return cleaned or "video_replica_pack"


def is_excluded(relative):
    return relative.name in EXCLUDED_FILES or any(
        part in EXCLUDED_DIRS for part in relative.parts
    )


def sensitive_reason(relative):
    name = relative.name.lower()
    if name in SENSITIVE_EXACT:
        return "sensitive filename"
    if name.startswith(".env") or name.endswith(".env"):
        return "environment file"
    if relative.suffix.lower() in SENSITIVE_SUFFIXES:
        return "private key or credential container"
    return None


def collect_files(source, allow_sensitive=False):
    if source.is_symlink():
        raise PackageError("pack root must not be a symlink")
    if not source.is_dir():
        raise PackageError("pack directory does not exist")
    if not (source / "MANIFEST.txt").is_file():
        raise PackageError("MANIFEST.txt is required at the pack root")

    files = []
    sensitive = []
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(source)
        if path.is_symlink():
            raise PackageError(f"symlink is not allowed: {relative.as_posix()}")
        if not path.is_file() or is_excluded(relative):
            continue
        reason = sensitive_reason(relative)
        if reason and not allow_sensitive:
            sensitive.append(f"{relative.as_posix()} ({reason})")
        files.append((path, relative))

    if sensitive:
        raise PackageError(
            "sensitive-looking files require explicit --allow-sensitive: "
            + "; ".join(sensitive)
        )
    if not files:
        raise PackageError("pack contains no packageable files")
    return files


def unique_archive_path(downloads, requested_name):
    filename = safe_name(requested_name)
    if not filename.lower().endswith(".zip"):
        filename += ".zip"
    candidate = downloads / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    for index in range(1, 1000):
        alternate = downloads / f"{stem}-{index:02d}.zip"
        if not alternate.exists():
            return alternate
    raise PackageError("could not allocate a non-overwriting archive name")


def validate_archive(path, expected_entries, manifest_entry):
    with zipfile.ZipFile(path, "r") as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise PackageError(f"ZIP integrity failure at {bad_member}")
        names = archive.namelist()
        for name in names:
            normalized = Path(name)
            if normalized.is_absolute() or ".." in normalized.parts:
                raise PackageError(f"unsafe ZIP member: {name}")
        if set(names) != set(expected_entries):
            raise PackageError("ZIP entries do not match the package plan")
        try:
            manifest_text = archive.read(manifest_entry).decode("utf-8")
        except (KeyError, UnicodeDecodeError) as exc:
            raise PackageError("ZIP hash manifest is missing or invalid UTF-8") from exc
        manifest_hashes = {}
        for line in manifest_text.splitlines():
            digest, separator, name = line.partition("  ")
            if (
                not separator
                or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or not name
                or name in manifest_hashes
            ):
                raise PackageError("ZIP hash manifest contains an invalid entry")
            manifest_hashes[name] = digest
        data_entries = set(expected_entries) - {manifest_entry}
        if set(manifest_hashes) != data_entries:
            raise PackageError("ZIP hash manifest does not cover every packaged file")
        for name, expected_digest in manifest_hashes.items():
            with archive.open(name, "r") as member:
                if sha256_stream(member) != expected_digest:
                    raise PackageError(f"ZIP SHA-256 mismatch at {name}")


def create_archive(
    source,
    downloads=None,
    archive_name=None,
    allow_sensitive=False,
    timestamp=None,
):
    source_input = Path(source).expanduser()
    if source_input.is_symlink():
        raise PackageError("pack root must not be a symlink")
    source = source_input.resolve()
    downloads = Path(downloads or (Path.home() / "Downloads")).expanduser().resolve()
    if not downloads.is_dir():
        raise PackageError(f"Downloads directory does not exist: {downloads}")
    if not os.access(str(downloads), os.W_OK):
        raise PackageError(f"Downloads directory is not writable: {downloads}")

    files = collect_files(source, allow_sensitive=allow_sensitive)
    timestamp = timestamp or datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    requested_name = archive_name or f"{safe_name(source.name)}_{timestamp}.zip"
    destination = unique_archive_path(downloads, requested_name)
    root_name = safe_name(source.name)

    manifest_lines = []
    expected_entries = []
    for path, relative in files:
        archive_path = f"{root_name}/{relative.as_posix()}"
        manifest_lines.append(f"{sha256_file(path)}  {archive_path}")
        expected_entries.append(archive_path)
    manifest_entry = f"{root_name}/PACKAGE_MANIFEST.sha256"
    expected_entries.append(manifest_entry)
    manifest_data = ("\n".join(manifest_lines) + "\n").encode("utf-8")

    handle = tempfile.NamedTemporaryFile(
        prefix=".video-replica-", suffix=".zip.tmp", dir=str(downloads), delete=False
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
            allowZip64=True,
        ) as archive:
            for path, relative in files:
                archive.write(path, f"{root_name}/{relative.as_posix()}")
            archive.writestr(manifest_entry, manifest_data)
        validate_archive(temporary, expected_entries, manifest_entry)
        for _ in range(1000):
            destination = unique_archive_path(downloads, requested_name)
            try:
                os.link(str(temporary), str(destination))
            except FileExistsError:
                continue
            try:
                temporary.unlink()
            except OSError:
                pass
            break
        else:
            raise PackageError("could not publish a non-overwriting archive")
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    result = {
        "archive_path": str(destination),
        "archive_sha256": sha256_file(destination),
        "file_count": len(files),
        "manifest_entry": manifest_entry,
        "schema_version": "1.0",
        "script_version": VERSION,
        "source_pack": str(source),
        "zip_entry_count": len(expected_entries),
    }
    return result


def build_parser():
    parser = argparse.ArgumentParser(
        description="Package a video-replica output pack into Downloads"
    )
    parser.add_argument("pack_dir", help="absolute or user-relative output-pack path")
    parser.add_argument(
        "--downloads",
        help="override Downloads only for controlled testing or an explicit Owner choice",
    )
    parser.add_argument("--archive-name", help="optional non-overwriting ZIP filename")
    parser.add_argument(
        "--allow-sensitive",
        action="store_true",
        help="include credential-like files only after explicit Owner authorization",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        result = create_archive(
            args.pack_dir,
            downloads=args.downloads,
            archive_name=args.archive_name,
            allow_sensitive=args.allow_sensitive,
        )
    except (OSError, PackageError, zipfile.BadZipFile) as exc:
        print(
            json.dumps(
                {"error": str(exc), "passed": False, "script_version": VERSION},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
