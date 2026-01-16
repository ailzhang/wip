"""Tests for mark gone command."""

import json
from click.testing import CliRunner

from wip.cli import main


class TestMarkGoneCommand:
    """Tests for wip mark <id> gone command."""

    def test_gone_task(self, isolated_storage_with_sample):
        """Test marking a task as gone."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "1", "gone"])

        assert result.exit_code == 0
        assert "Task [1] gone: Design API" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert "1" not in data["tasks"]

    def test_gone_removes_edges(self, isolated_storage_with_sample):
        """Test that gone also removes connected edges."""
        runner = CliRunner()
        # sample_state has edge from 1 to 2
        runner.invoke(main, ["mark", "1", "gone"])

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        # Edge should be removed
        assert len(data["edges"]) == 0

    def test_gone_blocked_task(self, isolated_storage_with_sample):
        """Test marking a blocked task as gone."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "4", "gone"])

        assert result.exit_code == 0
        assert "Task [4] gone" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert len(data["blocked"]) == 0

    def test_gone_history_entry(self, isolated_storage_with_sample):
        """Test marking a history entry as gone."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "5", "gone"])

        assert result.exit_code == 0
        assert "Task [5] gone" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert len(data["history"]) == 0

    def test_gone_nonexistent_task(self, isolated_storage_with_sample):
        """Test error when marking non-existent task as gone."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "999", "gone"])

        assert "Error: Task 999 not found" in result.output
