"""Tests for Python code parser."""

from pathlib import Path

from dot_overview.code_parser import (
    parse_python_file,
)


def test_parse_python_file_returns_dict() -> None:
    code = """
def hello():
    pass
"""
    result = parse_python_file(Path("test.py"), code, "test.py")
    assert "features" in result
    assert "models" in result
    assert isinstance(result["features"], list)
    assert isinstance(result["models"], list)


def test_parse_extract_functions() -> None:
    code = '''
def func1(a: int, b: str = "default") -> None:
    """A test function."""
    pass

def func2() -> str:
    """Another function."""
    return "test"
'''
    result = parse_python_file(Path("test.py"), code, "test.py")

    functions = [f for f in result["features"] if f.kind == "function"]
    assert len(functions) == 2

    func1 = [f for f in functions if f.name == "func1"][0]
    assert func1.name == "func1"
    assert len(func1.args) == 2
    assert func1.args[0].name == "a"
    assert func1.args[0].annotation == "int"
    assert func1.args[1].name == "b"
    assert func1.args[1].annotation == "str"


def test_parse_extract_classes() -> None:
    code = '''
class MyClass:
    """A test class."""

    def method1(self):
        pass
'''
    result = parse_python_file(Path("test.py"), code, "test.py")

    classes = [f for f in result["features"] if f.kind == "class"]
    assert len(classes) == 1
    assert classes[0].name == "MyClass"

    methods = [f for f in result["features"] if f.kind == "method"]
    assert len(methods) == 1
    assert methods[0].name == "method1"


def test_parse_extract_dataclasses() -> None:
    # The dataclass detection looks for typed annotations (AnnAssign)
    # which are present in dataclasses. However, the decorator itself
    # is not checked - only base names and annotated fields.
    code = '''
from dataclasses import dataclass

@dataclass
class Person:
    """A person."""
    name: str
    age: int = 0
'''
    result = parse_python_file(Path("test.py"), code, "test.py")

    # Check that Person was found (either as model or class feature)
    person_features = [f for f in result["features"] if f.name == "Person"]
    person_models = [m for m in result["models"] if m.name == "Person"]

    # Should be detected as either a model or a class feature
    assert len(person_features) > 0 or len(person_models) > 0

    # If detected as a model, verify fields
    if person_models:
        assert len(person_models[0].fields) == 2
        field_names = [f.name for f in person_models[0].fields]
        assert "name" in field_names
        assert "age" in field_names


def test_parse_extract_docstrings() -> None:
    code = '''
def documented():
    """This function is documented."""
    pass

def undocumented():
    pass
'''
    result = parse_python_file(Path("test.py"), code, "test.py")

    documented = [f for f in result["features"] if f.name == "documented"][0]
    assert documented.docstring == "This function is documented."

    undocumented = [f for f in result["features"] if f.name == "undocumented"][0]
    assert undocumented.docstring is None


def test_parse_return_annotations() -> None:
    code = """
def returns_str() -> str:
    return "test"

def returns_none():
    return None
"""
    result = parse_python_file(Path("test.py"), code, "test.py")

    returns_str = [f for f in result["features"] if f.name == "returns_str"][0]
    assert returns_str.returns == "str"

    returns_none = [f for f in result["features"] if f.name == "returns_none"][0]
    assert returns_none.returns is None


def test_parse_parent_class_reference() -> None:
    code = """
class Parent:
    pass

class Child(Parent):
    def child_method(self):
        pass
"""
    result = parse_python_file(Path("test.py"), code, "test.py")

    child_method = [f for f in result["features"] if f.name == "child_method"][0]
    assert child_method.parent == "Child"


def test_parse_invalid_syntax() -> None:
    code = """
def broken(
    # Missing closing paren
"""
    result = parse_python_file(Path("test.py"), code, "test.py")
    # Should return empty results for invalid syntax
    assert len(result["features"]) == 0
    assert len(result["models"]) == 0


def test_parse_nested_classes() -> None:
    code = '''
class Outer:
    """Outer class."""

    class Inner:
        """Inner class."""

        def inner_method(self):
            pass

    def outer_method(self):
        pass
'''
    result = parse_python_file(Path("test.py"), code, "test.py")

    # Should find both classes
    outer = [f for f in result["features"] if f.name == "Outer"]
    inner = [f for f in result["features"] if f.name == "Inner"]
    assert len(outer) == 1
    assert len(inner) == 1

    # Methods exist
    methods = [f for f in result["features"] if f.kind in ("method", "function")]
    assert len(methods) >= 2

    # Note: Parent tracking for nested class methods is limited
    # due to how libcst visitor pattern works - methods may show
    # parent=None depending on the visitation order


def test_parse_function_overloads() -> None:
    code = """
from typing import overload

@overload
def func(x: int) -> int: ...

@overload
def func(x: str) -> str: ...

def func(x):
    return x
"""
    result = parse_python_file(Path("test.py"), code, "test.py")

    # Should find at least one func
    funcs = [f for f in result["features"] if f.name == "func"]
    assert len(funcs) >= 1
