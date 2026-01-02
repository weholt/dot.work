"""
Dependency graph analysis for Python code.

Analyzes import relationships between modules.
"""

from collections import defaultdict
from pathlib import Path

from dot_work.python.scan.models import CodeIndex, Dependency


def build_dependency_graph(index: CodeIndex) -> dict[str, list[str]]:
    """Build a dependency graph from the code index.

    Args:
        index: CodeIndex to analyze.

    Returns:
        Dictionary mapping file paths to lists of dependencies.
    """
    graph: dict[str, list[str]] = defaultdict(list)

    for file_path_str, file_entity in index.files.items():
        for imp in file_entity.imports:
            module = imp.module.split(".")[0]

            # Check if module is in the current project
            for other_path_str in index.files:
                other_path = Path(other_path_str)
                if other_path.stem == module:
                    graph[file_path_str].append(other_path_str)
                    break

    return dict(graph)


def get_dependencies(index: CodeIndex, file_path: Path) -> list[Dependency]:
    """Get all dependencies for a specific file.

    Args:
        index: CodeIndex to query.
        file_path: File to get dependencies for.

    Returns:
        List of Dependency objects.
    """
    dependencies: list[Dependency] = []
    path_str = str(file_path)

    if path_str not in index.files:
        return dependencies

    file_entity = index.files[path_str]

    for imp in file_entity.imports:
        module = imp.module.split(".")[0]

        for other_entity in index.files.values():
            if other_entity.path.stem == module:
                dependencies.append(
                    Dependency(
                        from_file=file_path,
                        to_file=other_entity.path,
                        import_name=imp.module,
                        line_no=imp.line_no,
                    )
                )
                break

    return dependencies


def find_circular_dependencies(index: CodeIndex) -> list[list[str]]:
    """Find circular dependencies in the codebase.

    Args:
        index: CodeIndex to analyze.

    Returns:
        List of circular dependency chains.
    """
    graph = build_dependency_graph(index)

    visited: set[str] = set()
    rec_stack: set[str] = set()
    circles: list[list[str]] = []

    def _dfs(node: str, path: list[str]) -> None:
        """Depth-first search for cycles.

        Args:
            node: Current node.
            path: Current path.
        """
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                _dfs(neighbor, path)
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                circles.append(path[cycle_start:] + [neighbor])

        path.pop()
        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            _dfs(node, [])

    return circles


def get_layered_structure(index: CodeIndex) -> dict[str, list[str]]:
    """Get a layered view of the codebase structure.

    Args:
        index: CodeIndex to analyze.

    Returns:
        Dictionary mapping layer names to file paths.
    """
    graph = build_dependency_graph(index)

    # Calculate in-degree for each node
    in_degree: dict[str, int] = defaultdict(int)
    all_files = set()

    for file_path in index.files:
        all_files.add(str(file_path))
        in_degree[str(file_path)] += len(graph.get(str(file_path), []))

    # Find files with no dependencies (layer 0)
    layers: dict[str, list[str]] = {}
    remaining = set(all_files)
    layer_num = 0

    while remaining:
        # Find files with all dependencies in previous layers
        current_layer: list[str] = []
        for file_path in list(remaining):
            deps = graph.get(file_path, [])
            if not deps or all(d not in remaining for d in deps):
                current_layer.append(file_path)

        if not current_layer:
            # Circular dependency or leftover
            for file_path in remaining:
                layers[f"layer_{layer_num}"] = layers.get(f"layer_{layer_num}", [])
                layers[f"layer_{layer_num}"].append(file_path)
            break

        layers[f"layer_{layer_num}"] = current_layer
        for file_path in current_layer:
            remaining.remove(file_path)

        layer_num += 1

    return layers
