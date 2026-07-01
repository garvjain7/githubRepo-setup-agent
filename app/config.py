"""
Central configuration for the app.
Every tunable that matters for ingestion, caching, and cleanup lives here,
so no module hardcodes a threshold that another module needs to agree with.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- GitHub access ---
    github_token: str | None = None
    github_api_base: str = "https://api.github.com"
    github_request_timeout_seconds: int = 30

    # --- Workspace / filesystem ---
    workspace_root: Path = Path("workspaces")
    max_repo_size_mb: int = 300          # reject before extracting if tarball exceeds this
    max_tier1_file_bytes: int = 200_000  # don't fully read huge "small" files (e.g. a bloated README)

    # --- Session cache (Redis) ---
    redis_url: str = "redis://localhost:6379/0"
    session_cache_max_mb: int = 50       # LRU eviction threshold per session
    session_idle_timeout_minutes: int = 30

    # --- Logging ---
    log_level: str = "INFO"
    log_dir: Path = Path("logs")


settings = Settings()