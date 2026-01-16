"""Tests for JSON persistence."""

import json

from wip.model import State, Task
from wip.storage import load_state, save_state, backup_state


class TestLoadState:
    """Tests for load_state function."""

    def test_load_empty_state(self, state_file):
        """Test loading an empty state file."""
        state = load_state(state_file)
        assert state.tasks == {}
        assert state.edges == []
        assert state.blocked == []
        assert state.history == []
        assert state.next_id == 1

    def test_load_sample_state(self, sample_state_file, sample_state):
        """Test loading a state file with sample data."""
        state = load_state(sample_state_file)
        assert len(state.tasks) == 3
        assert len(state.edges) == 1
        assert len(state.blocked) == 1
        assert len(state.history) == 1
        assert state.next_id == 6

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent file returns empty state."""
        nonexistent = tmp_path / "does_not_exist.json"
        state = load_state(nonexistent)
        assert state.tasks == {}
        assert state.next_id == 1


class TestSaveState:
    """Tests for save_state function."""

    def test_save_empty_state(self, tmp_path):
        """Test saving an empty state."""
        state_file = tmp_path / ".wip" / "state.json"
        state = State()
        save_state(state, state_file)

        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["tasks"] == {}
        assert data["next_id"] == 1

    def test_save_state_with_tasks(self, tmp_path):
        """Test saving a state with tasks."""
        state_file = tmp_path / ".wip" / "state.json"
        state = State()
        state.tasks["1"] = Task(id=1, title="Test task", active=True)
        state.next_id = 2
        save_state(state, state_file)

        data = json.loads(state_file.read_text())
        assert "1" in data["tasks"]
        assert data["tasks"]["1"]["title"] == "Test task"
        assert data["next_id"] == 2

    def test_save_creates_directory(self, tmp_path):
        """Test save_state creates parent directory if needed."""
        state_file = tmp_path / "nested" / "dir" / "state.json"
        state = State()
        save_state(state, state_file)

        assert state_file.exists()

    def test_save_overwrites_existing(self, state_file):
        """Test save_state overwrites existing file."""
        state = load_state(state_file)
        state.tasks["1"] = Task(id=1, title="New task")
        state.next_id = 2
        save_state(state, state_file)

        # Load again to verify
        state2 = load_state(state_file)
        assert "1" in state2.tasks
        assert state2.tasks["1"].title == "New task"


class TestBackupState:
    """Tests for backup_state function."""

    def test_backup_existing_state(self, sample_state_file, tmp_path):
        """Test backing up an existing state file."""
        # Set up backup directory in tmp_path
        import wip.storage as storage

        original_backup_dir = storage.BACKUP_DIR
        storage.BACKUP_DIR = tmp_path / "backups"

        try:
            backup_path = backup_state(sample_state_file)
            assert backup_path is not None
            assert backup_path.exists()
            assert backup_path.parent == storage.BACKUP_DIR

            # Verify backup content matches original
            original = json.loads(sample_state_file.read_text())
            backup = json.loads(backup_path.read_text())
            assert original == backup
        finally:
            storage.BACKUP_DIR = original_backup_dir

    def test_backup_nonexistent_file(self, tmp_path):
        """Test backing up a non-existent file returns None."""
        nonexistent = tmp_path / "does_not_exist.json"
        result = backup_state(nonexistent)
        assert result is None


class TestRoundTrip:
    """Tests for save/load round-trip."""

    def test_round_trip(self, tmp_path, sample_state):
        """Test saving and loading preserves data."""
        state_file = tmp_path / "state.json"

        # Create state from sample data
        original = State.from_dict(sample_state)

        # Save and reload
        save_state(original, state_file)
        loaded = load_state(state_file)

        # Verify all data preserved
        assert len(loaded.tasks) == len(original.tasks)
        assert len(loaded.edges) == len(original.edges)
        assert len(loaded.blocked) == len(original.blocked)
        assert len(loaded.history) == len(original.history)
        assert loaded.next_id == original.next_id
        assert loaded.config.max_active == original.config.max_active
