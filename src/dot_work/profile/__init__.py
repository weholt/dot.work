"""User profile management for dot-work.

This module provides functionality for managing user profiles stored in
~/.work/profile.json, including profile creation, loading, saving, and
validation.
"""

from dot_work.profile.models import UserProfile, load_profile, save_profile, validate_profile

__all__ = ["UserProfile", "load_profile", "save_profile", "validate_profile"]
