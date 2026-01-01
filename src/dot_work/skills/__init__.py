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

from dot_work.skills.discovery import DEFAULT_DISCOVERY, SkillDiscovery
from dot_work.skills.models import Skill, SkillMetadata
from dot_work.skills.parser import SKILL_PARSER, SkillParser, SkillParserError
from dot_work.skills.prompt_generator import generate_skill_prompt, generate_skills_prompt
from dot_work.skills.validator import SKILL_VALIDATOR, SkillValidator, ValidationResult

__all__ = [
    # Models
    "Skill",
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
