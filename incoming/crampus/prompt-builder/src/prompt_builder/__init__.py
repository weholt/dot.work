"""
Prompt Builder: Multi-Agent Validation System

A comprehensive system for preventing code regressions through
iterative task decomposition and multi-agent validation.
"""

__version__ = "0.1.0"
__author__ = "Prompt Builder Team"

from .agents import (
    BehaviorValidatorAgent,
    ImplementerAgent,
    PlannerAgent,
    PRGeneratorAgent,
    RegressionSentinelAgent,
    StaticValidatorAgent,
)
from .models import (
    ChangeImpactResult,
    Snapshot,
    Subtask,
    SyntheticTestResult,
    ValidationResult,
)

__all__ = [
    # Models
    "Subtask",
    "ValidationResult",
    "Snapshot",
    "ChangeImpactResult",
    "SyntheticTestResult",
    # Agents
    "PlannerAgent",
    "ImplementerAgent",
    "StaticValidatorAgent",
    "BehaviorValidatorAgent",
    "RegressionSentinelAgent",
    "PRGeneratorAgent",
]
