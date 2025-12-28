"""Data models for git analysis and comparison."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ChangeType(Enum):
    """Types of changes in a commit."""

    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"
    COPIED = "copied"


class FileCategory(Enum):
    """Categories of files based on their purpose."""

    CODE = "code"
    TESTS = "tests"
    CONFIG = "config"
    DOCUMENTATION = "documentation"
    DATA = "data"
    BUILD = "build"
    DEPLOYMENT = "deployment"
    UNKNOWN = "unknown"


@dataclass
class CommitInfo:
    """Basic commit information."""

    hash: str
    short_hash: str
    author: str
    email: str
    timestamp: datetime
    message: str
    branch: str = "main"
    tags: list[str] = field(default_factory=list)


@dataclass
class FileChange:
    """Information about a changed file."""

    path: str
    old_path: str | None = None  # For renames/copies
    change_type: ChangeType = ChangeType.MODIFIED
    category: FileCategory = FileCategory.UNKNOWN
    lines_added: int = 0
    lines_deleted: int = 0
    binary_file: bool = False


@dataclass
class ChangeAnalysis:
    """Detailed analysis of a single commit."""

    commit_hash: str
    author: str
    email: str
    timestamp: datetime
    branch: str
    message: str
    short_message: str
    files_changed: list[FileChange]
    lines_added: int
    lines_deleted: int
    files_added: int
    files_deleted: int
    files_modified: int
    complexity_score: float
    summary: str
    tags: list[str]
    impact_areas: list[str]
    breaking_change: bool = False
    test_coverage_change: float = 0.0
    performance_impact: str | None = None
    security_relevant: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContributorStats:
    """Statistics for a contributor."""

    name: str
    email: str
    commits: int
    lines_added: int
    lines_deleted: int
    files_touched: int
    complexity_contribution: float
    first_commit: datetime
    last_commit: datetime


@dataclass
class ComparisonMetadata:
    """Metadata for a comparison between two git references."""

    from_ref: str
    to_ref: str
    from_commit_hash: str
    to_commit_hash: str
    date_range: tuple[datetime, datetime]
    total_commits: int
    total_files_changed: int
    total_lines_added: int
    total_lines_deleted: int
    total_complexity: float
    time_span_days: int
    branches_involved: list[str]


@dataclass
class ComparisonResult:
    """Result of comparing two git references."""

    metadata: ComparisonMetadata
    commits: list[ChangeAnalysis]
    contributors: dict[str, ContributorStats]
    aggregate_summary: str
    highlights: list[str]
    risk_assessment: str
    recommendations: list[str]
    file_categories: dict[FileCategory, int]
    complexity_distribution: dict[str, int]  # ranges -> count
    top_complex_files: list[dict[str, Any]]


@dataclass
class ComparisonDiff:
    """Natural language description of differences between commits."""

    commit_a_hash: str
    commit_b_hash: str
    similarity_score: float
    differences: list[str]
    common_themes: list[str]
    impact_description: str
    regression_risk: str
    migration_notes: list[str]


@dataclass
class AnalysisConfig:
    """Configuration for git analysis."""

    repo_path: Path = field(default_factory=lambda: Path.cwd())
    cache_dir: Path | None = None
    use_llm: bool = False
    llm_provider: str = "openai"  # openai, anthropic, local
    complexity_threshold: float = 50.0
    max_commits: int = 1000
    include_binary_files: bool = False
    detailed_file_analysis: bool = True
    generate_tags: bool = True
    analyze_dependencies: bool = False
    parallel_processing: bool = True
    max_workers: int = 4
    timeout_seconds: int = 300

    # LLM-specific settings
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1000

    # Output settings
    output_format: str = "json"  # json, yaml, toml
    include_raw_diff: bool = False
    include_file_contents: bool = False

    # Filtering settings
    file_ignore_patterns: list[str] = field(default_factory=list)
    author_ignore_patterns: list[str] = field(default_factory=list)
    commit_message_ignore_patterns: list[str] = field(default_factory=lambda: ["^Merge pull request", "^Auto-matic"])

    # Caching settings
    cache_ttl_hours: int = 24
    force_refresh: bool = False


@dataclass
class CacheEntry:
    """Entry in the analysis cache."""

    key: str
    data: dict[str, Any]
    timestamp: datetime
    ttl_hours: int = 24

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        from datetime import timedelta

        return datetime.now() - self.timestamp > timedelta(hours=self.ttl_hours)


@dataclass
class AnalysisError:
    """Error information for failed analysis."""

    error_type: str
    message: str
    commit_hash: str | None = None
    file_path: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: str | None = None


@dataclass
class AnalysisProgress:
    """Progress information for long-running analysis."""

    total_commits: int
    processed_commits: int
    current_step: str
    estimated_remaining_seconds: int
    stage: str = "processing"  # processing, analyzing, summarizing

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_commits == 0:
            return 0.0
        return (self.processed_commits / self.total_commits) * 100


# Type aliases
CommitHash = str
BranchName = str
TagName = str
FilePath = str
