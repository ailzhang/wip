"""JSON persistence for WIP state."""

import atexit
import json
import sys
import threading
from pathlib import Path

from .model import State

DEFAULT_STATE_DIR = Path.home() / ".wip"
DEFAULT_STATE_FILE = DEFAULT_STATE_DIR / "state.json"
BACKUP_DIR = DEFAULT_STATE_DIR / "backups"

# Can be disabled for testing
_auto_publish_enabled = True

# Track publish thread for cleanup
_publish_thread: threading.Thread | None = None


def _wait_for_publish() -> None:
    """Wait for any pending publish to complete before exit."""
    global _publish_thread
    if _publish_thread is not None and _publish_thread.is_alive():
        _publish_thread.join(timeout=20)


atexit.register(_wait_for_publish)


def set_auto_publish(enabled: bool) -> None:
    """Enable or disable auto-publish on save. Useful for testing."""
    global _auto_publish_enabled
    _auto_publish_enabled = enabled


def _get_state_file(state_file: Path | None = None) -> Path:
    """Get the state file path, using module-level default if not specified."""
    return state_file if state_file is not None else DEFAULT_STATE_FILE


def _get_backup_dir() -> Path:
    """Get the backup directory path."""
    return BACKUP_DIR


def load_state(state_file: Path | None = None) -> State:
    """Load state from JSON file.

    If the file doesn't exist, returns a new empty State.
    """
    state_file = _get_state_file(state_file)
    if not state_file.exists():
        return State()

    with open(state_file) as f:
        data = json.load(f)

    return State.from_dict(data)


def save_state(
    state: State, state_file: Path | None = None, *, skip_publish: bool = False
) -> None:
    """Save state to JSON file.

    Creates the parent directory if it doesn't exist.
    Also auto-publishes to gist if sharing is enabled.

    Args:
        state: The state to save
        state_file: Optional path to state file
        skip_publish: If True, skip auto-publish (useful after gist creation)
    """
    state_file = _get_state_file(state_file)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with open(state_file, "w") as f:
        json.dump(state.to_dict(), f, indent=2)

    # Auto-publish if sharing is enabled
    if (
        _auto_publish_enabled
        and not skip_publish
        and state.config.share.enabled
        and state.config.share.gist_id
    ):
        _auto_publish(state)


def _auto_publish(state: State) -> None:
    """Publish state to gist in background. Non-blocking."""
    global _publish_thread

    def publish():
        try:
            from .gist import update_gist
            from .render_md import render_state_md

            md = render_state_md(state)
            result = update_gist(state.config.share.gist_id, "wip.md", md)

            if not result.success:
                print(f"[share] Update failed: {result.error}", file=sys.stderr)
        except Exception as e:
            print(f"[share] Update failed: {e}", file=sys.stderr)

    _publish_thread = threading.Thread(target=publish)
    _publish_thread.start()


def backup_state(state_file: Path | None = None) -> Path | None:
    """Create a backup of the current state file.

    Returns the path to the backup file, or None if no state file exists.
    """
    state_file = _get_state_file(state_file)
    if not state_file.exists():
        return None

    from datetime import datetime

    backup_dir = _get_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"state_{timestamp}.json"

    # Copy current state to backup
    backup_file.write_text(state_file.read_text())

    return backup_file
