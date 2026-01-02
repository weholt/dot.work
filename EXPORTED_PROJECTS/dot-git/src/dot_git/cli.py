"""Command-line interface for git history analysis."""

import json
import logging
import sys
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

from dot_git.formatters import (
    display_commit_analysis,
    display_commit_comparison,
    display_complexity_analysis,
    display_contributor_stats,
    display_release_analysis,
    display_risk_assessment,
    display_table_results,
)
from dot_git.models import AnalysisConfig
from dot_git.services import GitAnalysisService
from dot_git.utils import setup_logging
from dot_work.utils.sanitization import sanitize_error_message

logger = logging.getLogger(__name__)

# Create Typer app for history subcommand
history_app = typer.Typer(
    name="history",
    help="Analyze git history between refs",
    no_args_is_help=True,
)

console = Console()


@history_app.command()
def compare(
    from_ref: str = typer.Argument(..., help="Source git reference (branch, tag, or commit)"),
    to_ref: str = typer.Argument(..., help="Target git reference (branch, tag, or commit)"),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    output_format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, yaml"
    ),
    output_file: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    use_llm: bool = typer.Option(False, "--llm", help="Use LLM for enhanced summaries"),
    llm_provider: str = typer.Option(
        "openai", "--llm-provider", help="LLM provider: openai, anthropic"
    ),
    max_commits: int = typer.Option(
        100, "--max-commits", help="Maximum number of commits to analyze"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Compare two git references with detailed analysis."""
    setup_logging(verbose)

    try:
        # Create configuration
        config = AnalysisConfig(
            repo_path=Path(repo_path),
            use_llm=use_llm,
            llm_provider=llm_provider,
            max_commits=max_commits,
        )

        # Create service
        console.print(f"[blue]Analyzing repository:[/blue] {repo_path}")
        console.print(f"[blue]Comparing:[/blue] {from_ref} → {to_ref}")
        console.print()

        service = GitAnalysisService(config)

        # Perform comparison
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            _ = progress.add_task("Analyzing git history...", total=None)

            result = service.compare_refs(from_ref, to_ref)

        # Display results
        if output_format == "json":
            output_data = _result_to_dict(result)
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(output_data, f, indent=2, default=str)
                console.print(f"[green]Results saved to:[/green] {output_file}")
            else:
                console.print_json(data=output_data)
        elif output_format == "yaml":
            output_data = _result_to_dict(result)
            yaml_output = yaml.dump(output_data, default_flow_style=False, sort_keys=False)
            if output_file:
                with open(output_file, "w") as f:
                    f.write(yaml_output)
                console.print(f"[green]Results saved to:[/green] {output_file}")
            else:
                console.print(Syntax(yaml_output, "yaml"))
        else:
            display_table_results(result)

        # Show risk assessment
        display_risk_assessment(result)

    except Exception as e:
        logger.error(f"Git analysis error: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


@history_app.command()
def analyze(
    commit_hash: str = typer.Argument(..., help="Git commit hash to analyze"),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    output_format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, yaml"
    ),
    use_llm: bool = typer.Option(False, "--llm", help="Use LLM for enhanced summaries"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Analyze a single commit with detailed metrics."""
    setup_logging(verbose)

    try:
        config = AnalysisConfig(repo_path=Path(repo_path), use_llm=use_llm)

        service = GitAnalysisService(config)
        analysis = service.analyze_commit(commit_hash)

        if output_format == "json":
            output_data = _analysis_to_dict(analysis)
            console.print_json(data=output_data)
        elif output_format == "yaml":
            output_data = _analysis_to_dict(analysis)
            yaml_output = yaml.dump(output_data, default_flow_style=False, sort_keys=False)
            console.print(Syntax(yaml_output, "yaml"))
        else:
            display_commit_analysis(analysis)

    except Exception as e:
        logger.error(f"Git analysis error: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


@history_app.command()
def diff_commits(
    commit_a: str = typer.Argument(..., help="First commit hash"),
    commit_b: str = typer.Argument(..., help="Second commit hash"),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Compare two commits and describe their differences."""
    setup_logging(verbose)

    try:
        config = AnalysisConfig(repo_path=Path(repo_path))
        service = GitAnalysisService(config)

        comparison = service.compare_commits(commit_a, commit_b)

        display_commit_comparison(comparison)

    except Exception as e:
        logger.error(f"Git analysis error: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


@history_app.command()
def contributors(
    from_ref: str = typer.Argument(..., help="Source git reference"),
    to_ref: str = typer.Argument(..., help="Target git reference"),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Show contributor statistics for commits between references."""
    setup_logging(verbose)

    try:
        config = AnalysisConfig(repo_path=Path(repo_path))
        service = GitAnalysisService(config)

        result = service.compare_refs(from_ref, to_ref)
        display_contributor_stats(result.contributors)

    except Exception as e:
        logger.error(f"Git analysis error: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


@history_app.command()
def complexity(
    from_ref: str = typer.Argument(..., help="Source git reference"),
    to_ref: str = typer.Argument(..., help="Target git reference"),
    threshold: float = typer.Option(
        50.0, "--threshold", "-t", help="Complexity threshold for highlighting"
    ),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Show complexity analysis for commits between references."""
    setup_logging(verbose)

    try:
        config = AnalysisConfig(repo_path=Path(repo_path), complexity_threshold=threshold)
        service = GitAnalysisService(config)

        result = service.compare_refs(from_ref, to_ref)
        display_complexity_analysis(result, threshold)

    except Exception as e:
        logger.error(f"Git analysis error: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


@history_app.command()
def releases(
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    count: int = typer.Option(10, "--count", "-n", help="Number of recent releases to analyze"),
    use_llm: bool = typer.Option(False, "--llm", help="Use LLM for enhanced summaries"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Analyze recent releases (tags)."""
    setup_logging(verbose)

    try:
        config = AnalysisConfig(repo_path=Path(repo_path), use_llm=use_llm)
        service = GitAnalysisService(config)

        # Get tags (releases)
        repo = service.repo
        if repo is None:
            console.print("[yellow]Repository not initialized[/yellow]")
            return
        tags = sorted(repo.tags, key=lambda t: t.commit.committed_date, reverse=True)[: count + 1]

        if len(tags) < 2:
            console.print("[yellow]Not enough tags found for release comparison[/yellow]")
            return

        display_release_analysis(service, tags)

    except Exception as e:
        logger.error(f"Git analysis error: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


def _result_to_dict(result):
    """Convert ComparisonResult to dictionary."""
    return {
        "metadata": {
            "from_ref": result.metadata.from_ref,
            "to_ref": result.metadata.to_ref,
            "total_commits": result.metadata.total_commits,
            "total_files_changed": result.metadata.total_files_changed,
            "total_lines_added": result.metadata.total_lines_added,
            "total_lines_deleted": result.metadata.total_lines_deleted,
            "total_complexity": result.metadata.total_complexity,
            "time_span_days": result.metadata.time_span_days,
        },
        "aggregate_summary": result.aggregate_summary,
        "highlights": result.highlights,
        "risk_assessment": result.risk_assessment,
        "recommendations": result.recommendations,
        "file_categories": {cat.value: count for cat, count in result.file_categories.items()},
        "complexity_distribution": result.complexity_distribution,
        "commits": [_analysis_to_dict(c) for c in result.commits[:20]],  # Limit to 20 commits
        "contributors": {
            name: {
                "name": stats.name,
                "commits": stats.commits,
                "lines_added": stats.lines_added,
                "lines_deleted": stats.lines_deleted,
                "files_touched": stats.files_touched,
                "complexity_contribution": stats.complexity_contribution,
            }
            for name, stats in result.contributors.items()
        },
    }


def _analysis_to_dict(analysis):
    """Convert ChangeAnalysis to dictionary."""
    return {
        "commit_hash": analysis.commit_hash,
        "author": analysis.author,
        "timestamp": analysis.timestamp.isoformat(),
        "message": analysis.message,
        "short_message": analysis.short_message,
        "files_changed": len(analysis.files_changed),
        "lines_added": analysis.lines_added,
        "lines_deleted": analysis.lines_deleted,
        "complexity_score": analysis.complexity_score,
        "summary": analysis.summary,
        "tags": analysis.tags,
        "impact_areas": analysis.impact_areas,
        "breaking_change": analysis.breaking_change,
        "security_relevant": analysis.security_relevant,
        "files": [
            {
                "path": f.path,
                "change_type": f.change_type.value,
                "category": f.category.value,
                "lines_added": f.lines_added,
                "lines_deleted": f.lines_deleted,
            }
            for f in analysis.files_changed
        ],
    }
