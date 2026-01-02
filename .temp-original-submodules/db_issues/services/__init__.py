"""Services layer for db-issues module.

Provides business logic services for issue management, search, import/export,
dependency analysis, and label management.
"""

from dot_work.db_issues.services.bulk_service import BulkResult, BulkService, IssueInputData
from dot_work.db_issues.services.comment_service import CommentService
from dot_work.db_issues.services.dependency_service import (
    BlockedIssue,
    CycleResult,
    DependencyService,
    ImpactResult,
    ReadyResult,
)
from dot_work.db_issues.services.duplicate_service import (
    DuplicateDetectionResult,
    DuplicateGroup,
    DuplicateService,
    JaccardDuplicateDetector,
)
from dot_work.db_issues.services.epic_service import EpicInfo, EpicService, EpicTreeItem
from dot_work.db_issues.services.issue_service import IssueService
from dot_work.db_issues.services.json_template_service import JsonTemplateService, TemplateInfo
from dot_work.db_issues.services.jsonl_service import JsonlService
from dot_work.db_issues.services.label_service import (
    NAMED_COLORS,
    LabelInfo,
    LabelService,
    get_terminal_color_code,
    parse_color,
)
from dot_work.db_issues.services.project_service import ProjectService, ProjectStatus
from dot_work.db_issues.services.search_service import SearchResult, SearchService
from dot_work.db_issues.services.stats_service import (
    IssueMetrics,
    PriorityStats,
    Statistics,
    StatsService,
    StatusStats,
    TypeStats,
)
from dot_work.db_issues.services.template_service import TemplateApplicationResult, TemplateService

__all__ = [
    "IssueService",
    "EpicService",
    "EpicInfo",
    "EpicTreeItem",
    "JsonlService",
    "SearchService",
    "SearchResult",
    "DependencyService",
    "CycleResult",
    "ImpactResult",
    "BlockedIssue",
    "ReadyResult",
    "LabelService",
    "LabelInfo",
    "CommentService",
    "JsonTemplateService",
    "TemplateInfo",
    "TemplateService",
    "TemplateApplicationResult",
    "BulkService",
    "BulkResult",
    "IssueInputData",
    "parse_color",
    "get_terminal_color_code",
    "NAMED_COLORS",
    "DuplicateService",
    "DuplicateGroup",
    "DuplicateDetectionResult",
    "JaccardDuplicateDetector",
    "StatsService",
    "Statistics",
    "StatusStats",
    "PriorityStats",
    "TypeStats",
    "IssueMetrics",
    "ProjectService",
    "ProjectStatus",
]
