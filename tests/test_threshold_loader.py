"""Tests for sqlsift.threshold_loader."""

from __future__ import annotations

import json
import os

import pytest

from sqlsift.threshold import ThresholdConfig
from sqlsift.threshold_loader import (
    _DEFAULT_FILENAME,
    _ENV_VAR,
    resolve_threshold_config,
)


def _write_cfg(directory, global_threshold=0.5, per_table=None):
    data = {"global_threshold": global_threshold, "per_table": per_table or {}}
    path = directory / _DEFAULT_FILENAME
    path.write_text(json.dumps(data))
    return path


class TestResolveThresholdConfig:
    def test_explicit_path_takes_priority(self, tmp_path):
        cfg_file = _write_cfg(tmp_path, global_threshold=0.3)
        cfg = resolve_threshold_config(explicit_path=str(cfg_file))
        assert cfg.global_threshold == 0.3

    def test_env_var_used_when_no_explicit_path(self, tmp_path, monkeypatch):
        cfg_file = _write_cfg(tmp_path, global_threshold=0.8)
        monkeypatch.setenv(_ENV_VAR, str(cfg_file))
        cfg = resolve_threshold_config()
        assert cfg.global_threshold == 0.8

    def test_explicit_path_overrides_env_var(self, tmp_path, monkeypatch):
        env_file = _write_cfg(tmp_path / "env", global_threshold=0.8)
        (tmp_path / "env").mkdir(exist_ok=True)
        explicit_dir = tmp_path / "explicit"
        explicit_dir.mkdir()
        explicit_file = _write_cfg(explicit_dir, global_threshold=0.2)
        monkeypatch.setenv(_ENV_VAR, str(env_file))
        cfg = resolve_threshold_config(explicit_path=str(explicit_file))
        assert cfg.global_threshold == 0.2

    def test_auto_discover_finds_config_in_cwd(self, tmp_path, monkeypatch):
        _write_cfg(tmp_path, global_threshold=0.6)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv(_ENV_VAR, raising=False)
        cfg = resolve_threshold_config()
        assert cfg.global_threshold == 0.6

    def test_returns_default_when_nothing_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv(_ENV_VAR, raising=False)
        cfg = resolve_threshold_config()
        assert isinstance(cfg, ThresholdConfig)
        assert cfg.global_threshold == 1.0

    def test_search_cwd_false_skips_discovery(self, tmp_path, monkeypatch):
        _write_cfg(tmp_path, global_threshold=0.6)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv(_ENV_VAR, raising=False)
        cfg = resolve_threshold_config(search_cwd=False)
        assert cfg.global_threshold == 1.0
