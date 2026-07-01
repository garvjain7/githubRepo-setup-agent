"""
Ties detector + env-var scanning + tier-1 file collection into one
RepositoryAnalysis object. This is the output of the entire "no LLM" phase
of the pipeline (see flowchart 1) — everything downstream, including the
AI agent, reads from this instead of re-walking the filesystem.

Env-var scanning runs here, independent of AST/language, and independent
of anything the agent chooses to ask about — this is the deliberate fix
for the "agent never thinks to expand the right function" recall gap
discussed earlier: env vars are found by static scan regardless of
whether any function containing them ever gets skeletonized or expanded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings
from app.repository.detector import DetectionResult, detect
from app.utils.filesystem import dir_size_bytes, iter_source_files, read_text_safely
from app.utils.logger import get_logger

logger = get_logger(__name__)

TIER1_FILENAMES = {
    "README.md", "README.rst", "README.txt", "README",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env.example", ".env.sample", "Procfile",
    "package.json", "requirements.txt", "pyproject.toml", "Pipfile",
    "go.mod", "Cargo.toml", "Gemfile", "composer.json",
}

# variable-capturing patterns across common languages/formats.
# Deliberately over-inclusive (better a false positive than a silent miss).
_ENV_VAR_PATTERNS = [
    re.compile(r"os\.environ\[[\'\"]([A-Z0-9_]+)[\'\"]\]"),
    re.compile(r"os\.getenv\([\'\"]([A-Z0-9_]+)[\'\"]"),
    re.compile(r"process\.env\.([A-Z0-9_]+)"),
    re.compile(r"process\.env\[[\'\"]([A-Z0-9_]+)[\'\"]\]"),
    re.compile(r"^\s*([A-Z][A-Z0-9_]+)\s*="),  # .env-style lines
]


@dataclass(frozen=True)
class EnvVarFinding:
    variable: str
    file: str
    line_number: int


@dataclass(frozen=True)
class Tier1File:
    relative_path: str
    content: str


@dataclass
class RepositoryAnalysis:
    root_path: Path
    detection: DetectionResult
    tier1_files: list[Tier1File] = field(default_factory=list)
    python_files: list[str] = field(default_factory=list)
    other_source_files: list[str] = field(default_factory=list)
    env_vars: list[EnvVarFinding] = field(default_factory=list)
    total_size_bytes: int = 0


def _collect_tier1_files(root: Path) -> list[Tier1File]:
    files = []
    for name in TIER1_FILENAMES:
        path = root / name
        if not path.is_file():
            continue
        content = read_text_safely(path, max_bytes=settings.max_tier1_file_bytes)
        if content is not None:
            files.append(Tier1File(relative_path=name, content=content))
    return files


def _split_python_vs_other(root: Path) -> tuple[list[str], list[str]]:
    python_files, other_files = [], []
    for src in iter_source_files(root):
        (python_files if src.extension == ".py" else other_files).append(src.relative_path)
    return python_files, other_files


def _scan_env_vars(root: Path) -> list[EnvVarFinding]:
    """Regex pass across every source file, independent of language and
    independent of the agent's tool calls. This is the safety net."""
    seen: set[str] = set()
    findings: list[EnvVarFinding] = []

    for src in iter_source_files(root):
        content = read_text_safely(src.absolute_path, max_bytes=500_000)
        if not content:
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            for pattern in _ENV_VAR_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                var_name = match.group(1)
                # dedupe by variable name — first occurrence wins
                if var_name in seen:
                    continue
                seen.add(var_name)
                findings.append(
                    EnvVarFinding(variable=var_name, file=src.relative_path, line_number=line_number)
                )
    return findings


def analyze_repository(root: Path) -> RepositoryAnalysis:
    logger.info("Starting static analysis of %s", root)

    detection = detect(root)
    tier1_files = _collect_tier1_files(root)
    python_files, other_files = _split_python_vs_other(root)
    env_vars = _scan_env_vars(root)
    total_size = dir_size_bytes(root)

    analysis = RepositoryAnalysis(
        root_path=root,
        detection=detection,
        tier1_files=tier1_files,
        python_files=python_files,
        other_source_files=other_files,
        env_vars=env_vars,
        total_size_bytes=total_size,
    )

    logger.info(
        "Analysis complete: %d python files, %d other, %d tier1 files, %d env vars",
        len(python_files), len(other_files), len(tier1_files), len(env_vars),
    )
    return analysis