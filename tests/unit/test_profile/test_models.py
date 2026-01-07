"""Unit tests for profile models."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from dot_work.profile.models import (
    UserProfile,
    load_profile,
    save_profile,
    validate_profile,
    STANDARD_FIELDS,
    INTERNAL_FIELDS,
    PROFILE_PATH,
)


class TestUserProfile:
    """Tests for UserProfile dataclass."""

    def test_create_minimal_profile(self) -> None:
        """Test creating a profile with minimal required fields."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        assert profile.username == "jdoe"
        assert profile.github_username == "johndoe"
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.email == "john@example.com"
        assert profile.default_license == "MIT"  # Default value

    def test_create_full_profile(self) -> None:
        """Test creating a profile with all fields."""
        now = datetime.now().isoformat()
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            default_license="Apache-2.0",
            created_at=now,
            updated_at=now,
            _exported_fields=["username", "email"],
            _custom_fields={"company": "Acme Corp"},
        )
        assert profile.default_license == "Apache-2.0"
        assert profile.created_at == now
        assert profile.updated_at == now
        assert profile._exported_fields == ["username", "email"]
        assert profile._custom_fields == {"company": "Acme Corp"}

    def test_get_standard_field(self) -> None:
        """Test getting a standard field value."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        assert profile.get("username") == "jdoe"
        assert profile.get("email") == "john@example.com"

    def test_get_custom_field(self) -> None:
        """Test getting a custom field value."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _custom_fields={"company": "Acme Corp"},
        )
        assert profile.get("company") == "Acme Corp"

    def test_get_missing_field_returns_default(self) -> None:
        """Test that get() returns default for missing fields."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        assert profile.get("missing_field") is None
        assert profile.get("missing_field", "default") == "default"

    def test_set_standard_field(self) -> None:
        """Test setting a standard field value."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        profile.set("email", "newemail@example.com")
        assert profile.email == "newemail@example.com"

    def test_set_custom_field(self) -> None:
        """Test setting a custom field value."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        profile.set("company", "Acme Corp")
        assert profile._custom_fields == {"company": "Acme Corp"}
        assert profile.get("company") == "Acme Corp"

    def test_is_exported(self) -> None:
        """Test checking if a field is exported."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _exported_fields=["username", "email"],
        )
        assert profile.is_exported("username") is True
        assert profile.is_exported("email") is True
        assert profile.is_exported("github_username") is False

    def test_get_exported_data(self) -> None:
        """Test getting only exported fields."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _exported_fields=["username", "email"],
            _custom_fields={"company": "Acme Corp"},
        )
        exported = profile.get_exported_data()
        assert exported == {"username": "jdoe", "email": "john@example.com"}
        # Non-exported fields not included
        assert "github_username" not in exported
        assert "company" not in exported

    def test_to_dict(self) -> None:
        """Test converting profile to dict."""
        now = datetime.now().isoformat()
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            default_license="MIT",
            created_at=now,
            updated_at=now,
            _exported_fields=["username", "email"],
            _custom_fields={"company": "Acme Corp"},
        )
        data = profile.to_dict()
        assert data["username"] == "jdoe"
        assert data["email"] == "john@example.com"
        assert data["company"] == "Acme Corp"
        assert "_custom_fields" not in data
        assert data["_exported_fields"] == ["username", "email"]

    def test_add_custom_field_not_exported(self) -> None:
        """Test adding a custom field without exporting."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        profile.add_custom_field("company", "Acme Corp", export=False)
        assert profile._custom_fields == {"company": "Acme Corp"}
        assert "company" not in profile._exported_fields

    def test_add_custom_field_exported(self) -> None:
        """Test adding a custom field with export."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        profile.add_custom_field("company", "Acme Corp", export=True)
        assert profile._custom_fields == {"company": "Acme Corp"}
        assert "company" in profile._exported_fields

    def test_remove_custom_field(self) -> None:
        """Test removing a custom field."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _custom_fields={"company": "Acme Corp"},
            _exported_fields=["company"],
        )
        assert profile.remove_custom_field("company") is True
        assert "company" not in profile._custom_fields
        assert "company" not in profile._exported_fields

    def test_remove_nonexistent_custom_field(self) -> None:
        """Test removing a field that doesn't exist."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        assert profile.remove_custom_field("nonexistent") is False

    def test_add_export(self) -> None:
        """Test adding a field to export list."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _exported_fields=["username"],
        )
        assert profile.add_export("email") is True
        assert "email" in profile._exported_fields

    def test_add_export_already_exists(self) -> None:
        """Test adding a field that's already exported."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _exported_fields=["username"],
        )
        assert profile.add_export("username") is False
        assert profile._exported_fields == ["username"]

    def test_remove_export(self) -> None:
        """Test removing a field from export list."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _exported_fields=["username", "email"],
        )
        assert profile.remove_export("email") is True
        assert "email" not in profile._exported_fields

    def test_remove_export_not_exists(self) -> None:
        """Test removing a field that's not exported."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _exported_fields=["username"],
        )
        assert profile.remove_export("email") is False


class TestLoadProfile:
    """Tests for load_profile function."""

    def test_load_profile_no_file(self, tmp_path: Path) -> None:
        """Test loading when profile file doesn't exist."""
        with patch.object(dot_work.profile.models, "PROFILE_PATH", tmp_path / "profile.json"):
            profile = load_profile()
            assert profile is None

    def test_load_profile_valid_json(self, tmp_path: Path) -> None:
        """Test loading a valid profile JSON file."""
        profile_data = {
            "username": "jdoe",
            "github_username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "default_license": "MIT",
            "created_at": "2026-01-07T12:00:00Z",
            "updated_at": "2026-01-07T12:00:00Z",
            "_exported_fields": ["username", "email"],
            "company": "Acme Corp",
        }
        profile_file = tmp_path / "profile.json"
        profile_file.write_text(json.dumps(profile_data))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_file):
            profile = load_profile()

        assert profile is not None
        assert profile.username == "jdoe"
        assert profile.email == "john@example.com"
        assert profile._custom_fields == {"company": "Acme Corp"}

    def test_load_profile_invalid_json(self, tmp_path: Path) -> None:
        """Test loading a file with invalid JSON."""
        profile_file = tmp_path / "profile.json"
        profile_file.write_text("{invalid json}")

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_file):
            with pytest.raises(json.JSONDecodeError):
                load_profile()

    def test_load_profile_missing_required_fields(self, tmp_path: Path) -> None:
        """Test loading profile with missing required fields."""
        profile_data = {
            "username": "jdoe",
            # Missing other required fields
        }
        profile_file = tmp_path / "profile.json"
        profile_file.write_text(json.dumps(profile_data))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_file):
            profile = load_profile()

        # Should still load, with empty defaults
        assert profile is not None
        assert profile.username == "jdoe"
        assert profile.email == ""


class TestSaveProfile:
    """Tests for save_profile function."""

    def test_save_profile_creates_directory(self, tmp_path: Path) -> None:
        """Test that save_profile creates parent directory."""
        profile_path = tmp_path / ".work" / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            save_profile(profile)

        assert profile_path.exists()
        assert profile_path.parent.exists()

    def test_save_profile_updates_timestamp(self, tmp_path: Path) -> None:
        """Test that save_profile updates updated_at timestamp."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            created_at="2026-01-01T12:00:00Z",
            updated_at="2026-01-01T12:00:00Z",
        )

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            save_profile(profile)

        saved_data = json.loads(profile_path.read_text())
        assert saved_data["updated_at"] != "2026-01-01T12:00:00Z"
        assert saved_data["created_at"] == "2026-01-01T12:00:00Z"

    def test_save_profile_custom_fields(self, tmp_path: Path) -> None:
        """Test that save_profile includes custom fields in JSON."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _custom_fields={"company": "Acme Corp", "timezone": "America/New_York"},
        )

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            save_profile(profile)

        saved_data = json.loads(profile_path.read_text())
        assert saved_data["company"] == "Acme Corp"
        assert saved_data["timezone"] == "America/New_York"
        assert "_custom_fields" not in saved_data


class TestValidateProfile:
    """Tests for validate_profile function."""

    def test_valid_profile(self) -> None:
        """Test validating a valid profile."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            default_license="MIT",
        )
        errors = validate_profile(profile)
        assert errors == []

    def test_missing_required_fields(self) -> None:
        """Test validating profile with missing required fields."""
        profile = UserProfile(
            username="",
            github_username="",
            first_name="",
            last_name="",
            email="",
        )
        errors = validate_profile(profile)
        assert len(errors) == 5
        assert "username is required" in errors
        assert "github_username is required" in errors
        assert "first_name is required" in errors
        assert "last_name is required" in errors
        assert "email is required" in errors

    def test_invalid_email_format(self) -> None:
        """Test validating profile with invalid email."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="invalid-email",
        )
        errors = validate_profile(profile)
        assert "email must contain @" in errors

    def test_invalid_license(self) -> None:
        """Test validating profile with invalid license."""
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            default_license="INVALID",
        )
        errors = validate_profile(profile)
        assert "default_license must be one of" in errors[0]

    def test_valid_licenses(self) -> None:
        """Test that all valid licenses pass validation."""
        for license_type in ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"]:
            profile = UserProfile(
                username="jdoe",
                github_username="johndoe",
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                default_license=license_type,
            )
            errors = validate_profile(profile)
            assert errors == []


class TestConstants:
    """Tests for module constants."""

    def test_standard_fields(self) -> None:
        """Test STANDARD_FIELDS contains expected fields."""
        assert "username" in STANDARD_FIELDS
        assert "email" in STANDARD_FIELDS
        assert "github_username" in STANDARD_FIELDS

    def test_internal_fields(self) -> None:
        """Test INTERNAL_FIELDS contains expected fields."""
        assert "_exported_fields" in INTERNAL_FIELDS
        assert "created_at" in INTERNAL_FIELDS
        assert "updated_at" in INTERNAL_FIELDS


# Import patch at module level for tests
import dot_work.profile.models
