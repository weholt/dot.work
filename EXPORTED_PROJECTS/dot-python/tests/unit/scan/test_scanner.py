"""
Tests for the ASTScanner class.
"""

from pathlib import Path

from dot_python.scan.scanner import ASTScanner


def test_scan_file_extracts_functions(sample_python_file: Path) -> None:
    """Test that scanning extracts functions from a file.

    Args:
        sample_python_file: Fixture providing sample Python file.
    """
    scanner = ASTScanner(sample_python_file.parent)
    index = scanner.scan()

    assert len(index.files) == 1
    file_entity = list(index.files.values())[0]

    function_names = [f.name for f in file_entity.functions]
    assert "simple_function" in function_names
    assert "async_function" in function_names


def test_scan_file_extracts_classes(sample_python_file: Path) -> None:
    """Test that scanning extracts classes from a file.

    Args:
        sample_python_file: Fixture providing sample Python file.
    """
    scanner = ASTScanner(sample_python_file.parent)
    index = scanner.scan()

    file_entity = list(index.files.values())[0]

    class_names = [c.name for c in file_entity.classes]
    assert "SampleClass" in class_names

    sample_class = file_entity.classes[0]
    assert len(sample_class.methods) == 2
    method_names = [m.name for m in sample_class.methods]
    assert "__init__" in method_names
    assert "compute" in method_names


def test_scan_file_handles_syntax_error(syntax_error_file: Path) -> None:
    """Test graceful handling of syntax errors.

    Args:
        syntax_error_file: Fixture providing file with syntax errors.
    """
    scanner = ASTScanner(syntax_error_file.parent)
    index = scanner.scan()

    file_entity = list(index.files.values())[0]
    assert file_entity.has_syntax_error is True
    assert file_entity.error_message is not None


def test_scan_ignores_patterns(tmp_path: Path) -> None:
    """Test that ignored patterns are excluded.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    # Create files
    (tmp_path / "module.py").write_text("pass")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cached.py").write_text("pass")

    scanner = ASTScanner(tmp_path)
    index = scanner.scan()

    # Should only scan module.py, not cached.py
    assert len(index.files) == 1
    assert "module.py" in list(index.files.keys())[0]


def test_scan_directory_finds_all_python(sample_python_file: Path) -> None:
    """Test recursive scanning finds all Python files.

    Args:
        sample_python_file: Fixture providing sample Python file.
    """
    scanner = ASTScanner(sample_python_file.parent)
    index = scanner.scan()

    assert len(index.files) >= 1


def test_scan_extracts_line_count(sample_python_file: Path) -> None:
    """Test that line count is extracted.

    Args:
        sample_python_file: Fixture providing sample Python file.
    """
    scanner = ASTScanner(sample_python_file.parent)
    index = scanner.scan()

    file_entity = list(index.files.values())[0]
    assert file_entity.line_count > 0


def test_scan_with_include_patterns(tmp_path: Path) -> None:
    """Test scanning with include patterns.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    (tmp_path / "test_module.py").write_text("pass")
    (tmp_path / "other.py").write_text("pass")

    scanner = ASTScanner(tmp_path, include_patterns=["test_*.py"])
    index = scanner.scan()

    assert len(index.files) == 1
    assert "test_module.py" in list(index.files.keys())[0]
