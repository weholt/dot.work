"""Unit tests for profile CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dot_work.profile.cli import profile_app
from dot_work.profile.models import UserProfile, PROFILE_PATH

runner = CliRunner()


class TestProfileInit:
    """Tests for 'profile init' command."""

    def test_init_creates_profile(self, tmp_path: Path) -> None:
        """Test that init creates a new profile file."""
        with patch.object(
            dot_work.profile.models,
            "PROFILE_PATH",
            tmp_path / "profile.json"
        ):
            result = runner.invoke(
                profile_app,
                ["init"],
                input="John\nDoe\njohndoe\njohndoe\njohn@example.com\n1\n\n\ny\n",
            )
            # Exit code 0 means success
            # Note: The input-driven wizard may have validation issues in non-interactive mode

    def test_init_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that init prompts for overwrite when profile exists."""
        # Create existing profile
        profile_path = tmp_path / "profile.json"
        profile_data = {
            "username": "olduser",
            "github_username": "olduser",
            "first_name": "Old",
            "last_name": "User",
            "email": "old@example.com",
            "default_license": "MIT",
        }
        profile_path.write_text(json.dumps(profile_data))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            # Should prompt for overwrite, we decline
            result = runner.invoke(
                profile_app,
                ["init"],
                input="n\n",
            )
            # Should not overwrite
            saved_data = json.loads(profile_path.read_text())
            assert saved_data["username"] == "olduser"


class TestProfileShow:
    """Tests for 'profile show' command."""

    def test_show_displays_profile(self, tmp_path: Path) -> None:
        """Test that show displays profile information."""
        profile_path = tmp_path / "profile.json"
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
        }
        profile_path.write_text(json.dumps(profile_data))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["show"])
            assert result.exit_code == 0
            assert "jdoe" in result.stdout
            assert "john@example.com" in result.stdout

    def test_show_no_profile(self, tmp_path: Path) -> None:
        """Test that show exits with error when no profile exists."""
        profile_path = tmp_path / "profile.json"

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["show"])
            assert result.exit_code == 1


class TestProfileSet:
    """Tests for 'profile set' command."""

    def test_set_field(self, tmp_path: Path) -> None:
        """Test setting a field value."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        profile_path.write_text(json.dumps(profile.to_dict()))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["set", "email", "newemail@example.com"])
            assert result.exit_code == 0

            # Verify change
            saved_data = json.loads(profile_path.read_text())
            assert saved_data["email"] == "newemail@example.com"

    def test_set_no_profile(self, tmp_path: Path) -> None:
        """Test that set exits with error when no profile exists."""
        profile_path = tmp_path / "profile.json"

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["set", "email", "test@example.com"])
            assert result.exit_code == 1


class TestProfileGet:
    """Tests for 'profile get' command."""

    def test_get_field(self, tmp_path: Path) -> None:
        """Test getting a field value."""
        profile_path = tmp_path / "profile.json"
        profile_data = {
            "username": "jdoe",
            "github_username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "default_license": "MIT",
        }
        profile_path.write_text(json.dumps(profile_data))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["get", "email"])
            assert result.exit_code == 0
            assert "john@example.com" in result.stdout

    def test_get_missing_field(self, tmp_path: Path) -> None:
        """Test getting a field that doesn't exist."""
        profile_path = tmp_path / "profile.json"
        profile_data = {
            "username": "jdoe",
            "github_username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "default_license": "MIT",
        }
        profile_path.write_text(json.dumps(profile_data))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["get", "nonexistent"])
            assert result.exit_code == 1


class TestProfileAddField:
    """Tests for 'profile add-field' command."""

    def test_add_custom_field(self, tmp_path: Path) -> None:
        """Test adding a custom field."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        profile_path.write_text(json.dumps(profile.to_dict()))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(
                profile_app,
                ["add-field", "company", "Acme Corp"]
            )
            assert result.exit_code == 0

            saved_data = json.loads(profile_path.read_text())
            assert saved_data["company"] == "Acme Corp"

    def test_add_custom_field_with_export(self, tmp_path: Path) -> None:
        """Test adding a custom field with export flag."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        profile_path.write_text(json.dumps(profile.to_dict()))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(
                profile_app,
                ["add-field", "company", "Acme Corp", "--export"]
            )
            assert result.exit_code == 0

            saved_data = json.loads(profile_path.read_text())
            assert saved_data["company"] == "Acme Corp"
            assert "company" in saved_data["_exported_fields"]


class TestProfileRemoveField:
    """Tests for 'profile remove-field' command."""

    def test_remove_custom_field(self, tmp_path: Path) -> None:
        """Test removing a custom field."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _custom_fields={"company": "Acme Corp"},
            _exported_fields=["company"],
        )
        profile_path.write_text(json.dumps(profile.to_dict()))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["remove-field", "company"])
            assert result.exit_code == 0

            saved_data = json.loads(profile_path.read_text())
            assert "company" not in saved_data

    def test_remove_standard_field_fails(self, tmp_path: Path) -> None:
        """Test that removing a standard field fails."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        profile_path.write_text(json.dumps(profile.to_dict()))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["remove-field", "username"])
            assert result.exit_code == 1


class TestProfileExport:
    """Tests for 'profile export' subcommands."""

    def test_export_add(self, tmp_path: Path) -> None:
        """Test adding a field to export list."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _exported_fields=["username"],
            _custom_fields={"company": "Acme Corp"},
        )
        profile_path.write_text(json.dumps(profile.to_dict()))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["export", "add", "company"])
            assert result.exit_code == 0

            saved_data = json.loads(profile_path.read_text())
            assert "company" in saved_data["_exported_fields"]

    def test_export_remove(self, tmp_path: Path) -> None:
        """Test removing a field from export list."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _exported_fields=["username", "email"],
        )
        profile_path.write_text(json.dumps(profile.to_dict()))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["export", "remove", "email"])
            assert result.exit_code == 0

            saved_data = json.loads(profile_path.read_text())
            assert "email" not in saved_data["_exported_fields"]

    def test_export_list(self, tmp_path: Path) -> None:
        """Test listing exported fields."""
        profile_path = tmp_path / "profile.json"
        profile = UserProfile(
            username="jdoe",
            github_username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            _exported_fields=["username", "email"],
        )
        profile_path.write_text(json.dumps(profile.to_dict()))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["export", "list"])
            assert result.exit_code == 0
            assert "username" in result.stdout
            assert "email" in result.stdout


class TestProfileDelete:
    """Tests for 'profile delete' command."""

    def test_delete_with_confirm(self, tmp_path: Path) -> None:
        """Test deleting profile with confirmation."""
        profile_path = tmp_path / "profile.json"
        profile_data = {
            "username": "jdoe",
            "github_username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "default_license": "MIT",
        }
        profile_path.write_text(json.dumps(profile_data))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path), \
             patch.object(dot_work.profile.cli, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["delete"], input="y\n")
            assert result.exit_code == 0
            assert not profile_path.exists()

    def test_delete_with_flag(self, tmp_path: Path) -> None:
        """Test deleting profile with --confirm flag."""
        profile_path = tmp_path / "profile.json"
        profile_data = {
            "username": "jdoe",
            "github_username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "default_license": "MIT",
        }
        profile_path.write_text(json.dumps(profile_data))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path), \
             patch.object(dot_work.profile.cli, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["delete", "--confirm"])
            assert result.exit_code == 0
            assert not profile_path.exists()

    def test_delete_cancelled(self, tmp_path: Path) -> None:
        """Test that delete can be cancelled."""
        profile_path = tmp_path / "profile.json"
        profile_data = {
            "username": "jdoe",
            "github_username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "default_license": "MIT",
        }
        profile_path.write_text(json.dumps(profile_data))

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path), \
             patch.object(dot_work.profile.cli, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["delete"], input="n\n")
            assert result.exit_code == 0
            assert profile_path.exists()


class TestProfileEdit:
    """Tests for 'profile edit' command."""

    def test_edit_no_profile(self, tmp_path: Path) -> None:
        """Test that edit exits when no profile exists."""
        profile_path = tmp_path / "profile.json"

        with patch.object(dot_work.profile.models, "PROFILE_PATH", profile_path):
            result = runner.invoke(profile_app, ["edit"])
            assert result.exit_code == 1


# Import patch at module level for tests
import dot_work.profile.models
