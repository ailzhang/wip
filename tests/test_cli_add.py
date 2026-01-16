"""Tests for add command."""

import json
from click.testing import CliRunner

from wip.cli import main


class TestAddCommand:
    """Tests for wip add command."""

    def test_add_task(self, isolated_storage):
        """Test adding a regular task."""
        runner = CliRunner()
        result = runner.invoke(main, ["add", "Test task"])

        assert result.exit_code == 0
        assert "Added task [1]: Test task" in result.output

        # Verify state was saved
        state_file = isolated_storage["state_file"]
        data = json.loads(state_file.read_text())
        assert "1" in data["tasks"]
        assert data["tasks"]["1"]["title"] == "Test task"
        assert data["tasks"]["1"]["id"] == 1
        assert data["next_id"] == 2

    def test_add_task_increments_id(self, isolated_storage):
        """Test that task IDs increment correctly."""
        runner = CliRunner()
        runner.invoke(main, ["add", "First task"])
        result = runner.invoke(main, ["add", "Second task"])

        assert result.exit_code == 0
        assert "Added task [2]: Second task" in result.output

        state_file = isolated_storage["state_file"]
        data = json.loads(state_file.read_text())
        assert "1" in data["tasks"]
        assert "2" in data["tasks"]
        assert data["next_id"] == 3

    def test_add_blocked_task(self, isolated_storage):
        """Test adding a blocked task."""
        runner = CliRunner()
        result = runner.invoke(main, ["add", "Blocked task", "--blocked", "Alice"])

        assert result.exit_code == 0
        assert "Added blocked task [1]: Blocked task (blocked by: Alice)" in result.output

        state_file = isolated_storage["state_file"]
        data = json.loads(state_file.read_text())
        assert len(data["blocked"]) == 1
        assert data["blocked"][0]["title"] == "Blocked task"
        assert data["blocked"][0]["blocker"] == "Alice"

    def test_add_blocked_task_short_option(self, isolated_storage):
        """Test adding a blocked task with -b shorthand."""
        runner = CliRunner()
        result = runner.invoke(main, ["add", "Blocked task", "-b", "Bob"])

        assert result.exit_code == 0
        assert "blocked by: Bob" in result.output

    def test_add_task_has_created_at(self, isolated_storage):
        """Test that added tasks have created_at timestamp."""
        runner = CliRunner()
        runner.invoke(main, ["add", "Test task"])

        state_file = isolated_storage["state_file"]
        data = json.loads(state_file.read_text())
        assert data["tasks"]["1"]["created_at"]
        # Should be ISO format
        assert "T" in data["tasks"]["1"]["created_at"]
