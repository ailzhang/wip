"""Tests for gist module."""

import json
from unittest.mock import MagicMock, patch

from wip.gist import check_gh_auth, create_gist, delete_gist, update_gist


class TestGhAuth:
    """Tests for gh auth checking."""

    def test_gh_not_installed(self):
        """Test handling when gh is not installed."""
        with patch("subprocess.run") as mock:
            mock.side_effect = FileNotFoundError()
            is_auth, error = check_gh_auth()

        assert is_auth is False
        assert "not installed" in error

    def test_gh_authenticated(self):
        """Test successful auth check."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0)
            is_auth, error = check_gh_auth()

        assert is_auth is True
        assert error is None

    def test_gh_not_authenticated(self):
        """Test failed auth check."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=1)
            is_auth, error = check_gh_auth()

        assert is_auth is False


class TestCreateGist:
    """Tests for gist creation."""

    def test_create_success(self):
        """Test successful gist creation."""
        with patch("subprocess.run") as mock:
            response = {"id": "abc123", "html_url": "https://gist.github.com/user/abc123"}
            mock.return_value = MagicMock(returncode=0, stdout=json.dumps(response))
            result = create_gist("test.md", "# Hello")

        assert result.success is True
        assert result.gist_id == "abc123"
        assert "gist.github.com" in result.gist_url

    def test_create_failure(self):
        """Test failed gist creation."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=1, stderr="Permission denied")
            result = create_gist("test.md", "# Hello")

        assert result.success is False
        assert "Permission denied" in result.error

    def test_create_gh_not_installed(self):
        """Test gist creation when gh not installed."""
        with patch("subprocess.run") as mock:
            mock.side_effect = FileNotFoundError()
            result = create_gist("test.md", "# Hello")

        assert result.success is False
        assert "not installed" in result.error


class TestUpdateGist:
    """Tests for gist updates."""

    def test_update_success(self):
        """Test successful gist update."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0)
            result = update_gist("abc123", "test.html", "<html></html>")

        assert result.success is True
        assert result.gist_id == "abc123"

    def test_update_failure(self):
        """Test failed gist update."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=1, stderr="Not found")
            result = update_gist("abc123", "test.html", "<html></html>")

        assert result.success is False
        assert "Not found" in result.error


class TestDeleteGist:
    """Tests for gist deletion."""

    def test_delete_success(self):
        """Test successful gist deletion."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0)
            result = delete_gist("abc123")

        assert result.success is True

    def test_delete_failure(self):
        """Test failed gist deletion."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=1, stderr="Not found")
            result = delete_gist("abc123")

        assert result.success is False
        assert "Not found" in result.error
