"""Utility functions for platform-service-framework CLI."""

import json
from importlib.metadata import distribution
from pathlib import Path

from git import Repo

# Constants
_FILE_URL_PREFIX = "file://"
_GIT_URL_PREFIX = "git+"


def _read_direct_url_metadata() -> dict:
    """Read direct_url.json from package installation metadata.

    Returns:
        Dict containing URL and VCS info

    Raises:
        RuntimeError: If metadata cannot be found or read
    """
    try:
        dist = distribution("platform-service-framework")
        if not dist._path:  # type: ignore
            raise RuntimeError(
                "Cannot detect template source: package metadata not found.\n"
                "Please install the framework using pip, uv, or uvx."
            )

        direct_url_file = dist._path / "direct_url.json"  # type: ignore
        if not direct_url_file.exists():
            raise RuntimeError(
                "Cannot detect template source: direct_url.json not found.\n"
                "This can happen when installing from PyPI.\n"
                "Please install from git URL or local source, e.g.:\n"
                "  uvx git+https://github.com/ansible/platform-service-framework init\n"
                "Or specify source manually in your copier commands."
            )

        return json.loads(direct_url_file.read_text())
    except RuntimeError:
        raise
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(
            f"Cannot detect template source: Failed to read direct_url.json: {e}"
        )


def _get_local_repo_ref(repo_path: Path) -> str:
    """Get VCS ref (branch or commit SHA) from local git repository.

    Args:
        repo_path: Path to git repository root

    Returns:
        Branch name or commit SHA

    Raises:
        RuntimeError: If repo is dirty or cannot be accessed
    """
    try:
        local_repo = Repo(repo_path)

        # Check for uncommitted changes
        if local_repo.is_dirty(untracked_files=True):
            raise RuntimeError(
                f"Local template repository at {repo_path} has uncommitted changes.\n"
                f"Copier requires a clean repository state.\n"
                f"Please commit or stash your changes in the template repo before using it."
            )

        # Check for detached HEAD
        if local_repo.head.is_detached:
            # Use the commit SHA when in detached HEAD state
            return local_repo.head.commit.hexsha

        # Get current branch name
        return local_repo.active_branch.name

    except RuntimeError:
        # Re-raise validation errors (dirty repo, etc)
        raise
    except Exception as e:
        # If .git exists but we can't access it, fail loudly
        raise RuntimeError(
            f"Found .git directory at {repo_path} but failed to access it.\n"
            f"Error: {e}\n"
            f"Please check the repository is not corrupted."
        )


def _parse_local_source(url: str) -> tuple[str, str]:
    """Parse local file:// URL and return repository path and ref.

    Args:
        url: URL starting with file://

    Returns:
        Tuple of (local_path, vcs_ref)

    Raises:
        RuntimeError: If local path is not a git repository
    """
    local_path = Path(url[len(_FILE_URL_PREFIX) :])

    # Check if it's a git repository
    if not (local_path / ".git").exists():
        raise RuntimeError(
            f"Local template source at {local_path} is not a git repository.\n"
            f"The framework requires templates to be in a git repository.\n"
            f"Please initialize git in this directory: git init && git add . && git commit -m 'Initial commit'"
        )

    # Get ref from git repository
    ref = _get_local_repo_ref(local_path)
    return (str(local_path), ref)


def _parse_git_url(url: str, vcs_info: dict) -> tuple[str, str | None]:
    """Parse git URL and return normalized URL with ref.

    Args:
        url: Git URL (may have git+ prefix)
        vcs_info: VCS metadata from direct_url.json

    Returns:
        Tuple of (normalized_url, vcs_ref)
    """
    # Handle git+ prefix
    if url.startswith(_GIT_URL_PREFIX):
        url = url[len(_GIT_URL_PREFIX) :]

    # Add .git extension if not present (copier prefers this)
    if not url.endswith(".git"):
        url = f"{url}.git"

    # Get ref if available (branch, tag, or commit sha)
    ref = vcs_info.get("requested_revision") or vcs_info.get("commit_id")

    return (url, ref)


def get_repo() -> tuple[str, str | None]:
    """Get the repository source path and VCS ref from installation source.

    When the CLI is installed from a git URL (e.g., via uvx git+https://...@branch),
    it will automatically use the same source for templates.

    When running from local source (e.g., uv run from development directory),
    it will use the local repository path.

    Returns:
        Tuple of (src_path, vcs_ref) where:
        - src_path: Local path or git URL
        - vcs_ref: Branch/tag/commit (None for local paths or when not specified)

    Raises:
        RuntimeError: If template source cannot be detected
    """
    # Detect source from installation metadata
    direct_url_data = _read_direct_url_metadata()

    url = direct_url_data.get("url")
    if not url:
        raise RuntimeError(
            "Cannot detect template source: URL not found in installation metadata.\n"
            "Please reinstall the framework from a git URL or local source."
        )

    # Handle local/editable installs (file:// URLs)
    if url.startswith(_FILE_URL_PREFIX):
        return _parse_local_source(url)

    # Handle git URLs
    vcs_info = direct_url_data.get("vcs_info", {})
    return _parse_git_url(url, vcs_info)
