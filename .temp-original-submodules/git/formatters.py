"""Display formatters for git analysis results.

This module contains functions for formatting and displaying git analysis
results in the CLI using Rich console output.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def display_risk_assessment(result):
    """Display risk assessment panel."""
    risk_panel = Panel(
        result.risk_assessment,
        title="⚠️  Risk Assessment",
        border_style="yellow" if "high" in result.risk_assessment.lower() else "blue",
    )
    console.print(risk_panel)


def display_table_results(result):
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
                commit.short_message[:50] + "..."
                if len(commit.short_message) > 50
                else commit.short_message,
                str(len(commit.files_changed)),
                f"+{commit.lines_added} -{commit.lines_deleted}",
                f"{commit.complexity_score:.1f}",
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
        for name, stats in sorted(
            result.contributors.items(), key=lambda x: x[1].commits, reverse=True
        )[:5]:
            console.print(
                f"  • {name}: {stats.commits} commits, {stats.complexity_contribution:.1f} complexity"
            )


def display_commit_analysis(analysis):
    """Display detailed commit analysis."""
    # Basic info
    info_text = f"""
[bold]Commit:[/bold] {analysis.commit_hash}
[bold]Author:[/bold] {analysis.author} <{analysis.email}>
[bold]Date:[/bold] {analysis.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
[bold]Branch:[/bold] {analysis.branch}
"""
    console.print(Panel(info_text, title="📋 Commit Information", border_style="blue"))

    # Message
    console.print("\n[bold]📝 Message:[/bold]")
    console.print(analysis.message)

    # Summary
    if analysis.summary:
        console.print("\n[bold]📄 Summary:[/bold]")
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
        console.print("\n[bold]📁 Files Changed:[/bold]")
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
                f"+{file_change.lines_added} -{file_change.lines_deleted}",
            )

        console.print(table)


def display_commit_comparison(comparison):
    """Display comparison between two commits."""
    console.print(
        f"[bold]🔄 Comparing Commits:[/bold] {comparison.commit_a_hash[:8]} → {comparison.commit_b_hash[:8]}"
    )
    console.print(f"[bold]Similarity Score:[/bold] {comparison.similarity_score:.2f}")

    if comparison.differences:
        console.print("\n[bold]🔍 Differences:[/bold]")
        for diff in comparison.differences:
            console.print(f"  • {diff}")

    if comparison.common_themes:
        console.print("\n[bold]🎯 Common Themes:[/bold]")
        for theme in comparison.common_themes:
            console.print(f"  • {theme}")

    console.print(f"\n[bold]💥 Impact:[/bold] {comparison.impact_description}")
    console.print(f"[bold]⚠️  Regression Risk:[/bold] {comparison.regression_risk}")

    if comparison.migration_notes:
        console.print("\n[bold]📋 Migration Notes:[/bold]")
        for note in comparison.migration_notes:
            console.print(f"  • {note}")


def display_contributor_stats(contributors):
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
            stats.first_commit.strftime("%Y-%m-%d"),
            stats.last_commit.strftime("%Y-%m-%d"),
        )

    console.print(table)


def display_complexity_analysis(result, threshold):
    """Display complexity analysis."""
    # Complexity distribution
    console.print("[bold]📊 Complexity Distribution:[/bold]")
    for range_name, count in result.complexity_distribution.items():
        color = "red" if int(range_name.split("-")[0]) >= threshold else "green"
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
                commit.short_message[:40] + "..."
                if len(commit.short_message) > 40
                else commit.short_message,
                f"{commit.complexity_score:.1f}",
                ", ".join(risk_factors) if risk_factors else "Low",
            )

        console.print(table)

    # Top complex files
    if result.top_complex_files:
        console.print("\n[bold]📁 Most Complex Files:[/bold]")
        table = Table()
        table.add_column("File", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Complexity", style="red")
        table.add_column("Commits", style="blue")
        table.add_column("Lines", style="yellow")

        for file_info in result.top_complex_files[:10]:
            table.add_row(
                file_info["path"],
                file_info["category"].value,
                f"{file_info['complexity_score']:.1f}",
                str(file_info["commits"]),
                f"+{file_info['total_lines_added']} -{file_info['total_lines_deleted']}",
            )

        console.print(table)


def display_release_analysis(service, tags):
    """Display release analysis."""
    console.print("[bold]📦 Recent Releases Analysis:[/bold]")

    for i in range(min(len(tags) - 1, 10)):
        from_tag = tags[i + 1]
        to_tag = tags[i]

        try:
            console.print(f"\n[bold]Release {from_tag.name} → {to_tag.name}:[/bold]")

            result = service.compare_refs(from_tag.name, to_tag.name)

            # Brief summary
            console.print(f"  Commits: {result.metadata.total_commits}")
            console.print(f"  Files: {result.metadata.total_files_changed}")
            console.print(
                f"  Lines: +{result.metadata.total_lines_added} -{result.metadata.total_lines_deleted}"
            )
            console.print(f"  Complexity: {result.metadata.total_complexity:.1f}")

            # Top highlights
            if result.highlights:
                console.print("  Highlights:")
                for highlight in result.highlights[:3]:
                    console.print(f"    • {highlight}")

        except Exception as e:
            console.print(f"  [red]Error analyzing release: {e}[/red]")
