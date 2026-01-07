"""XML prompt generation for Agent Skills.

This module generates <available_skills> XML sections for agent
system prompts, following the Agent Skills specification format.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from dot_work.skills.models import SkillMetadata


def generate_skills_prompt(
    skills: list[SkillMetadata],
    include_paths: bool = True,
) -> str:
    """Generate XML prompt section for available skills.

    Args:
        skills: List of SkillMetadata objects to include in prompt.
        include_paths: If True, include file paths in output (default: True).

    Returns:
        Formatted XML string with available skills.

    Example output:
        <available_skills>
          <skill>
            <name>pdf-processing</name>
            <description>Extracts text and tables from PDF files...</description>
            <location>/path/to/skills/pdf-processing/SKILL.md</location>
          </skill>
        </available_skills>
    """
    root = ET.Element("available_skills")

    for skill in skills:
        skill_elem = ET.SubElement(root, "skill")

        # Add name
        name_elem = ET.SubElement(skill_elem, "name")
        name_elem.text = skill.name

        # Add description
        desc_elem = ET.SubElement(skill_elem, "description")
        desc_elem.text = skill.description[:200]  # Truncate for brevity

        # Add optional location
        if include_paths:
            # Note: We don't have the path in SkillMetadata during discovery
            # This would need to be added if tracking source paths
            loc_elem = ET.SubElement(skill_elem, "location")
            loc_elem.text = f".skills/{skill.name}/SKILL.md"

        # Add optional license
        if skill.license:
            license_elem = ET.SubElement(skill_elem, "license")
            license_elem.text = skill.license

    # Add indentation for readability (Python 3.9+)
    ET.indent(root, space="  ")

    # Generate XML string
    result = ET.tostring(root, encoding="unicode")

    # Remove XML declaration if present
    if result.startswith("<?xml"):
        result = result.split("?>", 1)[1].lstrip()

    return result


def generate_skill_prompt(skill: SkillMetadata, include_path: bool = True) -> str:
    """Generate XML prompt for a single skill.

    Args:
        skill: SkillMetadata object to format.
        include_path: If True, include file path (default: True).

    Returns:
        Formatted XML string for the skill.

    Example output:
        <skill>
          <name>pdf-processing</name>
          <description>Extracts text and tables from PDF files...</description>
        </skill>
    """
    return generate_skills_prompt([skill], include_paths=include_path)
