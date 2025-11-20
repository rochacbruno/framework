"""Pytest configuration and fixtures for CLI tests."""

import os
from pathlib import Path
from typing import Tuple, Any, Generator

import pytest


@pytest.fixture
def isolated_dir(tmp_path, monkeypatch) -> Generator[Path, Any, None]:
    """Create an isolated temporary directory and change to it.

    Args:
        tmp_path: pytest's built-in temporary directory fixture
        monkeypatch: pytest's monkeypatch fixture

    Yields:
        Path: The temporary directory path
    """
    # Change to the temporary directory
    monkeypatch.chdir(tmp_path)
    yield tmp_path


@pytest.fixture
def local_repo_url(monkeypatch) -> str:
    """Override FRAMEWORK_REPO to use local git repository.

    Args:
        monkeypatch: pytest's monkeypatch fixture

    Returns:
        str: The local repository path
    """
    # Get the path to the current repository (3 levels up from tests/)
    repo_path = Path(__file__).parent.parent.absolute()

    # Set the environment variable to point to local repo
    monkeypatch.setenv("FRAMEWORK_REPO", str(repo_path))

    return str(repo_path)


@pytest.fixture
def isolated_env(isolated_dir, local_repo_url) -> Tuple[Path, str]:
    """Combined fixture providing both isolated directory and local repo URL.

    Args:
        isolated_dir: Fixture for isolated temporary directory
        local_repo_url: Fixture for local repository URL

    Returns:
        tuple: (tmp_path, repo_url)
    """
    return isolated_dir, local_repo_url
