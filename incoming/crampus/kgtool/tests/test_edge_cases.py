from pathlib import Path

import pytest
from kgtool.pipeline import build_graph, discover_topics


def test_build_graph_no_headings_raises(data_dir: Path, tmp_output_dir: Path):
    file = data_dir / "edge_cases" / "no_headings.md"
    with pytest.raises(ValueError, match="No headings found"):
        build_graph(
            input_file=str(file),
            output_dir=str(tmp_output_dir),
        )


def test_discover_topics_no_headings_raises(data_dir: Path, tmp_output_dir: Path):
    file = data_dir / "edge_cases" / "no_headings.md"
    with pytest.raises(ValueError, match="No headings found"):
        discover_topics(
            input_file=str(file),
            output_file=str(tmp_output_dir / "topics.json"),
        )


def test_build_graph_tiny_frontend(data_dir: Path, tmp_output_dir: Path):
    file = data_dir / "edge_cases" / "tiny_frontend.md"
    build_graph(
        input_file=str(file),
        output_dir=str(tmp_output_dir),
    )
    assert (tmp_output_dir / "graph.json").exists()
    assert any((tmp_output_dir / "nodes").iterdir())


def test_build_graph_tiny_backend(data_dir: Path, tmp_output_dir: Path):
    file = data_dir / "edge_cases" / "tiny_backend.md"
    build_graph(
        input_file=str(file),
        output_dir=str(tmp_output_dir),
    )
    assert (tmp_output_dir / "graph.json").exists()
    assert any((tmp_output_dir / "nodes").iterdir())
