"""Tests for source detection functionality."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from platform_service_framework.utils import get_repo


def _setup_direct_url(tmp_path, direct_url_data):
    """Helper to set up direct_url.json in a mock dist-info directory."""
    mock_path = tmp_path / "dist-info"
    mock_path.mkdir()
    direct_url_file = mock_path / "direct_url.json"
    direct_url_file.write_text(json.dumps(direct_url_data))
    return mock_path


def test_get_repo_no_metadata():
    """Test that RuntimeError is raised when package metadata not found."""
    with patch("platform_service_framework.utils.distribution") as mock_dist:
        # Simulate no package metadata
        mock_dist.return_value._path = None
        with pytest.raises(RuntimeError, match="Cannot detect template source"):
            get_repo()


def test_get_repo_from_git_with_branch(tmp_path):
    """Test source detection from git URL with branch."""
    direct_url_data = {
        "url": "git+https://github.com/TheRealHaoLiu/platform-service-framework",
        "vcs_info": {
            "vcs": "git",
            "requested_revision": "devel",
            "commit_id": "abc123def456",
        },
    }

    mock_path = _setup_direct_url(tmp_path, direct_url_data)

    with patch("platform_service_framework.utils.distribution") as mock_dist:
        mock_dist.return_value._path = mock_path
        src_path, ref = get_repo()
        assert src_path == "https://github.com/TheRealHaoLiu/platform-service-framework.git"
        assert ref == "devel"


def test_get_repo_from_git_with_tag(tmp_path):
    """Test source detection from git URL with tag."""
    direct_url_data = {
        "url": "git+https://github.com/ansible/platform-service-framework",
        "vcs_info": {
            "vcs": "git",
            "requested_revision": "v1.2.3",
            "commit_id": "abc123def456",
        },
    }

    mock_path = _setup_direct_url(tmp_path, direct_url_data)

    with patch("platform_service_framework.utils.distribution") as mock_dist:
        mock_dist.return_value._path = mock_path
        src_path, ref = get_repo()
        assert src_path == "https://github.com/ansible/platform-service-framework.git"
        assert ref == "v1.2.3"


def test_get_repo_from_git_with_sha(tmp_path):
    """Test source detection from git URL with commit SHA only."""
    direct_url_data = {
        "url": "git+https://github.com/ansible/platform-service-framework",
        "vcs_info": {
            "vcs": "git",
            "commit_id": "abc123def456",
        },
    }

    mock_path = _setup_direct_url(tmp_path, direct_url_data)

    with patch("platform_service_framework.utils.distribution") as mock_dist:
        mock_dist.return_value._path = mock_path
        src_path, ref = get_repo()
        assert src_path == "https://github.com/ansible/platform-service-framework.git"
        assert ref == "abc123def456"


def test_get_repo_from_git_without_prefix(tmp_path):
    """Test source detection from git URL without git+ prefix."""
    direct_url_data = {
        "url": "https://github.com/ansible/platform-service-framework",
        "vcs_info": {
            "vcs": "git",
            "requested_revision": "stable-2.6",
        },
    }

    mock_path = _setup_direct_url(tmp_path, direct_url_data)

    with patch("platform_service_framework.utils.distribution") as mock_dist:
        mock_dist.return_value._path = mock_path
        src_path, ref = get_repo()
        assert src_path == "https://github.com/ansible/platform-service-framework.git"
        assert ref == "stable-2.6"


def test_get_repo_with_existing_git_extension(tmp_path):
    """Test that .git extension is not added twice."""
    direct_url_data = {
        "url": "https://github.com/ansible/platform-service-framework.git",
        "vcs_info": {
            "vcs": "git",
            "requested_revision": "main",
        },
    }

    mock_path = _setup_direct_url(tmp_path, direct_url_data)

    with patch("platform_service_framework.utils.distribution") as mock_dist:
        mock_dist.return_value._path = mock_path
        src_path, ref = get_repo()
        assert src_path == "https://github.com/ansible/platform-service-framework.git"
        assert ref == "main"


def test_get_repo_no_direct_url_file(tmp_path):
    """Test that RuntimeError is raised when direct_url.json not found."""
    # Create dist-info directory without direct_url.json
    mock_path = tmp_path / "dist-info"
    mock_path.mkdir()

    with patch("platform_service_framework.utils.distribution") as mock_dist:
        mock_dist.return_value._path = mock_path
        with pytest.raises(RuntimeError, match="direct_url.json not found"):
            get_repo()


def test_get_repo_no_url_in_metadata(tmp_path):
    """Test that RuntimeError is raised when URL not in metadata."""
    direct_url_data = {
        "vcs_info": {
            "vcs": "git",
        }
        # Missing 'url' key
    }

    mock_path = _setup_direct_url(tmp_path, direct_url_data)

    with patch("platform_service_framework.utils.distribution") as mock_dist:
        mock_dist.return_value._path = mock_path
        with pytest.raises(RuntimeError, match="URL not found in installation metadata"):
            get_repo()


def test_get_repo_from_local_editable_install(tmp_path):
    """Test source detection from local editable install."""
    # Create a real local repository with git init
    from git import Repo

    local_repo = tmp_path / "my-framework"
    local_repo.mkdir()
    repo = Repo.init(str(local_repo))

    # Create an initial commit so the repo is valid
    test_file = local_repo / "README.md"
    test_file.write_text("Test repo")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    direct_url_data = {
        "url": f"file://{local_repo}",
        "dir_info": {"editable": True},
    }

    mock_path = _setup_direct_url(tmp_path, direct_url_data)

    with patch("platform_service_framework.utils.distribution") as mock_dist:
        mock_dist.return_value._path = mock_path
        src_path, ref = get_repo()
        assert src_path == str(local_repo)
        # Should return branch name (default is usually 'master' or 'main')
        assert ref in ("master", "main")


def test_get_repo_from_local_without_git(tmp_path):
    """Test that RuntimeError is raised for local path without .git directory."""
    # Create a local directory without .git
    local_dir = tmp_path / "my-framework"
    local_dir.mkdir()

    direct_url_data = {
        "url": f"file://{local_dir}",
        "dir_info": {"editable": True},
    }

    mock_path = _setup_direct_url(tmp_path, direct_url_data)

    with patch("platform_service_framework.utils.distribution") as mock_dist:
        mock_dist.return_value._path = mock_path
        with pytest.raises(RuntimeError, match="not a git repository"):
            get_repo()
