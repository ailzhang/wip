"""Tests for the data model classes."""

from datetime import datetime

from wip.model import Task, Edge, BlockedTask, HistoryEntry, Config, State


class TestTask:
    """Tests for Task dataclass."""

    def test_create_task(self):
        """Test creating a task with default values."""
        task = Task(id=1, title="Test task")
        assert task.id == 1
        assert task.title == "Test task"
        assert task.active is False

    def test_create_active_task(self):
        """Test creating an active task."""
        task = Task(id=1, title="Active task", active=True)
        assert task.active is True

    def test_to_dict(self):
        """Test converting task to dictionary."""
        task = Task(id=1, title="Test task", active=True)
        d = task.to_dict()
        assert d == {"id": 1, "title": "Test task", "active": True, "created_at": ""}

    def test_from_dict(self):
        """Test creating task from dictionary."""
        data = {"id": 1, "title": "Test task", "active": True}
        task = Task.from_dict(data)
        assert task.id == 1
        assert task.title == "Test task"
        assert task.active is True

    def test_from_dict_missing_active(self):
        """Test creating task when active is missing defaults to False."""
        data = {"id": 1, "title": "Test task"}
        task = Task.from_dict(data)
        assert task.active is False


class TestEdge:
    """Tests for Edge dataclass."""

    def test_create_edge(self):
        """Test creating an edge."""
        edge = Edge(from_id=1, to_id=2)
        assert edge.from_id == 1
        assert edge.to_id == 2

    def test_to_dict(self):
        """Test converting edge to dictionary."""
        edge = Edge(from_id=1, to_id=2)
        d = edge.to_dict()
        assert d == {"from": 1, "to": 2}

    def test_from_dict(self):
        """Test creating edge from dictionary."""
        data = {"from": 1, "to": 2}
        edge = Edge.from_dict(data)
        assert edge.from_id == 1
        assert edge.to_id == 2


class TestBlockedTask:
    """Tests for BlockedTask dataclass."""

    def test_create_blocked_task(self):
        """Test creating a blocked task."""
        task = BlockedTask(id=1, title="Blocked task", blocker="Alice")
        assert task.id == 1
        assert task.title == "Blocked task"
        assert task.blocker == "Alice"

    def test_to_dict(self):
        """Test converting blocked task to dictionary."""
        task = BlockedTask(id=1, title="Blocked task", blocker="Alice")
        d = task.to_dict()
        assert d == {"id": 1, "title": "Blocked task", "blocker": "Alice", "created_at": ""}

    def test_from_dict(self):
        """Test creating blocked task from dictionary."""
        data = {"id": 1, "title": "Blocked task", "blocker": "Alice"}
        task = BlockedTask.from_dict(data)
        assert task.id == 1
        assert task.title == "Blocked task"
        assert task.blocker == "Alice"


class TestHistoryEntry:
    """Tests for HistoryEntry dataclass."""

    def test_create_history_entry(self):
        """Test creating a history entry."""
        entry = HistoryEntry(id=1, title="Done task", completed_at="2025-01-13T10:30:00")
        assert entry.id == 1
        assert entry.title == "Done task"
        assert entry.completed_at == "2025-01-13T10:30:00"

    def test_to_dict(self):
        """Test converting history entry to dictionary."""
        entry = HistoryEntry(id=1, title="Done task", completed_at="2025-01-13T10:30:00")
        d = entry.to_dict()
        assert d == {"id": 1, "title": "Done task", "completed_at": "2025-01-13T10:30:00", "created_at": ""}

    def test_from_dict(self):
        """Test creating history entry from dictionary."""
        data = {"id": 1, "title": "Done task", "completed_at": "2025-01-13T10:30:00"}
        entry = HistoryEntry.from_dict(data)
        assert entry.id == 1
        assert entry.title == "Done task"
        assert entry.completed_at == "2025-01-13T10:30:00"

    def test_completed_datetime(self):
        """Test parsing completed_at as datetime."""
        entry = HistoryEntry(id=1, title="Done task", completed_at="2025-01-13T10:30:00")
        dt = entry.completed_datetime
        assert isinstance(dt, datetime)
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 13
        assert dt.hour == 10
        assert dt.minute == 30


class TestConfig:
    """Tests for Config dataclass."""

    def test_create_config_default(self):
        """Test creating config with default values."""
        config = Config()
        assert config.max_active == 2

    def test_create_config_custom(self):
        """Test creating config with custom values."""
        config = Config(max_active=5)
        assert config.max_active == 5

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = Config(max_active=3)
        d = config.to_dict()
        assert d == {
            "max_active": 3,
            "stale_days": 14,
            "share": {"enabled": False, "gist_id": None, "gist_url": None},
        }

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {"max_active": 4}
        config = Config.from_dict(data)
        assert config.max_active == 4

    def test_from_dict_missing_max_active(self):
        """Test creating config when max_active is missing defaults to 2."""
        config = Config.from_dict({})
        assert config.max_active == 2


class TestState:
    """Tests for State dataclass."""

    def test_create_empty_state(self):
        """Test creating an empty state."""
        state = State()
        assert state.tasks == {}
        assert state.edges == []
        assert state.blocked == []
        assert state.history == []
        assert state.next_id == 1
        assert state.config.max_active == 2

    def test_to_dict(self, sample_state):
        """Test converting state to dictionary."""
        state = State.from_dict(sample_state)
        d = state.to_dict()
        # Config gains default share settings after round-trip
        expected = sample_state.copy()
        expected["config"] = {
            **sample_state["config"],
            "share": {"enabled": False, "gist_id": None, "gist_url": None},
        }
        assert d == expected

    def test_from_dict(self, sample_state):
        """Test creating state from dictionary."""
        state = State.from_dict(sample_state)
        assert len(state.tasks) == 3
        assert len(state.edges) == 1
        assert len(state.blocked) == 1
        assert len(state.history) == 1
        assert state.next_id == 6
        assert state.config.max_active == 2

    def test_get_task_exists(self, sample_state):
        """Test getting an existing task."""
        state = State.from_dict(sample_state)
        task = state.get_task(1)
        assert task is not None
        assert task.id == 1
        assert task.title == "Design API"

    def test_get_task_not_exists(self, sample_state):
        """Test getting a non-existent task."""
        state = State.from_dict(sample_state)
        task = state.get_task(999)
        assert task is None

    def test_get_blocked_exists(self, sample_state):
        """Test getting an existing blocked task."""
        state = State.from_dict(sample_state)
        blocked = state.get_blocked(4)
        assert blocked is not None
        assert blocked.id == 4
        assert blocked.blocker == "Alice"

    def test_get_blocked_not_exists(self, sample_state):
        """Test getting a non-existent blocked task."""
        state = State.from_dict(sample_state)
        blocked = state.get_blocked(999)
        assert blocked is None

    def test_active_count(self, sample_state):
        """Test counting active tasks."""
        state = State.from_dict(sample_state)
        assert state.active_count() == 1

    def test_has_edge_true(self, sample_state):
        """Test checking for existing edge."""
        state = State.from_dict(sample_state)
        assert state.has_edge(1, 2) is True

    def test_has_edge_false(self, sample_state):
        """Test checking for non-existent edge."""
        state = State.from_dict(sample_state)
        assert state.has_edge(2, 3) is False

    def test_get_edges_from(self, sample_state):
        """Test getting edges starting from a task."""
        state = State.from_dict(sample_state)
        edges = state.get_edges_from(1)
        assert len(edges) == 1
        assert edges[0].to_id == 2

    def test_get_edges_to(self, sample_state):
        """Test getting edges ending at a task."""
        state = State.from_dict(sample_state)
        edges = state.get_edges_to(2)
        assert len(edges) == 1
        assert edges[0].from_id == 1
