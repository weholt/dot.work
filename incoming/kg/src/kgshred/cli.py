"""CLI entry point for kgshred.

This module provides a thin CLI layer using typer.
All business logic is delegated to core modules.
"""

from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from kgshred import __version__
from kgshred.config import get_db_path

if TYPE_CHECKING:
    from kgshred.db import Database

app = typer.Typer(
    name="kg",
    help="Knowledge-graph shredder for plain text/Markdown.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"kgshred version {__version__}")
        raise typer.Exit()


def _get_db(db_path: Path | None = None) -> Database:
    """Get database connection."""
    from kgshred.db import Database

    path = db_path or get_db_path()
    return Database(path)


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Knowledge-graph shredder for plain text/Markdown."""


@app.command()
def ingest(
    paths: Annotated[
        list[Path],
        typer.Argument(help="Files to ingest (use - for stdin)"),
    ],
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Database path"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Replace existing documents"),
    ] = False,
) -> None:
    """Ingest Markdown files into the knowledge graph."""
    from kgshred.db import DocumentExistsError
    from kgshred.graph import build_graph

    database = _get_db(db)

    total_nodes = 0
    total_docs = 0
    skipped_docs = 0

    try:
        for path in paths:
            if str(path) == "-":
                # Read from stdin
                content = sys.stdin.buffer.read()
                doc_id = hashlib.sha256(content).hexdigest()[:16]
                source = "<stdin>"
            else:
                if not path.exists():
                    console.print(f"[red]Error:[/red] File not found: {path}")
                    raise typer.Exit(1)

                content = path.read_bytes()
                doc_id = hashlib.sha256(content).hexdigest()[:16]
                source = str(path)

            try:
                result = build_graph(doc_id, content, database, source, force=force)
                total_nodes += len(result.nodes)
                total_docs += 1
                console.print(f"[green]✓[/green] {source}: {len(result.nodes)} nodes")
            except DocumentExistsError as e:
                if e.sha256_match:
                    console.print(f"[yellow]⊘[/yellow] {source}: already ingested (unchanged)")
                else:
                    console.print(
                        f"[yellow]⊘[/yellow] {source}: exists with different content (use --force)"
                    )
                skipped_docs += 1

        msg_parts = [f"Ingested {total_docs} document(s), {total_nodes} nodes total"]
        if skipped_docs > 0:
            msg_parts.append(f"{skipped_docs} skipped")
        console.print(f"\n[bold]{', '.join(msg_parts)}[/bold]")

    finally:
        database.close()


@app.command()
def stats(
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Database path"),
    ] = None,
) -> None:
    """Show database statistics."""
    database = _get_db(db)

    try:
        stats_data = database.get_stats()

        table = Table(title="Database Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green", justify="right")

        table.add_row("Documents", str(stats_data["documents"]))
        table.add_row("Nodes", str(stats_data["nodes"]))
        table.add_row("Edges", str(stats_data["edges"]))

        console.print(table)

        nodes_by_kind = stats_data.get("nodes_by_kind")
        if nodes_by_kind and isinstance(nodes_by_kind, dict):
            kind_table = Table(title="Nodes by Kind")
            kind_table.add_column("Kind", style="cyan")
            kind_table.add_column("Count", style="green", justify="right")

            for kind, count in nodes_by_kind.items():
                kind_table.add_row(kind, str(count))

            console.print(kind_table)

    finally:
        database.close()


@app.command()
def outline(
    doc: Annotated[
        str,
        typer.Option("--doc", "-d", help="Document ID"),
    ],
    max_depth: Annotated[
        int,
        typer.Option("--max-depth", help="Maximum depth to show"),
    ] = 10,
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Database path"),
    ] = None,
) -> None:
    """Show document outline as a tree."""
    from kgshred.graph import get_node_tree

    database = _get_db(db)

    try:
        document = database.get_document(doc)
        if not document:
            console.print(f"[red]Error:[/red] Document not found: {doc}")
            raise typer.Exit(1)

        tree_data = get_node_tree(database, doc)
        if not tree_data:
            console.print("[yellow]No nodes found[/yellow]")
            raise typer.Exit(0)

        # Build rich tree
        root_node, _ = tree_data[0]
        tree = Tree(f"[bold]{root_node.short_id}[/bold] {root_node.title or '(doc)'}")

        # Track tree nodes by depth
        tree_nodes = {0: tree}

        for node, depth in tree_data[1:]:
            if depth > max_depth:
                continue

            label = f"[cyan]{node.short_id}[/cyan] [{node.kind}]"
            if node.title:
                label += f" {node.title}"

            parent_tree = tree_nodes.get(depth - 1, tree)
            child = parent_tree.add(label)
            tree_nodes[depth] = child

        console.print(tree)

    finally:
        database.close()


@app.command()
def search(
    query: Annotated[
        str,
        typer.Option("--q", "-q", help="Search query"),
    ],
    k: Annotated[
        int,
        typer.Option("--k", "-k", help="Max results"),
    ] = 20,
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Database path"),
    ] = None,
) -> None:
    """Search for nodes matching a query."""
    from kgshred.search_fts import search as fts_search

    database = _get_db(db)

    try:
        results = fts_search(database, query, k=k)

        if not results:
            console.print("[yellow]No results found[/yellow]")
            raise typer.Exit(0)

        for result in results:
            console.print(f"\n[cyan]{result.short_id}[/cyan] [{result.kind}]", end="")
            if result.title:
                console.print(f" [bold]{result.title}[/bold]")
            else:
                console.print()
            console.print(f"  [dim]{result.snippet}[/dim]")

        console.print(f"\n[bold]{len(results)} result(s)[/bold]")

    finally:
        database.close()


@app.command()
def expand(
    node_id: Annotated[
        str,
        typer.Option("--id", "-i", help="Node short_id to expand"),
    ],
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Database path"),
    ] = None,
) -> None:
    """Show full content of a specific node."""
    from kgshred.render import render_node

    database = _get_db(db)

    try:
        content = render_node(database, node_id)

        if not content:
            console.print(f"[red]Error:[/red] Node not found: {node_id}")
            raise typer.Exit(1)

        # Output raw bytes to stdout
        sys.stdout.buffer.write(content)
        sys.stdout.buffer.write(b"\n")

    finally:
        database.close()


@app.command()
def render(
    doc: Annotated[
        str,
        typer.Option("--doc", "-d", help="Document ID"),
    ],
    filter_query: Annotated[
        str | None,
        typer.Option("--filter", "-f", help="Filter by search query"),
    ] = None,
    policy: Annotated[
        str,
        typer.Option("--policy", "-p", help="Expansion policy"),
    ] = "direct",
    window: Annotated[
        int,
        typer.Option("--window", "-w", help="Window size for siblings"),
    ] = 0,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file"),
    ] = None,
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Database path"),
    ] = None,
) -> None:
    """Render a document with optional filtering."""
    from kgshred.render import (
        ExpansionPolicy,
        RenderOptions,
        render_filtered,
        render_full,
    )
    from kgshred.search_fts import search as fts_search

    database = _get_db(db)

    try:
        document = database.get_document(doc)
        if not document:
            console.print(f"[red]Error:[/red] Document not found: {doc}")
            raise typer.Exit(1)

        if filter_query:
            # Search and get matching node IDs
            results = fts_search(database, filter_query, k=1000)
            matches = {r.short_id for r in results if r.doc_id == doc}

            # Parse policy
            policy_map = {
                "direct": ExpansionPolicy.DIRECT,
                "direct+ancestors": ExpansionPolicy.DIRECT_ANCESTORS,
                "direct+ancestors+siblings": ExpansionPolicy.DIRECT_ANCESTORS_SIBLINGS,
            }
            exp_policy = policy_map.get(policy, ExpansionPolicy.DIRECT)

            options = RenderOptions(policy=exp_policy, window=window)
            content = render_filtered(database, doc, matches, options)
        else:
            content = render_full(database, doc)

        if output:
            output.write_bytes(content)
            console.print(f"[green]Written to {output}[/green]")
        else:
            sys.stdout.buffer.write(content)

    finally:
        database.close()


@app.command()
def export(
    doc: Annotated[
        str,
        typer.Option("--doc", "-d", help="Document ID"),
    ],
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (json|jsonl)"),
    ] = "json",
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Database path"),
    ] = None,
) -> None:
    """Export document nodes as JSON."""
    database = _get_db(db)

    try:
        document = database.get_document(doc)
        if not document:
            console.print(f"[red]Error:[/red] Document not found: {doc}")
            raise typer.Exit(1)

        nodes = database.get_nodes_by_doc_id(doc)

        node_dicts = [
            {
                "short_id": n.short_id,
                "full_id": n.full_id,
                "kind": n.kind,
                "level": n.level,
                "title": n.title,
                "start": n.start,
                "end": n.end,
                "content": document.raw[n.start : n.end].decode("utf-8", errors="replace"),
            }
            for n in nodes
        ]

        if fmt == "jsonl":
            for node_dict in node_dicts:
                console.print(json.dumps(node_dict))
        else:
            console.print(json.dumps(node_dicts, indent=2))

    finally:
        database.close()


@app.command()
def status() -> None:
    """Show database status."""
    db_path = get_db_path()
    if db_path.exists():
        console.print(f"[green]Database found:[/green] {db_path}")
    else:
        console.print(f"[yellow]No database at:[/yellow] {db_path}")


# ============================================================================
# Project commands
# ============================================================================

project_app = typer.Typer(help="Manage projects (collections of documents).")
app.add_typer(project_app, name="project")


@project_app.command("create")
def project_create(
    name: Annotated[str, typer.Argument(help="Project name")],
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Create a new project."""
    import sqlite3

    database = _get_db(db)
    try:
        collection_id = str(uuid.uuid4())[:8]
        database.create_collection(collection_id, "project", name)
        console.print(f"[green]✓[/green] Created project: {name} ({collection_id})")
    except sqlite3.IntegrityError:
        console.print(f"[red]Error:[/red] Project '{name}' already exists")
        raise typer.Exit(1)
    finally:
        database.close()


@project_app.command("ls")
def project_ls(
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """List all projects."""
    database = _get_db(db)
    try:
        projects = database.list_collections(kind="project")
        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return

        table = Table(title="Projects")
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Members", justify="right")

        for proj in projects:
            members = database.list_collection_members(proj.collection_id)
            table.add_row(proj.name, proj.collection_id, str(len(members)))

        console.print(table)
    finally:
        database.close()


@project_app.command("add")
def project_add(
    name: Annotated[str, typer.Argument(help="Project name")],
    targets: Annotated[list[str], typer.Argument(help="Document IDs or node IDs to add")],
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Add documents or nodes to a project."""
    database = _get_db(db)
    try:
        proj = database.get_collection_by_name(name)
        if not proj:
            console.print(f"[red]Error:[/red] Project '{name}' not found")
            raise typer.Exit(1)

        added = 0
        for target in targets:
            # Check if it's a document or node
            doc = database.get_document(target)
            if doc:
                database.add_member_to_collection(proj.collection_id, "document", target)
                console.print(f"[green]✓[/green] Added document: {target}")
                added += 1
            else:
                # Try as node (could be short_id or full_id)
                node = database.get_node_by_short_id(target)
                if node:
                    database.add_member_to_collection(proj.collection_id, "node", node.full_id)
                    console.print(f"[green]✓[/green] Added node: {target}")
                    added += 1
                else:
                    console.print(f"[yellow]⊘[/yellow] Not found: {target}")

        console.print(f"\n[bold]Added {added} member(s) to '{name}'[/bold]")
    finally:
        database.close()


@project_app.command("rm")
def project_rm(
    name: Annotated[str, typer.Argument(help="Project name")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Delete a project."""
    database = _get_db(db)
    try:
        proj = database.get_collection_by_name(name)
        if not proj:
            console.print(f"[red]Error:[/red] Project '{name}' not found")
            raise typer.Exit(1)

        members = database.list_collection_members(proj.collection_id)
        if members and not force:
            confirm = typer.confirm(f"Delete project '{name}' with {len(members)} members?")
            if not confirm:
                raise typer.Abort()

        database.delete_collection(proj.collection_id)
        console.print(f"[green]✓[/green] Deleted project: {name}")
    finally:
        database.close()


@project_app.command("show")
def project_show(
    name: Annotated[str, typer.Argument(help="Project name")],
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Show project details and members."""
    database = _get_db(db)
    try:
        proj = database.get_collection_by_name(name)
        if not proj:
            console.print(f"[red]Error:[/red] Project '{name}' not found")
            raise typer.Exit(1)

        console.print(f"\n[bold]{proj.name}[/bold] ({proj.collection_id})")

        members = database.list_collection_members(proj.collection_id)
        if not members:
            console.print("[yellow]No members[/yellow]")
            return

        table = Table(title="Members")
        table.add_column("Type", style="cyan")
        table.add_column("ID")

        for member in members:
            table.add_row(member.member_type, member.member_pk)

        console.print(table)
    finally:
        database.close()


# ============================================================================
# Topic commands
# ============================================================================

topic_app = typer.Typer(help="Manage topics (reusable tags for content).")
app.add_typer(topic_app, name="topic")


@topic_app.command("create")
def topic_create(
    name: Annotated[str, typer.Argument(help="Topic name")],
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Create a new topic."""
    import sqlite3

    database = _get_db(db)
    try:
        topic_id = str(uuid.uuid4())[:8]
        database.create_topic(topic_id, name)
        console.print(f"[green]✓[/green] Created topic: {name} ({topic_id})")
    except sqlite3.IntegrityError:
        console.print(f"[red]Error:[/red] Topic '{name}' already exists")
        raise typer.Exit(1)
    finally:
        database.close()


@topic_app.command("ls")
def topic_ls(
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """List all topics."""
    database = _get_db(db)
    try:
        topics = database.list_topics()
        if not topics:
            console.print("[yellow]No topics found[/yellow]")
            return

        table = Table(title="Topics")
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Links", justify="right")

        for topic in topics:
            links = database.list_targets_for_topic(topic.topic_id)
            table.add_row(topic.name, topic.topic_id, str(len(links)))

        console.print(table)
    finally:
        database.close()


@topic_app.command("tag")
def topic_tag(
    name: Annotated[str, typer.Argument(help="Topic name")],
    target_id: Annotated[str, typer.Option("--id", "-i", help="Node or document ID to tag")],
    weight: Annotated[float, typer.Option("--weight", "-w", help="Relevance weight")] = 1.0,
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Tag a document or node with a topic."""
    database = _get_db(db)
    try:
        topic = database.get_topic_by_name(name)
        if not topic:
            console.print(f"[red]Error:[/red] Topic '{name}' not found")
            raise typer.Exit(1)

        # Check if it's a document or node
        doc = database.get_document(target_id)
        if doc:
            database.tag_with_topic(topic.topic_id, "document", target_id, weight)
            console.print(f"[green]✓[/green] Tagged document '{target_id}' with '{name}'")
        else:
            node = database.get_node_by_short_id(target_id)
            if node:
                database.tag_with_topic(topic.topic_id, "node", node.full_id, weight)
                console.print(f"[green]✓[/green] Tagged node '{target_id}' with '{name}'")
            else:
                console.print(f"[red]Error:[/red] Target not found: {target_id}")
                raise typer.Exit(1)
    finally:
        database.close()


@topic_app.command("untag")
def topic_untag(
    name: Annotated[str, typer.Argument(help="Topic name")],
    target_id: Annotated[str, typer.Option("--id", "-i", help="Node or document ID to untag")],
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Remove a topic tag from a document or node."""
    database = _get_db(db)
    try:
        topic = database.get_topic_by_name(name)
        if not topic:
            console.print(f"[red]Error:[/red] Topic '{name}' not found")
            raise typer.Exit(1)

        # Check if it's a document or node
        doc = database.get_document(target_id)
        if doc:
            removed = database.untag_topic(topic.topic_id, "document", target_id)
        else:
            node = database.get_node_by_short_id(target_id)
            if node:
                removed = database.untag_topic(topic.topic_id, "node", node.full_id)
            else:
                console.print(f"[red]Error:[/red] Target not found: {target_id}")
                raise typer.Exit(1)

        if removed:
            console.print(f"[green]✓[/green] Removed '{name}' from '{target_id}'")
        else:
            console.print("[yellow]⊘[/yellow] Tag not found on target")
    finally:
        database.close()


@topic_app.command("rm")
def topic_rm(
    name: Annotated[str, typer.Argument(help="Topic name")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Delete a topic."""
    database = _get_db(db)
    try:
        topic = database.get_topic_by_name(name)
        if not topic:
            console.print(f"[red]Error:[/red] Topic '{name}' not found")
            raise typer.Exit(1)

        links = database.list_targets_for_topic(topic.topic_id)
        if links and not force:
            confirm = typer.confirm(f"Delete topic '{name}' with {len(links)} links?")
            if not confirm:
                raise typer.Abort()

        database.delete_topic(topic.topic_id)
        console.print(f"[green]✓[/green] Deleted topic: {name}")
    finally:
        database.close()


@topic_app.command("show")
def topic_show(
    name: Annotated[str, typer.Argument(help="Topic name")],
    db: Annotated[Path | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Show topic details and linked targets."""
    database = _get_db(db)
    try:
        topic = database.get_topic_by_name(name)
        if not topic:
            console.print(f"[red]Error:[/red] Topic '{name}' not found")
            raise typer.Exit(1)

        console.print(f"\n[bold]{topic.name}[/bold] ({topic.topic_id})")

        links = database.list_targets_for_topic(topic.topic_id)
        if not links:
            console.print("[yellow]No linked targets[/yellow]")
            return

        table = Table(title="Linked Targets")
        table.add_column("Type", style="cyan")
        table.add_column("ID")
        table.add_column("Weight", justify="right")

        for link in links:
            table.add_row(link.target_type, link.target_pk, f"{link.weight:.1f}")

        console.print(table)
    finally:
        database.close()


if __name__ == "__main__":
    app()
