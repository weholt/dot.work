"""
Git Analysis: Structured Git History Comparison and Analysis Tool

A comprehensive tool for analyzing and comparing git history between branches,
commits, or tags with structured, reusable output and LLM-powered summaries.
"""

__version__ = "0.1.0"
__author__ = "Git Analysis Team"

from dot_work.git.models import (
    AnalysisConfig,
    ChangeAnalysis,
    CommitInfo,
    ComparisonDiff,
    ComparisonResult,
    ContributorStats,
)
from dot_work.git.services import (
    AnalysisCache,
    ComplexityCalculator,
    GitAnalysisService,
    LLMSummarizer,
)

__all__ = [
    # Models
    "ChangeAnalysis",
    "ComparisonResult",
    "ComparisonDiff",
    "CommitInfo",
    "ContributorStats",
    "AnalysisConfig",
    # Services
    "GitAnalysisService",
    "ComplexityCalculator",
    "LLMSummarizer",
    "AnalysisCache",
]
