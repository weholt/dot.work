"""
CLI commands for the Python code scanner.

Provides `dot-work python scan` subcommands.
"""

import json
from pathlib import Path

import typer

from dot_work.python.scan.config import ScanConfig
from dot_work.python.scan.dependency_graph import (
    build_dependency_graph,
    get_layered_structure,
)
from dot_work.python.scan.rules import load_rules
from dot_work.python.scan.scoring import QualityScorer
from dot_work.python.scan.service import ScanService

scan_app = typer.Typer(
    help="Scan Python codebase for structure and metrics.",
    no_args_is_help=True,
)


@scan_app.command("run")
def scan_run(
    path: Path = typer.Argument(Path("."), help="Path to scan (default: current directory)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output path for analysis results"),
    incremental: bool = typer.Option(
        False, "--incremental", "-i", help="Use incremental scanning with cache"
    ),
    config_path: str = typer.Option(
        None, "--config", "-c", help="Custom config path (DOT_WORK_SCAN_PATH)"
    ),
) -> None:
    """Scan Python codebase and generate index.

    Examples:
        dot-work python scan .
        dot-work python scan src/ --output analysis.json
        dot-work python scan . --incremental
    """
    if config_path:
        config = ScanConfig(base_path=Path(config_path))
    else:
        config = ScanConfig.from_env()

    service = ScanService(config)
    typer.echo(f"Scanning {path}...")

    index = service.scan(
        root_path=path,
        incremental=incremental,
        annotate_metrics=True,
    )

    typer.echo(f"Scanned {index.metrics.total_files} files")
    typer.echo(f"Found {index.metrics.total_functions} functions")
    typer.echo(f"Found {index.metrics.total_classes} classes")
    typer.echo(f"Total lines: {index.metrics.total_lines}")
    typer.echo(f"Avg complexity: {index.metrics.avg_complexity:.2f}")
    typer.echo(f"Max complexity: {index.metrics.max_complexity}")

    if output:
        results = {
            "metrics": {
                "total_files": index.metrics.total_files,
                "total_functions": index.metrics.total_functions,
                "total_classes": index.metrics.total_classes,
                "total_lines": index.metrics.total_lines,
                "avg_complexity": index.metrics.avg_complexity,
                "max_complexity": index.metrics.max_complexity,
            }
        }
        output.write_text(json.dumps(results, indent=2))
        typer.echo(f"Results saved to {output}")


@scan_app.command("query")
def scan_query(
    name: str = typer.Argument(..., help="Entity name to search for"),
    index_path: Path = typer.Option(None, "--index", "-i", help="Custom index path"),
) -> None:
    """Find entity by name in index.

    Examples:
        dot-work python scan query install_for_copilot
        dot-work python scan query ASTScanner
    """
    config = ScanConfig.from_env()
    service = ScanService(config)

    index = service.load_index()
    if not index:
        typer.echo("No index found. Run 'dot-work python scan run' first.", err=True)
        raise typer.Exit(1)

    results = service.query_index(index, name)
    if not results:
        typer.echo(f"No entities found with name '{name}'")
        raise typer.Exit(0)

    typer.echo(f"Results for '{name}':")

    if results["functions"]:
        typer.echo("\nFunctions:")
        for func in results["functions"]:
            typer.echo(f"  - {func['name']} ({func['file']}:{func['line']})")
            typer.echo(f"    Complexity: {func['complexity']}")

    if results["classes"]:
        typer.echo("\nClasses:")
        for cls in results["classes"]:
            typer.echo(f"  - {cls['name']} ({cls['file']}:{cls['line']})")
            if cls["methods"]:
                typer.echo(f"    Methods: {', '.join(cls['methods'])}")


@scan_app.command("complex")
def scan_complex(
    threshold: int = typer.Option(10, "--threshold", "-t", help="Complexity threshold"),
    index_path: Path = typer.Option(None, "--index", "-i", help="Custom index path"),
) -> None:
    """Find functions exceeding complexity threshold.

    Examples:
        dot-work python scan complex
        dot-work python scan complex --threshold 5
    """
    config = ScanConfig.from_env()
    service = ScanService(config)

    index = service.load_index()
    if not index:
        typer.echo("No index found. Run 'dot-work python scan run' first.", err=True)
        raise typer.Exit(1)

    functions = service.get_complex_functions(index, threshold)

    if not functions:
        typer.echo(f"No functions with complexity >= {threshold}")
        raise typer.Exit(0)

    typer.echo(f"Functions with complexity >= {threshold}:")
    for func in functions:
        typer.echo(f"  - {func['name']} ({func['file']}:{func['line']})")
        typer.echo(f"    Complexity: {func['complexity']}")


@scan_app.command("metrics")
def scan_metrics(
    index_path: Path = typer.Option(None, "--index", "-i", help="Custom index path"),
) -> None:
    """Show metrics summary from index.

    Examples:
        dot-work python scan metrics
    """
    config = ScanConfig.from_env()
    service = ScanService(config)

    index = service.load_index()
    if not index:
        typer.echo("No index found. Run 'dot-work python scan run' first.", err=True)
        raise typer.Exit(1)

    metrics = service.get_metrics(index)

    typer.echo("Codebase Metrics:")
    typer.echo(f"  Total files: {metrics['total_files']}")
    typer.echo(f"  Total functions: {metrics['total_functions']}")
    typer.echo(f"  Total classes: {metrics['total_classes']}")
    typer.echo(f"  Total lines: {metrics['total_lines']}")
    typer.echo(f"  Avg complexity: {metrics['avg_complexity']:.2f}")
    typer.echo(f"  Max complexity: {metrics['max_complexity']}")


@scan_app.command("export")
def scan_export(
    format: str = typer.Option("json", "--format", "-f", help="Export format"),
    output: Path = typer.Option(Path("export.json"), "--output", "-o", help="Output file"),
    index_path: Path = typer.Option(None, "--index", "-i", help="Custom index path"),
) -> None:
    """Export index to different format.

    Examples:
        dot-work python scan export --format json
        dot-work python scan export --format csv --output data.csv
    """
    config = ScanConfig.from_env()
    service = ScanService(config)

    index = service.load_index()
    if not index:
        typer.echo("No index found. Run 'dot-work python scan run' first.", err=True)
        raise typer.Exit(1)

    if format == "json":
        data = {
            "root_path": str(index.root_path),
            "metrics": {
                "total_files": index.metrics.total_files,
                "total_functions": index.metrics.total_functions,
                "total_classes": index.metrics.total_classes,
                "total_lines": index.metrics.total_lines,
                "avg_complexity": index.metrics.avg_complexity,
                "max_complexity": index.metrics.max_complexity,
            },
            "files": {
                path: {
                    "line_count": f.line_count,
                    "functions": len(f.functions),
                    "classes": len(f.classes),
                }
                for path, f in index.files.items()
            },
        }
        output.write_text(json.dumps(data, indent=2))

    elif format == "csv":
        import csv

        with output.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file", "lines", "functions", "classes", "imports"])
            for path, file_entity in index.files.items():
                writer.writerow(
                    [
                        path,
                        file_entity.line_count,
                        len(file_entity.functions),
                        len(file_entity.classes),
                        len(file_entity.imports),
                    ]
                )
    else:
        typer.echo(f"Unsupported format: {format}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Exported to {output}")


@scan_app.command("check")
def scan_check(
    rules: Path = typer.Argument(..., help="Path to YAML rules file"),
    index_path: Path = typer.Option(None, "--index", "-i", help="Custom index path"),
) -> None:
    """Check codebase against YAML rules.

    Examples:
        dot-work python scan check rules.yaml
    """
    config = ScanConfig.from_env()
    service = ScanService(config)

    index = service.load_index()
    if not index:
        typer.echo("No index found. Run 'dot-work python scan run' first.", err=True)
        raise typer.Exit(1)

    if not rules.exists():
        typer.echo(f"Rules file not found: {rules}", err=True)
        raise typer.Exit(1)

    engine = load_rules(rules)
    violations = engine.check(index)

    if not violations:
        typer.echo("No violations found!")
        raise typer.Exit(0)

    typer.echo(f"Found {len(violations)} violations:")

    for v in violations:
        typer.echo(f"  [{v.severity.upper()}] {v.rule}")
        typer.echo(f"    {v.file}:{v.line}")
        typer.echo(f"    {v.message}")

    error_count = sum(1 for v in violations if v.severity == "error")
    if error_count > 0:
        raise typer.Exit(1)


@scan_app.command("score")
def scan_score(
    index_path: Path = typer.Option(None, "--index", "-i", help="Custom index path"),
) -> None:
    """Calculate quality score for the codebase.

    Examples:
        dot-work python scan score
    """
    config = ScanConfig.from_env()
    service = ScanService(config)

    index = service.load_index()
    if not index:
        typer.echo("No index found. Run 'dot-work python scan run' first.", err=True)
        raise typer.Exit(1)

    scorer = QualityScorer()
    scores = scorer.score(index)

    typer.echo("Quality Scores:")
    typer.echo(f"  Overall: {scores['overall']} ({scores['grade']})")
    typer.echo(f"  Complexity: {scores['complexity']}")
    typer.echo(f"  Documentation: {scores['documentation']}")
    typer.echo(f"  Tests: {scores['tests']}")


@scan_app.command("deps")
def scan_deps(
    index_path: Path = typer.Option(None, "--index", "-i", help="Custom index path"),
) -> None:
    """Show dependency graph for the codebase.

    Examples:
        dot-work python scan deps
    """
    config = ScanConfig.from_env()
    service = ScanService(config)

    index = service.load_index()
    if not index:
        typer.echo("No index found. Run 'dot-work python scan run' first.", err=True)
        raise typer.Exit(1)

    graph = build_dependency_graph(index)

    typer.echo("Dependency Graph:")
    for file_path, deps in sorted(graph.items()):
        if deps:
            rel_path = Path(file_path).relative_to(index.root_path)
            typer.echo(f"  {rel_path}")
            for dep in deps:
                dep_rel = Path(dep).relative_to(index.root_path)
                typer.echo(f"    -> {dep_rel}")


@scan_app.command("layers")
def scan_layers(
    index_path: Path = typer.Option(None, "--index", "-i", help="Custom index path"),
) -> None:
    """Show layered structure of the codebase.

    Examples:
        dot-work python scan layers
    """
    config = ScanConfig.from_env()
    service = ScanService(config)

    index = service.load_index()
    if not index:
        typer.echo("No index found. Run 'dot-work python scan run' first.", err=True)
        raise typer.Exit(1)

    layers = get_layered_structure(index)

    typer.echo("Layered Structure:")
    for layer_name, files in sorted(layers.items()):
        typer.echo(f"\n{layer_name}:")
        for file_path in files:
            rel_path = Path(file_path).relative_to(index.root_path)
            typer.echo(f"  {rel_path}")


__all__ = ["scan_app"]
