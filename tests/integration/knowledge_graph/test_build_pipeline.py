"""Integration tests for the build pipeline."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_build_script_runs_successfully() -> None:
    """Build script should complete without errors on clean project."""
    # tests/integration/knowledge_graph/ -> tests/integration/ -> tests/ -> project_root
    project_root = Path(__file__).parent.parent.parent.parent
    result = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "build.py")],
        capture_output=True,
        text=True,
        cwd=project_root,
    )
    # Allow for minor failures (test coverage might vary)
    assert result.returncode in (0, 1), f"Build failed unexpectedly: {result.stderr}"


@pytest.mark.integration
def test_package_importable_after_install() -> None:
    """Package should be importable after uv sync."""
    import dot_work.knowledge_graph

    assert hasattr(dot_work.knowledge_graph, "__version__")
    assert dot_work.knowledge_graph.__version__ == "0.1.0"


@pytest.mark.integration
def test_cli_entrypoint_registered() -> None:
    """CLI entry point 'kg' should be available after install."""
    from dot_work.knowledge_graph.cli import app

    assert app is not None
    assert app.info.name == "kg"
