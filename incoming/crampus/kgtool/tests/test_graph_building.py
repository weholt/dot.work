import json
from pathlib import Path

from kgtool.pipeline import build_graph


def _load_graph(graph_path: Path):
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    return data


def test_build_graph_creates_graph_and_nodes(sample_doc: Path, tmp_output_dir: Path):
    build_graph(
        input_file=str(sample_doc),
        output_dir=str(tmp_output_dir),
        min_similarity=0.2,
        top_keywords=5,
        top_keyphrases=5,
    )

    graph_file = tmp_output_dir / "graph.json"
    assert graph_file.exists()

    graph = _load_graph(graph_file)
    assert len(graph["nodes"]) > 5
    # NetworkX node_link_data uses 'links' key for edges
    edges_key = "links" if "links" in graph else "edges"
    assert len(graph[edges_key]) > 0

    nodes_dir = tmp_output_dir / "nodes"
    assert nodes_dir.exists()
    assert len(list(nodes_dir.glob("*.md"))) > 5


def test_build_graph_with_topics_sets_tags(
    enterprise_doc: Path,
    tmp_output_dir: Path,
    gold_dir: Path,
):
    topic_file = gold_dir / "topic_terms_enterprise.json"

    build_graph(
        input_file=str(enterprise_doc),
        output_dir=str(tmp_output_dir),
        min_similarity=0.2,
        top_keywords=8,
        top_keyphrases=10,
        topic_terms_path=str(topic_file),
    )

    graph_file = tmp_output_dir / "graph.json"
    assert graph_file.exists()

    graph = _load_graph(graph_file)
    nodes = graph["nodes"]

    # Check that at least some nodes have topic tags
    topic_keys = json.loads(topic_file.read_text(encoding="utf-8")).keys()
    node_tags = [tag for node in nodes for tag in node.get("tags", [])]
    assert len(node_tags) > 0
    assert any(t in node_tags for t in topic_keys)
