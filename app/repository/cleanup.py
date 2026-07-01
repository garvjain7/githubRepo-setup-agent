"""
Deletes a session's extracted workspace. Kept deliberately simple: this
module handles the disk side only. Scheduling WHEN cleanup runs (idle
timeout, tab-close signal) belongs to session management, built alongside
the cache module — not duplicated here.
"""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.utils.filesystem import remove_dir_safely
from app.utils.logger import get_logger

logger = get_logger(__name__)


def workspace_path_for_session(session_id: str) -> Path:
    return settings.workspace_root / session_id


def cleanup_workspace(session_id: str) -> None:
    path = workspace_path_for_session(session_id)
    remove_dir_safely(path, must_be_within=settings.workspace_root)
    logger.info("Cleaned up workspace for session %s", session_id)