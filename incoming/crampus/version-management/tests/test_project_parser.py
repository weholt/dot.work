"""Tests for project_parser module."""

import tempfile
from pathlib import Path

from version_management.project_parser import ProjectInfo, PyProjectParser


def test_read_project_info_success():
    """Test reading project info from pyproject.toml."""
    parser = PyProjectParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        pyproject = project_root / "pyproject.toml"
        
        # Create test pyproject.toml
        pyproject.write_text("""
[project]
name = "test-project"
version = "1.0.0"
description = "Test project description"
""")
        
        info = parser.read_project_info(project_root)
        
        assert info.name == "test-project"
        assert info.version == "1.0.0"
        assert info.description == "Test project description"


def test_read_project_info_missing_file():
    """Test fallback when pyproject.toml doesn't exist."""
    parser = PyProjectParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "my-project"
        project_root.mkdir()
        
        info = parser.read_project_info(project_root)
        
        # Should fallback to directory name
        assert info.name == "my-project"
        assert info.version is None
        assert info.description is None


def test_read_project_info_partial_data():
    """Test reading project info with only name."""
    parser = PyProjectParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        pyproject = project_root / "pyproject.toml"
        
        # Create minimal pyproject.toml
        pyproject.write_text("""
[project]
name = "minimal-project"
""")
        
        info = parser.read_project_info(project_root)
        
        assert info.name == "minimal-project"
        assert info.version is None
        assert info.description is None


def test_read_project_info_malformed_toml():
    """Test fallback when pyproject.toml is malformed."""
    parser = PyProjectParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "bad-project"
        project_root.mkdir()
        pyproject = project_root / "pyproject.toml"
        
        # Create malformed TOML
        pyproject.write_text("this is not valid toml {{{")
        
        info = parser.read_project_info(project_root)
        
        # Should fallback to directory name
        assert info.name == "bad-project"
        assert info.version is None
        assert info.description is None


def test_project_info_repr():
    """Test ProjectInfo string representation."""
    info = ProjectInfo(
        name="test-project",
        version="1.0.0",
        description="A very long description that should be truncated in repr"
    )
    
    repr_str = repr(info)
    assert "name='test-project'" in repr_str
    assert "version='1.0.0'" in repr_str
    assert "..." in repr_str  # Description should be truncated
