"""
GitHub URL parsing and API helpers.

Fetch strategy: we use the /repos/{owner}/{repo}/tarball/{ref} endpoint,
which redirects to codeload.github.com and returns the ENTIRE repo as a
single .tar.gz — one API call regardless of repo size, instead of one call
per file. This is the fix for the rate-limit problem discussed earlier.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_GITHUB_URL_PATTERN = re.compile(
    r"^https?://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(\.git)?/?$"
)


class InvalidGitHubUrlError(ValueError):
    pass


class RepositoryNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class RepoRef:
    owner: str
    repo: str


def parse_github_url(url: str) -> RepoRef:
    match = _GITHUB_URL_PATTERN.match(url.strip())
    if not match:
        raise InvalidGitHubUrlError(
            f"Not a recognizable public GitHub repo URL: {url}"
        )
    return RepoRef(owner=match.group("owner"), repo=match.group("repo"))


def _auth_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


async def resolve_default_branch(ref: RepoRef) -> str:
    """Look up the repo's default branch — needed because we can't assume
    'main' (plenty of repos still use 'master', or something else entirely)."""
    url = f"{settings.github_api_base}/repos/{ref.owner}/{ref.repo}"
    async with httpx.AsyncClient(timeout=settings.github_request_timeout_seconds) as client:
        resp = await client.get(url, headers=_auth_headers())

    if resp.status_code == 404:
        raise RepositoryNotFoundError(f"{ref.owner}/{ref.repo} not found or private")
    resp.raise_for_status()

    return resp.json()["default_branch"]


def build_tarball_url(ref: RepoRef, git_ref: str) -> str:
    return f"{settings.github_api_base}/repos/{ref.owner}/{ref.repo}/tarball/{git_ref}"