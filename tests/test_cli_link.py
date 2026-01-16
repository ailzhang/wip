"""Tests for link and unlink commands."""

import json
from click.testing import CliRunner

from wip.cli import main


class TestLinkCommand:
    """Tests for wip link command."""

    def test_link_tasks(self, isolated_storage_with_sample):
        """Test linking two tasks."""
        runner = CliRunner()
        result = runner.invoke(main, ["link", "2", "3"])

        assert result.exit_code == 0
        assert "Linked task 2 -> 3" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert any(e["from"] == 2 and e["to"] == 3 for e in data["edges"])

    def test_link_rejects_cycle(self, isolated_storage_with_sample):
        """Test that linking rejects cycles."""
        runner = CliRunner()
        # sample_state has edge 1 -> 2
        result = runner.invoke(main, ["link", "2", "1"])

        assert "would create a cycle" in result.output

    def test_link_rejects_self_loop(self, isolated_storage_with_sample):
        """Test that linking rejects self-loops."""
        runner = CliRunner()
        result = runner.invoke(main, ["link", "1", "1"])

        assert "Cannot link a task to itself" in result.output

    def test_link_rejects_duplicate(self, isolated_storage_with_sample):
        """Test that linking rejects duplicate edges."""
        runner = CliRunner()
        # sample_state already has edge 1 -> 2
        result = runner.invoke(main, ["link", "1", "2"])

        assert "already exists" in result.output

    def test_link_nonexistent_from(self, isolated_storage_with_sample):
        """Test error when from task doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(main, ["link", "999", "1"])

        assert "Error: Task 999 not found" in result.output

    def test_link_nonexistent_to(self, isolated_storage_with_sample):
        """Test error when to task doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(main, ["link", "1", "999"])

        assert "Error: Task 999 not found" in result.output


class TestUnlinkCommand:
    """Tests for wip unlink command."""

    def test_unlink_tasks(self, isolated_storage_with_sample):
        """Test unlinking two tasks."""
        runner = CliRunner()
        # sample_state has edge 1 -> 2
        result = runner.invoke(main, ["unlink", "1", "2"])

        assert result.exit_code == 0
        assert "Unlinked task 1 -> 2" in result.output

        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())
        assert len(data["edges"]) == 0

    def test_unlink_nonexistent_edge(self, isolated_storage_with_sample):
        """Test error when edge doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(main, ["unlink", "2", "3"])

        assert "not found" in result.output
