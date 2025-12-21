"""Unit tests for YAML validation tool."""

from pathlib import Path

from dot_work.tools.yaml_validator import (
    YAMLError,
    YAMLValidationResult,
    YAMLWarning,
    extract_frontmatter,
    parse_yaml,
    validate_yaml,
    validate_yaml_file,
)


class TestDataClasses:
    """Tests for dataclass behavior."""

    def test_yaml_error_str_with_location(self) -> None:
        """Test YAMLError string with location."""
        error = YAMLError("Test error", line=5, column=10)
        assert "5" in str(error)
        assert "10" in str(error)
        assert "Test error" in str(error)

    def test_yaml_error_str_without_location(self) -> None:
        """Test YAMLError string without location."""
        error = YAMLError("Test error")
        assert "Test error" in str(error)

    def test_yaml_warning_str_with_location(self) -> None:
        """Test YAMLWarning string with location."""
        warning = YAMLWarning("Tab found", line=3, column=1)
        assert "3" in str(warning)
        assert "Tab found" in str(warning)

    def test_yaml_warning_str_without_location(self) -> None:
        """Test YAMLWarning string without location."""
        warning = YAMLWarning("Tab found")
        assert "Tab found" in str(warning)

    def test_validation_result_bool(self) -> None:
        """Test YAMLValidationResult boolean behavior."""
        assert bool(YAMLValidationResult(valid=True)) is True
        assert bool(YAMLValidationResult(valid=False)) is False


class TestValidateYaml:
    """Tests for validate_yaml function."""

    def test_simple_mapping(self) -> None:
        """Test parsing simple key-value."""
        result = validate_yaml("name: test")
        assert result.valid
        assert result.data == {"name": "test"}

    def test_multiple_keys(self) -> None:
        """Test parsing multiple keys."""
        yaml = "name: test\nversion: 1.0\nenabled: true"
        result = validate_yaml(yaml)
        assert result.valid
        assert result.data == {"name": "test", "version": 1.0, "enabled": True}

    def test_nested_mapping(self) -> None:
        """Test parsing nested mappings."""
        yaml = "database:\n  host: localhost\n  port: 5432"
        result = validate_yaml(yaml)
        assert result.valid
        assert result.data == {"database": {"host": "localhost", "port": 5432}}

    def test_block_sequence(self) -> None:
        """Test parsing block sequences."""
        yaml = "items:\n  - apple\n  - banana\n  - cherry"
        result = validate_yaml(yaml)
        assert result.valid
        assert result.data == {"items": ["apple", "banana", "cherry"]}

    def test_inline_sequence(self) -> None:
        """Test parsing inline sequences."""
        result = validate_yaml("items: [a, b, c]")
        assert result.valid
        assert result.data == {"items": ["a", "b", "c"]}

    def test_inline_mapping(self) -> None:
        """Test parsing inline mappings."""
        result = validate_yaml("point: {x: 1, y: 2}")
        assert result.valid
        assert result.data == {"point": {"x": 1, "y": 2}}

    def test_empty_content(self) -> None:
        """Test that empty content is invalid."""
        result = validate_yaml("")
        assert not result.valid

    def test_whitespace_only(self) -> None:
        """Test that whitespace-only content is invalid."""
        result = validate_yaml("   \n\n   ")
        assert not result.valid

    def test_integer(self) -> None:
        """Test parsing integers."""
        result = validate_yaml("count: 42")
        assert result.data == {"count": 42}

    def test_negative_integer(self) -> None:
        """Test parsing negative integers."""
        result = validate_yaml("offset: -10")
        assert result.data == {"offset": -10}

    def test_float(self) -> None:
        """Test parsing floats."""
        result = validate_yaml("price: 19.99")
        assert result.data == {"price": 19.99}

    def test_hex_number(self) -> None:
        """Test parsing hex numbers."""
        result = validate_yaml("color: 0xFF")
        assert result.valid
        assert result.data == {"color": 255}

    def test_null(self) -> None:
        """Test parsing null."""
        result = validate_yaml("value: null")
        assert result.data == {"value": None}

    def test_tilde_null(self) -> None:
        """Test parsing tilde as null."""
        result = validate_yaml("value: ~")
        assert result.data == {"value": None}

    def test_boolean_true(self) -> None:
        """Test parsing true values."""
        for val in ["true", "True", "yes", "Yes"]:
            result = validate_yaml(f"flag: {val}")
            assert result.data == {"flag": True}, f"Failed for {val}"

    def test_boolean_false(self) -> None:
        """Test parsing false values."""
        for val in ["false", "False", "no", "No"]:
            result = validate_yaml(f"flag: {val}")
            assert result.data == {"flag": False}, f"Failed for {val}"

    def test_quoted_string(self) -> None:
        """Test parsing quoted strings."""
        result = validate_yaml('name: "hello world"')
        assert result.data == {"name": "hello world"}

    def test_literal_block_scalar(self) -> None:
        """Test parsing literal block scalar (|)."""
        yaml = "desc: |\n  Line one\n  Line two"
        result = validate_yaml(yaml)
        assert result.valid
        assert "Line one" in result.data["desc"]

    def test_folded_block_scalar(self) -> None:
        """Test parsing folded block scalar (>)."""
        yaml = "desc: >\n  Long\n  text"
        result = validate_yaml(yaml)
        assert result.valid

    def test_comments(self) -> None:
        """Test that comments are ignored."""
        yaml = "# comment\nname: test\n# another"
        result = validate_yaml(yaml)
        assert result.data == {"name": "test"}

    def test_document_start(self) -> None:
        """Test document start marker."""
        yaml = "---\nname: test"
        result = validate_yaml(yaml)
        assert result.valid
        assert result.data == {"name": "test"}

    def test_top_level_sequence(self) -> None:
        """Test parsing top-level sequence."""
        yaml = "- item1\n- item2\n- item3"
        result = validate_yaml(yaml)
        assert result.valid
        assert result.data == ["item1", "item2", "item3"]

    def test_unicode(self) -> None:
        """Test parsing unicode."""
        result = validate_yaml("greeting: こんにちは")
        assert result.valid
        assert result.data == {"greeting": "こんにちは"}


class TestSyntaxErrors:
    """Tests for YAML syntax error detection."""

    def test_unclosed_bracket(self) -> None:
        """Test detection of unclosed bracket."""
        result = validate_yaml("items: [a, b, c")
        assert not result.valid

    def test_unclosed_brace(self) -> None:
        """Test detection of unclosed brace."""
        result = validate_yaml("point: {x: 1, y: 2")
        assert not result.valid

    def test_duplicate_key(self) -> None:
        """Test handling of duplicate keys."""
        yaml = "key: value1\nkey: value2"
        result = validate_yaml(yaml)
        # PyYAML takes the last value
        assert result.valid
        assert result.data == {"key": "value2"}


class TestFileValidation:
    """Tests for YAML file validation."""

    def test_valid_file(self, tmp_path: Path) -> None:
        """Test validation of valid YAML file."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("name: test\nvalue: 42")
        result = validate_yaml_file(yaml_file)
        assert result.valid
        assert result.data == {"name": "test", "value": 42}

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Test validation of nonexistent file."""
        result = validate_yaml_file(tmp_path / "missing.yaml")
        assert not result.valid
        assert "not found" in result.errors[0].message.lower()

    def test_invalid_file(self, tmp_path: Path) -> None:
        """Test validation of invalid YAML file."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("key: [unclosed")
        result = validate_yaml_file(yaml_file)
        assert not result.valid


class TestFrontmatter:
    """Tests for frontmatter extraction."""

    def test_valid_frontmatter(self) -> None:
        """Test extraction of valid frontmatter."""
        content = "---\ntitle: Hello\nauthor: Jane\n---\n# Content here"
        result = extract_frontmatter(content)
        assert result.valid
        assert result.frontmatter == {"title": "Hello", "author": "Jane"}
        assert "# Content here" in result.content

    def test_no_frontmatter(self) -> None:
        """Test content without frontmatter."""
        content = "# Just some content"
        result = extract_frontmatter(content)
        assert not result.valid
        assert result.content == content

    def test_unclosed_frontmatter(self) -> None:
        """Test unclosed frontmatter."""
        content = "---\ntitle: Hello\n# No closing"
        result = extract_frontmatter(content)
        assert not result.valid

    def test_empty_frontmatter(self) -> None:
        """Test empty frontmatter."""
        content = "---\n---\n# Content"
        result = extract_frontmatter(content)
        assert not result.valid

    def test_frontmatter_with_list(self) -> None:
        """Test frontmatter with list."""
        content = "---\ntitle: Test\ntags: [python, yaml]\n---\nContent"
        result = extract_frontmatter(content)
        assert result.valid
        assert result.frontmatter == {"title": "Test", "tags": ["python", "yaml"]}


class TestParseYaml:
    """Tests for parse_yaml function."""

    def test_parse_simple(self) -> None:
        """Test direct parsing."""
        data = parse_yaml("key: value")
        assert data == {"key": "value"}

    def test_parse_list(self) -> None:
        """Test parsing list."""
        data = parse_yaml("- a\n- b\n- c")
        assert data == ["a", "b", "c"]

    def test_parse_complex(self) -> None:
        """Test parsing complex structure."""
        yaml = """
config:
  name: app
  port: 8080
  hosts:
    - localhost
    - 127.0.0.1
"""
        data = parse_yaml(yaml)
        assert data["config"]["name"] == "app"
        assert data["config"]["hosts"] == ["localhost", "127.0.0.1"]
