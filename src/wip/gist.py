"""GitHub Gist integration for sharing WIP state."""

import subprocess
from dataclasses import dataclass


@dataclass
class GistResult:
    """Result of a gist operation."""

    success: bool
    gist_id: str | None = None
    gist_url: str | None = None
    error: str | None = None


def check_gh_auth() -> tuple[bool, str | None]:
    """Check if gh CLI is authenticated.

    Returns (is_authenticated, error_message).
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0, None
    except FileNotFoundError:
        return False, "gh CLI not installed. Install from https://cli.github.com/"
    except subprocess.TimeoutExpired:
        return False, "gh auth check timed out"


def create_gist(filename: str, content: str, description: str = "") -> GistResult:
    """Create a new secret gist.

    Args:
        filename: Name of the file in the gist (e.g., "wip.md")
        content: File content
        description: Gist description

    Returns:
        GistResult with success status and gist URL/ID
    """
    try:
        import json as json_module

        # Use GitHub API directly for consistent behavior
        payload = {
            "description": description,
            "public": False,
            "files": {filename: {"content": content}},
        }

        result = subprocess.run(
            ["gh", "api", "--method", "POST", "/gists", "--input", "-"],
            input=json_module.dumps(payload),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return GistResult(
                success=False, error=result.stderr.strip() or "Failed to create gist"
            )

        # Parse response to get gist ID and URL
        response = json_module.loads(result.stdout)
        gist_id = response.get("id")
        gist_url = response.get("html_url")

        return GistResult(success=True, gist_id=gist_id, gist_url=gist_url)

    except FileNotFoundError:
        return GistResult(success=False, error="gh CLI not installed")
    except subprocess.TimeoutExpired:
        return GistResult(success=False, error="Gist creation timed out")
    except Exception as e:
        return GistResult(success=False, error=str(e))


def update_gist(gist_id: str, filename: str, content: str) -> GistResult:
    """Update an existing gist with new content.

    Args:
        gist_id: The gist ID to update
        filename: Name of the file to update
        content: New file content

    Returns:
        GistResult with success status
    """
    try:
        import json as json_module

        # Use GitHub API directly - faster and more reliable than gh gist edit
        payload = {"files": {filename: {"content": content}}}

        result = subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "PATCH",
                f"/gists/{gist_id}",
                "--input",
                "-",
            ],
            input=json_module.dumps(payload),
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode != 0:
            return GistResult(
                success=False,
                gist_id=gist_id,
                error=result.stderr.strip() or "Failed to update gist",
            )

        return GistResult(success=True, gist_id=gist_id)

    except FileNotFoundError:
        return GistResult(success=False, error="gh CLI not installed")
    except subprocess.TimeoutExpired:
        return GistResult(success=False, error="Gist update timed out")
    except Exception as e:
        return GistResult(success=False, error=str(e))


def remove_gist_file(gist_id: str, filename: str) -> GistResult:
    """Remove a file from a gist.

    Args:
        gist_id: The gist ID
        filename: Name of the file to remove

    Returns:
        GistResult with success status
    """
    try:
        import json as json_module

        # Use GitHub API - set file content to null to delete it
        payload = {"files": {filename: None}}

        subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "PATCH",
                f"/gists/{gist_id}",
                "--input",
                "-",
            ],
            input=json_module.dumps(payload),
            capture_output=True,
            text=True,
            timeout=15,
        )

        # Ignore errors - file might not exist
        return GistResult(success=True, gist_id=gist_id)

    except Exception:
        return GistResult(success=True, gist_id=gist_id)


def delete_gist(gist_id: str) -> GistResult:
    """Delete a gist.

    Args:
        gist_id: The gist ID to delete

    Returns:
        GistResult with success status
    """
    try:
        result = subprocess.run(
            ["gh", "gist", "delete", gist_id, "--yes"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return GistResult(
                success=False, error=result.stderr.strip() or "Failed to delete gist"
            )

        return GistResult(success=True)

    except FileNotFoundError:
        return GistResult(success=False, error="gh CLI not installed")
    except subprocess.TimeoutExpired:
        return GistResult(success=False, error="Gist deletion timed out")
    except Exception as e:
        return GistResult(success=False, error=str(e))
