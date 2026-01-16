"""Tests for Markdown rendering."""

from wip.model import BlockedTask, HistoryEntry, State, Task
from wip.render_md import render_state_md


class TestRenderMd:
    """Tests for Markdown rendering."""

    def test_render_empty_state(self):
        """Test rendering empty state."""
        state = State()
        md = render_state_md(state)

        assert "# WIP Status" in md
        assert "No tasks completed this week" in md

    def test_render_with_active_task(self):
        """Test rendering state with active task."""
        state = State()
        state.tasks["1"] = Task(id=1, title="Test task", active=True)

        md = render_state_md(state)

        assert "Test task" in md
        assert "## Top of Mind" in md

    def test_render_with_blocked_task(self):
        """Test rendering state with blocked task."""
        state = State()
        state.blocked.append(BlockedTask(id=1, title="Blocked task", blocker="Alice"))

        md = render_state_md(state)

        assert "Blocked task" in md
        assert "## On Hold" in md
        assert "Alice" in md

    def test_render_with_backlog(self):
        """Test rendering state with backlog task."""
        state = State()
        state.tasks["1"] = Task(id=1, title="Backlog task", active=False)

        md = render_state_md(state)

        assert "Backlog task" in md
        assert "## Backlog" in md

    def test_render_includes_timestamp(self):
        """Test that Markdown includes last updated timestamp."""
        state = State()
        md = render_state_md(state)

        assert "Updated:" in md

    def test_render_with_history(self):
        """Test rendering with completed tasks this week."""
        from datetime import datetime

        state = State()
        # Add a task completed "today"
        now = datetime.now().isoformat()
        state.history.append(
            HistoryEntry(id=1, title="Completed task", completed_at=now)
        )

        md = render_state_md(state)

        assert "Completed task" in md
        assert "## This Week" in md
        assert "1 completed" in md
