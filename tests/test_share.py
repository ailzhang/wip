"""Tests for share command."""

from unittest.mock import patch

from click.testing import CliRunner

from wip.cli import main
from wip.gist import GistResult


class TestShareCommand:
    """Tests for wip share command."""

    def test_share_status_disabled(self, isolated_storage):
        """Test share --status when disabled."""
        runner = CliRunner()
        result = runner.invoke(main, ["share", "--status"])

        assert result.exit_code == 0
        assert "disabled" in result.output

    def test_share_status_enabled(self, isolated_storage_with_share):
        """Test share --status when enabled."""
        runner = CliRunner()
        result = runner.invoke(main, ["share", "--status"])

        assert result.exit_code == 0
        assert "enabled" in result.output
        assert "https://gist.github.com" in result.output

    def test_share_no_auth(self, isolated_storage):
        """Test share fails gracefully when gh not authenticated."""
        runner = CliRunner()

        with patch("wip.gist.check_gh_auth") as mock:
            mock.return_value = (False, "gh CLI not installed")
            result = runner.invoke(main, ["share"])

        assert "gh CLI not installed" in result.output
        assert "gh auth login" in result.output

    def test_share_creates_gist(self, isolated_storage):
        """Test share creates a new gist."""
        runner = CliRunner()

        with (
            patch("wip.gist.check_gh_auth") as mock_auth,
            patch("wip.gist.create_gist") as mock_create,
        ):
            mock_auth.return_value = (True, None)
            mock_create.return_value = GistResult(
                success=True,
                gist_id="abc123",
                gist_url="https://gist.github.com/user/abc123",
            )

            result = runner.invoke(main, ["share"])

        assert result.exit_code == 0
        assert "Sharing enabled" in result.output
        assert "https://gist.github.com" in result.output

    def test_share_already_enabled(self, isolated_storage_with_share):
        """Test share when already enabled shows URL."""
        runner = CliRunner()

        with patch("wip.gist.check_gh_auth") as mock_auth:
            mock_auth.return_value = (True, None)
            result = runner.invoke(main, ["share"])

        assert "already enabled" in result.output
        assert "--refresh" in result.output

    def test_share_disable(self, isolated_storage_with_share):
        """Test share --disable removes sharing."""
        runner = CliRunner()

        with patch("wip.gist.delete_gist") as mock_delete:
            mock_delete.return_value = GistResult(success=True)
            result = runner.invoke(main, ["share", "--disable"])

        assert result.exit_code == 0
        assert "disabled" in result.output

    def test_share_disable_when_not_enabled(self, isolated_storage):
        """Test share --disable when already disabled."""
        runner = CliRunner()
        result = runner.invoke(main, ["share", "--disable"])

        assert "already disabled" in result.output

    def test_share_refresh(self, isolated_storage_with_share):
        """Test share --refresh updates gist."""
        runner = CliRunner()

        with patch("wip.gist.update_gist") as mock_update:
            mock_update.return_value = GistResult(success=True, gist_id="test123")
            result = runner.invoke(main, ["share", "--refresh"])

        assert result.exit_code == 0
        assert "Updated" in result.output

    def test_share_refresh_not_enabled(self, isolated_storage):
        """Test share --refresh when not enabled."""
        runner = CliRunner()
        result = runner.invoke(main, ["share", "--refresh"])

        assert "not enabled" in result.output
