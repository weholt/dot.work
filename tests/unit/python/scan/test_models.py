"""
Tests for data models.
"""

from pathlib import Path

from dot_work.python.scan.models import (
    ClassEntity,
    CodeIndex,
    FileEntity,
    FunctionEntity,
    ImportInfo,
)


def test_function_entity_creation() -> None:
    """Test creating a FunctionEntity."""
    func = FunctionEntity(
        name="test_func",
        file_path=Path("test.py"),
        line_no=10,
    )

    assert func.name == "test_func"
    assert func.line_no == 10
    assert func.is_async is False
    assert func.complexity == 1


def test_class_entity_creation() -> None:
    """Test creating a ClassEntity."""
    cls = ClassEntity(
        name="TestClass",
        file_path=Path("test.py"),
        line_no=5,
        bases=["BaseClass"],
    )

    assert cls.name == "TestClass"
    assert cls.line_no == 5
    assert "BaseClass" in cls.bases


def test_import_info_creation() -> None:
    """Test creating an ImportInfo."""
    imp = ImportInfo(
        module="typing",
        name="Any",
        line_no=3,
        is_from_import=True,
    )

    assert imp.module == "typing"
    assert imp.name == "Any"
    assert imp.is_from_import is True


def test_file_entity_creation() -> None:
    """Test creating a FileEntity."""
    file_entity = FileEntity(
        path=Path("test.py"),
        line_count=100,
    )

    assert file_entity.path == Path("test.py")
    assert file_entity.line_count == 100
    assert file_entity.has_syntax_error is False


def test_code_index_add_file() -> None:
    """Test adding a file to the code index."""
    index = CodeIndex(root_path=Path("."))

    func = FunctionEntity(
        name="test_func",
        file_path=Path("test.py"),
        line_no=10,
    )

    file_entity = FileEntity(
        path=Path("test.py"),
        functions=[func],
    )

    index.add_file(file_entity)

    assert "test.py" in index.files
    assert "test_func" in index.functions


def test_code_index_find_function() -> None:
    """Test finding a function by name."""
    index = CodeIndex(root_path=Path("."))

    func = FunctionEntity(
        name="my_function",
        file_path=Path("test.py"),
        line_no=10,
    )

    file_entity = FileEntity(
        path=Path("test.py"),
        functions=[func],
    )

    index.add_file(file_entity)

    results = index.find_function("my_function")
    assert results is not None
    assert len(results) == 1
    assert results[0].name == "my_function"


def test_code_index_find_class() -> None:
    """Test finding a class by name."""
    index = CodeIndex(root_path=Path("."))

    cls = ClassEntity(
        name="MyClass",
        file_path=Path("test.py"),
        line_no=5,
    )

    file_entity = FileEntity(
        path=Path("test.py"),
        classes=[cls],
    )

    index.add_file(file_entity)

    results = index.find_class("MyClass")
    assert results is not None
    assert len(results) == 1
    assert results[0].name == "MyClass"


def test_code_index_get_complex_functions() -> None:
    """Test getting complex functions."""
    index = CodeIndex(root_path=Path("."))

    simple_func = FunctionEntity(
        name="simple",
        file_path=Path("test.py"),
        line_no=10,
        complexity=1,
    )

    complex_func = FunctionEntity(
        name="complex",
        file_path=Path("test.py"),
        line_no=20,
        complexity=15,
    )

    file_entity = FileEntity(
        path=Path("test.py"),
        functions=[simple_func, complex_func],
    )

    index.add_file(file_entity)

    complex_functions = index.get_complex_functions(threshold=10)
    assert len(complex_functions) == 1
    assert complex_functions[0].name == "complex"
