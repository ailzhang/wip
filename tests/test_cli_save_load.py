"""Tests for save and load commands."""

import json

from click.testing import CliRunner

from wip.cli import main


class TestSaveCommand:
    """Tests for wip save command."""

    def test_save_creates_file(self, isolated_storage_with_sample, tmp_path):
        """Test that save creates a JSON file with state."""
        runner = CliRunner()
        output_file = tmp_path / "export.json"

        result = runner.invoke(main, ["save", str(output_file)])

        assert result.exit_code == 0
        assert "Saved" in result.output
        assert output_file.exists()

        # Verify file contains valid JSON with expected structure
        data = json.loads(output_file.read_text())
        assert "tasks" in data
        assert "edges" in data
        assert "blocked" in data
        assert "history" in data
        assert "next_id" in data

    def test_save_includes_all_tasks(self, isolated_storage_with_sample, tmp_path):
        """Test that save includes tasks, blocked, and history."""
        runner = CliRunner()
        output_file = tmp_path / "export.json"

        result = runner.invoke(main, ["save", str(output_file)])

        assert result.exit_code == 0

        data = json.loads(output_file.read_text())
        # Sample state has 3 tasks, 1 blocked, 1 history
        assert len(data["tasks"]) == 3
        assert len(data["blocked"]) == 1
        assert len(data["history"]) == 1
        assert len(data["edges"]) == 1

    def test_save_empty_state(self, isolated_storage, tmp_path):
        """Test saving empty state."""
        runner = CliRunner()
        output_file = tmp_path / "export.json"

        result = runner.invoke(main, ["save", str(output_file)])

        assert result.exit_code == 0
        assert "Saved 0 tasks" in result.output


class TestLoadCommand:
    """Tests for wip load command."""

    def test_load_replaces_state(self, isolated_storage, tmp_path):
        """Test that load replaces current state."""
        runner = CliRunner()

        # Create a file to import
        import_data = {
            "tasks": {
                "1": {"id": 1, "title": "Imported task", "active": True, "created_at": "2025-01-15T10:00:00"}
            },
            "edges": [],
            "blocked": [],
            "history": [],
            "next_id": 2,
            "config": {"max_active": 2, "stale_days": 14},
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = runner.invoke(main, ["load", str(import_file)])

        assert result.exit_code == 0
        assert "Loaded 1 tasks" in result.output

        # Verify state was replaced
        state_file = isolated_storage["state_file"]
        data = json.loads(state_file.read_text())
        assert "1" in data["tasks"]
        assert data["tasks"]["1"]["title"] == "Imported task"

    def test_load_creates_backup(self, isolated_storage_with_sample, tmp_path):
        """Test that load creates backup before replacing."""
        runner = CliRunner()

        import_data = {
            "tasks": {},
            "edges": [],
            "blocked": [],
            "history": [],
            "next_id": 1,
            "config": {"max_active": 2, "stale_days": 14},
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = runner.invoke(main, ["load", str(import_file)])

        assert result.exit_code == 0
        assert "Backup saved to" in result.output

        # Verify backup was created
        backup_dir = isolated_storage_with_sample["backup_dir"]
        assert backup_dir.exists()
        backups = list(backup_dir.glob("state_*.json"))
        assert len(backups) >= 1

    def test_load_merge_renumbers_ids(self, isolated_storage_with_sample, tmp_path):
        """Test that load --merge renumbers imported IDs."""
        runner = CliRunner()

        # Import data with IDs that would conflict
        import_data = {
            "tasks": {
                "1": {"id": 1, "title": "Conflicting ID task", "active": False, "created_at": "2025-01-15T10:00:00"}
            },
            "edges": [],
            "blocked": [],
            "history": [],
            "next_id": 2,
            "config": {"max_active": 2, "stale_days": 14},
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = runner.invoke(main, ["load", str(import_file), "--merge"])

        assert result.exit_code == 0
        assert "Merged 1 tasks" in result.output
        assert "IDs remapped" in result.output

        # Verify original tasks still exist and imported task has new ID
        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())

        # Original task 1 should still exist
        assert "1" in data["tasks"]
        assert data["tasks"]["1"]["title"] == "Design API"

        # Imported task should have new ID (next_id was 6 in sample)
        assert "6" in data["tasks"]
        assert data["tasks"]["6"]["title"] == "Conflicting ID task"

    def test_load_merge_preserves_edges(self, isolated_storage_with_sample, tmp_path):
        """Test that load --merge remaps edge references."""
        runner = CliRunner()

        import_data = {
            "tasks": {
                "1": {"id": 1, "title": "Parent", "active": False, "created_at": "2025-01-15T10:00:00"},
                "2": {"id": 2, "title": "Child", "active": False, "created_at": "2025-01-15T10:00:00"},
            },
            "edges": [{"from": 1, "to": 2}],
            "blocked": [],
            "history": [],
            "next_id": 3,
            "config": {"max_active": 2, "stale_days": 14},
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = runner.invoke(main, ["load", str(import_file), "--merge"])

        assert result.exit_code == 0

        # Verify edges were remapped
        state_file = isolated_storage_with_sample["state_file"]
        data = json.loads(state_file.read_text())

        # Should have original edge (1->2) plus remapped edge (6->7)
        edges = data["edges"]
        assert len(edges) >= 2

        # Find the remapped edge (IDs 6 and 7)
        remapped_edge = next((e for e in edges if e["from"] == 6 and e["to"] == 7), None)
        assert remapped_edge is not None

    def test_load_invalid_json(self, isolated_storage, tmp_path):
        """Test error on invalid JSON file."""
        runner = CliRunner()

        import_file = tmp_path / "invalid.json"
        import_file.write_text("not valid json {")

        result = runner.invoke(main, ["load", str(import_file)])

        assert "Error: Invalid JSON" in result.output

    def test_load_nonexistent_file(self, isolated_storage):
        """Test error on nonexistent file."""
        runner = CliRunner()

        result = runner.invoke(main, ["load", "/nonexistent/file.json"])

        assert result.exit_code != 0
