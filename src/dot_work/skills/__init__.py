"""Agent Skills integration for dot-work.

This module provides functionality for discovering, parsing, validating,
and generating prompts for Agent Skills per the Agent Skills specification.

Skills are reusable agent capability packages with structured metadata,
progressive disclosure, and optional bundled resources.

Example usage:
    from dot_work.skills import SkillDiscovery, generate_skills_prompt

    discovery = SkillDiscovery()
    skills = discovery.discover()
    prompt = generate_skills_prompt(skills)
"""

from __future__ import annotations

from pathlib import Path

from dot_work.skills.discovery import DEFAULT_DISCOVERY, SkillDiscovery
from dot_work.skills.models import Skill, SkillEnvironmentConfig, SkillMetadata
from dot_work.skills.parser import SKILL_PARSER, SkillParser, SkillParserError
from dot_work.skills.prompt_generator import generate_skill_prompt, generate_skills_prompt
from dot_work.skills.validator import SKILL_VALIDATOR, SkillValidator, ValidationResult

__all__ = [
    # Models
    "Skill",
    "SkillEnvironmentConfig",
    "SkillMetadata",
    # Discovery
    "SkillDiscovery",
    "DEFAULT_DISCOVERY",
    # Parser
    "SkillParser",
    "SKILL_PARSER",
    "SkillParserError",
    # Validator
    "SkillValidator",
    "SKILL_VALIDATOR",
    "ValidationResult",
    # Prompt Generation
    "generate_skills_prompt",
    "generate_skill_prompt",
]


def get_bundled_skills_dir() -> Path:
    """Get the directory containing bundled skill assets.

    Returns:
        Path to the bundled skills directory (assets/skills/).
    """
    # __file__ is src/dot_work/skills/__init__.py
    # Go up to src/dot_work/ then down to assets/skills/
    return Path(__file__).parent.parent / "assets" / "skills"
