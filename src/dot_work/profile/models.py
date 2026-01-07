"""User profile data models and core operations."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

PROFILE_PATH = Path.home() / ".work" / "profile.json"

# Standard fields that are always available in UserProfile
STANDARD_FIELDS = {
    "username",
    "github_username",
    "first_name",
    "last_name",
    "email",
    "default_license",
    "created_at",
    "updated_at",
}

# Internal fields (not exported to agents)
INTERNAL_FIELDS = {"_exported_fields", "created_at", "updated_at", "_custom_fields"}


@dataclass
class UserProfile:
    """User profile information with support for custom fields.

    The profile supports both standard fields (defined as dataclass attributes)
    and custom fields (stored in _custom_fields dict). Only fields listed in
    _exported_fields are exposed to agents and CLI operations.
    """

    username: str
    github_username: str
    first_name: str
    last_name: str
    email: str
    default_license: str = "MIT"
    created_at: str | None = None
    updated_at: str | None = None
    _exported_fields: list[str] = field(default_factory=list)
    # Custom fields stored as arbitrary dict
    _custom_fields: dict[str, Any] = field(default_factory=dict, repr=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get field value (standard or custom).

        Args:
            key: Field name to retrieve
            default: Value to return if field doesn't exist

        Returns:
            Field value or default
        """
        if key in STANDARD_FIELDS:
            return getattr(self, key, default)
        return self._custom_fields.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set field value (standard or custom).

        Args:
            key: Field name to set
            value: Value to set
        """
        if key in STANDARD_FIELDS:
            setattr(self, key, value)
        else:
            self._custom_fields[key] = value

    def is_exported(self, key: str) -> bool:
        """Check if field is in _exported_fields list.

        Args:
            key: Field name to check

        Returns:
            True if field is exported, False otherwise
        """
        return key in self._exported_fields

    def get_exported_data(self) -> dict[str, Any]:
        """Return only fields that are in _exported_fields.

        Internal fields (_exported_fields, created_at, updated_at) are never
        included in the exported data.

        Returns:
            Dictionary of exported field names to values
        """
        result = {}
        for key in self._exported_fields:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization.

        Merges custom fields into top level and removes internal tracking field.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        data = asdict(self)
        # Merge custom fields into top level
        data.update(self._custom_fields)
        # Remove internal tracking field
        data.pop("_custom_fields", None)
        return data

    def add_custom_field(self, name: str, value: Any, export: bool = False) -> None:
        """Add a custom field to the profile.

        Args:
            name: Field name
            value: Field value
            export: Whether to add field to _exported_fields list
        """
        self._custom_fields[name] = value
        if export and name not in self._exported_fields:
            self._exported_fields.append(name)

    def remove_custom_field(self, name: str) -> bool:
        """Remove a custom field from the profile.

        Args:
            name: Field name to remove

        Returns:
            True if field was removed, False if it didn't exist
        """
        if name in self._custom_fields:
            del self._custom_fields[name]
            # Also remove from exports if present
            if name in self._exported_fields:
                self._exported_fields.remove(name)
            return True
        return False

    def add_export(self, field: str) -> bool:
        """Add a field to the export list.

        Args:
            field: Field name to export

        Returns:
            True if added, False if already in list
        """
        if field not in self._exported_fields:
            self._exported_fields.append(field)
            return True
        return False

    def remove_export(self, field: str) -> bool:
        """Remove a field from the export list.

        Args:
            field: Field name to stop exporting

        Returns:
            True if removed, False if not in list
        """
        if field in self._exported_fields:
            self._exported_fields.remove(field)
            return True
        return False


def load_profile() -> UserProfile | None:
    """Load user profile from ~/.work/profile.json.

    Returns:
        UserProfile instance if file exists and is valid, None otherwise

    Raises:
        ValueError: If profile.json exists but contains invalid data
        json.JSONDecodeError: If profile.json contains invalid JSON
    """
    if not PROFILE_PATH.exists():
        return None

    try:
        data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in profile.json: {e}")
        raise
    except OSError as e:
        logger.error(f"Error reading profile.json: {e}")
        return None

    # Extract custom fields (anything not in standard fields or internal)
    custom_fields = {
        k: v for k, v in data.items() if k not in STANDARD_FIELDS and k not in INTERNAL_FIELDS
    }

    # Get exported fields list
    exported_fields = data.get("_exported_fields", [])

    try:
        profile = UserProfile(
            username=data.get("username", ""),
            github_username=data.get("github_username", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            email=data.get("email", ""),
            default_license=data.get("default_license", "MIT"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            _exported_fields=exported_fields,
            _custom_fields=custom_fields,
        )
        return profile
    except (TypeError, ValueError) as e:
        logger.error(f"Invalid profile data: {e}")
        raise ValueError(f"Invalid profile data: {e}") from e


def save_profile(profile: UserProfile) -> None:
    """Save user profile to ~/.work/profile.json.

    Updates the updated_at timestamp before saving.

    Args:
        profile: UserProfile instance to save

    Raises:
        OSError: If unable to write to profile.json
    """
    # Update timestamp
    profile.updated_at = datetime.now().isoformat()

    # Ensure parent directory exists
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict and save
    data = profile.to_dict()
    try:
        PROFILE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        logger.info(f"Profile saved to {PROFILE_PATH}")
    except OSError as e:
        logger.error(f"Error saving profile: {e}")
        raise


def validate_profile(profile: UserProfile) -> list[str]:
    """Validate profile fields.

    Args:
        profile: UserProfile instance to validate

    Returns:
        List of error messages (empty if profile is valid)
    """
    errors = []

    # Check required fields
    if not profile.username:
        errors.append("username is required")
    if not profile.github_username:
        errors.append("github_username is required")
    if not profile.first_name:
        errors.append("first_name is required")
    if not profile.last_name:
        errors.append("last_name is required")
    if not profile.email:
        errors.append("email is required")

    # Basic email format validation
    if profile.email and "@" not in profile.email:
        errors.append("email must contain @")

    # Validate default license
    valid_licenses = {"MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"}
    if profile.default_license and profile.default_license not in valid_licenses:
        errors.append(f"default_license must be one of: {', '.join(sorted(valid_licenses))}")

    return errors
