"""
Downloads a repository as a single tarball. One network round trip,
regardless of how many files the repo contains — this is the piece that
avoids the per-file GitHub API rate limit entirely.
"""

from __future__ import annotations

from pathlib import Path

import httpx

from app.config import settings
from app.utils.github import RepoRef, build_tarball_url, _auth_headers
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RepositoryTooLargeError(Exception):
    pass


class RepositoryDownloadError(Exception):
    pass


async def download_repo_tarball(ref: RepoRef, git_ref: str, dest_path: Path) -> int:
    """Stream the tarball to dest_path. Returns the downloaded size in bytes.
    Raises RepositoryTooLargeError early if Content-Length reports a repo
    over the configured cap — no point downloading 2GB just to reject it."""
    url = build_tarball_url(ref, git_ref)
    max_bytes = settings.max_repo_size_mb * 1024 * 1024

    logger.info("Downloading tarball for %s/%s@%s", ref.owner, ref.repo, git_ref)

    downloaded = 0
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=settings.github_request_timeout_seconds
        ) as client:
            async with client.stream("GET", url, headers=_auth_headers()) as resp:
                resp.raise_for_status()

                content_length = resp.headers.get("content-length")
                if content_length and int(content_length) > max_bytes:
                    raise RepositoryTooLargeError(
                        f"Repo tarball reports {int(content_length)} bytes, "
                        f"exceeds cap of {max_bytes} bytes"
                    )

                with open(dest_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 256):
                        downloaded += len(chunk)
                        if downloaded > max_bytes:
                            raise RepositoryTooLargeError(
                                f"Repo tarball exceeded cap of {max_bytes} bytes "
                                f"mid-download"
                            )
                        f.write(chunk)

    except httpx.HTTPStatusError as exc:
        raise RepositoryDownloadError(
            f"GitHub returned {exc.response.status_code} for {url}"
        ) from exc
    except httpx.RequestError as exc:
        raise RepositoryDownloadError(f"Network error downloading {url}: {exc}") from exc

    logger.info("Downloaded %d bytes for %s/%s", downloaded, ref.owner, ref.repo)
    return downloaded