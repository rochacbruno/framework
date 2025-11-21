"""Tests for the validate command."""

from pathlib import Path

import pytest

from platform_service_framework.cli import app


def test_validate_empty_project(isolated_env, capsys):
    """Test validate command with default destination (current directory)."""
    tmp_path, _ = isolated_env

    # Run validate command - expect SystemExit(1)
    with pytest.raises(SystemExit) as exc_info:
        app(["validate"])

    assert exc_info.value.code == 1

    # Check output - git check happens first, so expect git error
    captured = capsys.readouterr()
    assert "Validating your app" in captured.out
    assert "Platform service framework is only supported in git-tracked repositories" in captured.out

def test_validate_on_initialized_project(isolated_env, capsys):
    """Test validate on an initialized project."""
    tmp_path, _ = isolated_env

    # First initialize a project - expect SystemExit(0)
    with pytest.raises(SystemExit) as exc_info:
        app(["init"])
    assert exc_info.value.code == 0

    # Clear the captured output
    capsys.readouterr()

    # Run validate - expect SystemExit(0)
    with pytest.raises(SystemExit) as exc_info:
        app(["validate"])

    assert exc_info.value.code == 0

    # Check output
    captured = capsys.readouterr()
    assert "Validating your app" in captured.out


def test_validate_protected_file_modification(isolated_env, capsys):
    """Test validate on an initialized project."""
    tmp_path, _ = isolated_env

    # First initialize a project - expect SystemExit(0)
    with pytest.raises(SystemExit) as exc_info:
        app(["init"])
    assert exc_info.value.code == 0

    # Clear the captured output
    capsys.readouterr()
    # Modify manage.py and project_name/settings.py, configured as protected under src/config/protected_files.yaml
    files_to_modify = [
        tmp_path / "manage.py",
        tmp_path / tmp_path.name / "settings.py"
    ]
    for file in files_to_modify:
        file.write_text("test")
    # Run validate - expect SystemExit(1)
    with pytest.raises(SystemExit) as exc_info:
        app(["validate"])
    assert exc_info.value.code == 1

    # Check output
    captured = capsys.readouterr()
    assert "Validating your app" in captured.out
    assert "The following files should not be modified" in captured.out
    assert "manage.py" in captured.out
    assert f"{tmp_path.name}/settings.py" in captured.out
    assert "Please undo these changes and run the command again" in captured.out


def test_validate_allowed_file_modification(isolated_env, capsys):
    """Test validate on an initialized project."""
    tmp_path, _ = isolated_env

    # First initialize a project - expect SystemExit(0)
    with pytest.raises(SystemExit) as exc_info:
        app(["init"])
    assert exc_info.value.code == 0

    # Clear the captured output
    capsys.readouterr()
    # Modify .github/dependabot.yml and README.md, shouldn't trigger any infractions
    files_to_modify = [
        tmp_path / ".github" / "dependabot.yml",
        tmp_path / "README.md"
    ]
    for file in files_to_modify:
        file.write_text("test")
    # Run validate - expect SystemExit(0)
    with pytest.raises(SystemExit) as exc_info:
        app(["validate"])
    assert exc_info.value.code == 0

    # Check output
    captured = capsys.readouterr()
    assert "Validating your app" in captured.out
    assert "No framework infractions found, your project is ready to be updated!" in captured.out

def test_validate_protected_file_deletion(isolated_env, capsys):
    """Test validate on an initialized project."""
    tmp_path, _ = isolated_env

    # First initialize a project - expect SystemExit(0)
    with pytest.raises(SystemExit) as exc_info:
        app(["init"])
    assert exc_info.value.code == 0

    # Clear the captured output
    capsys.readouterr()
    # Modify manage.py and project_name/settings.py, configured as protected under src/config/protected_files.yaml
    files_to_delete = [
        tmp_path / "manage.py",
        tmp_path / tmp_path.name / "settings.py"
    ]
    for file in files_to_delete:
        file.unlink()
    # Run validate - expect SystemExit(1)
    with pytest.raises(SystemExit) as exc_info:
        app(["validate"])
    assert exc_info.value.code == 1

    # Check output
    captured = capsys.readouterr()
    assert "Validating your app" in captured.out
    assert "The following files should not be modified" in captured.out
    assert "manage.py" in captured.out
    assert f"{tmp_path.name}/settings.py" in captured.out
    assert "Please undo these changes and run the command again" in captured.out

