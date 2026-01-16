"""Tests for mark command with active/inactive states."""

import json
from click.testing import CliRunner

from wip.cli import main


class TestMarkActiveCommand:
    """Tests for wip mark <id> active command."""

    def test_mark_active_task(self, isolated_storage_with_sample):
        """Test marking a task as active."""
        runner = CliRunner()
        # Task 3 has no dependencies, can be activated
        result = runner.invoke(main, ["mark", "3", "active"])

        assert result.exit_code == 0
        assert "Marked task [3] as active" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert data["tasks"]["3"]["active"] is True

    def test_mark_active_respects_max_active(self, isolated_storage_with_sample):
        """Test that active respects max_active limit."""
        runner = CliRunner()
        # sample_state has task 1 already active, max_active=2
        # Task 3 has no dependencies
        runner.invoke(main, ["mark", "3", "active"])
        # Now try to activate another task - but task 2 depends on 1
        # First complete task 1 to free up a slot and allow task 2
        runner.invoke(main, ["mark", "1", "done"])
        runner.invoke(main, ["mark", "2", "active"])
        # Now we have 2 active (3 and 2), try to add more
        # But we need a task without dependencies - add one
        runner.invoke(main, ["add", "New task"])
        result = runner.invoke(main, ["mark", "6", "active"])

        assert "Maximum active tasks (2) reached" in result.output

    def test_mark_active_already_active(self, isolated_storage_with_sample):
        """Test marking an already active task."""
        runner = CliRunner()
        # Task 1 is already active
        result = runner.invoke(main, ["mark", "1", "active"])

        assert "already active" in result.output

    def test_mark_active_nonexistent(self, isolated_storage_with_sample):
        """Test error when task doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "999", "active"])

        assert "Error: Task 999 not found" in result.output

    def test_mark_active_blocked_by_dependencies(self, isolated_storage_with_sample):
        """Test error when trying to activate a task with incomplete dependencies."""
        runner = CliRunner()
        # sample_state has edge 1 -> 2, so task 2 depends on task 1
        # Cannot activate task 2 while task 1 is incomplete
        result = runner.invoke(main, ["mark", "2", "active"])

        assert "Error: Cannot activate task 2" in result.output
        assert "depends on incomplete tasks [1]" in result.output


class TestMarkInactiveCommand:
    """Tests for wip mark <id> inactive command."""

    def test_mark_inactive_task(self, isolated_storage_with_sample):
        """Test marking a task as inactive."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "1", "inactive"])

        assert result.exit_code == 0
        assert "Marked task [1] as inactive" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert data["tasks"]["1"]["active"] is False

    def test_mark_inactive_already_inactive(self, isolated_storage_with_sample):
        """Test marking an already inactive task."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "2", "inactive"])

        assert "not active" in result.output

    def test_mark_inactive_nonexistent(self, isolated_storage_with_sample):
        """Test error when task doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "999", "inactive"])

        assert "Error: Task 999 not found" in result.output
