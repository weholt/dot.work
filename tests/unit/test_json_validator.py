"""Unit tests for JSON validation tool."""

from pathlib import Path

import pytest

from dot_work.tools.json_validator import (
    JSONError,
    JSONWarning,
    ValidationResult,
    validate_against_schema,
    validate_json,
    validate_json_file,
)


class TestValidateJson:
    """Tests for validate_json function."""

    def test_valid_object(self) -> None:
        """Test validation of valid JSON object."""
        result = validate_json('{"name": "test", "count": 42}')
        assert result.valid
        assert result.data == {"name": "test", "count": 42}

    def test_valid_array(self) -> None:
        """Test validation of valid JSON array."""
        result = validate_json('[1, 2, 3]')
        assert result.valid
        assert result.data == [1, 2, 3]

    def test_valid_nested(self) -> None:
        """Test validation of nested JSON."""
        result = validate_json('{"items": [{"id": 1}, {"id": 2}]}')
        assert result.valid
        assert result.data == {"items": [{"id": 1}, {"id": 2}]}

    def test_valid_primitives(self) -> None:
        """Test validation of JSON primitives."""
        assert validate_json("42").data == 42
        assert validate_json('"hello"').data == "hello"
        assert validate_json("true").data is True
        assert validate_json("null").data is None

    def test_empty_content(self) -> None:
        """Test that empty content is invalid."""
        result = validate_json("")
        assert not result.valid
        assert len(result.errors) == 1

    def test_whitespace_only(self) -> None:
        """Test that whitespace-only content is invalid."""
        result = validate_json("   \n\t  ")
        assert not result.valid

    def test_invalid_syntax_missing_comma(self) -> None:
        """Test detection of missing comma."""
        result = validate_json('{"a": 1 "b": 2}')
        assert not result.valid
        assert len(result.errors) == 1

    def test_invalid_syntax_unclosed_brace(self) -> None:
        """Test detection of unclosed brace."""
        result = validate_json('{"name": "test"')
        assert not result.valid

    def test_invalid_syntax_unclosed_bracket(self) -> None:
        """Test detection of unclosed bracket."""
        result = validate_json("[1, 2, 3")
        assert not result.valid

    def test_invalid_syntax_single_quotes(self) -> None:
        """Test detection of single quotes (invalid in JSON)."""
        result = validate_json("{'key': 'value'}")
        assert not result.valid

    def test_invalid_syntax_trailing_comma(self) -> None:
        """Test detection of trailing comma."""
        result = validate_json('{"a": 1,}')
        assert not result.valid

    def test_error_has_context(self) -> None:
        """Test that errors include context."""
        result = validate_json('{"key": value}')
        assert not result.valid
        assert result.errors[0].context  # Has context

    def test_error_has_line_column(self) -> None:
        """Test that errors include line/column."""
        result = validate_json('{\n  "a": 1\n  "b": 2\n}')
        assert not result.valid
        assert result.errors[0].line >= 1
        assert result.errors[0].column >= 1


class TestValidateJsonFile:
    """Tests for validate_json_file function."""

    def test_valid_file(self, tmp_path: Path) -> None:
        """Test validation of valid JSON file."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test"}')
        result = validate_json_file(json_file)
        assert result.valid
        assert result.data == {"name": "test"}

    def test_invalid_file(self, tmp_path: Path) -> None:
        """Test validation of invalid JSON file."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"name": }')
        result = validate_json_file(json_file)
        assert not result.valid

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Test validation of nonexistent file."""
        result = validate_json_file(tmp_path / "missing.json")
        assert not result.valid
        assert "not found" in result.errors[0].message.lower()

    def test_empty_file(self, tmp_path: Path) -> None:
        """Test validation of empty file."""
        json_file = tmp_path / "empty.json"
        json_file.write_text("")
        result = validate_json_file(json_file)
        assert not result.valid


class TestSchemaValidation:
    """Tests for JSON Schema validation."""

    def test_type_string_valid(self) -> None:
        """Test string type validation."""
        result = validate_against_schema("hello", {"type": "string"})
        assert result.valid

    def test_type_string_invalid(self) -> None:
        """Test string type validation fails for number."""
        result = validate_against_schema(42, {"type": "string"})
        assert not result.valid

    def test_type_number_valid(self) -> None:
        """Test number type validation."""
        assert validate_against_schema(3.14, {"type": "number"}).valid
        assert validate_against_schema(42, {"type": "number"}).valid

    def test_type_integer_valid(self) -> None:
        """Test integer type validation."""
        result = validate_against_schema(42, {"type": "integer"})
        assert result.valid

    def test_type_boolean_valid(self) -> None:
        """Test boolean type validation."""
        assert validate_against_schema(True, {"type": "boolean"}).valid
        assert validate_against_schema(False, {"type": "boolean"}).valid

    def test_type_null_valid(self) -> None:
        """Test null type validation."""
        result = validate_against_schema(None, {"type": "null"})
        assert result.valid

    def test_type_array_valid(self) -> None:
        """Test array type validation."""
        result = validate_against_schema([1, 2, 3], {"type": "array"})
        assert result.valid

    def test_type_object_valid(self) -> None:
        """Test object type validation."""
        result = validate_against_schema({"key": "value"}, {"type": "object"})
        assert result.valid

    def test_required_present(self) -> None:
        """Test required property is present."""
        schema = {"type": "object", "required": ["name"]}
        result = validate_against_schema({"name": "test"}, schema)
        assert result.valid

    def test_required_missing(self) -> None:
        """Test required property is missing."""
        schema = {"type": "object", "required": ["name"]}
        result = validate_against_schema({}, schema)
        assert not result.valid

    def test_enum_valid(self) -> None:
        """Test enum validation passes."""
        schema = {"enum": ["a", "b", "c"]}
        result = validate_against_schema("b", schema)
        assert result.valid

    def test_enum_invalid(self) -> None:
        """Test enum validation fails."""
        schema = {"enum": ["a", "b", "c"]}
        result = validate_against_schema("d", schema)
        assert not result.valid

    def test_pattern_valid(self) -> None:
        """Test pattern validation passes."""
        schema = {"type": "string", "pattern": r"^\d{3}-\d{4}$"}
        result = validate_against_schema("123-4567", schema)
        assert result.valid

    def test_pattern_invalid(self) -> None:
        """Test pattern validation fails."""
        schema = {"type": "string", "pattern": r"^\d{3}-\d{4}$"}
        result = validate_against_schema("invalid", schema)
        assert not result.valid

    def test_nested_object_validation(self) -> None:
        """Test nested object validation."""
        schema = {
            "type": "object",
            "properties": {"user": {"type": "object", "required": ["name"]}},
        }
        result = validate_against_schema({"user": {"name": "Alice"}}, schema)
        assert result.valid

    def test_array_items_validation(self) -> None:
        """Test array items validation."""
        schema = {"type": "array", "items": {"type": "integer"}}
        assert validate_against_schema([1, 2, 3], schema).valid
        assert not validate_against_schema([1, "two", 3], schema).valid


class TestDataClasses:
    """Tests for dataclass behavior."""

    def test_validation_result_bool(self) -> None:
        """Test ValidationResult boolean behavior."""
        assert bool(ValidationResult(valid=True)) is True
        assert bool(ValidationResult(valid=False)) is False

    def test_error_str(self) -> None:
        """Test JSONError string representation."""
        error = JSONError("Test error", line=5, column=10)
        assert "5" in str(error)
        assert "10" in str(error)
        assert "Test error" in str(error)

    def test_warning_str(self) -> None:
        """Test JSONWarning string representation."""
        warning = JSONWarning("Test warning", line=3, column=1)
        assert "3" in str(warning)
        assert "Test warning" in str(warning)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_content(self) -> None:
        """Test validation of unicode content."""
        result = validate_json('{"emoji": "🎉", "japanese": "こんにちは"}')
        assert result.valid
        assert result.data["emoji"] == "🎉"

    def test_escaped_characters(self) -> None:
        """Test validation of escaped characters."""
        result = validate_json('{"text": "line1\\nline2\\ttab"}')
        assert result.valid
        assert "\n" in result.data["text"]

    def test_large_numbers(self) -> None:
        """Test validation of large numbers."""
        result = validate_json('{"big": 12345678901234567890}')
        assert result.valid

    def test_deeply_nested(self) -> None:
        """Test validation of deeply nested structure."""
        deep = '{"a": {"b": {"c": {"d": {"e": 1}}}}}'
        result = validate_json(deep)
        assert result.valid
        assert result.data["a"]["b"]["c"]["d"]["e"] == 1
