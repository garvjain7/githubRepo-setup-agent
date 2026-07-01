"""
Extracts the downloaded tarball. GitHub's tarball endpoint always wraps the
repo in a single top-level folder like 'owner-repo-<sha>/' — this flattens
that so dest_dir contains the repo's actual root directly.
"""

from __future__ import annotations

import tarfile
from pathlib import Path

from app.utils.filesystem import ensure_dir
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UnsafeArchiveError(Exception):
    pass


def _is_within_directory(directory: Path, target: Path) -> bool:
    return str(target.resolve()).startswith(str(directory.resolve()))


def _validate_members(tar: tarfile.TarFile, dest_dir: Path) -> None:
    """Guard against path traversal ('..' entries, absolute paths, symlinks
    pointing outside dest_dir) before extracting anything. Tarballs from
    GitHub are trusted, but we don't assume that generally."""
    for member in tar.getmembers():
        member_path = dest_dir / member.name
        if not _is_within_directory(dest_dir, member_path):
            raise UnsafeArchiveError(f"Archive member escapes destination: {member.name}")
        if member.issym() or member.islnk():
            link_target = dest_dir / member.linkname
            if not _is_within_directory(dest_dir, link_target):
                raise UnsafeArchiveError(f"Archive link escapes destination: {member.name}")


def extract_tarball(tarball_path: Path, dest_dir: Path) -> Path:
    """Extract and flatten. Returns the path to the repo's actual root
    (i.e. dest_dir itself, after flattening)."""
    ensure_dir(dest_dir)

    with tarfile.open(tarball_path, mode="r:gz") as tar:
        _validate_members(tar, dest_dir)
        try:
            tar.extractall(dest_dir, filter="data")  # py3.12+ safe default
        except TypeError:
            tar.extractall(dest_dir)  # older Python without the filter kwarg

    top_level_entries = list(dest_dir.iterdir())
    if len(top_level_entries) == 1 and top_level_entries[0].is_dir():
        wrapper = top_level_entries[0]
        for item in wrapper.iterdir():
            item.rename(dest_dir / item.name)
        wrapper.rmdir()

    logger.info("Extracted and flattened archive into %s", dest_dir)
    return dest_dir