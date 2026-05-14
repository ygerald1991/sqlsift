"""Helpers for resolving a ThresholdConfig from multiple sources."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from sqlsift.threshold import ThresholdConfig, default_config, load_threshold_config

_ENV_VAR = "SQLSIFT_THRESHOLD_FILE"
_DEFAULT_FILENAME = "sqlsift_thresholds.json"


def _find_config_file(start: Path) -> Optional[Path]:
    """Walk up from *start* looking for a threshold config file."""
    for directory in (start, *start.parents):
        candidate = directory / _DEFAULT_FILENAME
        if candidate.is_file():
            return candidate
    return None


def resolve_threshold_config(
    explicit_path: Optional[str] = None,
    search_cwd: bool = True,
) -> ThresholdConfig:
    """Resolve a ThresholdConfig using the following priority:

    1. *explicit_path* argument
    2. ``SQLSIFT_THRESHOLD_FILE`` environment variable
    3. Auto-discovery of ``sqlsift_thresholds.json`` walking up from cwd
    4. Library defaults
    """
    if explicit_path:
        return load_threshold_config(explicit_path)

    env_path = os.environ.get(_ENV_VAR)
    if env_path:
        return load_threshold_config(env_path)

    if search_cwd:
        found = _find_config_file(Path.cwd())
        if found:
            return load_threshold_config(found)

    return default_config()
