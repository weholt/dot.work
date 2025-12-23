"""Template management for instruction-based issue creation.

This module provides functionality for managing instruction templates
that can be used to create structured issues and epics.
"""

from dot_work.db_issues.templates.instruction_template import (
    InstructionTemplate,
    InstructionTemplateParser,
    TaskMetadata,
    TemplateParseError,
)
from dot_work.db_issues.templates.template_manager import TemplateManager

__all__ = [
    "InstructionTemplate",
    "InstructionTemplateParser",
    "TaskMetadata",
    "TemplateManager",
    "TemplateParseError",
]
