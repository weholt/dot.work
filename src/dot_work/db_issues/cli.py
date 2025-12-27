"""CLI commands for db-issues module using Typer.

Provides basic command-line interface for issue tracking operations.

Source: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/src/issue_tracker/
"""

import csv
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import Literal, cast

import typer
from rich.console import Console
from rich.table import Table

from dot_work.db_issues.adapters import UnitOfWork, create_db_engine
from dot_work.db_issues.config import get_db_url, is_debug_mode
from dot_work.db_issues.domain.entities import (
    Clock,
    Dependency,
    DependencyType,
    EpicStatus,
    IdentifierService,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
    ProjectStatus,
)
from dot_work.db_issues.services import (
    BulkResult,
    BulkService,
    CommentService,
    CycleResult,
    DependencyService,
    DuplicateService,
    EpicService,
    ImpactResult,
    IssueService,
    JsonlService,
    JsonTemplateService,
    LabelService,
    ProjectService,
    SearchService,
    Statistics,
    StatsService,
    TemplateService,
)
from dot_work.db_issues.templates import TemplateManager

app = typer.Typer(
    name="db-issues",
    help="Database-backed issue tracking for dot-work",
    add_completion=False,
)
console = Console()

# Epic commands subgroup
epic_app = typer.Typer(
    name="epic",
    help="Epic management commands",
    add_completion=False,
)
app.add_typer(epic_app, name="epic")

# Project management commands subgroup
project_app = typer.Typer(
    name="project",
    help="Project management commands",
    add_completion=False,
)
app.add_typer(project_app, name="project")

# Child relationship commands subgroup
child_app = typer.Typer(
    name="child",
    help="Child epic relationship management commands",
    add_completion=False,
)
app.add_typer(child_app, name="child")

# Import/Export commands subgroup
io_app = typer.Typer(
    name="io",
    help="Import/export commands for issues",
    add_completion=False,
)
app.add_typer(io_app, name="io")

# Dependency analysis commands subgroup
deps_app = typer.Typer(
    name="deps",
    help="Dependency analysis and cycle detection commands",
    add_completion=False,
)
app.add_typer(deps_app, name="deps")

# Label management commands subgroup
labels_app = typer.Typer(
    name="labels",
    help="Label management with colors",
    add_completion=False,
)
app.add_typer(labels_app, name="labels")

# Comment management commands subgroup
comments_app = typer.Typer(
    name="comments",
    help="Comment management commands",
    add_completion=False,
)
app.add_typer(comments_app, name="comments")

# Instruction templates commands subgroup
instructions_app = typer.Typer(
    name="instructions",
    help="Instruction template management commands",
    add_completion=False,
)
app.add_typer(instructions_app, name="instructions")

# Template management commands subgroup
template_app = typer.Typer(
    name="template",
    help="JSON issue template management commands",
    add_completion=False,
)
app.add_typer(template_app, name="template")

# Bulk operations commands subgroup
bulk_app = typer.Typer(
    name="bulk",
    help="Bulk operations for batch issue management",
    add_completion=False,
)
app.add_typer(bulk_app, name="bulk")

# Search index management commands subgroup
search_index_app = typer.Typer(
    name="search-index",
    help="Full-text search index management commands",
    add_completion=False,
)
app.add_typer(search_index_app, name="search-index")


# =============================================================================
# Service Implementations (for Dependency Injection)
# =============================================================================


class DefaultClock(Clock):
    """Default time provider using system time."""

    def now(self) -> datetime:
        """Get current UTC datetime as naive datetime."""
        return datetime.now(UTC).replace(tzinfo=None)


class DefaultIdentifierService(IdentifierService):
    """Default ID generator using random hex strings."""

    import random

    def generate(self, prefix: str = "issue") -> str:
        """Generate a new unique identifier.

        Args:
            prefix: Entity type prefix (e.g., "issue", "comment")

        Returns:
            New identifier with format prefix-XXXXXX (6 hex chars)
        """
        suffix = "".join(self.random.choices("0123456789abcdef", k=6))
        return f"{prefix}-{suffix}"


# =============================================================================
# CLI Commands
# =============================================================================


@app.command()
def create(
    title: str = typer.Argument(..., help="Issue title"),
    description: str = typer.Option("", "--description", "-d", help="Issue description"),
    priority: str = typer.Option(
        "medium", "--priority", "-p", help="Priority (critical, high, medium, low, backlog)"
    ),
    type_: str = typer.Option(
        "task", "--type", "-t", help="Issue type (task, bug, feature, epic, chore)"
    ),
    assignee: str | None = typer.Option(None, "--assignee", "-a", help="Assignee username"),
    labels: list[str] | None = typer.Option(None, "--label", "-l", help="Labels to add"),  # noqa: B008
    project: str = typer.Option("default", "--project", "-P", help="Project ID"),
) -> None:
    """Create a new issue."""
    # Parse priority
    try:
        issue_priority = IssuePriority[priority.upper()]
    except KeyError:
        console.print(f"[red]Invalid priority: {priority}[/red]")
        console.print("Valid options: critical, high, medium, low, backlog")
        raise typer.Exit(1) from None

    # Parse issue type
    try:
        issue_type = IssueType[type_.upper()]
    except KeyError:
        console.print(f"[red]Invalid type: {type_}[/red]")
        console.print("Valid options: task, bug, feature, epic, chore")
        raise typer.Exit(1) from None

    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        try:
            issue = service.create_issue(
                title=title,
                description=description,
                priority=issue_priority,
                issue_type=issue_type,
                assignee=assignee,
                labels=labels or [],
                project_id=project,
            )
            console.print(f"[green]✓[/green] Issue created: [bold]{issue.id}[/bold]")
            console.print(f"  Title: {issue.title}")
            console.print(f"  Status: {issue.status.value}")
            console.print(f"  Priority: {issue.priority.value}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@app.command()
def list_cmd(  # noqa: B008
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),
    priority: str | None = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    assignee: str | None = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
    project: str | None = typer.Option(None, "--project", "-P", help="Filter by project ID"),
    include_backlog: bool = typer.Option(False, "--include-backlog", help="Include backlog priority issues"),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum number of issues"),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, jsonl, csv, markdown"
    ),
    fields: str | None = typer.Option(None, "--fields", help="Comma-separated fields to display"),
    sort: str | None = typer.Option(None, "--sort", help="Field to sort by"),
    order: str = typer.Option("asc", "--order", help="Sort order: asc, desc"),
) -> None:
    """List issues with optional filtering and multiple output formats."""
    # Parse sort order
    reverse_order = order.lower() == "desc"

    # Parse filters
    status_filter = IssueStatus(status) if status else None
    priority_filter = IssuePriority[priority.upper()] if priority else None

    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        issues = service.list_issues(
            status=status_filter,
            priority=priority_filter,
            assignee=assignee,
            project_id=project,
            limit=limit,
            exclude_backlog=not include_backlog,
        )

        if not issues:
            if format == "table":
                console.print("[yellow]No issues found[/yellow]")
            else:
                console.print("")  # Empty output for machine-readable formats
            return

        # Apply sorting
        if sort:
            issues = _sort_issues(issues, sort, reverse_order)

        # Format-specific output
        if format == "json":
            _output_json(issues, fields, console)
        elif format == "jsonl":
            _output_jsonl(issues, fields, console)
        elif format == "csv":
            _output_csv(issues, fields, console)
        elif format == "markdown":
            _output_markdown(issues, fields, console)
        else:  # table (default)
            _output_table(issues, fields, console)


@app.command()
def search_cmd(  # noqa: B008
    query: str = typer.Argument(..., help="Search query text"),
    in_fields: str | None = typer.Option(
        None,
        "--in",
        help="Fields to search: title, description, labels, comments (comma-separated)",
    ),
    match: str = typer.Option(
        "all", "--match", help="Match mode: 'all' (AND) or 'any' (OR) for multiple terms"
    ),
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),
    priority: str | None = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    type_filter: str | None = typer.Option(None, "--type", "-t", help="Filter by type"),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum number of results"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, jsonl"),
) -> None:
    """Search issues with field filtering and multiple output formats."""
    # Parse match mode
    match_any = match.lower() == "any"

    # Parse filters
    status_filter = IssueStatus(status) if status else None
    priority_filter = IssuePriority[priority.upper()] if priority else None
    type_filter_enum = IssueType[type_filter.upper()] if type_filter else None

    # Parse field list
    search_fields = []
    if in_fields:
        search_fields = [f.strip().lower() for f in in_fields.split(",")]
        # Validate fields
        valid_fields = {"title", "description", "labels", "comments"}
        for field in search_fields:
            if field not in valid_fields:
                console.print(f"[red]Invalid field: {field}[/red]")
                console.print(f"Valid fields: {', '.join(sorted(valid_fields))}")
                raise typer.Exit(1)

    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)

        # Build search query based on options
        search_query = query

        # Handle match mode for multiple terms
        terms = query.split()
        if len(terms) > 1:
            if match_any:
                search_query = " OR ".join(terms)
            else:  # match all (AND)
                search_query = " ".join(terms)

        # Add field-specific search
        if search_fields:
            field_queries = []
            for field in search_fields:
                if field == "title":
                    field_queries.append(f"title:{search_query}")
                elif field == "description":
                    field_queries.append(f"description:{search_query}")
                elif field == "labels":
                    field_queries.append(f"labels:{search_query}")
                elif field == "comments":
                    # Comments not indexed yet, search full text
                    field_queries.append(search_query)

            if len(field_queries) == 1:
                search_query = field_queries[0]
            elif match_any:
                search_query = f"({' OR '.join(field_queries)})"
            else:  # match all (AND)
                search_query = f"({' AND '.join(field_queries)})"

        # Perform search
        search_service = SearchService(session)
        results = search_service.search(search_query, limit=limit, include_closed=True)

        if not results:
            if format == "table":
                console.print("[yellow]No results found[/yellow]")
            else:
                console.print("")
            return

        # Get full issue objects for results
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        issues = []
        for result in results:
            issue = issue_service.get_issue(result.issue_id)
            if issue:
                # Apply filters
                if status_filter and issue.status != status_filter:
                    continue
                if priority_filter and issue.priority != priority_filter:
                    continue
                if type_filter_enum and issue.type != type_filter_enum:
                    continue
                issues.append((issue, result.rank, result.snippet))

        if not issues:
            if format == "table":
                console.print("[yellow]No results found after filtering[/yellow]")
            else:
                console.print("")
            return

        # Format-specific output
        if format == "json":
            _output_search_json(issues, console)
        elif format == "jsonl":
            _output_search_jsonl(issues, console)
        else:  # table (default)
            _output_search_table(issues, console)


@app.command()
def ready(
    priority: str | None = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    sort: str | None = typer.Option(None, "--sort", help="Sort by field: id, title, priority, status"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
) -> None:
    """Show issues ready to work on (no blocking dependencies).

    Ready issues are those that:
    - Have status "proposed" or "in-progress"
    - Are not in "blocked" status
    - Have no open "blocks" dependencies pointing to them

    Also shows blocked issues separately with their blocking reasons.
    """
    # Parse priority filter (comma-separated)
    priority_filter: list[IssuePriority] | None = None
    if priority:
        priority_filter = []
        for p in priority.split(","):
            p = p.strip().upper()
            try:
                priority_filter.append(IssuePriority[p])
            except KeyError:
                console.print(f"[red]Invalid priority: {p}[/red]")
                console.print("Valid priorities: critical, high, medium, low")
                raise typer.Exit(1)

    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)
        dep_service = DependencyService(uow)

        # Get ready queue
        ready_result = dep_service.get_ready_queue()

        # Get full issue objects for ready issues
        ready_issues = []
        for issue_id in ready_result.ready_issues:
            issue = issue_service.get_issue(issue_id)
            if issue:
                # Apply priority filter
                if priority_filter and issue.priority not in priority_filter:
                    continue
                ready_issues.append(issue)

        # Get full issue objects for blocked issues
        blocked_with_info: list[tuple[Issue, list[str]]] = []
        for blocked in ready_result.blocked_issues:
            issue = issue_service.get_issue(blocked.issue_id)
            if issue:
                # Apply priority filter to blocked issues too
                if priority_filter and issue.priority not in priority_filter:
                    continue
                blocked_with_info.append((issue, blocked.blockers))

        # Apply sorting
        reverse_order = False
        if sort:
            # For priority, we want ascending (critical first)
            # For other fields, ascending is default
            reverse_order = sort.lower() not in ("priority", "created", "updated")
            ready_issues = _sort_issues(ready_issues, sort, reverse_order)

        # Format output
        if format == "json":
            _output_ready_json(ready_issues, blocked_with_info, console)
        else:  # table (default)
            _output_ready_table(ready_issues, blocked_with_info, console)


# =============================================================================
# Output Formatters
# =============================================================================


def _sort_issues(issues: list[Issue], sort_field: str, reverse: bool) -> list[Issue]:
    """Sort issues by the specified field.

    Args:
        issues: List of issues to sort
        sort_field: Field name to sort by
        reverse: Whether to sort in descending order

    Returns:
        Sorted list of issues
    """
    sort_key = {
        "id": lambda i: i.id,
        "title": lambda i: i.title.lower(),
        "status": lambda i: i.status.value,
        "priority": lambda i: i.priority.value,
        "type": lambda i: i.type.value,
        "assignee": lambda i: i.assignee or "",
        "created": lambda i: i.created_at,
        "updated": lambda i: i.updated_at,
    }.get(sort_field.lower())

    if sort_key is None:
        return issues

    return sorted(issues, key=sort_key, reverse=reverse)


def _get_field_value(issue: Issue, field: str) -> str:
    """Get a formatted field value from an issue.

    Args:
        issue: Issue entity
        field: Field name

    Returns:
        Formatted field value as string
    """
    field_map = {
        "id": issue.id,
        "title": issue.title,
        "description": issue.description or "",
        "status": issue.status.value,
        "priority": str(issue.priority.value),
        "type": issue.type.value,
        "assignee": issue.assignee or "",
        "epic_id": issue.epic_id or "",
        "labels": ",".join(issue.labels) if issue.labels else "",
        "created_at": issue.created_at.isoformat() if issue.created_at else "",
        "updated_at": issue.updated_at.isoformat() if issue.updated_at else "",
        "closed_at": issue.closed_at.isoformat() if issue.closed_at else "",
    }
    return str(field_map.get(field, ""))


def _parse_fields(fields_str: str | None) -> list[str] | None:
    """Parse comma-separated fields string.

    Args:
        fields_str: Comma-separated field names

    Returns:
        List of field names, or None for all fields
    """
    if not fields_str:
        return None
    return [f.strip() for f in fields_str.split(",") if f.strip()]


def _output_table(issues: list[Issue], fields: str | None, console: Console) -> None:
    """Output issues as a Rich table.

    Args:
        issues: List of issues to output
        fields: Optional comma-separated field names
        console: Rich console for output
    """
    field_list = _parse_fields(fields)
    if field_list:
        # Custom fields
        table = Table(title=f"Issues ({len(issues)} found)")
        for field in field_list:
            table.add_column(field.capitalize().replace("_", " "))
        for issue in issues:
            row = [_get_field_value(issue, f) for f in field_list]
            table.add_row(*row)
    else:
        # Default table format
        table = Table(title=f"Issues ({len(issues)} found)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Status", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Type", style="blue")
        table.add_column("Assignee", style="magenta")

        for issue in issues:
            table.add_row(
                issue.id,
                issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
                issue.status.value,
                str(issue.priority.value),
                issue.type.value,
                issue.assignee or "-",
            )

    console.print(table)


def _output_json(issues: list[Issue], fields: str | None, console: Console) -> None:
    """Output issues as JSON array with wrapper metadata.

    Args:
        issues: List of issues to output
        fields: Optional comma-separated field names
        console: Rich console for output
    """
    field_list = _parse_fields(fields)
    issue_list: list[dict[str, object]] = []

    for issue in issues:
        if field_list:
            # Custom fields - use string values
            data_dict: dict[str, object] = {f: _get_field_value(issue, f) for f in field_list}
        else:
            # All fields - use proper types
            data_dict = {
                "id": issue.id,
                "project_id": issue.project_id,
                "title": issue.title,
                "description": issue.description or "",
                "status": issue.status.value,
                "priority": issue.priority.value,
                "type": issue.type.value,
                "assignees": issue.assignees,
                "epic_id": issue.epic_id,
                "labels": issue.labels,
                "blocked_reason": issue.blocked_reason,
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            }
        issue_list.append(data_dict)

    # Wrap with metadata
    wrapper: dict[str, object] = {
        "command": "list",
        "issues": issue_list,
        "total": len(issue_list),
        "filtered": len(issue_list),
    }
    console.print(json.dumps(wrapper, indent=2))


def _output_jsonl(issues: list[Issue], fields: str | None, console: Console) -> None:
    """Output issues as JSONL (one JSON object per line).

    Args:
        issues: List of issues to output
        fields: Optional comma-separated field names
        console: Rich console for output
    """
    field_list = _parse_fields(fields)

    for issue in issues:
        if field_list:
            # Custom fields - use string values
            data_dict: dict[str, object] = {f: _get_field_value(issue, f) for f in field_list}
        else:
            # All fields - use proper types
            data_dict = {
                "id": issue.id,
                "title": issue.title,
                "description": issue.description or "",
                "status": issue.status.value,
                "priority": issue.priority.value,
                "type": issue.type.value,
                "assignee": issue.assignee,
                "epic_id": issue.epic_id,
                "labels": issue.labels,
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            }
        console.print(json.dumps(data_dict, separators=(",", ":")))


def _output_csv(issues: list[Issue], fields: str | None, console: Console) -> None:
    """Output issues as CSV.

    Args:
        issues: List of issues to output
        fields: Optional comma-separated field names
        console: Rich console for output
    """
    field_list = _parse_fields(fields) or [
        "id",
        "title",
        "status",
        "priority",
        "type",
        "assignee",
    ]

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=field_list)
    writer.writeheader()

    for issue in issues:
        row = {f: _get_field_value(issue, f) for f in field_list}
        writer.writerow(row)

    console.print(output.getvalue().rstrip())


def _output_markdown(issues: list[Issue], fields: str | None, console: Console) -> None:
    """Output issues as Markdown table.

    Args:
        issues: List of issues to output
        fields: Optional comma-separated field names
        console: Rich console for output
    """
    field_list = _parse_fields(fields) or [
        "ID",
        "Title",
        "Status",
        "Priority",
        "Type",
        "Assignee",
    ]

    # Create header row
    header = "| " + " | ".join(f.capitalize() for f in field_list) + " |"
    separator = "|" + "|".join(["---" for _ in field_list]) + "|"

    console.print(header)
    console.print(separator)

    # Create data rows
    for issue in issues:
        row = "| " + " | ".join(_get_field_value(issue, f.lower()) for f in field_list) + " |"
        console.print(row)


def _output_show_json(issue: Issue, console: Console) -> None:
    """Output a single issue as JSON with wrapper metadata.

    Args:
        issue: Issue to output
        console: Rich console for output
    """
    data_dict: dict[str, object] = {
        "command": "show",
        "issue": {
            "id": issue.id,
            "project_id": issue.project_id,
            "title": issue.title,
            "description": issue.description or "",
            "status": issue.status.value,
            "priority": issue.priority.value,
            "type": issue.type.value,
            "assignees": issue.assignees,
            "epic_id": issue.epic_id,
            "labels": issue.labels,
            "blocked_reason": issue.blocked_reason,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
        },
    }
    console.print(json.dumps(data_dict, indent=2))


# =============================================================================
# Search Output Formatters
# =============================================================================


def _output_search_table(issues: list[tuple[Issue, float, str]], console: Console) -> None:
    """Output search results as a formatted table with rank and snippet.

    Args:
        issues: List of (issue, rank, snippet) tuples
        console: Rich console for output
    """
    table = Table(title="Search Results", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="cyan", width=16)
    table.add_column("Title", style="white")
    table.add_column("Status", width=12)
    table.add_column("Rank", width=8, justify="right")
    table.add_column("Snippet", style="dim")

    for issue, rank, snippet in issues:
        # Strip HTML-like <mark> tags from snippet for display
        clean_snippet = snippet.replace("<mark>", "[bold cyan]").replace("</mark>", "[/bold cyan]")
        table.add_row(
            issue.id,
            issue.title,
            issue.status.value,
            f"{rank:.2f}",
            clean_snippet[:80] + "..." if len(clean_snippet) > 80 else clean_snippet,
        )

    console.print(table)


def _output_search_json(issues: list[tuple[Issue, float, str]], console: Console) -> None:
    """Output search results as JSON with wrapper metadata.

    Args:
        issues: List of (issue, rank, snippet) tuples
        console: Rich console for output
    """
    results = []
    for issue, rank, snippet in issues:
        data_dict: dict[str, object] = {
            "id": issue.id,
            "project_id": issue.project_id,
            "title": issue.title,
            "description": issue.description or "",
            "status": issue.status.value,
            "priority": issue.priority.value,
            "type": issue.type.value,
            "assignees": issue.assignees,
            "epic_id": issue.epic_id,
            "labels": issue.labels,
            "blocked_reason": issue.blocked_reason,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            "search_rank": rank,
            "snippet": snippet.replace("<mark>", "").replace("</mark>", ""),
        }
        results.append(data_dict)

    # Wrap with metadata
    wrapper: dict[str, object] = {
        "command": "search",
        "results": results,
        "total": len(results),
        "filtered": len(results),
    }
    console.print(json.dumps(wrapper, indent=2))


def _output_search_jsonl(issues: list[tuple[Issue, float, str]], console: Console) -> None:
    """Output search results as JSONL.

    Args:
        issues: List of (issue, rank, snippet) tuples
        console: Rich console for output
    """
    for issue, rank, snippet in issues:
        data_dict: dict[str, object] = {
            "id": issue.id,
            "title": issue.title,
            "description": issue.description or "",
            "status": issue.status.value,
            "priority": issue.priority.value,
            "type": issue.type.value,
            "assignee": issue.assignee,
            "epic_id": issue.epic_id,
            "labels": issue.labels,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            "search_rank": rank,
            "snippet": snippet.replace("<mark>", "").replace("</mark>", ""),
        }
        console.print(json.dumps(data_dict, separators=(",", ":")))


def _output_ready_table(
    ready_issues: list[Issue],
    blocked_with_info: list[tuple[Issue, list[str]]],
    console: Console,
) -> None:
    """Output ready queue as a table.

    Args:
        ready_issues: List of ready issues
        blocked_with_info: List of (issue, blockers) tuples
        console: Rich console for output
    """
    # Print ready issues
    if ready_issues:
        console.print(f"[bold green]Ready to work on ({len(ready_issues)} issues):[/bold green]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Title", style="white", width=40)
        table.add_column("Priority", style="yellow", width=10)
        table.add_column("Status", style="green", width=12)

        for issue in ready_issues:
            table.add_row(
                issue.id,
                issue.title[:37] + "..." if len(issue.title) > 37 else issue.title,
                issue.priority.value,
                issue.status.value,
            )
        console.print(table)
    else:
        console.print("[yellow]No ready issues found[/yellow]")

    # Print blocked issues
    if blocked_with_info:
        console.print(f"\n[bold red]Blocked issues ({len(blocked_with_info)}):[/bold red]")
        for issue, blockers in blocked_with_info:
            blockers_str = ", ".join(blockers)
            console.print(
                f"  {issue.id} [red]{issue.title[:40]}[/red] "
                f"- [yellow]blocked by {blockers_str}[/yellow]"
            )


def _output_ready_json(
    ready_issues: list[Issue],
    blocked_with_info: list[tuple[Issue, list[str]]],
    console: Console,
) -> None:
    """Output ready queue as JSON.

    Args:
        ready_issues: List of ready issues
        blocked_with_info: List of (issue, blockers) tuples
        console: Rich console for output
    """
    ready_data = [
        {
            "id": issue.id,
            "title": issue.title,
            "description": issue.description or "",
            "status": issue.status.value,
            "priority": issue.priority.value,
            "type": issue.type.value,
            "assignee": issue.assignee,
            "epic_id": issue.epic_id,
            "labels": issue.labels,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
        }
        for issue in ready_issues
    ]

    blocked_data = [
        {
            "id": issue.id,
            "title": issue.title,
            "status": issue.status.value,
            "priority": issue.priority.value,
            "blockers": blockers,
        }
        for issue, blockers in blocked_with_info
    ]

    output = {
        "ready_issues": ready_data,
        "ready_count": len(ready_data),
        "blocked_issues": blocked_data,
        "blocked_count": len(blocked_data),
    }

    console.print(json.dumps(output, indent=2))


@app.command()
def show(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
) -> None:
    """Show issue details."""
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        issue = service.get_issue(issue_id)
        if not issue:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        if format == "json":
            _output_show_json(issue, console)
        else:
            # Display issue details
            console.print(f"[bold cyan]Issue:[/bold cyan] {issue.id}")
            console.print(f"[bold]Title:[/bold] {issue.title}")
            console.print(f"[bold]Status:[/bold] {issue.status.value}")
            console.print(f"[bold]Priority:[/bold] {issue.priority.value}")
            console.print(f"[bold]Type:[/bold] {issue.type.value}")
            console.print(f"[bold]Assignee:[/bold] {issue.assignee or 'Unassigned'}")
            if issue.labels:
                console.print(f"[bold]Labels:[/bold] {', '.join(issue.labels)}")
            console.print("[bold]Description:[/bold]")
            console.print(issue.description or "No description")
            console.print(f"\n[bold]Created:[/bold] {issue.created_at}")
            console.print(f"[bold]Updated:[/bold] {issue.updated_at}")


@app.command()
def update(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    title: str | None = typer.Option(None, "--title", "-t", help="New title"),
    description: str | None = typer.Option(None, "--description", "-d", help="New description"),
    priority: str | None = typer.Option(None, "--priority", "-p", help="New priority"),
    assignee: str | None = typer.Option(None, "--assignee", "-a", help="New assignee"),
    status: str | None = typer.Option(None, "--status", "-s", help="New status"),
    type: str | None = typer.Option(None, "--type", "-T", help="New issue type"),
) -> None:
    """Update issue fields.

    Supports updating title, description, priority, assignee, status, and type.
    Status transitions are validated according to the issue workflow rules.
    """
    from dot_work.db_issues.domain.entities import InvalidTransitionError

    # Parse priority
    priority_filter = IssuePriority[priority.upper()] if priority else None

    # Parse status
    status_filter = None
    if status:
        status_upper = status.upper().replace("-", "_").replace(" ", "_")
        status_filter = IssueStatus[status_upper]

    # Parse type
    type_filter = None
    if type:
        type_upper = type.upper()
        type_filter = IssueType[type_upper]

    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        try:
            issue = service.update_issue(
                issue_id=issue_id,
                title=title,
                description=description,
                priority=priority_filter,
                assignee=assignee,
                status=status_filter,
                type=type_filter,
            )
        except InvalidTransitionError as e:
            console.print(f"[red]Invalid status transition: {e}[/red]")
            raise typer.Exit(1) from e

        if not issue:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Issue updated: [bold]{issue.id}[/bold]")


# =============================================================================
# Editor Integration
# =============================================================================


def _generate_issue_template(issue: Issue) -> str:
    """Generate YAML template for issue editing.

    Args:
        issue: Issue entity

    Returns:
        YAML string with issue fields
    """
    lines = [
        "# dot-work db-issues edit",
        "# Edit the fields below. Save and exit to apply changes.",
        "#",
        "# Valid values for status:",
        "#   proposed, in-progress, blocked, completed, wont-fix",
        "#",
        "# Valid values for priority:",
        "#   critical, high, medium, low",
        "#",
        "# Valid values for type:",
        "#   bug, feature, task, enhancement, refactor, docs, test, security, performance",
        "#",
        "",
        f"id: {issue.id}",
        f"title: {issue.title}",
        "description: |",
        "  " + (issue.description or "No description").replace("\n", "\n  "),
        f"priority: {issue.priority.name.lower()}",
        f"status: {issue.status.value}",
        f"type: {issue.type.value}",
        f"assignee: {issue.assignee or ''}",
    ]
    if issue.labels:
        lines.append(f"labels: {', '.join(issue.labels)}")
    return "\n".join(lines)


def _parse_edited_issue(content: str, original: Issue) -> dict:
    """Parse edited issue content from YAML.

    Args:
        content: Edited YAML content
        original: Original issue for defaults

    Returns:
        Dictionary with parsed field values
    """
    import yaml

    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError("Invalid YAML format")

    result = {}

    if "title" in data and data["title"] != original.title:
        result["title"] = data["title"]

    if "description" in data:
        desc = data["description"]
        if isinstance(desc, str) and desc != original.description:
            result["description"] = desc
        elif isinstance(desc, list):
            # Handle YAML multi-line format
            joined = "\n".join(desc)
            if joined != original.description:
                result["description"] = joined

    if "priority" in data:
        try:
            priority = IssuePriority[data["priority"].upper()]
            if priority != original.priority:
                result["priority"] = priority
        except KeyError:
            pass  # Invalid priority, skip

    if "status" in data:
        status_str = data["status"].upper().replace("-", "_")
        try:
            status = IssueStatus[status_str]
            if status != original.status:
                result["status"] = status
        except KeyError:
            pass  # Invalid status, skip

    if "type" in data:
        try:
            type_val = IssueType[data["type"].upper()]
            if type_val != original.type:
                result["type"] = type_val
        except KeyError:
            pass  # Invalid type, skip

    if "assignee" in data:
        assignee = data["assignee"]
        if assignee != original.assignee:
            result["assignee"] = assignee if assignee else None

    return result


# Whitelist of allowed editors to prevent command injection
# Users can add to this list if they need other editors
_ALLOWED_EDITORS = {
    "vi", "vim", "nvim", "neovim",
    "emacs", "emacsclient",
    "nano",
    "code", "code-server", "codium",
    "subl", "sublime_text",
    "atom", "mate",
    "kak", "micro", "xed",
    "gedit", "kate", "geany",
}


def _validate_editor(editor_cmd: str | None) -> tuple[str, list[str]]:
    """Validate editor command and return (executable, args).

    Enforces a whitelist of allowed editors to prevent command injection
    via unvalidated editor commands from CLI arguments, environment
    variables, or user prompts.

    Args:
        editor_cmd: Editor command string (e.g., "code", "vim", "code --wait")

    Returns:
        Tuple of (executable_name, additional_args)

    Raises:
        ValueError: If editor is not in the allowed whitelist or contains
            shell metacharacters (command injection attempt)

    Examples:
        >>> _validate_editor("vim")
        ('vim', [])
        >>> _validate_editor("code --wait")
        ('code', ['--wait'])
        >>> _validate_editor("nano")
        ('nano', [])
    """
    # Shell metacharacters that indicate command injection attempts
    _SHELL_METACHARACTERS = set(";|&`$()<>{}[]'\"'")

    if not editor_cmd:
        editor_cmd = os.environ.get("EDITOR", "vi")

    # Check for shell metacharacters (command injection)
    if any(char in editor_cmd for char in _SHELL_METACHARACTERS):
        raise ValueError(
            f"Editor command contains invalid characters: {editor_cmd!r}. "
            f"Only the editor name and arguments are allowed."
        )

    parts = editor_cmd.strip().split()
    if not parts or not parts[0]:
        editor_cmd = "vi"
        parts = ["vi"]

    executable = parts[0]

    # Extract base name (remove path)
    base_name = Path(executable).name

    if base_name not in _ALLOWED_EDITORS:
        allowed_list = ", ".join(sorted(_ALLOWED_EDITORS))
        raise ValueError(
            f"Editor '{executable}' is not allowed. "
            f"Allowed editors: {allowed_list}. "
            f"Set the EDITOR environment variable or use --editor option."
        )

    # Special handling for VS Code to ensure it blocks
    if base_name in ("code", "code-server", "codium") and "--wait" not in parts:
        parts.insert(1, "--wait")

    return base_name, parts[1:]


def _get_text_from_editor(template: str = "") -> str:
    """Open editor and get text input from user.

    Args:
        template: Initial text to display in editor

    Returns:
        Text content from editor (with comment lines removed)
    """
    # Determine and validate editor
    editor_name, editor_args = _validate_editor(os.environ.get("EDITOR"))

    # Create temp file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        prefix="db-issues-editor-",
        delete=False,
    ) as f:
        f.write(template)
        temp_path = Path(f.name)

    # Set restrictive permissions (owner read/write only) for security
    temp_path.chmod(0o600)

    try:
        # Open editor
        console.print(f"Opening [cyan]{editor_name}[/cyan]...")
        result = subprocess.run([editor_name, *editor_args, str(temp_path)])

        if result.returncode != 0:
            console.print(f"[red]Editor exited with error code {result.returncode}[/red]")
            raise typer.Exit(1)

        # Read edited content
        edited_content = temp_path.read_text()

        # Remove comment lines (lines starting with #)
        lines = []
        for line in edited_content.splitlines():
            if not line.strip().startswith("#"):
                lines.append(line)

        return "\n".join(lines).strip()

    finally:
        # Clean up temp file
        try:
            temp_path.unlink()
        except Exception:
            pass


@app.command()
def edit(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    editor: str | None = typer.Option(
        None, "--editor", "-e", help="Editor command (default: $EDITOR or vi)"
    ),
) -> None:
    """Edit issue using external editor.

    Opens the issue in a text editor for editing. Changes are applied when you save and exit.
    If the file is unchanged, no update is performed.
    """
    from dot_work.db_issues.domain.entities import InvalidTransitionError

    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        issue = service.get_issue(issue_id)
        if not issue:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        # Determine and validate editor
        editor_name, editor_args = _validate_editor(editor)

        # Generate template
        template = _generate_issue_template(issue)

        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            prefix="db-issues-edit-",
            delete=False,
        ) as f:
            f.write(template)
            temp_path = Path(f.name)

        # Set restrictive permissions (owner read/write only) for security
        temp_path.chmod(0o600)

        try:
            # Open editor
            console.print(f"Opening [cyan]{editor_name}[/cyan] to edit issue [bold]{issue.id}[/bold]...")
            result = subprocess.run([editor_name, *editor_args, str(temp_path)])

            if result.returncode != 0:
                console.print(f"[red]Editor exited with error code {result.returncode}[/red]")
                raise typer.Exit(1)

            # Read edited content
            edited_content = temp_path.read_text()

            # Parse changes
            changes = _parse_edited_issue(edited_content, issue)

            if not changes:
                console.print("[yellow]No changes detected.[/yellow]")
                return

            # Apply changes
            console.print("Applying changes:")
            for key, value in changes.items():
                if isinstance(value, Enum):
                    console.print(f"  {key}: {value.value}")
                else:
                    console.print(f"  {key}: {value}")

            updated = service.update_issue(
                issue_id=issue_id,
                title=changes.get("title"),
                description=changes.get("description"),
                priority=changes.get("priority"),
                assignee=changes.get("assignee"),
                status=changes.get("status"),
                type=changes.get("type"),
            )

            console.print(
                f"[green]✓[/green] Issue updated: [bold]{updated.id if updated else 'unknown'}[/bold]"
            )

        except InvalidTransitionError as e:
            console.print(f"[red]Invalid status transition: {e}[/red]")
            console.print("[yellow]Issue was not updated.[/yellow]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error editing issue: {e}[/red]")
            raise typer.Exit(1)
        finally:
            # Clean up temp file
            try:
                temp_path.unlink()
            except Exception:
                pass


@app.command()
def close(
    issue_id: str = typer.Argument(..., help="Issue ID"),
) -> None:
    """Close an issue."""
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        issue = service.close_issue(issue_id)
        if not issue:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Issue closed: [bold]{issue.id}[/bold]")


@app.command()
def start(
    issue_id: str = typer.Argument(..., help="Issue ID"),
) -> None:
    """Start an issue (proposed → in-progress)."""
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        issue = service.transition_issue(issue_id, IssueStatus.IN_PROGRESS)
        if not issue:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Issue started: [bold]{issue.id}[/bold]")


@app.command()
def reopen(
    issue_id: str = typer.Argument(..., help="Issue ID"),
) -> None:
    """Reopen a completed issue (completed → proposed)."""
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        issue = service.reopen_issue(issue_id)
        if not issue:
            console.print(f"[red]Issue not found or cannot be reopened: {issue_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Issue reopened: [bold]{issue.id}[/bold]")


@app.command()
def resolve(
    issue_id: str = typer.Argument(..., help="Issue ID"),
) -> None:
    """Mark an issue as resolved."""
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        issue = service.transition_issue(issue_id, IssueStatus.RESOLVED)
        if not issue:
            console.print(f"[red]Issue not found or cannot be resolved: {issue_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Issue resolved: [bold]{issue.id}[/bold]")


@app.command()
def blocked(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    reason: str | None = typer.Option(None, "--reason", "-r", help="Reason for blocking"),
) -> None:
    """Mark an issue as blocked with an optional reason."""
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        issue = service.block_issue(issue_id, reason)
        if not issue:
            console.print(f"[red]Issue not found or cannot be blocked: {issue_id}[/red]")
            raise typer.Exit(1)

        if reason:
            console.print(f"[green]✓[/green] Issue blocked: [bold]{issue.id}[/bold] - {reason}")
        else:
            console.print(f"[green]✓[/green] Issue blocked: [bold]{issue.id}[/bold]")


@app.command()
def stale(
    issue_id: str | None = typer.Argument(None, help="Issue ID to mark as stale"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Auto-detect stale issues"),
    days: int = typer.Option(30, "--days", "-d", help="Days of inactivity for auto-detection"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
) -> None:
    """Mark an issue as stale, or list stale issues with --auto."""
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        if auto:
            # Auto-detect stale issues
            stale_issues = service.get_stale_issues(days=days)

            if format == "json":
                from dot_work.db_issues.cli_utils import format_issues_json

                json_output = format_issues_json(stale_issues)
                console.print(json_output)
            else:
                from dot_work.db_issues.cli_utils import format_issues_table

                if not stale_issues:
                    console.print("[dim]No stale issues found[/dim]")
                else:
                    console.print(f"\n[bold]Stale Issues[/bold] (not updated in {days}+ days):")
                    format_issues_table(stale_issues, console)
        else:
            # Mark specific issue as stale
            if not issue_id:
                console.print("[red]Error: issue_id required when not using --auto[/red]")
                raise typer.Exit(1)

            issue = service.transition_issue(issue_id, IssueStatus.STALE)
            if not issue:
                console.print(f"[red]Issue not found or cannot be marked stale: {issue_id}[/red]")
                raise typer.Exit(1)

            console.print(f"[green]✓[/green] Issue marked as stale: [bold]{issue.id}[/bold]")


@app.command()
def delete(
    issue_ids: list[str] = typer.Argument(..., help="Issue ID(s) to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete one or more issues.

    Multiple issue IDs can be provided. With --force, all are deleted without
    confirmation. Without --force, a single confirmation is requested for
    all issues.
    """
    if not force:
        if len(issue_ids) == 1:
            confirm = typer.confirm(f"Are you sure you want to delete issue {issue_ids[0]}?")
        else:
            confirm = typer.confirm(f"Are you sure you want to delete {len(issue_ids)} issues?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit()

    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = IssueService(uow, id_service, clock)

        deleted_count = 0
        not_found: list[str] = []

        for issue_id in issue_ids:
            deleted = service.delete_issue(issue_id)
            if deleted:
                deleted_count += 1
            else:
                not_found.append(issue_id)

        # Report results
        if deleted_count > 0:
            if deleted_count == 1:
                console.print(f"[green]✓[/green] Deleted [bold]{deleted_count}[/bold] issue")
            else:
                console.print(f"[green]✓[/green] Deleted [bold]{deleted_count}[/bold] issues")

        if not_found:
            for issue_id in not_found:
                console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)


# =============================================================================
# Epic Commands
# =============================================================================


@epic_app.command("create")
def epic_create(
    title: str = typer.Argument(..., help="Epic title"),
    description: str = typer.Option("", "--description", "-d", help="Epic description"),
    parent_epic_id: str | None = typer.Option(  # noqa: B008
        None, "--parent", "-p", help="Parent epic ID for hierarchy"
    ),
) -> None:
    """Create a new epic."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = EpicService(uow, id_service, clock)

        try:
            epic = service.create_epic(
                title=title,
                description=description or None,
                parent_epic_id=parent_epic_id,
            )
            console.print(f"[green]✓[/green] Epic created: [bold]{epic.id}[/bold]")
            console.print(f"  Title: {epic.title}")
            console.print(f"  Status: {epic.status.value}")
            if epic.parent_epic_id:
                console.print(f"  Parent: {epic.parent_epic_id}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@epic_app.command("list")
def epic_list(
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),  # noqa: B008
) -> None:
    """List all epics, optionally filtered by status."""
    status_filter = EpicStatus(status.lower()) if status else None

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = EpicService(uow, id_service, clock)

        epics = service.list_epics(status=status_filter)

        if not epics:
            console.print("[yellow]No epics found[/yellow]")
            return

        # Create rich table
        table = Table(title=f"Epics ({len(epics)} found)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Status", style="green")
        table.add_column("Parent", style="magenta")

        for epic in epics:
            table.add_row(
                epic.id,
                epic.title[:50] + "..." if len(epic.title) > 50 else epic.title,
                epic.status.value,
                epic.parent_epic_id or "-",
            )

        console.print(table)


@epic_app.command("show")
def epic_show(
    epic_id: str = typer.Argument(..., help="Epic ID"),
) -> None:
    """Show epic details."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = EpicService(uow, id_service, clock)

        epic = service.get_epic(epic_id)
        if not epic:
            console.print(f"[red]Epic not found: {epic_id}[/red]")
            raise typer.Exit(1)

        # Display epic details
        console.print(f"[bold cyan]Epic:[/bold cyan] {epic.id}")
        console.print(f"[bold]Title:[/bold] {epic.title}")
        console.print(f"[bold]Status:[/bold] {epic.status.value}")
        console.print(f"[bold]Parent:[/bold] {epic.parent_epic_id or 'None'}")
        console.print("[bold]Description:[/bold]")
        console.print(epic.description or "No description")
        console.print(f"\n[bold]Created:[/bold] {epic.created_at}")
        console.print(f"[bold]Updated:[/bold] {epic.updated_at}")
        if epic.closed_at:
            console.print(f"[bold]Closed:[/bold] {epic.closed_at}")

        # Show child epics
        children = service.list_child_epics(epic_id)
        if children:
            console.print(f"\n[bold]Child Epics ({len(children)}):[/bold]")
            for child in children:
                console.print(f"  - {child.id}: {child.title}")


@epic_app.command("delete")
def epic_delete(
    epic_id: str = typer.Argument(..., help="Epic ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an epic."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete epic {epic_id}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit()

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = EpicService(uow, id_service, clock)

        deleted = service.delete_epic(epic_id)
        if not deleted:
            console.print(f"[red]Epic not found: {epic_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Epic deleted: [bold]{epic_id}[/bold]")


@epic_app.command("set")
def epic_set(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    epic_id: str = typer.Argument(..., help="Epic ID to assign"),
) -> None:
    """Assign an issue to an epic (overwrites existing epic assignment)."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        from dot_work.db_issues.services import IssueService

        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        # First verify epic exists
        epic_service = EpicService(uow, id_service, clock)
        epic = epic_service.get_epic(epic_id)
        if not epic:
            console.print(f"[red]Epic not found: {epic_id}[/red]")
            raise typer.Exit(1)

        # Set epic for issue
        updated = issue_service.set_epic(issue_id, epic_id)
        if not updated:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Assigned issue [bold]{issue_id}[/bold] to epic [bold]{epic_id}[/bold]")


@epic_app.command("clear")
def epic_clear(
    issue_id: str = typer.Argument(..., help="Issue ID"),
) -> None:
    """Remove epic assignment from an issue."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        from dot_work.db_issues.services import IssueService

        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        updated = issue_service.clear_epic(issue_id)
        if not updated:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Cleared epic assignment from issue [bold]{issue_id}[/bold]")


@epic_app.command("all")
def epic_all() -> None:
    """List all epics with issue counts by status."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = EpicService(uow, id_service, clock)

        epic_infos = service.get_all_epics_with_counts()

        if not epic_infos:
            console.print("[yellow]No epics found[/yellow]")
            return

        # Create rich table
        table = Table(title=f"Epics ({len(epic_infos)} found)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Total", style="bold", justify="right")
        table.add_column("Open", style="yellow", justify="right")
        table.add_column("In-Progress", style="blue", justify="right")
        table.add_column("Completed", style="green", justify="right")

        for info in epic_infos:
            table.add_row(
                info.epic_id,
                info.title[:50] + "..." if len(info.title) > 50 else info.title,
                str(info.total_count),
                str(info.proposed_count),
                str(info.in_progress_count),
                str(info.completed_count),
            )

        console.print(table)


@epic_app.command("tree")
def epic_tree(
    epic_id: str | None = typer.Argument(None, help="Epic ID (omit for --all)"),
    all_epics: bool = typer.Option(False, "--all", help="Show all epic trees"),
    format_output: str = typer.Option(
        "ascii",
        "--format",
        "-f",
        help="Output format (ascii, mermaid)",
    ),
) -> None:
    """Show hierarchical epic structure.

    If epic_id is provided, shows tree for that epic.
    With --all, shows trees for all epics.
    With --format mermaid, generates Mermaid diagram.
    """
    if format_output == "mermaid" and all_epics:
        console.print("[red]Error: --format mermaid cannot be used with --all[/red]")
        raise typer.Exit(1)

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = EpicService(uow, id_service, clock)

        if all_epics:
            all_trees = service.get_all_epic_trees()
            if not all_trees:
                console.print("[yellow]No epics found[/yellow]")
                return

            for epic_id_key, items in all_trees.items():
                epic = service.get_epic(epic_id_key)
                if epic:
                    console.print(f"\n[bold cyan]{epic_id_key}:[/bold cyan] {epic.title}")
                    if items:
                        _print_epic_tree_items(items)
                    else:
                        console.print("  [dim](no issues)[/dim]")
        else:
            if not epic_id:
                console.print("[red]Error: Either provide epic_id or use --all[/red]")
                raise typer.Exit(1)

            epic = service.get_epic(epic_id)
            if not epic:
                console.print(f"[red]Epic not found: {epic_id}[/red]")
                raise typer.Exit(1)

            if format_output == "mermaid":
                # Generate Mermaid diagram for epic
                mermaid = _generate_epic_mermaid(epic_id, epic.title, service, uow)
                console.print(f"\n[cyan]Mermaid diagram for {epic_id}:[/cyan]\n")
                console.print(mermaid)
                console.print("\n[dim]Copy this to https://mermaid.live/ to render[/dim]")
            else:
                # ASCII tree format
                console.print(f"[bold cyan]{epic_id}:[/bold cyan] {epic.title}")

                items = service.get_epic_tree(epic_id)
                if items:
                    _print_epic_tree_items(items)
                else:
                    console.print("  [dim](no issues)[/dim]")


def _print_epic_tree_items(items: list) -> None:
    """Print epic tree items with indentation."""
    from dot_work.db_issues.domain.entities import IssueStatus

    for item in items:
        indent = "  " * item.indent_level
        # Status color
        status_color = {
            IssueStatus.PROPOSED.value: "yellow",
            IssueStatus.IN_PROGRESS.value: "blue",
            IssueStatus.BLOCKED.value: "red",
            IssueStatus.COMPLETED.value: "green",
            IssueStatus.WONT_FIX.value: "dim",
        }.get(item.status, "white")

        # Tree connector
        if item.indent_level > 0:
            connector = "└── "
        else:
            connector = ""

        console.print(f"{indent}{connector}[{status_color}]{item.issue_id}[/{status_color}] [dim]{item.title}[/dim] ([{status_color}]{item.status}[/{status_color}])")


def _generate_epic_mermaid(
    epic_id: str, epic_title: str, service: EpicService, uow: UnitOfWork
) -> str:
    """Generate Mermaid diagram for epic hierarchy.

    Args:
        epic_id: Root epic ID
        epic_title: Root epic title
        service: EpicService instance
        uow: UnitOfWork instance

    Returns:
        Mermaid diagram as string
    """
    items = service.get_epic_tree(epic_id)

    if not items:
        return f"graph TD\n    {epic_id}[{epic_id}: {epic_title}]"

    lines = ["graph TD"]

    # Add root node
    safe_id = epic_id.replace("-", "_")
    lines.append(f"    {safe_id}[{epic_id}: {epic_title}]")

    # Track nodes to avoid duplicates
    nodes: set[str] = {epic_id}

    # Helper to recursively build the Mermaid diagram
    def build_mermaid(current_items: list, parent_id: str, indent: int = 0) -> None:
        """Recursively build Mermaid diagram for epic items."""
        grouped_by_level: dict[int, list] = {}
        for item in current_items:
            if item.indent_level not in grouped_by_level:
                grouped_by_level[item.indent_level] = []
            grouped_by_level[item.indent_level].append(item)

        for level in sorted(grouped_by_level.keys()):
            if level <= indent:
                continue
            for item in grouped_by_level[level]:
                safe_child_id = item.issue_id.replace("-", "_")
                if item.issue_id not in nodes:
                    # Get issue for title
                    issue = uow.issues.get(item.issue_id)
                    title = issue.title[:30] if issue else "Unknown"
                    lines.append(f"    {safe_child_id}[{item.issue_id}: {title}]")
                    nodes.add(item.issue_id)

                # Add edge from parent to child
                lines.append(f"    {parent_id} --> {safe_child_id}")

                # Recursively process children
                # For epic hierarchies, we don't have child relationships
                # in the same way as dependencies, so we just show the flat hierarchy

    # Build the diagram
    build_mermaid(items, safe_id)

    return "\n".join(lines)


# =============================================================================
# Project Commands
# =============================================================================


@project_app.command("create")
def project_create(
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option(None, "--description", "-d", help="Project description"),
    set_as_default: bool = typer.Option(
        False, "--default", help="Set as the default project"
    ),
) -> None:
    """Create a new project."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = ProjectService(uow, id_service, clock)

        try:
            project = service.create_project(
                name=name,
                description=description,
                set_as_default=set_as_default,
            )

            default_marker = " [bold][default][/bold]" if project.is_default else ""
            console.print(
                f"[green]✓[/green] Created project: [bold]{project.name}[/bold] ({project.id}){default_marker}"
            )
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@project_app.command("list")
def project_list(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
) -> None:
    """List all projects."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = ProjectService(uow, id_service, clock)

        # Parse status if provided
        project_status = None
        if status:
            try:
                project_status = ProjectStatus(status)
            except ValueError:
                console.print(f"[red]Invalid status: {status}[/red]")
                console.print(
                    "Valid statuses: [cyan]active[/cyan], [cyan]archived[/cyan], [cyan]on_hold[/cyan]"
                )
                raise typer.Exit(1)

        projects = service.list_projects(status=project_status)

        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return

        table = Table(title="Projects")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="blue")
        table.add_column("Status", style="yellow")
        table.add_column("Default")

        for project in projects:
            default_marker = "[green]✓[/green]" if project.is_default else ""
            desc = project.description or "-"
            table.add_row(
                project.id,
                project.name,
                desc[:40] + "..." if desc and len(desc) > 40 else desc,
                project.status.value,
                default_marker,
            )

        console.print(table)
        console.print(f"\nTotal: {len(projects)} project(s)")


@project_app.command("show")
def project_show(
    project_id: str = typer.Argument(..., help="Project ID"),
) -> None:
    """Show project details."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = ProjectService(uow, id_service, clock)

        project = service.get_project(project_id)
        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[bold cyan]Project:[/bold cyan] {project.name} ({project.id})")
        console.print(f"[bold]Status:[/bold] {project.status.value}")
        default_display = "[green]Yes[/green]" if project.is_default else "[bold]No[/bold]"
        console.print(f"[bold]Default:[/bold] {default_display}")

        if project.description:
            console.print(f"[bold]Description:[/bold] {project.description}")

        console.print(f"\n[bold]Created:[/bold] {project.created_at}")
        console.print(f"[bold]Updated:[/bold] {project.updated_at}")


@project_app.command("update")
def project_update(
    project_id: str = typer.Argument(..., help="Project ID"),
    name: str = typer.Option(None, "--name", "-n", help="New project name"),
    description: str = typer.Option(None, "--description", "-d", help="New description"),
    status: str = typer.Option(None, "--status", "-s", help="New status"),
) -> None:
    """Update a project."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = ProjectService(uow, id_service, clock)

        # Parse status if provided
        project_status = None
        if status:
            try:
                project_status = ProjectStatus(status)
            except ValueError:
                console.print(f"[red]Invalid status: {status}[/red]")
                raise typer.Exit(1)

        try:
            project = service.update_project(
                project_id,
                name=name,
                description=description,
                status=project_status,
            )

            if not project:
                console.print(f"[red]Project not found: {project_id}[/red]")
                raise typer.Exit(1)

            console.print(
                f"[green]✓[/green] Updated project: [bold]{project.name}[/bold] ({project.id})"
            )
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@project_app.command("delete")
def project_delete(
    project_id: str = typer.Argument(..., help="Project ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete a project."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = ProjectService(uow, id_service, clock)

        # Check if project exists
        project = service.get_project(project_id)
        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            raise typer.Exit(1)

        # Confirm deletion
        if not yes:
            console.print(
                f"Delete project '[bold]{project.name}[/bold]' ({project_id})? [y/N]: ",
                end="",
            )
            response = input().strip().lower()
            if response != "y":
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)

        try:
            success = service.delete_project(project_id)
            if success:
                console.print(
                    f"[green]✓[/green] Deleted project: [bold]{project.name}[/bold] ({project_id})"
                )
            else:
                console.print(f"[red]Failed to delete project: {project_id}[/red]")
                raise typer.Exit(1)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@project_app.command("set-default")
def project_set_default(
    project_id: str = typer.Argument(..., help="Project ID"),
) -> None:
    """Set a project as the default."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = ProjectService(uow, id_service, clock)

        project = service.set_default_project(project_id)
        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            raise typer.Exit(1)

        console.print(
            f"[green]✓[/green] Set default project: [bold]{project.name}[/bold] ({project.id})"
        )


@project_app.command("archive")
def project_archive(
    project_id: str = typer.Argument(..., help="Project ID"),
) -> None:
    """Archive a project."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = ProjectService(uow, id_service, clock)

        project = service.archive_project(project_id)
        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            raise typer.Exit(1)

        console.print(
            f"[green]✓[/green] Archived project: [bold]{project.name}[/bold] ({project.id})"
        )


@project_app.command("activate")
def project_activate(
    project_id: str = typer.Argument(..., help="Project ID"),
) -> None:
    """Activate an archived project."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = ProjectService(uow, id_service, clock)

        project = service.activate_project(project_id)
        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            raise typer.Exit(1)

        console.print(
            f"[green]✓[/green] Activated project: [bold]{project.name}[/bold] ({project.id})"
        )


# =============================================================================
# Child Epic Relationship Commands
# =============================================================================


@child_app.command("add")
def child_add(
    parent_id: str = typer.Argument(..., help="Parent epic ID"),
    child_id: str = typer.Argument(..., help="Child epic ID"),
) -> None:
    """Add a child epic to a parent epic."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = EpicService(uow, id_service, clock)

        try:
            success = service.add_child_epic(parent_id, child_id)
            if not success:
                console.print("[red]Failed to add child epic[/red]")
                console.print(f"Parent '{parent_id}' or child '{child_id}' not found")
                raise typer.Exit(1)

            console.print(
                f"[green]✓[/green] Added child epic: [bold]{child_id}[/bold] -> [bold]{parent_id}[/bold]"
            )
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@child_app.command("remove")
def child_remove(
    child_id: str = typer.Argument(..., help="Child epic ID"),
) -> None:
    """Remove a child epic from its parent."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = EpicService(uow, id_service, clock)

        success = service.remove_child_epic(child_id)
        if not success:
            console.print("[red]Failed to remove child epic[/red]")
            console.print(f"Child epic '{child_id}' not found or has no parent")
            raise typer.Exit(1)

        console.print(
            f"[green]✓[/green] Removed child epic: [bold]{child_id}[/bold] from its parent"
        )


@child_app.command("list")
def child_list(
    parent_id: str = typer.Argument(..., help="Parent epic ID"),
) -> None:
    """List all child epics of a parent epic."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = EpicService(uow, id_service, clock)

        # Verify parent exists
        parent = service.get_epic(parent_id)
        if not parent:
            console.print(f"[red]Parent epic not found: {parent_id}[/red]")
            raise typer.Exit(1)

        children = service.list_child_epics(parent_id)

        if not children:
            console.print(f"[yellow]No child epics found for {parent_id}[/yellow]")
            return

        console.print(f"[bold]Child epics of {parent_id}: ({len(children)} found)[/bold]")
        for child in children:
            console.print(f"  - {child.id}: [cyan]{child.title}[/cyan] ({child.status.value})")


# =============================================================================
# Import/Export Commands
# =============================================================================


@io_app.command("export")
def io_export(
    output: str = typer.Option(
        ".work/db-issues/issues.jsonl", "--output", "-o", help="Output JSONL file path"
    ),
    include_completed: bool = typer.Option(
        True, "--include-completed/--no-completed", help="Include completed issues"
    ),
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),  # noqa: B008
) -> None:
    """Export issues to JSONL format.

    One issue per line in JSON format. Useful for backups, migration, and version control.
    """
    # Parse status filter
    status_filter = IssueStatus(status) if status else None

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = JsonlService(uow, id_service, clock)

        try:
            count = service.export(
                output_path=output,
                include_completed=include_completed,
                status_filter=status_filter,
            )
            console.print(
                f"[green]✓[/green] Exported [bold]{count}[/bold] issues to [cyan]{output}[/cyan]"
            )
        except OSError as e:
            console.print(f"[red]Error exporting:[/red] {e}")
            raise typer.Exit(1) from None


@io_app.command("import")
def io_import(
    input: str = typer.Option(
        ".work/db-issues/issues.jsonl", "--input", "-i", help="Input JSONL file path"
    ),
    strategy: str = typer.Option(
        "merge",
        "--strategy",
        "-s",
        help="Import strategy: 'merge' (update existing) or 'replace' (clear and reload)",
    ),
) -> None:
    """Import issues from JSONL format.

    Merge strategy: Updates existing issues, creates new ones.
    Replace strategy: Deletes all existing issues first, then imports.
    """
    if strategy not in ("merge", "replace"):
        console.print(f"[red]Invalid strategy: {strategy}[/red]")
        console.print("Valid options: merge, replace")
        raise typer.Exit(1)

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = JsonlService(uow, id_service, clock)

        try:
            created, skipped, updated = service.import_(
                input_path=input, strategy=cast(Literal["merge", "replace"], strategy)
            )
            console.print("[green]✓[/green] Import complete:")
            console.print(f"  Created: [cyan]{created}[/cyan]")
            console.print(f"  Updated: [cyan]{updated}[/cyan]")
            console.print(f"  Skipped: [cyan]{skipped}[/cyan]")
        except (OSError, json.JSONDecodeError) as e:
            console.print(f"[red]Error importing:[/red] {e}")
            raise typer.Exit(1) from None


@io_app.command("sync")
def io_sync(
    repo: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    message: str | None = typer.Option(None, "--message", "-m", help="Commit message"),  # noqa: B008
    push: bool = typer.Option(False, "--push", "-p", help="Push to remote after commit"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without making changes"),
) -> None:
    """Export issues to JSONL and commit to git.

    Combines export with git version control for automatic backups.
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        # Get issue count for dry run
        all_issues = issue_service.list_issues(limit=100000)
        count = len(all_issues)

        if dry_run:
            from pathlib import Path

            console.print("[bold]Dry run mode - preview:[/bold]")
            console.print(f"\n[cyan]Would export:[/cyan] {count} issues")

            # Get JSONL path
            repo_path = Path(repo) if repo else Path.cwd()
            jsonl_path = repo_path / ".work" / "db-issues" / "issues.jsonl"

            console.print(f"[cyan]Would write to:[/cyan] {jsonl_path}")

            # Generate commit message
            if message is None:
                from datetime import UTC, datetime

                timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                message = f"Update issues ({count} issues) - {timestamp}"

            console.print(f"[cyan]Would commit:[/cyan] {message}")

            if push:
                console.print("[cyan]Would push to:[/cyan] origin")

            console.print("\n[yellow]Run without --dry-run to perform these actions.[/yellow]")
            return

        service = JsonlService(uow, id_service, clock)

        try:
            count, commit_hash = service.sync_git(repo_path=repo, message=message, push=push)
            console.print(f"[green]✓[/green] Synced [bold]{count}[/bold] issues")
            console.print(f"  Commit: [cyan]{commit_hash}[/cyan]")
            if push:
                console.print("  Pushed to remote")
        except (OSError, ImportError) as e:
            console.print(f"[red]Error syncing:[/red] {e}")
            raise typer.Exit(1) from None


# =============================================================================
# Dependency Commands
# =============================================================================


@deps_app.command("check")
def deps_check(
    issue_id: str = typer.Argument(..., help="Issue ID to check"),
) -> None:
    """Check if an issue has circular dependencies."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        service = DependencyService(uow)

        try:
            result: CycleResult = service.check_circular(issue_id)

            if result.has_cycle:
                console.print("[red]✗[/red] Circular dependency detected:")
                console.print(f"  [yellow]{' -> '.join(result.cycle_path)}[/yellow]")
                console.print(f"  {result.message}")
                raise typer.Exit(1) from None
            else:
                console.print(
                    f"[green]✓[/green] No circular dependencies found for [cyan]{issue_id}[/cyan]"
                )
        except Exception as e:
            console.print(f"[red]Error checking dependencies:[/red] {e}")
            raise typer.Exit(1) from None


@deps_app.command("check-all")
def deps_check_all() -> None:
    """Check all issues for circular dependencies."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        service = DependencyService(uow)

        try:
            results: list[CycleResult] = service.check_circular_all()

            if results:
                console.print(f"[red]Found {len(results)} circular dependencies:[/red]\n")
                for i, result in enumerate(results, 1):
                    console.print(f"{i}. [yellow]{' -> '.join(result.cycle_path)}[/yellow]")
                raise typer.Exit(1) from None
            else:
                console.print("[green]✓[/green] No circular dependencies found")
        except Exception as e:
            console.print(f"[red]Error checking dependencies:[/red] {e}")
            raise typer.Exit(1) from None


@deps_app.command("impact")
def deps_impact(
    issue_id: str = typer.Argument(..., help="Issue ID to analyze"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),  # noqa: B008
) -> None:
    """Show what issues are blocked if this issue closes."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        service = DependencyService(uow)

        try:
            impact: ImpactResult = service.get_impact(issue_id)

            if impact.impact_count == 0:
                console.print(
                    f"[green]✓[/green] Issue [cyan]{issue_id}[/cyan] does not block "
                    f"any other issues"
                )
                return

            if format == "json":
                import json

                data = {
                    "issue_id": impact.issue_id,
                    "direct_count": len(impact.direct_impact),
                    "total_count": impact.impact_count,
                    "direct_impact": [
                        {
                            "from": d.from_issue_id,
                            "to": d.to_issue_id,
                            "type": d.dependency_type.value,
                        }
                        for d in impact.direct_impact
                    ],
                    "total_impact": [
                        {
                            "from": d.from_issue_id,
                            "to": d.to_issue_id,
                            "type": d.dependency_type.value,
                        }
                        for d in impact.total_impact
                    ],
                }
                console.print(json.dumps(data, indent=2))
            else:
                # Table output
                console.print(f"\nIssues blocked by [cyan]{issue_id}[/cyan]:\n")

                # Show direct impact
                if impact.direct_impact:
                    console.print("[yellow]Direct dependencies:[/yellow]")
                    for dep in impact.direct_impact:
                        dep_issue = uow.issues.get(dep.from_issue_id)
                        title = dep_issue.title if dep_issue else "(unknown)"
                        console.print(f"  [cyan]{dep.from_issue_id}[/cyan] - {title}")

                # Show total count
                console.print(
                    f"\nTotal: [bold]{impact.impact_count}[/bold] issue(s) indirectly affected"
                )

        except Exception as e:
            console.print(f"[red]Error analyzing impact:[/red] {e}")
            raise typer.Exit(1) from None


@deps_app.command("blocked-by")
def deps_blocked_by(
    issue_id: str = typer.Argument(..., help="Issue ID to analyze"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),  # noqa: B008
) -> None:
    """Show what issues are blocking this issue."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        service = DependencyService(uow)

        try:
            blockers: list[Dependency] = service.get_blocked_by(issue_id)

            if not blockers:
                console.print(
                    f"[green]✓[/green] Issue [cyan]{issue_id}[/cyan] is not blocked by "
                    f"any other issues"
                )
                return

            if format == "json":
                import json

                data = {
                    "issue_id": issue_id,
                    "blocker_count": len(blockers),
                    "blockers": [
                        {
                            "from": b.from_issue_id,
                            "to": b.to_issue_id,
                            "type": b.dependency_type.value,
                        }
                        for b in blockers
                    ],
                }
                console.print(json.dumps(data, indent=2))
            else:
                # Table output
                console.print(f"\nIssues blocking [cyan]{issue_id}[/cyan]:\n")

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Issue ID", style="cyan")
                table.add_column("Title")
                table.add_column("Type")

                for dep in blockers:
                    blocker_issue = uow.issues.get(dep.from_issue_id)
                    title = blocker_issue.title if blocker_issue else "(unknown)"
                    table.add_row(dep.from_issue_id, title[:60], dep.dependency_type.value)

                console.print(table)

        except Exception as e:
            console.print(f"[red]Error analyzing blockers:[/red] {e}")
            raise typer.Exit(1) from None


@deps_app.command("tree")
def deps_tree(
    issue_id: str = typer.Argument(..., help="Root issue ID"),
    max_depth: int = typer.Option(5, "--max-depth", "-d", help="Maximum depth to traverse"),
    format_output: str = typer.Option(
        "ascii",
        "--format",
        "-f",
        help="Output format (ascii, mermaid)",
    ),
) -> None:
    """Show dependency tree for an issue."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        service = DependencyService(uow)

        try:
            if format_output == "mermaid":
                # Generate Mermaid diagram
                mermaid = service.generate_mermaid(issue_id, max_depth=max_depth)
                console.print(f"\n[cyan]Mermaid diagram for {issue_id}:[/cyan]\n")
                console.print(mermaid)
                console.print("\n[dim]Copy this to https://mermaid.live/ to render[/dim]")
            else:
                # ASCII tree format
                tree: dict[str, list[tuple[str, str, DependencyType]]] = service.get_dependency_tree(
                    issue_id, max_depth=max_depth
                )

                if not tree:
                    console.print(f"[green]✓[/green] Issue [cyan]{issue_id}[/cyan] has no dependencies")
                    return

                console.print(f"\nDependency tree for [cyan]{issue_id}[/cyan]:\n")
                _print_tree(tree, issue_id, "", uow)

        except Exception as e:
            console.print(f"[red]Error building tree:[/red] {e}")
            raise typer.Exit(1) from None


def _print_tree(
    tree: dict[str, list[tuple[str, str, DependencyType]]],
    issue_id: str,
    prefix: str,
    uow: UnitOfWork,
) -> None:
    """Recursively print dependency tree."""
    if issue_id not in tree:
        return

    children = tree[issue_id]
    for i, (_from_id, to_id, dep_type) in enumerate(children):
        is_last = i == len(children) - 1
        connector = "└──" if is_last else "├──"
        child_prefix = "    " if is_last else "│   "

        issue = uow.issues.get(to_id)
        title = issue.title if issue else "(unknown)"

        console.print(f"{prefix}[cyan]{connector} {to_id}[/cyan] ({dep_type.value}): {title[:50]}")
        _print_tree(tree, to_id, prefix + child_prefix, uow)


@deps_app.command("list-all")
def deps_list_all(
    dependency_type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by dependency type (blocks, depends-on, related-to, discovered-from)",
    ),
    format_output: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format (table, json)",
    ),
) -> None:
    """List all dependencies in the system."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        service = DependencyService(uow)

        try:
            # Parse dependency type filter
            dep_type_filter = None
            if dependency_type:
                try:
                    dep_type_filter = DependencyType(dependency_type.replace("-", "_"))
                except ValueError:
                    console.print(f"[red]Invalid dependency type: {dependency_type}[/red]")
                    console.print(
                        "Valid types: [cyan]blocks, depends-on, related-to, discovered-from[/cyan]"
                    )
                    raise typer.Exit(1) from None

            deps = service.get_all_dependencies(dep_type_filter)

            if not deps:
                console.print("[green]✓[/green] No dependencies found")
                return

            if format_output == "json":
                import json

                output = [
                    {
                        "from": d.from_issue_id,
                        "to": d.to_issue_id,
                        "type": d.dependency_type.value,
                    }
                    for d in deps
                ]
                console.print(json.dumps(output, indent=2))
            else:
                # Table format
                from rich.table import Table

                table = Table(title=f"All Dependencies ({len(deps)} total)")
                table.add_column("From Issue", style="cyan")
                table.add_column("Type", style="yellow")
                table.add_column("To Issue", style="cyan")

                for dep in deps:
                    table.add_row(dep.from_issue_id, dep.dependency_type.value, dep.to_issue_id)

                console.print(table)

        except Exception as e:
            console.print(f"[red]Error listing dependencies:[/red] {e}")
            raise typer.Exit(1) from None


@deps_app.command("cycles")
def deps_cycles(
    fix: bool = typer.Option(False, "--fix", help="Suggest fixes for detected cycles"),
) -> None:
    """Check all issues for circular dependencies and optionally suggest fixes."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        service = DependencyService(uow)

        try:
            cycles = service.check_circular_all()

            if not cycles or all(not c.has_cycle for c in cycles):
                console.print("[green]✓[/green] No circular dependencies found")
                return

            console.print(f"[red]Found {len(cycles)} circular dependencies:[/red]\n")

            for i, cycle in enumerate(cycles, 1):
                if not cycle.has_cycle:
                    continue

                console.print(f"[red]{i}.[/red] {cycle.message}")

                if fix:
                    fixes = service.suggest_cycle_fixes([cycle])
                    for suggestion in fixes:
                        console.print(f"   [yellow]Suggestion:[/yellow] {suggestion}")
                console.print()

        except Exception as e:
            console.print(f"[red]Error checking cycles:[/red] {e}")
            raise typer.Exit(1) from None


# =============================================================================
# Label Commands
# =============================================================================


@labels_app.command("create")
def labels_create(
    name: str = typer.Argument(..., help="Label name"),
    color: str | None = typer.Option(
        None,
        "--color",
        "-c",
        help="Label color (named, hex, or RGB)",
    ),  # noqa: B008
    description: str | None = typer.Option(
        None,
        "--description",
        "-d",
        help="Label description",
    ),  # noqa: B008
) -> None:
    """Create a new label with optional color."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = LabelService(uow, id_service, clock)

        try:
            label = service.create_label(name, color, description)
            console.print(f"[green]✓[/green] Created label: [cyan]{name}[/cyan]")
            if label.color:
                console.print(f"  Color: {label.color}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]Error creating label:[/red] {e}")
            raise typer.Exit(1) from None


@labels_app.command("list")
def labels_list(
    unused: bool = typer.Option(False, "--unused", "-u", help="Show only unused labels"),
) -> None:
    """List all defined labels."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = LabelService(uow, id_service, clock)

        labels = service.list_labels(include_unused=unused)

        if not labels:
            if unused:
                console.print("[yellow]No unused labels found[/yellow]")
            else:
                console.print("[yellow]No labels defined[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Color")
        table.add_column("Description")

        for label in labels:
            color_display = label.color or "N/A"
            table.add_row(label.name, color_display, label.description or "")

        console.print(table)


@labels_app.command("update")
def labels_update(
    label_id: str = typer.Argument(..., help="Label ID"),
    color: str | None = typer.Option(
        None,
        "--color",
        "-c",
        help="New color (named, hex, or RGB)",
    ),  # noqa: B008
    description: str | None = typer.Option(
        None,
        "--description",
        "-d",
        help="New description",
    ),  # noqa: B008
) -> None:
    """Update an existing label."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = LabelService(uow, id_service, clock)

        try:
            label = service.update_label(label_id, color, description)
            console.print(f"[green]✓[/green] Updated label: [cyan]{label.name}[/cyan]")
            if label.color:
                console.print(f"  Color: {label.color}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]Error updating label:[/red] {e}")
            raise typer.Exit(1) from None


@labels_app.command("rename")
def labels_rename(
    label_id: str = typer.Argument(..., help="Label ID or name"),
    new_name: str = typer.Argument(..., help="New label name"),
) -> None:
    """Rename a label."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = LabelService(uow, id_service, clock)

        try:
            _ = service.rename_label(label_id, new_name)
            console.print(f"[green]✓[/green] Renamed label to: [cyan]{new_name}[/cyan]")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]Error renaming label:[/red] {e}")
            raise typer.Exit(1) from None


@labels_app.command("delete")
def labels_delete(
    label_id: str = typer.Argument(..., help="Label ID or name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a label."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = LabelService(uow, id_service, clock)

        # Get label for confirmation
        label = service.get_label(label_id)
        if not label:
            console.print(f"[red]Error:[/red] Label not found: {label_id}")
            raise typer.Exit(1) from None

        # Confirm unless force
        if not force:
            typer.confirm(f"Delete label '{label.name}'?", abort=True)

        result = service.delete_label(label_id)
        if result:
            console.print(f"[green]✓[/green] Deleted label: [cyan]{label.name}[/cyan]")
        else:
            console.print(f"[red]Error:[/red] Failed to delete label: {label_id}")
            raise typer.Exit(1) from None


@labels_app.command("bulk-add")
def labels_bulk_add(
    labels: str = typer.Argument(..., help="Labels to add (comma-separated)"),
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),
    priority: str | None = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    type_filter: str | None = typer.Option(None, "--type", "-t", help="Filter by issue type"),
    assignee: str | None = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
    existing_label: str | None = typer.Option(
        None, "--label", "-l", help="Filter by existing label"
    ),
    all_issues: bool = typer.Option(False, "--all", help="Apply to all issues"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
) -> None:
    """Add labels to multiple issues by filter criteria.

    Examples:
        # Add 'urgent' label to all open issues
        labels bulk-add urgent --status open

        # Add 'review' and 'test' to high priority issues
        labels bulk-add "review,test" --priority high

        # Add 'backlog' to all task issues
        labels bulk-add backlog --type task
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)
        bulk_service = BulkService(issue_service, id_service, clock)

        try:
            # Parse labels (comma-separated)
            label_list = [label.strip() for label in labels.split(",") if label.strip()]

            if not label_list:
                console.print("[red]Error:[/red] At least one label must be specified")
                raise typer.Exit(1) from None

            # Parse filters
            status_filter = IssueStatus(status) if status else None
            priority_filter = IssuePriority[priority.upper()] if priority else None
            type_filter_enum = IssueType[type_filter.upper()] if type_filter else None

            if dry_run:
                # Show what would be updated
                issues = issue_service.list_issues(
                    status=status_filter,
                    priority=priority_filter,
                    issue_type=type_filter_enum,
                    assignee=assignee,
                    limit=1000,
                )
                if existing_label:
                    issues = [i for i in issues if existing_label in i.labels]

                console.print(
                    f"[bold]Dry run mode - {len(issues)} issues would be updated:[/bold]"
                )
                for idx, issue in enumerate(issues[:10], start=1):
                    console.print(f"  {idx}. {issue.id}: {issue.title[:50]}")
                    console.print(f"     Adding: {', '.join(label_list)}")
                if len(issues) > 10:
                    console.print(f"  ... and {len(issues) - 10} more")
                return

            # Perform bulk label add
            result = bulk_service.bulk_label_add(
                labels=label_list,
                status=status_filter,
                priority=priority_filter,
                issue_type=type_filter_enum,
                assignee=assignee,
                existing_label=existing_label,
            )

            # Show results
            console.print(f"\n[bold]Result:[/bold] {result.succeeded}/{result.total} issues updated")
            console.print(f"[green]✓[/green] Added: {', '.join(label_list)}")

            if result.succeeded > 0:
                console.print(f"[green]✓[/green] {result.succeeded} issue(s) updated")

            if result.failed > 0:
                console.print(f"[red]✗[/red] {result.failed} issue(s) failed")

            if result.issue_ids:
                console.print(f"\n[cyan]Affected issues ({len(result.issue_ids)}):[/cyan]")
                for idx, issue_id in enumerate(result.issue_ids[:20], start=1):
                    console.print(f"  {idx}. {issue_id}")

        except KeyError as e:
            console.print(f"[red]Error:[/red] Invalid filter value: {e}")
            console.print("Valid statuses: proposed, in_progress, blocked, completed, wont_fix")
            console.print("Valid priorities: critical, high, medium, low")
            console.print(
                "Valid types: bug, feature, task, enhancement, refactor, docs, test, security, performance"
            )
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@labels_app.command("bulk-remove")
def labels_bulk_remove(
    labels: str = typer.Argument(..., help="Labels to remove (comma-separated)"),
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),
    priority: str | None = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    type_filter: str | None = typer.Option(None, "--type", "-t", help="Filter by issue type"),
    assignee: str | None = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
    must_have: bool = typer.Option(False, "--must-have", help="Only remove from issues that have the labels"),
    all_issues: bool = typer.Option(False, "--all", help="Apply to all issues"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
) -> None:
    """Remove labels from multiple issues by filter criteria.

    Examples:
        # Remove 'wontfix' label from all issues
        labels bulk-remove wontfix --all

        # Remove 'old-label' from completed issues
        labels bulk-remove old-label --status completed

        # Remove multiple labels from issues that have them
        labels bulk-remove "deprecated,legacy" --must-have
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)
        bulk_service = BulkService(issue_service, id_service, clock)

        try:
            # Parse labels (comma-separated)
            label_list = [label.strip() for label in labels.split(",") if label.strip()]

            if not label_list:
                console.print("[red]Error:[/red] At least one label must be specified")
                raise typer.Exit(1) from None

            # Parse filters
            status_filter = IssueStatus(status) if status else None
            priority_filter = IssuePriority[priority.upper()] if priority else None
            type_filter_enum = IssueType[type_filter.upper()] if type_filter else None

            if dry_run:
                # Show what would be updated
                issues = issue_service.list_issues(
                    status=status_filter,
                    priority=priority_filter,
                    issue_type=type_filter_enum,
                    assignee=assignee,
                    limit=1000,
                )
                if must_have:
                    issues = [
                        i for i in issues if any(label in i.labels for label in label_list)
                    ]

                console.print(
                    f"[bold]Dry run mode - {len(issues)} issues would be updated:[/bold]"
                )
                for idx, issue in enumerate(issues[:10], start=1):
                    console.print(f"  {idx}. {issue.id}: {issue.title[:50]}")
                    console.print(f"     Removing: {', '.join(label_list)}")
                if len(issues) > 10:
                    console.print(f"  ... and {len(issues) - 10} more")
                return

            # Perform bulk label remove
            result = bulk_service.bulk_label_remove(
                labels=label_list,
                status=status_filter,
                priority=priority_filter,
                issue_type=type_filter_enum,
                assignee=assignee,
                must_have_label=must_have,
            )

            # Show results
            console.print(f"\n[bold]Result:[/bold] {result.succeeded}/{result.total} issues updated")
            console.print(f"[green]✓[/green] Removed: {', '.join(label_list)}")

            if result.succeeded > 0:
                console.print(f"[green]✓[/green] {result.succeeded} issue(s) updated")

            if result.failed > 0:
                console.print(f"[red]✗[/red] {result.failed} issue(s) failed")

            if result.issue_ids:
                console.print(f"\n[cyan]Affected issues ({len(result.issue_ids)}):[/cyan]")
                for idx, issue_id in enumerate(result.issue_ids[:20], start=1):
                    console.print(f"  {idx}. {issue_id}")

        except KeyError as e:
            console.print(f"[red]Error:[/red] Invalid filter value: {e}")
            console.print("Valid statuses: proposed, in_progress, blocked, completed, wont_fix")
            console.print("Valid priorities: critical, high, medium, low")
            console.print(
                "Valid types: bug, feature, task, enhancement, refactor, docs, test, security, performance"
            )
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@labels_app.command("set")
def labels_set(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    labels: str = typer.Argument(..., help="Labels to set (comma-separated)"),
) -> None:
    """Replace all labels on an issue.

    Examples:
        # Set labels to bug, critical, security
        dot-work db-issues labels set bd-a1b2 bug,critical,security

        # Clear all labels
        dot-work db-issues labels set bd-a1b2 ""
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        # Parse labels (comma-separated, empty string clears all labels)
        label_list = [label.strip() for label in labels.split(",") if label.strip()]

        # Get issue for display
        issue = issue_service.get_issue(issue_id)
        if not issue:
            console.print(f"[red]Error:[/red] Issue not found: {issue_id}")
            raise typer.Exit(1)

        # Show previous labels
        old_labels = ", ".join(issue.labels) if issue.labels else "None"

        # Set new labels
        updated = issue_service.set_labels(issue_id, label_list)
        if not updated:
            console.print("[red]Error:[/red] Failed to update labels")
            raise typer.Exit(1)

        # Show result
        console.print(f"[green]✓[/green] Labels updated: [bold]{issue_id}[/bold]")
        console.print(f"  Old labels: {old_labels}")
        new_labels = ", ".join(label_list) if label_list else "None"
        console.print(f"  New labels: {new_labels}")


@labels_app.command("all")
def labels_all(
    with_counts: bool = typer.Option(False, "--with-counts", "-c", help="Show usage counts"),
    unused: bool = typer.Option(False, "--unused", "-u", help="Show only unused labels"),
) -> None:
    """List all unique labels globally.

    Shows all unique labels across all issues, with optional usage counts.

    Examples:
        # List all unique labels
        dot-work db-issues labels all

        # List with usage counts
        dot-work db-issues labels all --with-counts

        # Show only unused labels
        dot-work db-issues labels all --unused
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = LabelService(uow, id_service, clock)

        label_infos = service.get_all_labels_with_counts(include_unused=unused)

        if not label_infos:
            if unused:
                console.print("[yellow]No unused labels found[/yellow]")
            else:
                console.print("[yellow]No labels found[/yellow]")
            return

        if unused:
            console.print(f"[bold]Unused labels ({len(label_infos)} found):[/bold]")
        else:
            console.print(f"[bold]All labels ({len(label_infos)} unique):[/bold]")

        # Create table for display
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        if with_counts:
            table.add_column("Count", style="green", justify="right")
        table.add_column("Color")

        for info in label_infos:
            color_display = info.color or "N/A"
            if with_counts:
                if info.count == 0:
                    count_display = "[dim]0[/dim]"
                else:
                    count_display = str(info.count)
                table.add_row(info.name, count_display, color_display)
            else:
                table.add_row(info.name, color_display)

        console.print(table)


if __name__ == "__main__":
    app()


# =============================================================================
# Comment Commands
# =============================================================================


@comments_app.command("add")
def comment_add(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    text: str | None = typer.Option(None, "--text", "-t", help="Comment text"),
    author: str = typer.Option(..., "--author", "-a", help="Comment author"),
    editor: bool = typer.Option(False, "--editor", "-e", help="Use $EDITOR to write comment"),
) -> None:
    """Add a comment to an issue.

    Either provide --text with the comment content, or use --editor to compose
    the comment in your configured text editor ($EDITOR or vi).
    """

    # If using editor, get text from editor
    comment_text = text
    if editor:
        comment_text = _get_text_from_editor(
            template=f"# Comment for issue {issue_id}\n"
            f"# Lines starting with # will be ignored\n"
            f"# Enter your comment below:\n",
        )
        if not comment_text.strip():
            console.print("[yellow]No comment text provided.[/yellow]")
            raise typer.Exit(1)

    if not comment_text:
        console.print("[red]Error:[/red] Either --text or --editor is required")
        raise typer.Exit(1)

    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = CommentService(uow, id_service, clock)

        comment = service.add_comment(issue_id, author, comment_text)
        if not comment:
            console.print(f"[red]Error:[/red] Issue not found: {issue_id}")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Comment added: [bold]{comment.id}[/bold]")
        console.print(f"  Author: {comment.author}")
        console.print(f"  Created: {comment.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


@comments_app.command("list")
def comment_list(
    issue_id: str = typer.Argument(..., help="Issue ID"),
) -> None:
    """List all comments for an issue."""
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = CommentService(uow, id_service, clock)

        comments = service.list_comments(issue_id)

        if not comments:
            console.print(f"[yellow]No comments found for issue: {issue_id}[/yellow]")
            return

        # Verify issue exists
        issue = uow.issues.get(issue_id)
        if not issue:
            console.print(f"[red]Error:[/red] Issue not found: {issue_id}")
            raise typer.Exit(1)

        # Create rich table
        table = Table(title=f"Comments for {issue_id}: {issue.title}")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Author", style="green")
        table.add_column("Created", style="yellow")
        table.add_column("Text", style="white")

        for comment in comments:
            # Truncate long comments for display
            display_text = comment.text
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            table.add_row(
                comment.id,
                comment.author,
                comment.created_at.strftime("%Y-%m-%d %H:%M"),
                display_text,
            )

        console.print(table)


@comments_app.command("delete")
def comment_delete(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    comment_ids: list[str] = typer.Argument(..., help="Comment ID(s) to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete one or more comments from an issue.

    Multiple comment IDs can be provided. All comments must belong to the
    specified issue. With --force, all are deleted without confirmation.
    """
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = CommentService(uow, id_service, clock)

        # Verify all comments belong to the issue
        not_found: list[str] = []
        wrong_issue: list[tuple[str, str]] = []  # (comment_id, actual_issue_id)
        valid_comments: list[tuple[str, str]] = []  # (comment_id, author)

        for comment_id in comment_ids:
            comment = service.get_comment(comment_id)
            if not comment:
                not_found.append(comment_id)
            elif comment.issue_id != issue_id:
                wrong_issue.append((comment_id, comment.issue_id))
            else:
                valid_comments.append((comment_id, comment.author))

        # Report errors first
        if not_found:
            for comment_id in not_found:
                console.print(f"[red]Error:[/red] Comment not found: {comment_id}")

        if wrong_issue:
            for comment_id, actual_issue in wrong_issue:
                console.print(
                    f"[red]Error:[/red] Comment {comment_id} belongs to issue {actual_issue}, not {issue_id}"
                )

        if not_found or wrong_issue:
            raise typer.Exit(1)

        if not valid_comments:
            console.print("[yellow]No valid comments to delete[/yellow]")
            raise typer.Exit(1)

        # Confirm unless force
        if not force:
            if len(valid_comments) == 1:
                _, author = valid_comments[0]
                typer.confirm(f"Delete comment from {author}?", abort=True)
            else:
                typer.confirm(f"Delete {len(valid_comments)} comments?", abort=True)

        # Delete valid comments
        deleted_count = 0
        failed: list[str] = []

        for comment_id, _author in valid_comments:
            result = service.delete_comment(comment_id)
            if result:
                deleted_count += 1
            else:
                failed.append(comment_id)

        # Report results
        if deleted_count > 0:
            if deleted_count == 1:
                console.print(f"[green]✓[/green] Deleted [bold]{deleted_count}[/bold] comment")
            else:
                console.print(f"[green]✓[/green] Deleted [bold]{deleted_count}[/bold] comments")

        if failed:
            for comment_id in failed:
                console.print(f"[red]Error:[/red] Failed to delete comment: {comment_id}")
            raise typer.Exit(1)


# =============================================================================
# Instruction Template Commands
# =============================================================================


@instructions_app.command("list")
def instructions_list(
    templates_dir: str = typer.Option(
        ".work/instructions",
        "--templates-dir",
        "-d",
        help="Path to templates directory",
    ),
) -> None:
    """List all available instruction templates."""
    manager = TemplateManager(templates_dir)
    templates = manager.list_templates()

    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        console.print(f"  Templates directory: {templates_dir}")
        console.print("\nCreate templates with: [cyan]instructions init[/cyan]")
        return

    table = Table(title=f"Instruction Templates ({len(templates)} found)")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Tasks", style="green", justify="right")
    table.add_column("Source", style="dim")

    for template in templates:
        table.add_row(
            template.name,
            template.title[:50] + "..." if len(template.title) > 50 else template.title,
            str(template.task_count),
            str(template.source_path),
        )

    console.print(table)


@instructions_app.command("show")
def instructions_show(
    name: str = typer.Argument(..., help="Template name (filename without .md extension)"),
    templates_dir: str = typer.Option(
        ".work/instructions",
        "--templates-dir",
        "-d",
        help="Path to templates directory",
    ),
) -> None:
    """Show details of a specific instruction template."""
    manager = TemplateManager(templates_dir)
    template = manager.get_template(name)

    if not template:
        console.print(f"[red]Template not found: {name}[/red]")
        console.print(f"  Searched in: {templates_dir}")
        raise typer.Exit(1)

    # Display template details
    console.print(f"[bold cyan]Template:[/bold cyan] {template.name}")
    console.print(f"[bold]Title:[/bold] {template.title}")
    console.print(f"[bold]Description:[/bold] {template.description or 'No description'}")
    console.print(f"[bold]Tasks:[/bold] {template.task_count}")
    console.print(f"[bold]Source:[/bold] {template.source_path}")

    if template.tasks:
        console.print("\n[bold]Task Breakdown:[/bold]")
        for i, task in enumerate(template.tasks, 1):
            console.print(f"\n[cyan]Task {i}:[/cyan] {task.title}")
            console.print(f"  Type: {task.task_type.value}")
            console.print(f"  Priority: {task.priority.value}")
            if task.assignee:
                console.print(f"  Assignee: {task.assignee}")
            if task.labels:
                console.print(f"  Labels: {', '.join(task.labels)}")
            if task.acceptance_criteria:
                console.print(f"  Acceptance Criteria ({len(task.acceptance_criteria)} items):")
                for ac in task.acceptance_criteria:
                    console.print(f"    - [ ] {ac}")


@instructions_app.command("apply")
def instructions_apply(
    name: str = typer.Argument(..., help="Template name (filename without .md extension)"),
    templates_dir: str = typer.Option(
        ".work/instructions",
        "--templates-dir",
        "-d",
        help="Path to templates directory",
    ),
    project_id: str = typer.Option(
        "default",
        "--project-id",
        "-p",
        help="Project identifier",
    ),
    no_deps: bool = typer.Option(
        False,
        "--no-deps",
        help="Do not create dependencies between tasks",
    ),
) -> None:
    """Apply an instruction template to create epic and child issues.

    Creates a parent epic issue with child issues for each task in the template.
    Dependencies are created between tasks in order.
    """
    from dot_work.db_issues.templates import TemplateParseError

    manager = TemplateManager(templates_dir)
    template = manager.get_template(name)

    if not template:
        console.print(f"[red]Template not found: {name}[/red]")
        console.print(f"  Searched in: {templates_dir}")
        raise typer.Exit(1)

    # Verify template has tasks
    if not template.tasks:
        console.print(f"[red]Template has no tasks: {name}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Applying template:[/bold] {template.name}")
    console.print(f"  Title: {template.title}")
    console.print(f"  Tasks: {template.task_count}")
    console.print("")

    # Create database session and services
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)
        epic_service = EpicService(uow, id_service, clock)
        template_service = TemplateService(uow, id_service, clock, issue_service, epic_service)

        try:
            result = template_service.apply_template(
                template,
                project_id=project_id,
                create_dependencies=not no_deps,
            )

            console.print("[green]✓[/green] Template applied successfully!")
            console.print(f"  [bold]Epic ID:[/bold] {result.epic_id}")
            console.print(f"  [bold]Issues created:[/bold] {result.task_count}")

            console.print("\n[cyan]Created issues:[/cyan]")
            for issue_id in result.issue_ids:
                issue = issue_service.get_issue(issue_id)
                if issue:
                    console.print(f"  - {issue_id}: {issue.title}")

        except (ValueError, TemplateParseError) as e:
            console.print(f"[red]Error applying template:[/red] {e}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Unexpected error:[/red] {e}")
            raise typer.Exit(1)


@instructions_app.command("init")
def instructions_init(
    path: str = typer.Option(
        ".work/instructions",
        "--path",
        "-p",
        help="Path for templates directory",
    ),
) -> None:
    """Initialize the instruction templates directory.

    Creates the templates directory with a README example.
    """
    manager = TemplateManager(path)
    manager.create_templates_directory()

    console.print(f"[green]✓[/green] Templates directory created: [cyan]{path}[/cyan]")
    console.print("\nNext steps:")
    console.print("  1. Create template files in the templates directory")
    console.print("  2. Use [cyan]instructions list[/cyan] to see available templates")
    console.print("  3. Use [cyan]instructions apply <name>[/cyan] to create issues")


# =============================================================================
# JSON Template Commands
# =============================================================================


@template_app.command("save")
def template_save(
    issue_id: str = typer.Argument(..., help="Issue ID to save as template"),
    name: str = typer.Option(..., "--name", "-n", help="Template name"),
    description: str = typer.Option("", "--description", "-d", help="Template description"),
    templates_dir: str = typer.Option(
        ".work/db-issues/templates",
        "--templates-dir",
        help="Path to templates directory",
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing template"),
) -> None:
    """Save an issue as a JSON template.

    Saves the current configuration of an issue as a reusable template.
    """
    service = JsonTemplateService(templates_dir)

    # Check if template exists
    if service.template_exists(name) and not overwrite:
        console.print(f"[red]Template already exists: {name}[/red]")
        console.print("Use --overwrite to replace the existing template.")
        raise typer.Exit(1)

    # Get issue from database
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        issue = issue_service.get_issue(issue_id)
        if not issue:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        # Save as template
        template = service.save_issue_as_template(
            issue,
            name=name,
            description=description or None,
            overwrite=overwrite,
        )

    console.print(f"[green]✓[/green] Saved issue as template: [cyan]{name}[/cyan]")
    console.print(f"  Description: {template.description}")
    console.print(
        f"  Defaults: type={template.issue_type.value}, priority={template.priority.value}"
    )
    if template.labels:
        console.print(f"  Labels: {', '.join(template.labels)}")


@template_app.command("list")
def template_list(
    templates_dir: str = typer.Option(
        ".work/db-issues/templates",
        "--templates-dir",
        "-t",
        help="Path to templates directory",
    ),
) -> None:
    """List all available JSON templates."""
    service = JsonTemplateService(templates_dir)
    templates = service.list_templates()

    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        console.print(f"  Templates directory: {templates_dir}")
        console.print("\nCreate templates with:")
        console.print("  [cyan]template save <issue_id> --name <name>[/cyan]")
        return

    table = Table(title=f"JSON Templates ({len(templates)} found)")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Type", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Labels", style="magenta")

    for template in templates:
        labels_str = ", ".join(template.labels) if template.labels else ""
        table.add_row(
            template.name,
            template.description[:40] + "..."
            if len(template.description) > 40
            else template.description,
            template.issue_type.value,
            template.priority.name,
            labels_str,
        )

    console.print(table)


@template_app.command("show")
def template_show(
    name: str = typer.Argument(..., help="Template name (filename without .json extension)"),
    templates_dir: str = typer.Option(
        ".work/db-issues/templates",
        "--templates-dir",
        "-t",
        help="Path to templates directory",
    ),
) -> None:
    """Show details of a specific JSON template."""
    service = JsonTemplateService(templates_dir)
    template = service.get_template(name)

    if not template:
        console.print(f"[red]Template not found: {name}[/red]")
        console.print(f"  Searched in: {templates_dir}")
        raise typer.Exit(1)

    # Display template details
    console.print(f"[bold cyan]Template:[/bold cyan] {template.name}")
    console.print(f"[bold]Description:[/bold] {template.description}")
    console.print(f"[bold]Source:[/bold] {template.source_path}")

    console.print("\n[bold]Defaults:[/bold]")
    console.print(f"  Type: {template.issue_type.value}")
    console.print(f"  Priority: {template.priority.name}")
    if template.labels:
        console.print(f"  Labels: {', '.join(template.labels)}")

    if template.description_template:
        console.print("\n[bold]Description Template:[/bold]")
        # Show first few lines of template
        lines = template.description_template.split("\n")[:5]
        for line in lines:
            console.print(f"  {line}")
        if len(template.description_template.split("\n")) > 5:
            console.print("  ...")


@template_app.command("delete")
def template_delete(
    name: str = typer.Argument(..., help="Template name (filename without .json extension)"),
    templates_dir: str = typer.Option(
        ".work/db-issues/templates",
        "--templates-dir",
        "-t",
        help="Path to templates directory",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a JSON template."""
    service = JsonTemplateService(templates_dir)

    if not service.template_exists(name):
        console.print(f"[red]Template not found: {name}[/red]")
        console.print(f"  Searched in: {templates_dir}")
        raise typer.Exit(1)

    if not force:
        typer.confirm(f"Delete template '{name}'?", abort=True)

    if service.delete_template(name):
        console.print(f"[green]✓[/green] Template deleted: [cyan]{name}[/cyan]")
    else:
        console.print(f"[red]Error:[/red] Failed to delete template: {name}")
        raise typer.Exit(1)


# =============================================================================
# Bulk Operations Commands
# =============================================================================


@bulk_app.command("create")
def bulk_create(
    file: str = typer.Option(..., "--file", "-f", help="Input file (CSV or JSON)"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
) -> None:
    """Bulk create issues from CSV or JSON file.

    CSV format:
        title,priority,type,description,assignee,labels
        "Fix parser",high,bug,"Parser fails","john","bug,urgent"

    JSON format:
        [{"title": "Fix parser", "priority": "high", "type": "bug"}]
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)
        bulk_service = BulkService(issue_service, id_service, clock)

        try:
            # Parse input file
            console.print(f"[cyan]Reading:[/cyan] {file}")
            issues_data = bulk_service.parse_file(file)

            if not issues_data:
                console.print("[yellow]No issues found in input file[/yellow]")
                return

            console.print(f"[cyan]Found:[/cyan] {len(issues_data)} issue(s) to create")

            if dry_run:
                console.print("\n[bold]Dry run mode - no changes will be made[/bold]")
                for idx, issue_data in enumerate(issues_data, start=1):
                    console.print(f"  {idx}. {issue_data.title[:50]}")
                return

            # Show preview
            console.print("\n[bold]Preview:[/bold]")
            for idx, issue_data in enumerate(issues_data[:5], start=1):
                preview = (
                    f"{idx}. {issue_data.title[:50]} ({issue_data.priority}, {issue_data.type})"
                )
                console.print(f"  {preview}")
            if len(issues_data) > 5:
                console.print(f"  ... and {len(issues_data) - 5} more")

            # Confirm
            console.print(f"\n[cyan]Creating {len(issues_data)} issues...[/cyan]")
            result = bulk_service.bulk_create(issues_data)

            # Show results
            _show_bulk_result(result)

        except FileNotFoundError:
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(1) from None
        except ValueError as e:
            console.print(f"[red]Error:[/red] Invalid input format: {e}")
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@bulk_app.command("close")
def bulk_close(
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),
    priority: str | None = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    type_filter: str | None = typer.Option(None, "--type", "-t", help="Filter by issue type"),
    assignee: str | None = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
) -> None:
    """Bulk close issues by filter criteria.

    By default, closes all open and in-progress issues.
    Use filters to narrow the scope.
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)
        bulk_service = BulkService(issue_service, id_service, clock)

        try:
            # Parse filters
            status_filter = IssueStatus(status) if status else None
            priority_filter = IssuePriority[priority.upper()] if priority else None
            type_filter_enum = IssueType[type_filter.upper()] if type_filter else None

            if dry_run:
                # Show what would be closed
                issues = issue_service.list_issues(
                    status=status_filter,
                    priority=priority_filter,
                    issue_type=type_filter_enum,
                    assignee=assignee,
                    limit=1000,
                )
                # Filter to only close open/in-progress if no status specified
                if status is None:
                    issues = [
                        i
                        for i in issues
                        if i.status in (IssueStatus.PROPOSED, IssueStatus.IN_PROGRESS)
                    ]

                console.print(f"[bold]Dry run mode - {len(issues)} issues would be closed:[/bold]")
                for idx, issue in enumerate(issues[:10], start=1):
                    console.print(f"  {idx}. {issue.id}: {issue.title[:50]} ({issue.status.value})")
                if len(issues) > 10:
                    console.print(f"  ... and {len(issues) - 10} more")
                return

            # Show what will be closed
            issues = issue_service.list_issues(
                status=status_filter,
                priority=priority_filter,
                issue_type=type_filter_enum,
                assignee=assignee,
                limit=1000,
            )
            # Filter to only close open/in-progress if no status specified
            if status is None:
                issues = [
                    i for i in issues if i.status in (IssueStatus.PROPOSED, IssueStatus.IN_PROGRESS)
                ]

            if not issues:
                console.print("[yellow]No issues found matching close criteria[/yellow]")
                return

            console.print(f"[cyan]Closing {len(issues)} issue(s)...[/cyan]")

            # Perform bulk close
            result = bulk_service.bulk_close(
                status=status_filter,
                priority=priority_filter,
                issue_type=type_filter_enum,
                assignee=assignee,
            )

            # Show results
            _show_bulk_result(result)

        except KeyError as e:
            console.print(f"[red]Error:[/red] Invalid filter value: {e}")
            console.print("Valid statuses: proposed, in_progress, blocked, completed, wont_fix")
            console.print("Valid priorities: critical, high, medium, low")
            console.print(
                "Valid types: bug, feature, task, enhancement, refactor, docs, test, security, performance"
            )
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


@bulk_app.command("update")
def bulk_update(
    set_status: str | None = typer.Option(None, "--set-status", help="New status to set"),
    set_priority: str | None = typer.Option(None, "--set-priority", help="New priority to set"),
    set_type: str | None = typer.Option(None, "--set-type", help="New type to set"),
    set_assignee: str | None = typer.Option(None, "--set-assignee", help="New assignee to set"),
    set_epic: str | None = typer.Option(None, "--set-epic", help="New epic ID to set"),
    filter_status: str | None = typer.Option(
        None, "--status", "-s", help="Filter by current status"
    ),
    filter_priority: str | None = typer.Option(
        None, "--priority", "-p", help="Filter by current priority"
    ),
    filter_type: str | None = typer.Option(None, "--type", "-t", help="Filter by current type"),
    filter_assignee: str | None = typer.Option(
        None, "--assignee", "-a", help="Filter by current assignee"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
) -> None:
    """Bulk update issues by filter criteria.

    At least one --set-* option must be specified.

    Examples:
        # Set high priority for all bugs
        bulk-update --type bug --set-priority high

        # Set in-progress for all high priority issues
        bulk-update --priority high --set-status in_progress

        # Assign all unassigned issues to john
        bulk-update --set-assignee john
    """
    # Check that at least one --set option is provided
    if not any([set_status, set_priority, set_type, set_assignee, set_epic]):
        console.print("[red]Error:[/red] At least one --set-* option must be specified")
        console.print("\nAvailable options:")
        console.print("  --set-status STATUS    Set new status")
        console.print("  --set-priority PRIORITY Set new priority")
        console.print("  --set-type TYPE        Set new type")
        console.print("  --set-assignee USER    Set new assignee")
        console.print("  --set-epic EPIC_ID     Set new epic ID")
        raise typer.Exit(1)

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)
        bulk_service = BulkService(issue_service, id_service, clock)

        try:
            # Parse --set values
            new_status = IssueStatus(set_status) if set_status else None
            new_priority = IssuePriority[set_priority.upper()] if set_priority else None
            new_type = IssueType[set_type.upper()] if set_type else None

            # Parse filter values
            filter_status_enum = IssueStatus(filter_status) if filter_status else None
            filter_priority_enum = (
                IssuePriority[filter_priority.upper()] if filter_priority else None
            )
            filter_type_enum = IssueType[filter_type.upper()] if filter_type else None

            if dry_run:
                # Show what would be updated
                issues = issue_service.list_issues(
                    status=filter_status_enum,
                    priority=filter_priority_enum,
                    issue_type=filter_type_enum,
                    assignee=filter_assignee,
                    limit=1000,
                )

                console.print(f"[bold]Dry run mode - {len(issues)} issues would be updated:[/bold]")
                for idx, issue in enumerate(issues[:10], start=1):
                    console.print(f"  {idx}. {issue.id}: {issue.title[:50]}")
                if len(issues) > 10:
                    console.print(f"  ... and {len(issues) - 10} more")
                return

            console.print("[cyan]Updating issues...[/cyan]")

            # Perform bulk update
            result = bulk_service.bulk_update(
                status=new_status,
                priority=new_priority,
                issue_type=new_type,
                assignee=set_assignee,
                epic_id=set_epic,
                filter_status=filter_status_enum,
                filter_priority=filter_priority_enum,
                filter_type=filter_type_enum,
                filter_assignee=filter_assignee,
            )

            # Show results
            _show_bulk_result(result)

        except KeyError as e:
            console.print(f"[red]Error:[/red] Invalid value: {e}")
            console.print("Valid statuses: proposed, in_progress, blocked, completed, wont_fix")
            console.print("Valid priorities: critical, high, medium, low")
            console.print(
                "Valid types: bug, feature, task, enhancement, refactor, docs, test, security, performance"
            )
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None


def _show_bulk_result(result: BulkResult) -> None:
    """Display bulk operation result.

    Args:
        result: Bulk operation result to display
    """
    console.print(f"\n[bold]Result:[/bold] {result.succeeded}/{result.total} succeeded")

    if result.succeeded > 0:
        console.print(f"[green]✓[/green] {result.succeeded} operation(s) successful")

    if result.failed > 0:
        console.print(f"[red]✗[/red] {result.failed} operation(s) failed")

        # Show errors (limited to first 10)
        if result.errors:
            console.print("\n[bold]Errors:[/bold]")
            for idx, (item, error) in enumerate(result.errors[:10], start=1):
                console.print(f"  {idx}. {item[:50]}: {error}")
            if len(result.errors) > 10:
                console.print(f"  ... and {len(result.errors) - 10} more errors")

    # Show created/modified issue IDs (limited to first 20)
    if result.issue_ids:
        console.print(f"\n[cyan]Affected issues ({len(result.issue_ids)}):[/cyan]")
        for idx, issue_id in enumerate(result.issue_ids[:20], start=1):
            console.print(f"  {idx}. {issue_id}")
        if len(result.issue_ids) > 20:
            console.print(f"  ... and {len(result.issue_ids) - 20} more")



# =============================================================================
# Search Index Commands
# =============================================================================


@search_index_app.command("create")
def search_index_create() -> None:
    """Create full-text search index for existing databases.

    Creates the FTS5 virtual table and triggers if they don't exist.
    Populates the index with existing issues.

    Examples:
        db-issues search-index create
    """
    from dot_work.db_issues.config import DbIssuesConfig

    config = DbIssuesConfig.from_env()

    if not config.db_path.exists():
        console.print(f"[red]Error:[/red] Database not found at {config.db_path}")
        console.print("Run 'db-issues init' to create the database first")
        raise typer.Exit(1)

    console.print("[cyan]Creating full-text search index...[/cyan]")
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session, text

    with Session(engine) as session:
        # Check if FTS5 table already exists
        result = session.exec(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='issues_fts';")
        )  # type: ignore[call-overload]
        exists = result.first() is not None

        if exists:
            console.print("[yellow]FTS5 index already exists[/yellow]")
            console.print("Use 'db-issues search-index rebuild' to rebuild the index")
            return

        # Create FTS5 virtual table
        session.exec(text("""
            CREATE VIRTUAL TABLE issues_fts USING fts5(
                rowid,
                id UNINDEXED,
                title,
                description,
                content='issues',
                content_rowid='rowid'
            );
        """))  # type: ignore[call-overload]

        # Populate FTS5 table with existing data
        insert_result = session.exec(text("""
            INSERT INTO issues_fts(rowid, id, title, description)
            SELECT rowid, id, title, COALESCE(description, '')
            FROM issues;
        """))  # type: ignore[call-overload]

        # Create triggers to keep FTS table in sync
        session.exec(text("""
            CREATE TRIGGER issues_fts_insert AFTER INSERT ON issues BEGIN
                INSERT INTO issues_fts(rowid, id, title, description)
                VALUES (NEW.rowid, NEW.id, NEW.title, COALESCE(NEW.description, ''));
            END;
        """))  # type: ignore[call-overload]

        session.exec(text("""
            CREATE TRIGGER issues_fts_update AFTER UPDATE ON issues BEGIN
                UPDATE issues_fts
                SET title = NEW.title,
                    description = COALESCE(NEW.description, '')
                WHERE rowid = NEW.rowid;
            END;
        """))  # type: ignore[call-overload]

        session.exec(text("""
            CREATE TRIGGER issues_fts_delete AFTER DELETE ON issues BEGIN
                DELETE FROM issues_fts WHERE rowid = OLD.rowid;
            END;
        """))  # type: ignore[call-overload]

        session.commit()

        # Count indexed issues
        count_result = session.exec(text("SELECT COUNT(*) as cnt FROM issues_fts;"))  # type: ignore[call-overload]
        indexed_count = count_result.first().cnt if count_result else 0

    console.print(f"[green]✓[/green] FTS5 index created with [bold]{indexed_count}[/bold] issues")


@search_index_app.command("rebuild")
def search_index_rebuild() -> None:
    """Rebuild the full-text search index from scratch.

    Clears and repopulates the FTS5 index with all current issues.

    Examples:
        db-issues search-index rebuild
    """
    from dot_work.db_issues.config import DbIssuesConfig

    config = DbIssuesConfig.from_env()

    if not config.db_path.exists():
        console.print(f"[red]Error:[/red] Database not found at {config.db_path}")
        raise typer.Exit(1)

    console.print("[cyan]Rebuilding full-text search index...[/cyan]")
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session, text

    with Session(engine) as session:
        # Check if FTS5 table exists
        result = session.exec(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='issues_fts';")
        )  # type: ignore[call-overload]
        exists = result.first() is not None

        if not exists:
            console.print("[yellow]FTS5 index does not exist[/yellow]")
            console.print("Use 'db-issues search-index create' to create the index")
            raise typer.Exit(1)

        # Clear existing FTS data
        session.exec(text("DELETE FROM issues_fts;"))  # type: ignore[call-overload]

        # Rebuild from issues table
        insert_result = session.exec(text("""
            INSERT INTO issues_fts(rowid, id, title, description)
            SELECT rowid, id, title, COALESCE(description, '')
            FROM issues;
        """))  # type: ignore[call-overload]

        session.commit()

        # Count indexed issues
        count_result = session.exec(text("SELECT COUNT(*) as cnt FROM issues_fts;"))  # type: ignore[call-overload]
        indexed_count = count_result.first().cnt if count_result else 0

    console.print(f"[green]✓[/green] FTS5 index rebuilt with [bold]{indexed_count}[/bold] issues")


@search_index_app.command("status")
def search_index_status() -> None:
    """Show full-text search index status.

    Displays information about the FTS5 index including
    the number of indexed issues and index health.

    Examples:
        db-issues search-index status
    """
    from dot_work.db_issues.config import DbIssuesConfig

    config = DbIssuesConfig.from_env()

    if not config.db_path.exists():
        console.print(f"[red]Error:[/red] Database not found at {config.db_path}")
        raise typer.Exit(1)

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session, text

    with Session(engine) as session:
        # Check if FTS5 table exists
        result = session.exec(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='issues_fts';")
        )  # type: ignore[call-overload]
        exists = result.first() is not None

        if not exists:
            console.print("[yellow]FTS5 index not created[/yellow]")
            console.print("Run 'db-issues search-index create' to create the index")
            return

        # Count indexed issues
        fts_count_result = session.exec(text("SELECT COUNT(*) as cnt FROM issues_fts;"))  # type: ignore[call-overload]
        fts_count = fts_count_result.first().cnt if fts_count_result else 0

        # Count total issues
        issues_count_result = session.exec(text("SELECT COUNT(*) as cnt FROM issues;"))  # type: ignore[call-overload]
        issues_count = issues_count_result.first().cnt if issues_count_result else 0

        # Check triggers
        triggers_result = session.exec(text("""
            SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'issues_fts%';
        """))  # type: ignore[call-overload]
        triggers = [row.name for row in triggers_result]

    console.print("[bold]Full-Text Search Index Status[/bold]\n")
    console.print(f"[cyan]Index Status:[/cyan] {'Created' if exists else 'Not created'}")
    console.print(f"[cyan]Indexed Issues:[/cyan] {fts_count}")
    console.print(f"[cyan]Total Issues:[/cyan] {issues_count}")

    if fts_count < issues_count:
        console.print(f"[yellow]Warning:[/yellow] {issues_count - fts_count} issues not indexed")
        console.print("Run 'db-issues search-index rebuild' to fix")
    elif fts_count == issues_count:
        console.print("[green]✓[/green] All issues indexed")

    console.print(f"\n[cyan]Sync Triggers ({len(triggers)}):[/cyan]")
    for trigger in triggers:
        console.print(f"  - {trigger}")


# =============================================================================
# System Commands
# =============================================================================


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Reinitialize database (overwrite)"),
) -> None:
    """Initialize the issue tracker database.

    Creates the database directory and initializes all tables.

    Examples:
        # Initialize database
        db-issues init

        # Reinitialize (overwrite existing database)
        db-issues init --force
    """
    from dot_work.db_issues.config import DbIssuesConfig

    config = DbIssuesConfig.from_env()

    # Check if database already exists
    if config.db_path.exists():
        if not force:
            console.print(f"[yellow]Database already exists at:[/yellow] {config.db_path}")
            console.print("\nTo reinitialize and overwrite, use:")
            console.print("  db-issues init --force")
            raise typer.Exit(1)

        console.print(f"[yellow]Removing existing database:[/yellow] {config.db_path}")
        config.db_path.unlink()
        console.print("[green]✓[/green] Existing database removed")

    # Create directory
    console.print(f"[cyan]Creating database directory:[/cyan] {config.base_path}")
    config.ensure_directory()
    console.print("[green]✓[/green] Directory created")

    # Create database schema
    console.print("[cyan]Creating database schema...[/cyan]")
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())

    # Import all models to ensure they're registered with SQLModel metadata
    from sqlmodel import SQLModel


    # Create all tables
    SQLModel.metadata.create_all(engine)
    console.print("[green]✓[/green] Database schema created")

    # Create FTS5 virtual table for full-text search
    console.print("[cyan]Creating full-text search index...[/cyan]")
    from sqlmodel import Session, text

    with Session(engine) as session:
        # Create FTS5 virtual table
        session.exec(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS issues_fts USING fts5(
                rowid,
                id UNINDEXED,
                title,
                description,
                content='issues',
                content_rowid='rowid'
            );
        """))  # type: ignore[call-overload]

        # Populate FTS5 table with existing data
        session.exec(text("""
            INSERT INTO issues_fts(rowid, id, title, description)
            SELECT rowid, id, title, COALESCE(description, '')
            FROM issues;
        """))  # type: ignore[call-overload]

        # Create triggers to keep FTS table in sync
        # Trigger for INSERT
        session.exec(text("""
            CREATE TRIGGER IF NOT EXISTS issues_fts_insert AFTER INSERT ON issues BEGIN
                INSERT INTO issues_fts(rowid, id, title, description)
                VALUES (NEW.rowid, NEW.id, NEW.title, COALESCE(NEW.description, ''));
            END;
        """))  # type: ignore[call-overload]

        # Trigger for UPDATE
        session.exec(text("""
            CREATE TRIGGER IF NOT EXISTS issues_fts_update AFTER UPDATE ON issues BEGIN
                UPDATE issues_fts
                SET title = NEW.title,
                    description = COALESCE(NEW.description, '')
                WHERE rowid = NEW.rowid;
            END;
        """))  # type: ignore[call-overload]

        # Trigger for DELETE
        session.exec(text("""
            CREATE TRIGGER IF NOT EXISTS issues_fts_delete AFTER DELETE ON issues BEGIN
                DELETE FROM issues_fts WHERE rowid = OLD.rowid;
            END;
        """))  # type: ignore[call-overload]

        session.commit()

    console.print("[green]✓[/green] Full-text search index created")

    # Report success
    console.print("\n[bold green]Database initialized successfully![/bold green]")
    console.print(f"\n[cyan]Database location:[/cyan] {config.db_path}")

    # Show initial state
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)

        # Count issues
        issue_count = len(uow.issues.list_issues(limit=1))
        epic_count = len(uow.epics.list_epics(limit=1))
        label_count = len(uow.labels.list_labels(limit=1))

    console.print("\n[cyan]Current state:[/cyan]")
    console.print(f"  Issues: {issue_count}")
    console.print(f"  Epics: {epic_count}")
    console.print(f"  Labels: {label_count}")


@app.command()
def info() -> None:
    """Show system information and database statistics.

    Displays database path, size, and counts of issues, epics, labels, etc.

    Examples:
        db-issues info
    """
    from dot_work.db_issues.config import DbIssuesConfig

    config = DbIssuesConfig.from_env()
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())

    console.print("[bold]Issue Tracker Information[/bold]\n")

    # Database information
    console.print(f"[cyan]Database:[/cyan] {config.db_path}")

    # Get database size
    if config.db_path.exists():
        size_bytes = config.db_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        console.print(f"[cyan]Size:[/cyan] {size_mb:.2f} MB")
    else:
        console.print("[cyan]Size:[/cyan] (database does not exist)")
        console.print("\n[yellow]Run 'db-issues init' to initialize the database.[/yellow]")
        raise typer.Exit(1)

    # Get statistics
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        issue_service = IssueService(uow, DefaultIdentifierService(), DefaultClock())

        # Get all issues
        all_issues = issue_service.list_issues(limit=100000)

        # Count by status
        status_counts: dict[str, int] = {}
        for issue in all_issues:
            status = issue.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        # Count by priority
        priority_counts: dict[str, int] = {}
        for issue in all_issues:
            priority = issue.priority.name
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Count epics and labels
        epics = uow.epics.list_epics(limit=100000)
        labels = uow.labels.list_labels(limit=100000)

        # Get dependencies count
        deps = uow.graph.list_all_dependencies()

        # Get last activity
        last_activity = None
        if all_issues:
            last_activity = max(issue.updated_at for issue in all_issues)

    console.print(f"\n[cyan]Issues:[/cyan] {len(all_issues)}")

    # Status breakdown
    if status_counts:
        console.print("\n  [cyan]By Status:[/cyan]")
        for status, count in sorted(status_counts.items()):
            percentage = (count / len(all_issues)) * 100 if all_issues else 0
            console.print(f"    {status}: {count} ({percentage:.1f}%)")

    # Priority breakdown
    if priority_counts:
        console.print("\n  [cyan]By Priority:[/cyan]")
        for priority, count in sorted(priority_counts.items()):
            percentage = (count / len(all_issues)) * 100 if all_issues else 0
            console.print(f"    {priority}: {count} ({percentage:.1f}%)")

    console.print(f"\n[cyan]Epics:[/cyan] {len(epics)}")
    console.print(f"[cyan]Labels:[/cyan] {len(labels)}")
    console.print(f"[cyan]Dependencies:[/cyan] {len(deps)}")

    if last_activity:
        console.print(f"\n[cyan]Last activity:[/cyan] {last_activity.strftime('%Y-%m-%d %H:%M:%S')}")


@app.command()
def stats(
    group_by: str | None = typer.Option(None, "--by", "-b", help="Group by: status, priority, type"),
    trend: bool = typer.Option(False, "--trend", "-t", help="Show trends over time"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
) -> None:
    """Show statistics and metrics for issues.

    Displays comprehensive statistics including counts by status, priority,
    type, and calculated metrics like average resolution time.

    Examples:
        # Overall statistics
        db-issues stats

        # Group by status
        db-issues stats --by status

        # Group by priority
        db-issues stats --by priority

        # JSON output
        db-issues stats --format json
    """
    from dot_work.db_issues.config import DbIssuesConfig

    config = DbIssuesConfig.from_env()

    if not config.db_path.exists():
        console.print(f"[red]Error:[/red] Database not found at {config.db_path}")
        raise typer.Exit(1)

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        stats_service = StatsService(session)
        stats = stats_service.get_statistics()

    if format == "json":
        _output_stats_json(stats, console)
    else:
        _output_stats_table(stats, console, group_by)


def _output_stats_table(stats: Statistics, console: Console, group_by: str | None) -> None:
    """Output statistics as a formatted table."""
    console.print("[bold]Issue Statistics[/bold]\n")
    console.print(f"[cyan]Total Issues:[/cyan] {stats.total}")

    if group_by == "status" or group_by is None:
        if stats.by_status:
            console.print("\n[bold]By Status:[/bold]")
            for stat in stats.by_status:
                console.print(f"  {stat.status:15} {stat.count:4} ({stat.percentage:5.1f}%)")

    if group_by == "priority" or group_by is None:
        if stats.by_priority:
            console.print("\n[bold]By Priority:[/bold]")
            for stat in stats.by_priority:
                console.print(f"  {stat.priority:15} {stat.count:4} ({stat.percentage:5.1f}%)")

    if group_by == "type" or group_by is None:
        if stats.by_type:
            console.print("\n[bold]By Type:[/bold]")
            for stat in stats.by_type:
                console.print(f"  {stat.type:15} {stat.count:4} ({stat.percentage:5.1f}%)")

    console.print("\n[bold]Metrics:[/bold]")
    console.print(f"  Blocked issues:        {stats.metrics.blocked_count}")
    console.print(f"  Ready to work:         {stats.metrics.ready_to_work_count}")
    console.print(f"  Longest chain:         {stats.metrics.longest_dependency_chain}")
    if stats.metrics.avg_resolution_time_days:
        console.print(f"  Avg resolution time:  {stats.metrics.avg_resolution_time_days} days")


def _output_stats_json(stats: Statistics, console: Console) -> None:
    """Output statistics as JSON."""
    from rich.json import JSON

    data = {
        "total": stats.total,
        "by_status": [
            {"status": s.status, "count": s.count, "percentage": s.percentage}
            for s in stats.by_status
        ],
        "by_priority": [
            {"priority": s.priority, "count": s.count, "percentage": s.percentage}
            for s in stats.by_priority
        ],
        "by_type": [
            {"type": s.type, "count": s.count, "percentage": s.percentage}
            for s in stats.by_type
        ],
        "metrics": {
            "blocked_count": stats.metrics.blocked_count,
            "ready_to_work_count": stats.metrics.ready_to_work_count,
            "longest_dependency_chain": stats.metrics.longest_dependency_chain,
            "avg_resolution_time_days": stats.metrics.avg_resolution_time_days,
        },
    }

    console.print(JSON(data))


@app.command()
def compact(
    vacuum: bool = typer.Option(
        False, "--vacuum", "-v", help="Run VACUUM for deep compaction"
    ),
) -> None:
    """Compact database to reduce size.

    Runs SQLite optimization to reclaim space and reduce database size.

    Examples:
        # Compact database
        db-issues compact

        # Deep compact with VACUUM
        db-issues compact --vacuum
    """
    from dot_work.db_issues.config import DbIssuesConfig

    config = DbIssuesConfig.from_env()

    if not config.db_path.exists():
        console.print(f"[red]Error:[/red] Database not found at {config.db_path}")
        console.print("\nRun 'db-issues init' to initialize the database.")
        raise typer.Exit(1)

    # Get size before
    size_before = config.db_path.stat().st_size
    size_before_mb = size_before / (1024 * 1024)

    console.print("[cyan]Compacting database...[/cyan]")
    console.print(f"Before: {size_before_mb:.2f} MB")

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())

    if vacuum:
        # Run VACUUM for deep compaction
        from sqlmodel import Session

        with Session(engine) as session:
            console.print("[cyan]Running VACUUM...[/cyan]")
            session.exec("VACUUM")
            session.commit()
    else:
        # Run ANALYZE for optimization
        from sqlmodel import Session

        with Session(engine) as session:
            console.print("[cyan]Running ANALYZE...[/cyan]")
            session.exec("ANALYZE")
            session.commit()

    # Get size after
    size_after = config.db_path.stat().st_size
    size_after_mb = size_after / (1024 * 1024)
    saved_mb = size_before_mb - size_after_mb
    saved_pct = (saved_mb / size_before_mb) * 100 if size_before_mb > 0 else 0

    console.print(f"After: {size_after_mb:.2f} MB")

    if saved_mb > 0:
        console.print(
            f"[green]Saved: {saved_mb:.2f} MB ({saved_pct:.1f}% reduction)[/green]"
        )
    else:
        console.print("[yellow]No space saved (database may already be optimized)[/yellow]")


@app.command()
def rename_prefix(
    old_prefix: str = typer.Argument(..., help="Current prefix to rename (e.g., FEAT)"),
    new_prefix: str = typer.Argument(..., help="New prefix (e.g., FEATURE)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without making changes"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Rename issue ID prefixes for consistency.

    Examples:
        # Rename FEAT to FEATURE
        db-issues rename-prefix FEAT FEATURE

        # Preview changes
        db-issues rename-prefix BUG DEFECT --dry-run

        # Skip confirmation
        db-issues rename-prefix TASK WORK --yes
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        # Find all issues with the old prefix
        all_issues = issue_service.list_issues(limit=100000)
        matching_issues = [issue for issue in all_issues if issue.id.startswith(f"{old_prefix}-")]

        if not matching_issues:
            console.print(f"[yellow]No issues found with prefix:[/yellow] {old_prefix}-")
            raise typer.Exit(0)

        # Show what will be renamed
        console.print(f"[bold]Found {len(matching_issues)} issue(s) with prefix:[/bold] {old_prefix}-")
        console.print()

        # Show first few examples
        for idx, issue in enumerate(matching_issues[:5], start=1):
            old_id = issue.id
            new_id = f"{new_prefix}-{old_id.split('-', 1)[1]}"
            console.print(f"  {idx}. {old_id} -> {new_id}")

        if len(matching_issues) > 5:
            console.print(f"  ... and {len(matching_issues) - 5} more")

        if dry_run:
            console.print("\n[yellow]Dry run mode - no changes made.[/yellow]")
            console.print("Run without --dry-run to perform the rename.")
            raise typer.Exit(0)

        # Confirmation prompt
        if not yes:
            console.print(f"\n[bold]Rename {len(matching_issues)} issue(s)?[/bold] [y/N]: ", end="")
            response = input().strip().lower()
            if response not in ("y", "yes"):
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(0)

        # Perform rename
        console.print(f"\n[cyan]Renaming {len(matching_issues)} issue(s)...[/cyan]")

        # Use UnitOfWork context for transactional updates
        with uow:
            renamed_count = 0
            for issue in matching_issues:
                # Generate new ID
                old_id = issue.id
                suffix = old_id.split('-', 1)[1]
                new_id = f"{new_prefix}-{suffix}"

                # Delete old issue and create new one with renamed ID
                uow.issues.delete(old_id)

                # Create new issue with new ID
                renamed_issue = Issue(
                    id=new_id,
                    project_id=issue.project_id,
                    title=issue.title,
                    description=issue.description,
                    status=issue.status,
                    priority=issue.priority,
                    type=issue.type,
                    assignee=issue.assignee,
                    epic_id=issue.epic_id,
                    labels=issue.labels.copy(),
                    blocked_reason=issue.blocked_reason,
                    created_at=issue.created_at,
                    updated_at=clock.now(),
                    closed_at=issue.closed_at,
                )
                uow.issues.save(renamed_issue)
                renamed_count += 1

        console.print(f"[green]✓[/green] Renamed [bold]{renamed_count}[/bold] issue(s)")


@app.command()
def cleanup(
    status: str = typer.Option("completed", "--status", "-s", help="Filter by status"),
    days: int = typer.Option(90, "--days", "-d", help="Issues older than N days"),
    archive: bool = typer.Option(False, "--archive", "-a", help="Archive instead of delete"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without changes"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Clean up old completed issues by archiving or deleting them.

    Examples:
        # Delete completed issues older than 90 days
        db-issues cleanup --status completed --days 90

        # Archive instead of delete
        db-issues cleanup --archive

        # Preview what would be cleaned up
        db-issues cleanup --dry-run
    """
    from datetime import timedelta

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        # Parse status filter
        try:
            status_enum = IssueStatus(status)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid status '{status}'")
            console.print(f"Valid values: {', '.join(s.value for s in IssueStatus)}")
            raise typer.Exit(1)

        # Get all issues and filter by status and age
        all_issues = issue_service.list_issues(limit=100000)
        cutoff = clock.now() - timedelta(days=days)

        matching_issues = [
            issue
            for issue in all_issues
            if issue.status == status_enum and issue.updated_at < cutoff
        ]

        if not matching_issues:
            console.print(
                f"[yellow]No issues found with status:[/yellow] {status} older than {days} days"
            )
            raise typer.Exit(0)

        # Sort by updated_at
        matching_issues.sort(key=lambda x: x.updated_at)

        # Show what will be cleaned up
        action = "Archived" if archive else "Deleted"
        console.print(
            f"[bold]Found {len(matching_issues)} issue(s) with status:[/bold] {status} older than {days} days"
        )
        console.print()

        # Show oldest issues
        for idx, issue in enumerate(matching_issues[:5], start=1):
            age_days = (clock.now() - issue.updated_at).days
            console.print(
                f"  {idx}. {issue.id}: {issue.title[:40]}... ({age_days} days old)"
            )

        if len(matching_issues) > 5:
            console.print(f"  ... and {len(matching_issues) - 5} more")

        if dry_run:
            console.print("\n[yellow]Dry run mode - no changes made.[/yellow]")
            console.print("Run without --dry-run to perform the cleanup.")
            raise typer.Exit(0)

        # Confirmation prompt
        if not force:
            console.print(f"\n[bold]{action} {len(matching_issues)} issue(s)?[/bold] [y/N]: ", end="")
            response = input().strip().lower()
            if response not in ("y", "yes"):
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(0)

        if archive:
            # Archive to JSONL file
            from pathlib import Path

            # Create archive directory
            archive_dir = Path.cwd() / ".work" / "db-issues" / "archive"
            month_dir = archive_dir / clock.now().strftime("%Y-%m")
            month_dir.mkdir(parents=True, exist_ok=True)

            # Create archive file
            timestamp = clock.now().strftime("%Y-%m-%d")
            archive_file = month_dir / f"issues-{timestamp}.jsonl"

            console.print(f"\n[cyan]Archiving to:[/cyan] {archive_file}")

            # Write archive
            import json

            with open(archive_file, "w") as f:
                for issue in matching_issues:
                    data = {
                        "id": issue.id,
                        "project_id": issue.project_id,
                        "title": issue.title,
                        "description": issue.description,
                        "status": issue.status.value,
                        "priority": issue.priority.value,
                        "type": issue.type.value,
                        "assignee": issue.assignee,
                        "epic_id": issue.epic_id,
                        "labels": issue.labels,
                        "blocked_reason": issue.blocked_reason,
                        "created_at": issue.created_at.isoformat(),
                        "updated_at": issue.updated_at.isoformat(),
                    }
                    if issue.closed_at:
                        data["closed_at"] = issue.closed_at.isoformat()
                    f.write(json.dumps(data, separators=(",", ":")) + "\n")

            # Delete archived issues from database
            with uow:
                for issue in matching_issues:
                    uow.issues.delete(issue.id)

            console.print(
                f"[green]✓[/green] Archived [bold]{len(matching_issues)}[/bold] issue(s)"
            )
        else:
            # Delete issues
            console.print(f"\n[cyan]Deleting {len(matching_issues)} issue(s)...[/cyan]")

            with uow:
                for issue in matching_issues:
                    uow.issues.delete(issue.id)

            console.print(
                f"[green]✓[/green] Deleted [bold]{len(matching_issues)}[/bold] issue(s)"
            )


@app.command()
def duplicates(
    threshold: float = typer.Option(0.7, "--threshold", "-t", help="Similarity threshold (0-1)"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
) -> None:
    """Find potential duplicate issues based on title similarity.

    Examples:
        # Find duplicates with default threshold (0.7)
        db-issues duplicates

        # Use higher threshold for stricter matching
        db-issues duplicates --threshold 0.85

        # Output as JSON
        db-issues duplicates --format json
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        # Get all issues
        all_issues = issue_service.list_issues(limit=100000)

        if not all_issues:
            console.print("[yellow]No issues found to scan.[/yellow]")
            raise typer.Exit(0)

        # Run duplicate detection
        console.print(f"[cyan]Scanning {len(all_issues)} issues for duplicates...[/cyan]")

        duplicate_service = DuplicateService(clock=clock)
        result = duplicate_service.find_duplicates(all_issues, threshold=threshold)

        if format == "json":
            # Output as JSON

            output = {
                "total_issues": result.total_issues,
                "duplicates_found": result.duplicates_found,
                "scan_time": result.scan_time,
                "groups": [
                    {
                        "similarity": g.similarity,
                        "issues": g.issues,
                        "representative": g.representative_issue,
                    }
                    for g in result.groups
                ],
            }
            console.print_json(data=output)
        else:
            # Output as table
            if not result.groups:
                console.print(
                    f"[green]No duplicates found with threshold {threshold}.[/green]"
                )
                raise typer.Exit(0)

            console.print(
                f"\n[bold]Potential duplicates found:[/bold] {len(result.groups)} group(s)"
            )
            console.print(f"[dim]Total issues: {result.total_issues}[/dim]")
            console.print(f"[dim]Duplicates: {result.duplicates_found}[/dim]")
            console.print(f"[dim]Scan time: {result.scan_time:.3f}s[/dim]\n")

            # Show each group
            for idx, group in enumerate(result.groups, start=1):
                console.print(f"[bold]{idx}.[/bold] Similarity: [cyan]{group.similarity:.2f}[/cyan]")

                # Show issue details
                issue_map = {issue.id: issue for issue in all_issues}

                for issue_id in group.issues:
                    issue = issue_map.get(issue_id)
                    if issue:
                        # Truncate title if too long
                        title = issue.title[:50] + "..." if len(issue.title) > 50 else issue.title
                        marker = " →" if issue_id == group.representative_issue else "  -"
                        console.print(f"  {marker} [cyan]{issue_id}[/cyan]: {title}")

                console.print()  # Blank line between groups


@app.command()
def merge(
    source_id: str = typer.Argument(..., help="Source issue ID to merge from"),
    target_id: str = typer.Argument(..., help="Target issue ID to merge into"),
    keep_comments: bool = typer.Option(False, "--keep-comments", help="Copy comments from source"),
    keep_labels: bool = typer.Option(True, "--keep-labels/--no-keep-labels", help="Merge labels (default: yes)"),
    close_source: bool = typer.Option(False, "--close-source", help="Close source instead of deleting"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Merge source issue into target issue.

    Combines data from source into target:
    - Labels: union of both sets
    - Dependencies: all dependencies remapped to target
    - Comments: optionally copied from source

    By default, the source issue is deleted after merge.
    Use --close-source to close it instead.

    Examples:
        # Merge bd-c3d4 into bd-a1b2
        db-issues merge bd-c3d4 bd-a1b2

        # Merge with comments
        db-issues merge bd-c3d4 bd-a1b2 --keep-comments

        # Close source instead of delete
        db-issues merge bd-c3d4 bd-a1b2 --close-source
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        # Get both issues for preview
        source = issue_service.get_issue(source_id)
        target = issue_service.get_issue(target_id)

        if not source:
            console.print(f"[red]Source issue not found: {source_id}[/red]")
            raise typer.Exit(1)

        if not target:
            console.print(f"[red]Target issue not found: {target_id}[/red]")
            raise typer.Exit(1)

        if source_id == target_id:
            console.print("[red]Cannot merge issue into itself[/red]")
            raise typer.Exit(1)

        # Show merge preview
        console.print("\n[bold]Merge Preview[/bold]")
        console.print(f"[cyan]Source:[/cyan] {source_id} - {source.title[:60]}")
        console.print(f"[cyan]Target:[/cyan] {target_id} - {target.title[:60]}")

        # Calculate what will happen
        source_label_set = set(source.labels)
        target_label_set = set(target.labels)
        new_labels = source_label_set - target_label_set
        merged_labels = target.labels + sorted(new_labels)

        source_deps = uow.issues.get_dependencies(source_id)
        source_dependents = uow.issues.get_dependents(source_id)
        source_comments = uow.issues.get_comments(source_id) if keep_comments else []

        console.print(f"\n[dim]Labels to add:[/dim] {len(new_labels)} new label(s)")
        if new_labels:
            for label in sorted(new_labels):
                console.print(f"  [green]+[/green] {label}")

        console.print(f"[dim]Merged labels:[/dim] {', '.join(merged_labels)}")

        console.print("\n[dim]Dependencies to remap:[/dim]")
        console.print(f"  [dim]From source ({len(source_deps)} outgoing):[/dim]")
        if source_deps:
            for dep in source_deps[:5]:  # Show max 5
                console.print(f"    {source_id} → {dep.to_issue_id} ({dep.dependency_type.value})")
            if len(source_deps) > 5:
                console.print(f"    ... and {len(source_deps) - 5} more")
        else:
            console.print("    [dim](none)[/dim]")

        console.print(f"  [dim]To source ({len(source_dependents)} incoming):[/dim]")
        if source_dependents:
            for dep in source_dependents[:5]:  # Show max 5
                console.print(f"    {dep.from_issue_id} → {source_id} ({dep.dependency_type.value})")
            if len(source_dependents) > 5:
                console.print(f"    ... and {len(source_dependents) - 5} more")
        else:
            console.print("    [dim](none)[/dim]")

        if keep_comments:
            console.print(f"\n[dim]Comments to copy:[/dim] {len(source_comments)}")

        action = "close" if close_source else "delete"
        console.print(f"\n[dim]Source will be:[/dim] [yellow]{action}d[/yellow]")

        # Confirm
        if not yes:
            console.print("\n[yellow]Proceed with merge?[/yellow] [bold][y/N][/bold]")
            response = input().strip().lower()
            if response not in ("y", "yes"):
                console.print("[yellow]Merge cancelled[/yellow]")
                raise typer.Exit(0)

        # Perform merge
        console.print(f"\n[cyan]Merging {source_id} into {target_id}...[/cyan]")

        try:
            result = issue_service.merge_issues(
                source_id=source_id,
                target_id=target_id,
                keep_comments=keep_comments,
                close_source=close_source,
            )
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

        if result:
            console.print("\n[green]✓ Merge complete[/green]")
            console.print(f"[dim]Labels: {len(result.labels)} total[/dim]")
            console.print(f"[dim]Source {source_id}: {action}d[/dim]")
            console.print("\n[cyan]View target issue:[/cyan]")
            console.print(f"  db-issues show {target_id}")
        else:
            console.print("[red]Merge failed[/red]")
            raise typer.Exit(1)


@app.command()
def edit(
    issue_id: str = typer.Argument(..., help="Issue ID to edit"),
    editor: str | None = typer.Option(None, "--editor", "-e", help="Editor to use (default: $EDITOR)"),
) -> None:
    """Edit an issue in an external editor.

    Opens the issue in your configured editor ($EDITOR or specified via --editor).
    The issue is presented as YAML for easy editing.

    Examples:
        # Edit with default editor
        db-issues edit bd-a1b2

        # Edit with specific editor
        db-issues edit bd-a1b2 --editor vim
        db-issues edit bd-a1b2 -e code
    """
    import hashlib
    import os
    import subprocess
    import tempfile

    import yaml

    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        # Get the issue
        issue = issue_service.get_issue(issue_id)
        if not issue:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        # Determine editor to use
        editor_cmd = editor or os.environ.get("EDITOR")
        if not editor_cmd:
            console.print(
                "[red]No editor configured. Set $EDITOR or use --editor.[/red]"
            )
            console.print("[dim]Examples: --editor vim, --editor nano, --editor code[/dim]")
            raise typer.Exit(1)

        # Get dependencies for this issue
        deps = uow.issues.get_dependencies(issue_id)

        # Build the YAML content
        yaml_content = {
            "id": issue.id,
            "title": issue.title,
            "description": issue.description or "",
            "priority": issue.priority.value,
            "type": issue.issue_type.value,
            "status": issue.status.value,
            "labels": issue.labels,
            "assignee": issue.assignee or "",
        }

        # Add dependencies if any
        if deps:
            yaml_content["dependencies"] = {
                "blocks": [d.to_issue_id for d in deps if d.dependency_type.value == "blocks"],
                "depends_on": [
                    d.to_issue_id for d in deps if d.dependency_type.value == "depends_on"
                ],
            }

        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", prefix=f"edit-{issue.id}-", delete=False
        ) as f:
            # Write header comments
            f.write(f"# dot-work db-issues edit: {issue.id}\n")
            f.write("# Lines starting with # are comments\n")
            f.write("# Save and exit to apply changes\n")
            f.write("# Exit without saving to cancel\n")
            f.write("#\n")

            # Write YAML content
            yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)
            temp_path = f.name

        # Set restrictive permissions (owner read/write only) for security
        Path(temp_path).chmod(0o600)

        # Calculate initial hash for change detection
        with open(temp_path, "rb") as f:
            initial_hash = hashlib.sha256(f.read()).hexdigest()

        try:
            # Validate and parse editor command
            editor_name, editor_args = _validate_editor(editor_cmd)
            console.print(f"[cyan]Opening {issue_id} in {editor_name}...[/cyan]")
            console.print(f"[dim]Temp file: {temp_path}[/dim]")

            # Build editor args with validated components
            result = subprocess.run([editor_name, *editor_args, temp_path])

            if result.returncode != 0:
                console.print(f"[yellow]Editor exited with code {result.returncode}[/yellow]")

            # Check if file was modified
            with open(temp_path, "rb") as f:
                final_hash = hashlib.sha256(f.read()).hexdigest()

            if initial_hash == final_hash:
                console.print("[yellow]No changes detected[/yellow]")
                raise typer.Exit(0)

            # Parse modified file
            with open(temp_path) as f:
                modified_data = yaml.safe_load(f)

            # Validate required fields
            if not isinstance(modified_data, dict):
                console.print("[red]Invalid YAML: must be a dictionary[/red]")
                raise typer.Exit(1)

            required_fields = ["title", "priority", "type", "status"]
            missing = [f for f in required_fields if f not in modified_data]
            if missing:
                console.print(f"[red]Missing required fields: {', '.join(missing)}[/red]")
                raise typer.Exit(1)

            # Build update parameters
            update_params: dict[str, Any] = {}

            # Title
            if modified_data.get("title") != issue.title:
                update_params["title"] = str(modified_data["title"])

            # Description
            new_description = modified_data.get("description", "")
            if new_description != issue.description:
                update_params["description"] = str(new_description) if new_description else None

            # Priority
            try:
                new_priority = IssuePriority(modified_data["priority"])
                if new_priority != issue.priority:
                    update_params["priority"] = new_priority
            except ValueError:
                console.print(f"[red]Invalid priority: {modified_data['priority']}[/red]")
                console.print("[dim]Valid: critical, high, medium, low[/dim]")
                raise typer.Exit(1)

            # Type
            try:
                new_type = IssueType(modified_data["type"])
                if new_type != issue.issue_type:
                    update_params["issue_type"] = new_type
            except ValueError:
                console.print(f"[red]Invalid type: {modified_data['type']}[/red]")
                console.print("[dim]Valid: bug, feature, task, enhancement, refactor, docs, test, security, performance[/dim]")
                raise typer.Exit(1)

            # Status
            try:
                new_status = IssueStatus(modified_data["status"])
                if new_status != issue.status:
                    update_params["status"] = new_status
            except ValueError:
                console.print(f"[red]Invalid status: {modified_data['status']}[/red]")
                console.print("[dim]Valid: proposed, in_progress, blocked, resolved, completed, stale, wont_fix[/dim]")
                raise typer.Exit(1)

            # Labels
            new_labels = modified_data.get("labels", [])
            if isinstance(new_labels, list):
                if new_labels != issue.labels:
                    update_params["labels"] = new_labels
            else:
                console.print("[yellow]Warning: labels must be a list, ignoring[/yellow]")

            # Assignee
            new_assignee = modified_data.get("assignee", "")
            if isinstance(new_assignee, str):
                if new_assignee != (issue.assignee or ""):
                    update_params["assignee"] = new_assignee if new_assignee else None

            # Apply changes
            if update_params:
                console.print(f"\n[cyan]Updating {issue_id}...[/cyan]")

                # Handle status transition
                if "status" in update_params:
                    updated = issue_service.transition_issue(issue_id, update_params["status"])
                    # Remove status from params so we don't double-apply
                    update_params.pop("status")
                else:
                    updated = issue_service.get_issue(issue_id)

                if updated:
                    # Apply remaining updates
                    if update_params:
                        updated = issue_service.update_issue(issue_id, **update_params)

                    if updated:
                        console.print("[green]✓ Issue updated[/green]")
                        console.print(f"[dim]Changes: {', '.join(update_params.keys())}[/dim]")
                    else:
                        console.print("[red]Failed to update issue[/red]")
                        raise typer.Exit(1)

            console.print("\n[cyan]View updated issue:[/cyan]")
            console.print(f"  db-issues show {issue_id}")

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except OSError:
                pass


@app.command()
def restore(
    issue_id: str | None = typer.Argument(None, help="Issue ID to restore"),
    list_deleted: bool = typer.Option(False, "--list", "-l", help="List deleted issues"),
    restore_all: bool = typer.Option(False, "--all", "-a", help="Restore all deleted issues"),
) -> None:
    """Restore soft-deleted issues.

    Examples:
        # List deleted issues
        db-issues restore --list

        # Restore specific issue
        db-issues restore bd-a1b2

        # Restore all deleted issues
        db-issues restore --all
    """
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        issue_service = IssueService(uow, id_service, clock)

        if list_deleted:
            # List deleted issues
            deleted_issues = issue_service.list_deleted_issues(limit=1000)

            if not deleted_issues:
                console.print("[green]No deleted issues found[/green]")
                raise typer.Exit(0)

            console.print(f"\n[bold]Deleted issues:[/bold] {len(deleted_issues)} issue(s)\n")

            for issue in deleted_issues:
                deleted_date = issue.deleted_at.strftime("%Y-%m-%d") if issue.deleted_at else "unknown"
                console.print(f"  [cyan]{issue.id}[/cyan]: {issue.title[:60]}")
                console.print(f"    [dim]Deleted:[/dim] {deleted_date}")
                console.print(f"    [dim]Status:[/dim] {issue.status.value} [dim]Type:[/dim] {issue.issue_type.value}")
                console.print()

        elif restore_all:
            # Restore all deleted issues
            deleted_issues = issue_service.list_deleted_issues(limit=1000)

            if not deleted_issues:
                console.print("[green]No deleted issues found[/green]")
                raise typer.Exit(0)

            console.print(f"\n[cyan]Restoring {len(deleted_issues)} deleted issue(s)...[/cyan]\n")

            restored_count = 0
            failed_count = 0

            for issue in deleted_issues:
                restored = issue_service.restore_issue(issue.id)
                if restored:
                    restored_count += 1
                    console.print(f"  [green]✓[/green] {issue.id}: {issue.title[:50]}")
                else:
                    failed_count += 1
                    console.print(f"  [red]✗[/red] {issue.id}: Failed to restore")

            console.print(f"\n[green]Restored {restored_count} issue(s)[/green]")
            if failed_count > 0:
                console.print(f"[yellow]Failed to restore {failed_count} issue(s)[/yellow]")

        else:
            # Restore specific issue
            if not issue_id:
                console.print("[red]Error: Issue ID required (unless using --list or --all)[/red]")
                console.print("[dim]Usage: db-issues restore <id>[/dim]")
                raise typer.Exit(1)

            # Check if issue exists (is deleted)
            # We need to check if the issue is in the deleted list
            deleted_issues = issue_service.list_deleted_issues(limit=1000)
            deleted_ids = [issue.id for issue in deleted_issues]

            if issue_id not in deleted_ids:
                console.print(f"[yellow]Issue {issue_id} is not deleted or does not exist[/yellow]")
                raise typer.Exit(1)

            console.print(f"[cyan]Restoring {issue_id}...[/cyan]")

            restored = issue_service.restore_issue(issue_id)

            if restored:
                console.print(f"[green]✓ Issue restored: {restored.id}[/green]")
                console.print(f"[dim]{restored.title}[/dim]")
                console.print("\n[cyan]View restored issue:[/cyan]")
                console.print(f"  db-issues show {issue_id}")
            else:
                console.print(f"[red]Failed to restore issue: {issue_id}[/red]")
                raise typer.Exit(1)
