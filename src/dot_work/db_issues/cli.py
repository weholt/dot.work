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
)
from dot_work.db_issues.services import (
    BulkResult,
    BulkService,
    CommentService,
    CycleResult,
    DependencyService,
    EpicService,
    ImpactResult,
    IssueService,
    JsonlService,
    JsonTemplateService,
    LabelService,
    SearchService,
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
            limit=limit,
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
    """Output issues as JSON array.

    Args:
        issues: List of issues to output
        fields: Optional comma-separated field names
        console: Rich console for output
    """
    field_list = _parse_fields(fields)
    output: list[dict[str, object]] = []

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
        output.append(data_dict)

    console.print(json.dumps(output, indent=2))


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
    """Output search results as JSON.

    Args:
        issues: List of (issue, rank, snippet) tuples
        console: Rich console for output
    """
    output = []
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
        output.append(data_dict)

    console.print(json.dumps(output, indent=2))


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


@app.command()
def show(
    issue_id: str = typer.Argument(..., help="Issue ID"),
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


def _get_text_from_editor(template: str = "") -> str:
    """Open editor and get text input from user.

    Args:
        template: Initial text to display in editor

    Returns:
        Text content from editor (with comment lines removed)
    """
    # Determine editor
    editor = os.environ.get("EDITOR", "vi")

    # Create temp file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        prefix="db-issues-editor-",
        delete=False,
    ) as f:
        f.write(template)
        temp_path = Path(f.name)

    try:
        # Open editor
        console.print(f"Opening [cyan]{editor}[/cyan]...")
        result = subprocess.run([editor, str(temp_path)])

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

        # Determine editor
        if not editor:
            editor = os.environ.get("EDITOR", "vi")

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

        try:
            # Open editor
            console.print(f"Opening [cyan]{editor}[/cyan] to edit issue [bold]{issue.id}[/bold]...")
            result = subprocess.run([editor, str(temp_path)])

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
def delete(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an issue."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete issue {issue_id}?")
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

        deleted = service.delete_issue(issue_id)
        if not deleted:
            console.print(f"[red]Issue not found: {issue_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Issue deleted: [bold]{issue_id}[/bold]")


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
) -> None:
    """Show dependency tree for an issue."""
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        service = DependencyService(uow)

        try:
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
    comment_id: str = typer.Argument(..., help="Comment ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a comment."""
    # Create database session and service
    engine = create_db_engine(get_db_url(), echo=is_debug_mode())
    from sqlmodel import Session

    with Session(engine) as session:
        uow = UnitOfWork(session)
        id_service = DefaultIdentifierService()
        clock = DefaultClock()
        service = CommentService(uow, id_service, clock)

        # Get comment to show details
        comment = service.get_comment(comment_id)
        if not comment:
            console.print(f"[red]Error:[/red] Comment not found: {comment_id}")
            raise typer.Exit(1)

        # Verify comment belongs to issue
        if comment.issue_id != issue_id:
            console.print(
                f"[red]Error:[/red] Comment {comment_id} does not belong to issue {issue_id}"
            )
            raise typer.Exit(1)

        # Confirm unless force
        if not force:
            typer.confirm(
                f"Delete comment from {comment.author}?",
                abort=True,
            )

        result = service.delete_comment(comment_id)
        if result:
            console.print(f"[green]✓[/green] Comment deleted: [cyan]{comment_id}[/cyan]")
        else:
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
