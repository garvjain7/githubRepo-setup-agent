"""
Generates a deterministic, rule-based baseline setup guide from a
RepositoryAnalysis. No LLM involved — this is the guide shown immediately
after ingestion, before any chat happens. The AI agent (later module) can
refine or correct this conversationally, but this baseline must stand on
its own since a user may never open the chat at all.

Explicitly framed as best-effort: these are inferences from static files,
never verified by actually running anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.repository.analyzer import RepositoryAnalysis

_LOCKFILE_TO_INSTALL_CMD = {
    "package-lock.json": "npm install",
    "yarn.lock": "yarn install",
    "pnpm-lock.yaml": "pnpm install",
}


@dataclass(frozen=True)
class SetupStep:
    title: str
    command: str | None = None
    note: str | None = None


@dataclass
class SetupGuide:
    steps: list[SetupStep] = field(default_factory=list)
    confidence_notes: list[str] = field(default_factory=list)


def _docker_step(analysis: RepositoryAnalysis) -> SetupStep | None:
    if analysis.detection.has_docker_compose:
        return SetupStep(
            title="Fastest path: run with Docker Compose",
            command="docker compose up",
            note="Handles dependencies and services for you if this repo defines them.",
        )
    if analysis.detection.has_dockerfile:
        return SetupStep(
            title="Alternative: build and run with Docker",
            command="docker build -t app . && docker run -p 8000:8000 app",
            note="Port mapping is a guess — check the Dockerfile's EXPOSE line.",
        )
    return None


def _install_step(analysis: RepositoryAnalysis, notes: list[str]) -> SetupStep | None:
    manifests = set(analysis.detection.manifests)
    primary = analysis.detection.primary_language

    if "package.json" in manifests:
        lockfiles_present = [
            name for name in _LOCKFILE_TO_INSTALL_CMD
            if (analysis.root_path / name).is_file()
        ]
        if len(lockfiles_present) > 1:
            notes.append(
                f"Multiple lockfiles found ({', '.join(lockfiles_present)}) — "
                f"verify which package manager this project actually uses."
            )
        cmd = _LOCKFILE_TO_INSTALL_CMD.get(lockfiles_present[0], "npm install") if lockfiles_present else "npm install"
        return SetupStep(title="Install JavaScript/Node dependencies", command=cmd)

    if "pyproject.toml" in manifests:
        return SetupStep(
            title="Install Python dependencies",
            command="poetry install",
            note="Detected pyproject.toml. If this project doesn't use Poetry, "
                 "try: pip install -e . or pip install -r requirements.txt",
        )

    if "requirements.txt" in manifests:
        return SetupStep(
            title="Install Python dependencies",
            command="pip install -r requirements.txt",
            note="Consider using a virtual environment first: python -m venv venv",
        )

    if "go.mod" in manifests:
        return SetupStep(title="Install Go dependencies", command="go mod download")

    if "Cargo.toml" in manifests:
        return SetupStep(title="Build Rust dependencies", command="cargo build")

    if "Gemfile" in manifests:
        return SetupStep(title="Install Ruby dependencies", command="bundle install")

    if primary:
        notes.append(
            f"No recognized manifest file found, though {primary} source files "
            f"are present — dependency setup couldn't be inferred automatically."
        )
    return None


def _env_step(analysis: RepositoryAnalysis) -> SetupStep | None:
    if not analysis.env_vars:
        return None
    var_names = ", ".join(sorted({e.variable for e in analysis.env_vars})[:12])
    suffix = "..." if len({e.variable for e in analysis.env_vars}) > 12 else ""
    return SetupStep(
        title="Set required environment variables",
        note=f"Found references to: {var_names}{suffix}. "
             f"Check for a .env.example file, or ask the assistant about a specific variable.",
    )


def generate_setup_guide(analysis: RepositoryAnalysis) -> SetupGuide:
    notes: list[str] = [
        "This guide is inferred from repository files, not verified by execution — "
        "treat it as a starting point."
    ]
    steps: list[SetupStep] = []

    docker_step = _docker_step(analysis)
    if docker_step:
        steps.append(docker_step)

    install_step = _install_step(analysis, notes)
    if install_step:
        steps.append(install_step)

    env_step = _env_step(analysis)
    if env_step:
        steps.append(env_step)

    if not steps:
        notes.append(
            "No manifest, Dockerfile, or dependency signal was detected. "
            "This repo may need manual inspection, or may not be a runnable application."
        )

    return SetupGuide(steps=steps, confidence_notes=notes)