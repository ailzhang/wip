"""Tests for mark command with done state."""

import json
from click.testing import CliRunner

from wip.cli import main


class TestMarkDoneCommand:
    """Tests for wip mark <id> done command."""

    def test_mark_done_task(self, isolated_storage_with_sample):
        """Test marking a task as done."""
        runner = CliRunner()
        # Task 3 has no dependencies, can be completed
        result = runner.invoke(main, ["mark", "3", "done"])

        assert result.exit_code == 0
        assert "Completed task [3]: Update docs" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert "3" not in data["tasks"]
        assert any(h["id"] == 3 and h["title"] == "Update docs" for h in data["history"])

    def test_mark_done_removes_edges(self, isolated_storage_with_sample):
        """Test that done removes connected edges."""
        runner = CliRunner()
        # sample_state has edge 1 -> 2, complete 1 first (no deps)
        runner.invoke(main, ["mark", "1", "done"])

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert len(data["edges"]) == 0

    def test_mark_done_preserves_created_at(self, isolated_storage_with_sample):
        """Test that done preserves created_at in history."""
        runner = CliRunner()
        # Task 1 has no dependencies
        runner.invoke(main, ["mark", "1", "done"])

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        history_entry = next(h for h in data["history"] if h["id"] == 1)
        assert history_entry["created_at"] == "2025-01-12T09:00:00"

    def test_mark_done_sets_completed_at(self, isolated_storage_with_sample):
        """Test that done sets completed_at timestamp."""
        runner = CliRunner()
        # Task 3 has no dependencies
        runner.invoke(main, ["mark", "3", "done"])

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        history_entry = next(h for h in data["history"] if h["id"] == 3)
        assert history_entry["completed_at"]
        assert "T" in history_entry["completed_at"]

    def test_mark_done_nonexistent(self, isolated_storage_with_sample):
        """Test error when task doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(main, ["mark", "999", "done"])

        assert "Error: Task 999 not found" in result.output

    def test_mark_done_blocked_by_dependencies(self, isolated_storage_with_sample):
        """Test error when trying to complete a task with incomplete dependencies."""
        runner = CliRunner()
        # sample_state has edge 1 -> 2, so task 2 depends on task 1
        # Cannot complete task 2 while task 1 is incomplete
        result = runner.invoke(main, ["mark", "2", "done"])

        assert "Error: Cannot complete task 2" in result.output
        assert "depends on incomplete tasks [1]" in result.output
