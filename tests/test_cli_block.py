"""Tests for mark command with hold/release states."""

import json
from click.testing import CliRunner

from wip.cli import main


class TestMarkHoldCommand:
    """Tests for wip mark <id> hold command."""

    def test_mark_hold_task(self, isolated_storage_with_sample):
        """Test putting a task on hold."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "2", "hold", "--by", "Bob"])

        assert result.exit_code == 0
        assert "Task [2] on hold (Bob)" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert "2" not in data["tasks"]
        assert any(b["id"] == 2 and b["blocker"] == "Bob" for b in data["blocked"])

    def test_mark_hold_preserves_edges(self, isolated_storage_with_sample):
        """Test that holding a task preserves connected edges for DAG display."""
        runner = CliRunner()
        # Task 1 has edge to task 2
        runner.invoke(main, ["mark", "1", "hold", "--by", "Alice"])

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert len(data["edges"]) == 1  # Edge preserved for DAG display

    def test_mark_hold_nonexistent_task(self, isolated_storage_with_sample):
        """Test error when holding non-existent task."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "999", "hold", "--by", "Alice"])

        assert "Error: Task 999 not found" in result.output

    def test_mark_hold_requires_by(self, isolated_storage_with_sample):
        """Test error when --by option is missing for hold state."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "2", "hold"])

        assert "Error: --by option is required" in result.output


class TestMarkReleaseCommand:
    """Tests for wip mark <id> release command."""

    def test_mark_release_task(self, isolated_storage_with_sample):
        """Test releasing a task from hold."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "4", "release"])

        assert result.exit_code == 0
        assert "Released task [4]" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert "4" in data["tasks"]
        assert len(data["blocked"]) == 0

    def test_mark_release_nonexistent(self, isolated_storage_with_sample):
        """Test error when releasing non-existent held task."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "999", "release"])

        assert "Error: Task 999 not found in hold" in result.output


class TestLinkBlockedTasks:
    """Tests for linking blocked tasks."""

    def test_link_blocked_task_to_regular(self, isolated_storage_with_sample):
        """Test linking a blocked task to a regular task."""
        runner = CliRunner()
        # Task 4 is blocked, task 2 is regular
        result = runner.invoke(main, ["link", "4", "2"])

        assert result.exit_code == 0
        assert "Linked task 4 -> 2" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert any(e["from"] == 4 and e["to"] == 2 for e in data["edges"])

    def test_link_regular_to_blocked(self, isolated_storage_with_sample):
        """Test linking a regular task to a blocked task."""
        runner = CliRunner()
        # Task 2 is regular, task 4 is blocked
        result = runner.invoke(main, ["link", "2", "4"])

        assert result.exit_code == 0
        assert "Linked task 2 -> 4" in result.output

    def test_link_two_blocked_tasks(self, isolated_storage_with_sample):
        """Test linking two blocked tasks."""
        runner = CliRunner()
        # First add another blocked task
        runner.invoke(main, ["add", "Another blocked", "-b", "Charlie"])

        # Now link task 4 (blocked) to task 6 (blocked)
        result = runner.invoke(main, ["link", "4", "6"])

        assert result.exit_code == 0
        assert "Linked task 4 -> 6" in result.output

    def test_link_cascades_hold_status(self, isolated_storage_with_sample):
        """Test that linking to a blocked task cascades hold status."""
        runner = CliRunner()
        # Task 4 is blocked, task 2 is regular
        # Link 4 -> 2 means task 2 depends on task 4
        result = runner.invoke(main, ["link", "4", "2"])

        assert result.exit_code == 0
        assert "Linked task 4 -> 2" in result.output
        assert "Moved to hold" in result.output
        assert "[2]" in result.output

        # Verify task 2 is now blocked
        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert "2" not in data["tasks"]
        assert any(b["id"] == 2 and "Task 4" in b["blocker"] for b in data["blocked"])

    def test_link_cascades_to_descendants(self, isolated_storage_with_sample):
        """Test that linking cascades hold status to all descendants."""
        runner = CliRunner()
        # Create a chain: task 2 -> task 3 (3 depends on 2)
        runner.invoke(main, ["link", "2", "3"])

        # Now link blocked task 4 -> task 2 (2 depends on 4)
        # This should cascade hold to both 2 and 3
        result = runner.invoke(main, ["link", "4", "2"])

        assert result.exit_code == 0
        assert "Moved to hold" in result.output

        # Verify both task 2 and 3 are now blocked
        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert "2" not in data["tasks"]
        assert "3" not in data["tasks"]
        blocked_ids = [b["id"] for b in data["blocked"]]
        assert 2 in blocked_ids
        assert 3 in blocked_ids
