"""Pytest fixtures for wip tests."""

import json

import pytest


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory for state files."""
    state_dir = tmp_path / ".wip"
    state_dir.mkdir()
    return state_dir


@pytest.fixture
def empty_state():
    """Return an empty state dict."""
    return {
        "tasks": {},
        "edges": [],
        "blocked": [],
        "history": [],
        "next_id": 1,
        "config": {"max_active": 2, "stale_days": 14},
    }


@pytest.fixture
def sample_state():
    """Return a sample state with some tasks."""
    return {
        "tasks": {
            "1": {"id": 1, "title": "Design API", "active": True, "created_at": "2025-01-12T09:00:00"},
            "2": {"id": 2, "title": "Write tests", "active": False, "created_at": "2025-01-12T10:00:00"},
            "3": {"id": 3, "title": "Update docs", "active": False, "created_at": "2025-01-12T11:00:00"},
        },
        "edges": [{"from": 1, "to": 2}],
        "blocked": [{"id": 4, "title": "Wait for review", "blocker": "Alice", "created_at": "2025-01-12T12:00:00"}],
        "history": [
            {"id": 5, "title": "Set up repo", "completed_at": "2025-01-13T10:30:00", "created_at": "2025-01-11T08:00:00"}
        ],
        "next_id": 6,
        "config": {"max_active": 2, "stale_days": 14},
    }


@pytest.fixture
def state_file(temp_state_dir, empty_state):
    """Create a state file with empty state."""
    state_path = temp_state_dir / "state.json"
    state_path.write_text(json.dumps(empty_state))
    return state_path


@pytest.fixture
def sample_state_file(temp_state_dir, sample_state):
    """Create a state file with sample data."""
    state_path = temp_state_dir / "state.json"
    state_path.write_text(json.dumps(sample_state))
    return state_path


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """Fixture that isolates storage to a temp directory."""
    state_dir = tmp_path / ".wip"
    state_file = state_dir / "state.json"
    backup_dir = state_dir / "backups"

    import wip.storage as storage
    monkeypatch.setattr(storage, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(storage, "DEFAULT_STATE_FILE", state_file)
    monkeypatch.setattr(storage, "BACKUP_DIR", backup_dir)

    return {"state_dir": state_dir, "state_file": state_file, "backup_dir": backup_dir}


@pytest.fixture
def isolated_storage_with_sample(tmp_path, monkeypatch, sample_state):
    """Fixture that isolates storage and pre-populates with sample state."""
    state_dir = tmp_path / ".wip"
    state_file = state_dir / "state.json"
    backup_dir = state_dir / "backups"

    state_dir.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(sample_state))

    import wip.storage as storage
    monkeypatch.setattr(storage, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(storage, "DEFAULT_STATE_FILE", state_file)
    monkeypatch.setattr(storage, "BACKUP_DIR", backup_dir)

    return {"state_dir": state_dir, "state_file": state_file, "backup_dir": backup_dir}


@pytest.fixture
def isolated_storage_with_share(tmp_path, monkeypatch, sample_state):
    """Fixture that isolates storage with sharing enabled."""
    state_dir = tmp_path / ".wip"
    state_file = state_dir / "state.json"
    backup_dir = state_dir / "backups"

    # Add share config to sample state
    sample_state["config"]["share"] = {
        "enabled": True,
        "gist_id": "test123",
        "gist_url": "https://gist.github.com/user/test123",
    }

    state_dir.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(sample_state))

    import wip.storage as storage

    monkeypatch.setattr(storage, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(storage, "DEFAULT_STATE_FILE", state_file)
    monkeypatch.setattr(storage, "BACKUP_DIR", backup_dir)
    # Disable auto-publish during tests
    monkeypatch.setattr(storage, "_auto_publish_enabled", False)

    return {"state_dir": state_dir, "state_file": state_file, "backup_dir": backup_dir}
