"""
Static detection of language, package manager, and framework signals.
Zero LLM calls — this runs before the AI ever sees the repo, matching the
"static analysis first" principle from the design discussion.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from app.utils.filesystem import iter_source_files, read_text_safely
from app.utils.logger import get_logger

logger = get_logger(__name__)

# manifest filename -> language it signals
MANIFEST_LANGUAGE_SIGNALS = {
    "package.json": "javascript",
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "Pipfile": "python",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "Gemfile": "ruby",
    "composer.json": "php",
}

EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
    ".php": "php",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".hpp": "cpp",
}

# package.json dependency name -> framework label
JS_FRAMEWORK_SIGNALS = {
    "react": "React", "next": "Next.js", "vue": "Vue", "nuxt": "Nuxt",
    "express": "Express", "@nestjs/core": "NestJS", "svelte": "Svelte",
}

PY_FRAMEWORK_TEXT_SIGNALS = {
    "flask": "Flask", "django": "Django", "fastapi": "FastAPI",
}


@dataclass
class DetectionResult:
    primary_language: str | None
    language_breakdown: dict[str, int] = field(default_factory=dict)
    manifests: list[str] = field(default_factory=list)
    framework_hints: list[str] = field(default_factory=list)
    has_dockerfile: bool = False
    has_docker_compose: bool = False


def detect_manifests(root: Path) -> list[str]:
    found = []
    for name in MANIFEST_LANGUAGE_SIGNALS:
        if (root / name).is_file():
            found.append(name)
    return found


def detect_language_breakdown(root: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for src in iter_source_files(root):
        lang = EXTENSION_LANGUAGE_MAP.get(src.extension)
        if lang:
            counts[lang] += 1
    return dict(counts)


def _detect_js_frameworks(root: Path) -> list[str]:
    pkg_path = root / "package.json"
    if not pkg_path.is_file():
        return []
    content = read_text_safely(pkg_path, max_bytes=500_000)
    if not content:
        return []
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    return [label for key, label in JS_FRAMEWORK_SIGNALS.items() if key in deps]


def _detect_py_frameworks(root: Path, manifests: list[str]) -> list[str]:
    hints: set[str] = set()
    for manifest_name in ("requirements.txt", "pyproject.toml"):
        if manifest_name not in manifests:
            continue
        content = read_text_safely(root / manifest_name, max_bytes=200_000)
        if not content:
            continue
        lowered = content.lower()
        for key, label in PY_FRAMEWORK_TEXT_SIGNALS.items():
            if key in lowered:
                hints.add(label)
    if (root / "manage.py").is_file():
        hints.add("Django")
    return sorted(hints)


def detect(root: Path) -> DetectionResult:
    manifests = detect_manifests(root)
    language_breakdown = detect_language_breakdown(root)

    primary_language = None
    if language_breakdown:
        primary_language = max(language_breakdown.items(), key=lambda kv: kv[1])[0]

    framework_hints = _detect_js_frameworks(root) + _detect_py_frameworks(root, manifests)

    result = DetectionResult(
        primary_language=primary_language,
        language_breakdown=language_breakdown,
        manifests=manifests,
        framework_hints=framework_hints,
        has_dockerfile=(root / "Dockerfile").is_file(),
        has_docker_compose=any(
            (root / name).is_file() for name in ("docker-compose.yml", "docker-compose.yaml")
        ),
    )
    logger.info(
        "Detection: primary=%s manifests=%s frameworks=%s",
        result.primary_language, result.manifests, result.framework_hints,
    )
    return result