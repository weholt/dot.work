"""Fixtures for python build tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dot_python.build.runner import BuildRunner


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root."""
    project = tmp_path / "test_project"
    project.mkdir()
    return project


@pytest.fixture
def mock_runner(project_root: Path) -> BuildRunner:
    """Create a BuildRunner with mocked commands."""
    runner = BuildRunner(
        project_root=project_root,
        verbose=False,
        fix=False,
        source_dirs=["."],
        test_dirs=["tests"],
        coverage_threshold=70,
        use_uv=False,
    )
    return runner


@pytest.fixture
def mock_subprocess(mocker: MagicMock) -> MagicMock:
    """Mock subprocess.run for all build commands."""
    mock = mocker.patch("subprocess.run")
    mock.return_value = MagicMock(
        stdout="",
        stderr="",
        returncode=0,
    )
    return mock
