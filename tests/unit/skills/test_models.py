"""Unit tests for dot_work.skills.models module.

Tests for SkillEnvironmentConfig and SkillMetadata dataclasses.
"""

import pytest

from dot_work.skills.models import (
    Skill,
    SkillEnvironmentConfig,
    SkillMetadata,
)


class TestSkillEnvironmentConfig:
    """Test SkillEnvironmentConfig validation and behavior."""

    def test_valid_with_target_only(self):
        """Valid config with only target (required field)."""
        config = SkillEnvironmentConfig(target=".claude/skills/")
        assert config.target == ".claude/skills/"
        assert config.filename is None
        assert config.filename_suffix is None

    def test_valid_with_filename(self):
        """Valid config with target and filename."""
        config = SkillEnvironmentConfig(
            target=".claude/skills/", filename="custom-name.md"
        )
        assert config.target == ".claude/skills/"
        assert config.filename == "custom-name.md"
        assert config.filename_suffix is None

    def test_valid_with_filename_suffix(self):
        """Valid config with target and filename_suffix."""
        config = SkillEnvironmentConfig(
            target=".claude/skills/", filename_suffix="-custom"
        )
        assert config.target == ".claude/skills/"
        assert config.filename is None
        assert config.filename_suffix == "-custom"

    def test_mutual_exclusion_both_provided_raises(self):
        """Cannot specify both filename and filename_suffix."""
        with pytest.raises(ValueError, match="both 'filename' and 'filename_suffix'"):
            SkillEnvironmentConfig(
                target=".claude/skills/",
                filename="custom.md",
                filename_suffix="-custom",
            )

    def test_empty_filename_raises(self):
        """Empty filename should raise ValueError."""
        with pytest.raises(ValueError, match="filename cannot be empty"):
            SkillEnvironmentConfig(target=".claude/skills/", filename="")

    def test_empty_filename_suffix_raises(self):
        """Empty filename_suffix should raise ValueError."""
        with pytest.raises(ValueError, match="filename_suffix cannot be empty"):
            SkillEnvironmentConfig(target=".claude/skills/", filename_suffix="")

    def test_none_values_are_allowed(self):
        """None is distinct from empty string and is allowed."""
        config = SkillEnvironmentConfig(
            target=".claude/skills/", filename=None, filename_suffix=None
        )
        assert config.filename is None
        assert config.filename_suffix is None


class TestSkillMetadata:
    """Test SkillMetadata validation and behavior."""

    def test_valid_minimal_metadata(self):
        """Valid metadata with only required fields."""
        metadata = SkillMetadata(name="test-skill", description="A test skill")
        assert metadata.name == "test-skill"
        assert metadata.description == "A test skill"
        assert metadata.license is None
        assert metadata.compatibility is None
        assert metadata.metadata is None
        assert metadata.allowed_tools is None
        assert metadata.environments is None

    def test_valid_full_metadata(self):
        """Valid metadata with all optional fields."""
        environments = {
            "claude": SkillEnvironmentConfig(target=".claude/skills/"),
        }
        metadata = SkillMetadata(
            name="test-skill",
            description="A test skill",
            license="MIT",
            compatibility="Claude Code 1.0+",
            metadata={"author": "Test", "version": "1.0.0"},
            allowed_tools=["read", "write"],
            environments=environments,
        )
        assert metadata.name == "test-skill"
        assert metadata.license == "MIT"
        assert metadata.compatibility == "Claude Code 1.0+"
        assert metadata.metadata == {"author": "Test", "version": "1.0.0"}
        assert metadata.allowed_tools == ["read", "write"]
        assert metadata.environments == environments

    def test_name_validation_lowercase_only(self):
        """Name must contain only lowercase letters, numbers, and hyphens."""
        with pytest.raises(ValueError, match="lowercase letters, numbers, and hyphens"):
            SkillMetadata(name="TestSkill", description="Invalid name")

    def test_name_validation_no_leading_hyphen(self):
        """Name cannot start with hyphen."""
        with pytest.raises(ValueError, match="cannot start/end with hyphen"):
            SkillMetadata(name="-test-skill", description="Invalid name")

    def test_name_validation_no_trailing_hyphen(self):
        """Name cannot end with hyphen."""
        with pytest.raises(ValueError, match="cannot start/end with hyphen"):
            SkillMetadata(name="test-skill-", description="Invalid name")

    def test_name_validation_allows_consecutive_hyphens(self):
        """The regex pattern allows consecutive hyphens (implementation detail).

        Note: The NAME_PATTERN regex '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'
        uses '[a-z0-9-]*' which allows consecutive hyphens. This is a
        known behavior of the current implementation.
        """
        # This should NOT raise - consecutive hyphens are currently allowed
        metadata = SkillMetadata(name="test--skill", description="Consecutive hyphens")
        assert metadata.name == "test--skill"

    def test_name_validation_valid_patterns(self):
        """Test valid name patterns."""
        valid_names = [
            "test",
            "test-skill",
            "my-skill-123",
            "a",
            "test123",
            "123test",
        ]
        for name in valid_names:
            metadata = SkillMetadata(name=name, description="Valid name")
            assert metadata.name == name

    def test_name_length_validation_too_short(self):
        """Name must be at least 1 character."""
        with pytest.raises(ValueError, match="must be 1-64 characters"):
            SkillMetadata(name="", description="Invalid name")

    def test_name_length_validation_too_long(self):
        """Name must be at most 64 characters."""
        with pytest.raises(ValueError, match="must be 1-64 characters"):
            SkillMetadata(name="a" * 65, description="Invalid name")

    def test_description_must_be_non_empty(self):
        """Description cannot be empty or whitespace only."""
        with pytest.raises(ValueError, match="cannot be empty"):
            SkillMetadata(name="test-skill", description="")

        with pytest.raises(ValueError, match="cannot be empty"):
            SkillMetadata(name="test-skill", description="   ")

    def test_description_length_validation_too_long(self):
        """Description must be at most 1024 characters."""
        with pytest.raises(ValueError, match="must be 1-1024 characters"):
            SkillMetadata(name="test-skill", description="a" * 1025)

    def test_compatibility_length_validation_too_long(self):
        """Compatibility must be at most 500 characters."""
        with pytest.raises(ValueError, match="must be <= 500 characters"):
            SkillMetadata(
                name="test-skill",
                description="Test",
                compatibility="a" * 501,
            )

    def test_metadata_must_be_dict(self):
        """Metadata field must be a dictionary if provided."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            SkillMetadata(
                name="test-skill",
                description="Test",
                metadata="not-a-dict",
            )

    def test_metadata_keys_and_values_must_be_strings(self):
        """Metadata keys and values must be strings."""
        with pytest.raises(ValueError, match="key must be string"):
            SkillMetadata(
                name="test-skill",
                description="Test",
                metadata={123: "value"},
            )

        with pytest.raises(ValueError, match="value must be string"):
            SkillMetadata(
                name="test-skill",
                description="Test",
                metadata={"key": 123},
            )

    def test_allowed_tools_must_be_list(self):
        """allowed_tools field must be a list if provided."""
        with pytest.raises(ValueError, match="must be a list"):
            SkillMetadata(
                name="test-skill",
                description="Test",
                allowed_tools="not-a-list",
            )

    def test_allowed_tools_items_must_be_strings(self):
        """allowed_tools items must be strings."""
        with pytest.raises(ValueError, match="must be string"):
            SkillMetadata(
                name="test-skill",
                description="Test",
                allowed_tools=["read", 123, "write"],
            )


class TestSkill:
    """Test Skill dataclass validation."""

    def test_valid_skill(self, tmp_path):
        """Valid skill with required fields."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()

        meta = SkillMetadata(name="test-skill", description="A test skill")
        skill = Skill(
            meta=meta,
            content="# Test Skill\n\nThis is a test skill.",
            path=skill_dir,
        )
        assert skill.meta.name == "test-skill"
        assert skill.path == skill_dir
        assert skill.content == "# Test Skill\n\nThis is a test skill."

    def test_path_must_match_name(self, tmp_path):
        """Skill directory name must match metadata name."""
        skill_dir = tmp_path / "different-name"
        skill_dir.mkdir()

        meta = SkillMetadata(name="test-skill", description="A test skill")
        with pytest.raises(ValueError, match="must match metadata name"):
            Skill(
                meta=meta,
                content="Test",
                path=skill_dir,
            )

    def test_content_must_be_string(self, tmp_path):
        """Content must be a string."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()

        meta = SkillMetadata(name="test-skill", description="A test skill")
        with pytest.raises(ValueError, match="content must be a string"):
            Skill(
                meta=meta,
                content=123,  # type: ignore
                path=skill_dir,
            )

    def test_path_converted_to_path_object(self, tmp_path):
        """Path is converted to Path object if string is provided."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()

        meta = SkillMetadata(name="test-skill", description="A test skill")
        skill = Skill(
            meta=meta,
            content="Test",
            path=str(skill_dir),  # Pass string instead of Path
        )
        assert isinstance(skill.path, type(skill_dir))
        assert skill.path == skill_dir

    def test_resource_directories_resolved(self, tmp_path):
        """Optional resource directories are resolved if they exist."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "test.sh").write_text("echo test")
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "ref.md").write_text("# Reference")

        meta = SkillMetadata(name="test-skill", description="A test skill")
        skill = Skill(
            meta=meta,
            content="Test",
            path=skill_dir,
        )

        assert skill.scripts is not None
        assert len(skill.scripts) == 1
        assert skill.references is not None
        assert len(skill.references) == 1
        assert skill.assets is None
