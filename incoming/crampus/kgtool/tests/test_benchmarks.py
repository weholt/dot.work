import pytest
from kgtool.pipeline import build_graph, discover_topics

pytest.importorskip("pytest_benchmark")


def test_benchmark_discover_topics_extreme(extreme_doc, tmp_output_dir, benchmark):
    def _run():
        discover_topics(
            input_file=str(extreme_doc),
            output_file=str(tmp_output_dir / "topics.json"),
            num_topics=5,  # Reduced from 8 to match document size
            terms_per_topic=12,
        )

    benchmark(_run)


def test_benchmark_build_graph_extreme(extreme_doc, tmp_output_dir, benchmark):
    def _run():
        build_graph(
            input_file=str(extreme_doc),
            output_dir=str(tmp_output_dir),
            min_similarity=0.25,
            top_keywords=8,
            top_keyphrases=10,
        )

    benchmark(_run)
