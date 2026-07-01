"""
Filesystem helpers shared by the repository and parser modules.

Design note: noise (node_modules, .git, build output, binaries) is filtered
HERE, at the walk level, rather than relied on to be evicted later by LRU.
Keeping junk out of the cache in the first place is cheaper than caching it
and evicting it.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

EXCLUDED_DIR_NAMES = {
    "node_modules", ".git", ".hg", ".svn", "dist", "build", "out",
    "__pycache__", ".venv", "venv", "env", "vendor", ".next", ".nuxt",
    "target", ".idea", ".vscode", ".pytest_cache", ".mypy_cache",
    "coverage", ".tox", "site-packages", "egg-info",
}

# Extensions that are almost never worth reading as "source" — binaries,
# media, compiled artifacts. Presence is fine to note; content is not fetched.
BINARY_LIKE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".bmp",
    ".mp4", ".mov", ".avi", ".mp3", ".wav",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pyc", ".pyo", ".so", ".dll", ".dylib", ".exe", ".bin",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pdf", ".db", ".sqlite", ".sqlite3",
}

# Lockfiles: their PRESENCE matters (tells you the package manager), but
# their content is large and low-value — never read in full.
LOCKFILE_NAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "Cargo.lock", "composer.lock",
    "Gemfile.lock", "go.sum",
}


@dataclass(frozen=True)
class SourceFile:
    relative_path: str
    absolute_path: Path
    size_bytes: int
    extension: str


def safe_join(base: Path, *parts: str) -> Path:
    """Join path segments under `base`, raising if the result would escape
    `base` (path traversal guard). Always use this for any path built from
    repo-controlled strings — file names inside a downloaded repo are not
    trusted input."""
    base_resolved = base.resolve()
    candidate = (base_resolved / Path(*parts)).resolve()
    if not str(candidate).startswith(str(base_resolved)):
        raise ValueError(f"Path traversal attempt blocked: {parts}")
    return candidate


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def remove_dir_safely(path: Path, must_be_within: Path) -> None:
    """Delete a directory tree, but only if it's actually inside
    `must_be_within`. Prevents a bug elsewhere from deleting something
    outside the workspace root."""
    path_resolved = path.resolve()
    root_resolved = must_be_within.resolve()
    if not str(path_resolved).startswith(str(root_resolved)):
        raise ValueError(f"Refusing to delete path outside workspace root: {path}")
    if path_resolved.exists():
        shutil.rmtree(path_resolved, ignore_errors=True)


def human_readable_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def dir_size_bytes(root: Path) -> int:
    total = 0
    for p in root.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def iter_source_files(root: Path, max_file_bytes: int = 2_000_000):
    """Walk `root`, skipping excluded directories and binary-like files.
    Yields SourceFile entries only for things worth analyzing — this is the
    single choke point that keeps noise out of every downstream module."""
    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in EXCLUDED_DIR_NAMES for part in path.relative_to(root).parts[:-1]):
            continue

        if path.name in LOCKFILE_NAMES:
            continue  # presence noted elsewhere by the detector, content skipped

        ext = path.suffix.lower()
        if ext in BINARY_LIKE_EXTENSIONS:
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue

        if size > max_file_bytes:
            continue  # oversized "source" file — likely generated/vendored, skip

        yield SourceFile(
            relative_path=str(path.relative_to(root)),
            absolute_path=path,
            size_bytes=size,
            extension=ext,
        )


def read_text_safely(path: Path, max_bytes: int) -> str | None:
    """Read a file as text, returning None instead of raising if it's not
    decodable as UTF-8 or exceeds max_bytes. Callers should treat None as
    'skip this file' rather than a hard failure."""
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None