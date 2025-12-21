"""Command-line interface for git analysis."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax
import yaml

from .models import AnalysisConfig
from .services import GitAnalysisService
from .utils import setup_logging, format_duration


# Create Typer app
app = typer.Typer(
    name="git-analysis",
    help="Structured Git History Comparison and Analysis Tool",
    no_args_is_help=True,
)

console = Console()


@app.command()
def compare(
    from_ref: str = typer.Argument(..., help="Source git reference (branch, tag, or commit)"),
    to_ref: str = typer.Argument(..., help="Target git reference (branch, tag, or commit)"),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, yaml"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    use_llm: bool = typer.Option(False, "--llm", help="Use LLM for enhanced summaries"),
    llm_provider: str = typer.Option("openai", "--llm-provider", help="LLM provider: openai, anthropic"),
    max_commits: int = typer.Option(100, "--max-commits", help="Maximum number of commits to analyze"),
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
            max_commits=max_commits
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
            transient=True
        ) as progress:
            task = progress.add_task("Analyzing git history...", total=None)

            result = service.compare_refs(from_ref, to_ref)

        # Display results
        if output_format == "json":
            output_data = _result_to_dict(result)
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(output_data, f, indent=2, default=str)
                console.print(f"[green]Results saved to:[/green] {output_file}")
            else:
                console.print_json(data=output_data)
        elif output_format == "yaml":
            output_data = _result_to_dict(result)
            yaml_output = yaml.dump(output_data, default_flow_style=False, sort_keys=False)
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(yaml_output)
                console.print(f"[green]Results saved to:[/green] {output_file}")
            else:
                console.print(yaml_output, syntax="yaml")
        else:
            _display_table_results(result)

        # Show risk assessment
        _display_risk_assessment(result)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@app.command()
def analyze(
    commit_hash: str = typer.Argument(..., help="Git commit hash to analyze"),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, yaml"),
    use_llm: bool = typer.Option(False, "--llm", help="Use LLM for enhanced summaries"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Analyze a single commit with detailed metrics."""
    setup_logging(verbose)

    try:
        config = AnalysisConfig(
            repo_path=Path(repo_path),
            use_llm=use_llm
        )

        service = GitAnalysisService(config)
        analysis = service.analyze_commit(commit_hash)

        if output_format == "json":
            output_data = _analysis_to_dict(analysis)
            console.print_json(data=output_data)
        elif output_format == "yaml":
            output_data = _analysis_to_dict(analysis)
            yaml_output = yaml.dump(output_data, default_flow_style=False, sort_keys=False)
            console.print(yaml_output, syntax="yaml")
        else:
            _display_commit_analysis(analysis)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@app.command()
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

        _display_commit_comparison(comparison)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@app.command()
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
        _display_contributor_stats(result.contributors)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@app.command()
def complexity(
    from_ref: str = typer.Argument(..., help="Source git reference"),
    to_ref: str = typer.Argument(..., help="Target git reference"),
    threshold: float = typer.Option(50.0, "--threshold", "-t", help="Complexity threshold for highlighting"),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to git repository"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Show complexity analysis for commits between references."""
    setup_logging(verbose)

    try:
        config = AnalysisConfig(repo_path=Path(repo_path), complexity_threshold=threshold)
        service = GitAnalysisService(config)

        result = service.compare_refs(from_ref, to_ref)
        _display_complexity_analysis(result, threshold)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@app.command()
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
        tags = sorted(repo.tags, key=lambda t: t.commit.committed_date, reverse=True)[:count+1]

        if len(tags) < 2:
            console.print("[yellow]Not enough tags found for release comparison[/yellow]")
            return

        _display_release_analysis(service, tags)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def _display_table_results(result):
    """Display comparison results in table format."""
    # Metadata panel
    metadata = result.metadata
    metadata_text = f"""
[bold]Comparison:[/bold] {metadata.from_ref} → {metadata.to_ref}
[bold]Commits:[/bold] {metadata.total_commits}
[bold]Files:[/bold] {metadata.total_files_changed}
[bold]Lines:[/bold] +{metadata.total_lines_added} -{metadata.total_lines_deleted}
[bold]Complexity:[/bold] {metadata.total_complexity:.1f}
[bold]Time span:[/bold] {metadata.time_span_days} days
"""
    console.print(Panel(metadata_text, title="📊 Comparison Summary", border_style="blue"))

    # Aggregate summary
    console.print("\n[bold]📝 Aggregate Summary:[/bold]")
    console.print(result.aggregate_summary)

    # Highlights
    if result.highlights:
        console.print("\n[bold]⭐ Highlights:[/bold]")
        for highlight in result.highlights:
            console.print(f"  • {highlight}")

    # Top commits table
    if result.commits:
        console.print("\n[bold]🔥 Top Commits by Complexity:[/bold]")
        table = Table(title="Most Complex Commits")
        table.add_column("Hash", style="cyan")
        table.add_column("Author", style="green")
        table.add_column("Message", style="white")
        table.add_column("Files", style="blue")
        table.add_column("Lines", style="yellow")
        table.add_column("Complexity", style="red")

        top_commits = sorted(result.commits, key=lambda x: x.complexity_score, reverse=True)[:10]
        for commit in top_commits:
            table.add_row(
                commit.commit_hash[:8],
                commit.author,
                commit.short_message[:50] + "..." if len(commit.short_message) > 50 else commit.short_message,
                str(len(commit.files_changed)),
                f"+{commit.lines_added} -{commit.lines_deleted}",
                f"{commit.complexity_score:.1f}"
            )

        console.print(table)

    # File categories
    if result.file_categories:
        console.print("\n[bold]📁 File Categories:[/bold]")
        for category, count in result.file_categories.items():
            console.print(f"  • {category.value}: {count} files")

    # Contributors summary
    if result.contributors:
        console.print(f"\n[bold]👥 Contributors:[/bold] {len(result.contributors)} contributors")
        for name, stats in sorted(result.contributors.items(), key=lambda x: x[1].commits, reverse=True)[:5]:
            console.print(f"  • {name}: {stats.commits} commits, {stats.complexity_contribution:.1f} complexity")


def _display_commit_analysis(analysis):
    """Display detailed commit analysis."""
    # Basic info
    info_text = f"""
[bold]Commit:[/bold] {analysis.commit_hash}
[bold]Author:[/bold] {analysis.author} <{analysis.email}>
[bold]Date:[/bold] {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
[bold]Branch:[/bold] {analysis.branch}
"""
    console.print(Panel(info_text, title="📋 Commit Information", border_style="blue"))

    # Message
    console.print(f"\n[bold]📝 Message:[/bold]")
    console.print(analysis.message)

    # Summary
    if analysis.summary:
        console.print(f"\n[bold]📄 Summary:[/bold]")
        console.print(analysis.summary)

    # Metrics
    metrics_text = f"""
[bold]Files:[/bold] {len(analysis.files_changed)} total ({analysis.files_added} added, {analysis.files_deleted} deleted, {analysis.files_modified} modified)
[bold]Lines:[/bold] +{analysis.lines_added} -{analysis.lines_deleted}
[bold]Complexity:[/bold] {analysis.complexity_score:.1f}
"""
    console.print(Panel(metrics_text, title="📊 Metrics", border_style="green"))

    # Tags
    if analysis.tags:
        console.print(f"\n[bold]🏷️  Tags:[/bold] {', '.join(analysis.tags)}")

    # Impact areas
    if analysis.impact_areas:
        console.print(f"\n[bold]🎯 Impact Areas:[/bold] {', '.join(analysis.impact_areas)}")

    # Special flags
    flags = []
    if analysis.breaking_change:
        flags.append("🔴 Breaking Change")
    if analysis.security_relevant:
        flags.append("🔒 Security Related")

    if flags:
        console.print(f"\n[bold]⚠️  Flags:[/bold] {' | '.join(flags)}")

    # Files table
    if analysis.files_changed:
        console.print(f"\n[bold]📁 Files Changed:[/bold]")
        table = Table()
        table.add_column("Path", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Category", style="yellow")
        table.add_column("Lines", style="blue")

        for file_change in analysis.files_changed:
            table.add_row(
                file_change.path,
                file_change.change_type.value,
                file_change.category.value,
                f"+{file_change.lines_added} -{file_change.lines_deleted}"
            )

        console.print(table)


def _display_commit_comparison(comparison):
    """Display comparison between two commits."""
    console.print(f"[bold]🔄 Comparing Commits:[/bold] {comparison.commit_a_hash[:8]} → {comparison.commit_b_hash[:8]}")
    console.print(f"[bold]Similarity Score:[/bold] {comparison.similarity_score:.2f}")

    if comparison.differences:
        console.print(f"\n[bold]🔍 Differences:[/bold]")
        for diff in comparison.differences:
            console.print(f"  • {diff}")

    if comparison.common_themes:
        console.print(f"\n[bold]🎯 Common Themes:[/bold]")
        for theme in comparison.common_themes:
            console.print(f"  • {theme}")

    console.print(f"\n[bold]💥 Impact:[/bold] {comparison.impact_description}")
    console.print(f"[bold]⚠️  Regression Risk:[/bold] {comparison.regression_risk}")

    if comparison.migration_notes:
        console.print(f"\n[bold]📋 Migration Notes:[/bold]")
        for note in comparison.migration_notes:
            console.print(f"  • {note}")


def _display_contributor_stats(contributors):
    """Display contributor statistics."""
    if not contributors:
        console.print("[yellow]No contributor data available[/yellow]")
        return

    table = Table(title="Contributor Statistics")
    table.add_column("Name", style="cyan")
    table.add_column("Commits", style="green")
    table.add_column("Lines Added", style="blue")
    table.add_column("Lines Deleted", style="red")
    table.add_column("Files Touched", style="yellow")
    table.add_column("Complexity", style="magenta")
    table.add_column("First Commit", style="dim")
    table.add_column("Last Commit", style="dim")

    for stats in sorted(contributors.values(), key=lambda x: x.commits, reverse=True):
        table.add_row(
            stats.name,
            str(stats.commits),
            str(stats.lines_added),
            str(stats.lines_deleted),
            str(stats.files_touched),
            f"{stats.complexity_contribution:.1f}",
            stats.first_commit.strftime('%Y-%m-%d'),
            stats.last_commit.strftime('%Y-%m-%d')
        )

    console.print(table)


def _display_complexity_analysis(result, threshold):
    """Display complexity analysis."""
    # Complexity distribution
    console.print("[bold]📊 Complexity Distribution:[/bold]")
    for range_name, count in result.complexity_distribution.items():
        color = "red" if int(range_name.split('-')[0]) >= threshold else "green"
        console.print(f"  {range_name}: {count} commits", style=color)

    # High complexity commits
    high_complexity = [c for c in result.commits if c.complexity_score >= threshold]
    if high_complexity:
        console.print(f"\n[bold]🔴 High Complexity Commits (≥{threshold}):[/bold]")
        table = Table()
        table.add_column("Hash", style="cyan")
        table.add_column("Author", style="green")
        table.add_column("Message", style="white")
        table.add_column("Complexity", style="red")
        table.add_column("Risk Factors", style="yellow")

        for commit in sorted(high_complexity, key=lambda x: x.complexity_score, reverse=True):
            risk_factors = []
            if commit.breaking_change:
                risk_factors.append("Breaking")
            if commit.security_relevant:
                risk_factors.append("Security")
            if len(commit.files_changed) > 20:
                risk_factors.append("Many files")

            table.add_row(
                commit.commit_hash[:8],
                commit.author,
                commit.short_message[:40] + "..." if len(commit.short_message) > 40 else commit.short_message,
                f"{commit.complexity_score:.1f}",
                ", ".join(risk_factors) if risk_factors else "Low"
            )

        console.print(table)

    # Top complex files
    if result.top_complex_files:
        console.print(f"\n[bold]📁 Most Complex Files:[/bold]")
        table = Table()
        table.add_column("File", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Complexity", style="red")
        table.add_column("Commits", style="blue")
        table.add_column("Lines", style="yellow")

        for file_info in result.top_complex_files[:10]:
            table.add_row(
                file_info['path'],
                file_info['category'].value,
                f"{file_info['complexity_score']:.1f}",
                str(file_info['commits']),
                f"+{file_info['total_lines_added']} -{file_info['total_lines_deleted']}"
            )

        console.print(table)


def _display_release_analysis(service, tags):
    """Display release analysis."""
    console.print("[bold]📦 Recent Releases Analysis:[/bold]")

    for i in range(min(len(tags)-1, 10)):
        from_tag = tags[i+1]
        to_tag = tags[i]

        try:
            console.print(f"\n[bold]Release {from_tag.name} → {to_tag.name}:[/bold]")

            result = service.compare_refs(from_tag.name, to_tag.name)

            # Brief summary
            console.print(f"  Commits: {result.metadata.total_commits}")
            console.print(f"  Files: {result.metadata.total_files_changed}")
            console.print(f"  Lines: +{result.metadata.total_lines_added} -{result.metadata.total_lines_deleted}")
            console.print(f"  Complexity: {result.metadata.total_complexity:.1f}")

            # Top highlights
            if result.highlights:
                console.print("  Highlights:")
                for highlight in result.highlights[:3]:
                    console.print(f"    • {highlight}")

        except Exception as e:
            console.print(f"  [red]Error analyzing release: {e}[/red]")


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
        "contributors": {name: {
            "name": stats.name,
            "commits": stats.commits,
            "lines_added": stats.lines_added,
            "lines_deleted": stats.lines_deleted,
            "files_touched": stats.files_touched,
            "complexity_contribution": stats.complexity_contribution,
        } for name, stats in result.contributors.items()},
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


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()