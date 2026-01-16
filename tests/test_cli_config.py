"""Tests for config command."""

import json
from click.testing import CliRunner

from wip.cli import main


class TestConfigCommand:
    """Tests for wip config command."""

    def test_config_max_active(self, isolated_storage):
        """Test setting max_active config."""
        runner = CliRunner()
        result = runner.invoke(main, ["config", "max_active", "5"])

        assert result.exit_code == 0
        assert "Set max_active = 5" in result.output

        state_file = isolated_storage["state_file"]
        data = json.loads(state_file.read_text())
        assert data["config"]["max_active"] == 5

    def test_config_max_active_persists(self, isolated_storage):
        """Test that max_active config persists and is respected."""
        runner = CliRunner()
        runner.invoke(main, ["config", "max_active", "1"])
        runner.invoke(main, ["add", "Task 1"])
        runner.invoke(main, ["mark", "1", "active"])
        runner.invoke(main, ["add", "Task 2"])
        result = runner.invoke(main, ["mark", "2", "active"])

        assert "Maximum active tasks (1) reached" in result.output

    def test_config_invalid_value(self, isolated_storage):
        """Test error for invalid config value."""
        runner = CliRunner()
        result = runner.invoke(main, ["config", "max_active", "abc"])

        assert "must be an integer" in result.output

    def test_config_invalid_key(self, isolated_storage):
        """Test error for unknown config key."""
        runner = CliRunner()
        result = runner.invoke(main, ["config", "unknown_key", "value"])

        assert "Unknown config key" in result.output

    def test_config_min_value(self, isolated_storage):
        """Test error for max_active less than 1."""
        runner = CliRunner()
        result = runner.invoke(main, ["config", "max_active", "0"])

        assert "must be at least 1" in result.output
