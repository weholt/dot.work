from pathlib import Path

from kgtool.pipeline import build_graph, extract_topic_context


def test_extract_frontend_context_from_sample(sample_doc: Path, tmp_output_dir: Path):
    # Build graph without custom topics; fallback will use keywords/title
    build_graph(
        input_file=str(sample_doc),
        output_dir=str(tmp_output_dir),
        min_similarity=0.2,
        top_keywords=5,
        top_keyphrases=5,
    )

    graph_file = tmp_output_dir / "graph.json"
    output_file = tmp_output_dir / "frontend_context.md"

    extract_topic_context(
        topic="frontend",
        graph_path=str(graph_file),
        output_file=str(output_file),
        include_neighbors=False,
    )

    assert output_file.exists()
    text = output_file.read_text(encoding="utf-8")
    assert "frontend" in text.lower()
    # Should not heavily include backend content
    assert "backend architecture" not in text or text.count("backend architecture") < text.count("frontend architecture")


def test_extract_frontend_context_with_topics(
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
    output_file = tmp_output_dir / "frontend_context.md"

    extract_topic_context(
        topic="frontend",
        graph_path=str(graph_file),
        output_file=str(output_file),
        include_neighbors=True,
    )

    assert output_file.exists()
    text = output_file.read_text(encoding="utf-8")
    assert "frontend" in text.lower()
    assert text.count("## [") >= 2
