"""Tests for sqlsift.threshold."""

from __future__ import annotations

import json
import pytest

from sqlsift.threshold import ThresholdConfig, default_config, load_threshold_config


class TestThresholdConfig:
    def test_default_global_threshold(self):
        cfg = ThresholdConfig()
        assert cfg.global_threshold == 1.0

    def test_get_threshold_no_table_uses_global(self):
        cfg = ThresholdConfig(global_threshold=2.0)
        assert cfg.get_threshold() == 2.0

    def test_get_threshold_unknown_table_uses_global(self):
        cfg = ThresholdConfig(global_threshold=1.5, per_table={"orders": 0.5})
        assert cfg.get_threshold("users") == 1.5

    def test_get_threshold_known_table_uses_per_table(self):
        cfg = ThresholdConfig(global_threshold=1.5, per_table={"orders": 0.5})
        assert cfg.get_threshold("orders") == 0.5

    def test_is_slow_below_threshold_returns_false(self):
        cfg = ThresholdConfig(global_threshold=1.0)
        assert cfg.is_slow(0.9) is False

    def test_is_slow_at_threshold_returns_true(self):
        cfg = ThresholdConfig(global_threshold=1.0)
        assert cfg.is_slow(1.0) is True

    def test_is_slow_above_threshold_returns_true(self):
        cfg = ThresholdConfig(global_threshold=1.0)
        assert cfg.is_slow(2.5) is True

    def test_is_slow_uses_per_table_threshold(self):
        cfg = ThresholdConfig(global_threshold=1.0, per_table={"events": 0.2})
        assert cfg.is_slow(0.3, table="events") is True
        assert cfg.is_slow(0.3, table="users") is False


class TestLoadThresholdConfig:
    def test_loads_global_threshold(self, tmp_path):
        data = {"global_threshold": 0.75}
        cfg_file = tmp_path / "thresholds.json"
        cfg_file.write_text(json.dumps(data))
        cfg = load_threshold_config(cfg_file)
        assert cfg.global_threshold == 0.75

    def test_loads_per_table(self, tmp_path):
        data = {"global_threshold": 1.0, "per_table": {"orders": 0.4}}
        cfg_file = tmp_path / "thresholds.json"
        cfg_file.write_text(json.dumps(data))
        cfg = load_threshold_config(cfg_file)
        assert cfg.per_table["orders"] == 0.4

    def test_missing_keys_use_defaults(self, tmp_path):
        cfg_file = tmp_path / "thresholds.json"
        cfg_file.write_text(json.dumps({}))
        cfg = load_threshold_config(cfg_file)
        assert cfg.global_threshold == 1.0
        assert cfg.per_table == {}

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_threshold_config(tmp_path / "missing.json")


def test_default_config_returns_threshold_config():
    cfg = default_config()
    assert isinstance(cfg, ThresholdConfig)
    assert cfg.global_threshold == 1.0
