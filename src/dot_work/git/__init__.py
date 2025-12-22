"""
Git Analysis: Structured Git History Comparison and Analysis Tool

A comprehensive tool for analyzing and comparing git history between branches,
commits, or tags with structured, reusable output and LLM-powered summaries.
"""

__version__ = "0.1.0"
__author__ = "Git Analysis Team"

from dot_work.git.models import (
    ChangeAnalysis,
    ComparisonResult,
    ComparisonDiff,
    CommitInfo,
    ContributorStats,
    AnalysisConfig,
)

from dot_work.git.services import (
    GitAnalysisService,
    ComplexityCalculator,
    LLMSummarizer,
    AnalysisCache,
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
