from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


def _terminate_tree(process: subprocess.Popen) -> None:
    """Best-effort termination of a bounded command and its process group."""
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:  # pragma: no cover - exercised on Windows runtimes
            process.kill()
    except (OSError, ProcessLookupError):
        try:
            process.kill()
        except (OSError, ProcessLookupError):
            pass


def _read_capped(stream: Any, limit: int) -> Tuple[str, bool, int]:
    stream.flush()
    stream.seek(0, os.SEEK_END)
    size = int(stream.tell())
    stream.seek(0)
    if size <= limit:
        data = stream.read()
        return data.decode("utf-8", errors="replace"), False, size
    marker = b"\n...[OUTPUT TRUNCATED BY WHITE-BOX ITERATION SKILL]...\n"
    available = max(0, limit - len(marker))
    head_size = available // 2
    tail_size = available - head_size
    head = stream.read(head_size)
    stream.seek(max(0, size - tail_size))
    tail = stream.read(tail_size)
    return (head + marker + tail).decode("utf-8", errors="replace"), True, size


def run_bounded(
    command: Iterable[str],
    *,
    input_text: Optional[str] = None,
    cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout_seconds: float = 300.0,
    max_output_bytes: int = 1024 * 1024,
    max_input_bytes: int = 1024 * 1024,
) -> Dict[str, Any]:
    """Run a subprocess with bounded input/output, hard timeout, and group cleanup.

    Stdout/stderr are written to temporary files rather than pipes so a hostile or
    accidental log flood cannot grow controller memory without bound. When a
    stream exceeds the limit, the returned text preserves both its head and tail.
    """
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a positive number")
    for label, value in (("max_output_bytes", max_output_bytes), ("max_input_bytes", max_input_bytes)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 256:
            raise ValueError("%s must be an integer of at least 256 bytes" % label)
    argv = [str(item) for item in command]
    if not argv:
        raise ValueError("command must not be empty")
    input_bytes = input_text.encode("utf-8") if input_text is not None else None
    if input_bytes is not None and len(input_bytes) > max_input_bytes:
        raise ValueError("input_text exceeds max_input_bytes")
    creationflags = 0
    start_new_session = os.name == "posix"
    if os.name == "nt":  # pragma: no cover - exercised on Windows runtimes
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    started = time.monotonic()
    with tempfile.TemporaryFile(mode="w+b") as stdout_file, tempfile.TemporaryFile(mode="w+b") as stderr_file:
        process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
            stdout=stdout_file,
            stderr=stderr_file,
            text=False,
            cwd=str(cwd) if cwd else None,
            env=dict(env) if env is not None else None,
            start_new_session=start_new_session,
            creationflags=creationflags,
        )
        timed_out = False
        try:
            process.communicate(input=input_bytes, timeout=float(timeout_seconds))
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_tree(process)
            process.communicate()
        stdout, stdout_truncated, stdout_bytes = _read_capped(stdout_file, max_output_bytes)
        stderr, stderr_truncated, stderr_bytes = _read_capped(stderr_file, max_output_bytes)
        return {
            "command": argv,
            "returncode": -9 if timed_out else int(process.returncode),
            "stdout": stdout,
            "stderr": stderr,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "stdout_bytes": stdout_bytes,
            "stderr_bytes": stderr_bytes,
            "timed_out": timed_out,
            "timeout_seconds": float(timeout_seconds),
            "max_output_bytes": max_output_bytes,
            "elapsed_seconds": round(time.monotonic() - started, 6),
        }


def run_bounded_to_file(
    command: Iterable[str],
    output_path: Path,
    *,
    cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout_seconds: float = 300.0,
    max_output_bytes: int = 256 * 1024 * 1024,
    max_stderr_bytes: int = 1024 * 1024,
) -> Dict[str, Any]:
    """Run a subprocess with stdout streamed to a file rather than RAM.

    This is intended for bounded binary artifacts such as ``git archive``. The
    caller must establish an independent upper bound on expected output (for
    example, a Git tree preflight). Oversized output is deleted and reported as
    a failure; stderr remains head/tail capped in the returned evidence.
    """
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a positive number")
    for label, value in (("max_output_bytes", max_output_bytes), ("max_stderr_bytes", max_stderr_bytes)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 256:
            raise ValueError("%s must be an integer of at least 256 bytes" % label)
    argv = [str(item) for item in command]
    if not argv:
        raise ValueError("command must not be empty")
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    creationflags = 0
    start_new_session = os.name == "posix"
    if os.name == "nt":  # pragma: no cover - exercised on Windows runtimes
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    timed_out = False
    started = time.monotonic()
    with output_path.open("wb") as stdout_file, tempfile.TemporaryFile(mode="w+b") as stderr_file:
        process = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=stdout_file, stderr=stderr_file,
            text=False, cwd=str(cwd) if cwd else None,
            env=dict(env) if env is not None else None,
            start_new_session=start_new_session, creationflags=creationflags,
        )
        try:
            process.wait(timeout=float(timeout_seconds))
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_tree(process)
            process.wait()
        stderr, stderr_truncated, stderr_bytes = _read_capped(stderr_file, max_stderr_bytes)
    output_bytes = output_path.stat().st_size if output_path.exists() else 0
    output_limit_exceeded = output_bytes > max_output_bytes
    if output_limit_exceeded:
        output_path.unlink(missing_ok=True)
    return {
        "command": argv,
        "returncode": -9 if timed_out else int(process.returncode),
        "output_path": str(output_path),
        "output_bytes": output_bytes,
        "output_limit_exceeded": output_limit_exceeded,
        "stderr": stderr,
        "stderr_truncated": stderr_truncated,
        "stderr_bytes": stderr_bytes,
        "timed_out": timed_out,
        "timeout_seconds": float(timeout_seconds),
        "max_output_bytes": max_output_bytes,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
