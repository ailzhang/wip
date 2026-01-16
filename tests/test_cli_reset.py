"""Tests for reset command."""

import json
from click.testing import CliRunner

from wip.cli import main


class TestResetCommand:
    """Tests for wip reset command."""

    def test_reset_clears_state(self, isolated_storage_with_sample):
        """Test that reset clears all tasks."""
        runner = CliRunner()
        result = runner.invoke(main, ["reset"])

        assert result.exit_code == 0
        assert "State reset" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert data["tasks"] == {}
        assert data["edges"] == []
        assert data["blocked"] == []
        assert data["history"] == []

    def test_reset_preserves_config(self, isolated_storage_with_sample):
        """Test that reset preserves config."""
        runner = CliRunner()
        runner.invoke(main, ["config", "max_active", "5"])
        runner.invoke(main, ["reset"])

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert data["config"]["max_active"] == 5

    def test_reset_creates_backup(self, isolated_storage_with_sample):
        """Test that reset creates a backup."""
        runner = CliRunner()
        result = runner.invoke(main, ["reset"])

        assert "Backup saved to:" in result.output

        backup_dir = isolated_storage_with_sample["backup_dir"]
        assert backup_dir.exists()
        backup_files = list(backup_dir.glob("state_*.json"))
        assert len(backup_files) == 1

    def test_reset_backup_contains_original_data(self, isolated_storage_with_sample, sample_state):
        """Test that backup contains original data."""
        runner = CliRunner()
        runner.invoke(main, ["reset"])

        backup_dir = isolated_storage_with_sample["backup_dir"]
        backup_files = list(backup_dir.glob("state_*.json"))
        backup_data = json.loads(backup_files[0].read_text())

        # Should contain original tasks
        assert "1" in backup_data["tasks"]
        assert backup_data["tasks"]["1"]["title"] == "Design API"

    def test_reset_empty_state_no_backup(self, isolated_storage):
        """Test that reset on empty state doesn't create backup."""
        runner = CliRunner()
        result = runner.invoke(main, ["reset"])

        assert "Backup saved to:" not in result.output
