"""
Tests for the BuildRunner class.
"""

from pathlib import Path

import pytest

from builder.runner import BuildRunner


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    # Create a simple Python package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()

    (pkg_dir / "__init__.py").write_text('"""Test package."""\n\n__version__ = "0.1.0"\n')
    (pkg_dir / "module.py").write_text(
        '"""Test module."""\n\ndef add(a: int, b: int) -> int:\n    """Add two numbers."""\n    return a + b\n'
    )

    # Create tests directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_module.py").write_text(
        '"""Test module."""\nfrom mypackage.module import add\n\ndef test_add():\n    """Test add function."""\n    assert add(1, 2) == 3\n'
    )

    # Create pyproject.toml
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "mypackage"\nversion = "0.1.0"\n\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
    )

    return tmp_path


def test_builder_init():
    """Test BuildRunner initialization."""
    builder = BuildRunner()
    assert builder.project_root == Path.cwd()
    assert builder.coverage_threshold == 70
    assert not builder.use_uv
    assert not builder.fix
    assert not builder.verbose


def test_builder_with_custom_settings():
    """Test BuildRunner with custom settings."""
    builder = BuildRunner(
        project_root=Path("/tmp"),
        verbose=True,
        fix=True,
        coverage_threshold=80,
        use_uv=True,
        source_dirs=["src"],
    )
    assert builder.project_root == Path("/tmp")
    assert builder.verbose
    assert builder.fix
    assert builder.coverage_threshold == 80
    assert builder.use_uv
    assert builder.source_dirs == ["src"]


def test_detect_source_dirs(temp_project):
    """Test source directory detection."""
    builder = BuildRunner(project_root=temp_project)
    assert "mypackage" in builder.source_dirs


def test_command_prefix():
    """Test command prefix generation."""
    builder_no_uv = BuildRunner(use_uv=False)
    assert builder_no_uv._get_command_prefix() == []

    builder_with_uv = BuildRunner(use_uv=True)
    assert builder_with_uv._get_command_prefix() == ["uv", "run"]


def test_print_step(capsys):
    """Test step printing."""
    builder = BuildRunner()
    builder.print_step("Test Step")
    captured = capsys.readouterr()
    assert "Test Step" in captured.out
    assert "====" in captured.out


def test_print_result_success(capsys):
    """Test result printing for success."""
    builder = BuildRunner()
    builder.print_result(True, "Test Step")
    captured = capsys.readouterr()
    assert "PASSED" in captured.out
    assert len(builder.failed_steps) == 0


def test_print_result_failure(capsys):
    """Test result printing for failure."""
    builder = BuildRunner()
    builder.print_result(False, "Test Step", error="Something went wrong")
    captured = capsys.readouterr()
    assert "FAILED" in captured.out
    assert "Something went wrong" in captured.out
    assert "Test Step" in builder.failed_steps


def test_clean_artifacts(temp_project):
    """Test artifact cleaning."""
    builder = BuildRunner(project_root=temp_project)

    # Create some artifacts
    (temp_project / ".coverage").write_text("")
    pycache = temp_project / "__pycache__"
    pycache.mkdir()
    (pycache / "test.pyc").write_text("")

    assert (temp_project / ".coverage").exists()
    assert pycache.exists()

    # Clean
    builder.clean_artifacts()

    assert not (temp_project / ".coverage").exists()
    assert not pycache.exists()
