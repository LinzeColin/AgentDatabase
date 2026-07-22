"""Create the local-only runtime layout without tracked placeholders."""

from pathlib import Path
from typing import Tuple


RUNTIME_DIRECTORIES = (
    "cache",
    "runs",
    "decisions",
    "input_resolutions",
    "identity_master",
    "review_tasks",
    "reference_baseline",
)


def ensure_private_runtime(module_root: Path) -> Tuple[Path, ...]:
    root = module_root.resolve()
    runtime = root / "private_runtime"
    if runtime.is_symlink():
        raise RuntimeError("private_runtime must not be a symbolic link")
    if runtime.exists() and not runtime.is_dir():
        raise RuntimeError("private_runtime exists but is not a directory")
    runtime.mkdir(parents=True, exist_ok=True)
    created = []
    for name in RUNTIME_DIRECTORIES:
        child = runtime / name
        if child.is_symlink():
            raise RuntimeError("private runtime child must not be a symbolic link: %s" % name)
        if child.exists() and not child.is_dir():
            raise RuntimeError("private runtime child is not a directory: %s" % name)
        child.mkdir(exist_ok=True)
        created.append(child)
    return tuple(created)
