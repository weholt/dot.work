"""Tests for version project_parser module."""

from pathlib import Path

from dot_work.version.project_parser import ProjectInfo, PyProjectParser


def test_read_project_info_success(project_with_pyproject: Path):
    """Test reading project info from pyproject.toml."""
    parser = PyProjectParser()

    info = parser.read_project_info(project_with_pyproject)

    assert info.name == "test-project"
    assert info.version == "0.1.0"
    assert info.description == "A test project for version management"


def test_read_project_info_missing_file(temp_dir: Path):
    """Test fallback when pyproject.toml doesn't exist."""
    parser = PyProjectParser()

    # Create a project directory without pyproject.toml
    project_dir = temp_dir / "my-project"
    project_dir.mkdir()

    info = parser.read_project_info(project_dir)

    # Should fallback to directory name
    assert info.name == "my-project"
    assert info.version is None
    assert info.description is None


def test_read_project_info_partial_data(temp_dir: Path):
    """Test reading project info with only name."""
    parser = PyProjectParser()

    # Create pyproject.toml with only name
    pyproject = temp_dir / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "minimal-project"
""")

    info = parser.read_project_info(temp_dir)

    assert info.name == "minimal-project"
    assert info.version is None
    assert info.description is None


def test_read_project_info_invalid_toml(temp_dir: Path):
    """Test handling of invalid pyproject.toml."""
    parser = PyProjectParser()

    # Create invalid pyproject.toml
    pyproject = temp_dir / "pyproject.toml"
    pyproject.write_text("invalid toml content [")

    info = parser.read_project_info(temp_dir)

    # Should fallback to directory name
    assert info.name == temp_dir.name
    assert info.version is None
    assert info.description is None


def test_read_project_info_with_build_system(temp_dir: Path):
    """Test reading project info with build system but no [project] section."""
    parser = PyProjectParser()

    # Create pyproject.toml with only build system
    pyproject = temp_dir / "pyproject.toml"
    pyproject.write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")

    info = parser.read_project_info(temp_dir)

    # Should fallback to directory name
    assert info.name == temp_dir.name
    assert info.version is None
    assert info.description is None


def test_read_project_info_name_from_directory(temp_dir: Path):
    """Test that directory name is used as fallback for project name."""
    parser = PyProjectParser()

    # Create a nested directory structure
    nested_dir = temp_dir / "nested-project"
    nested_dir.mkdir()

    info = parser.read_project_info(nested_dir)

    assert info.name == "nested-project"