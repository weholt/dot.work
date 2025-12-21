from pathlib import Path

import json
import pytest

from kgtool.pipeline import discover_topics


def test_discover_topics_creates_json(sample_doc: Path, tmp_output_dir: Path):
    out = tmp_output_dir / "topics.json"
    discover_topics(
        input_file=str(sample_doc),
        output_file=str(out),
        num_topics=3,
        terms_per_topic=8,
    )
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 3
    assert "topic_0" in data


def test_discover_topics_enterprise_has_reasonable_topics(enterprise_doc: Path, tmp_output_dir: Path):
    out = tmp_output_dir / "topics_enterprise.json"
    discover_topics(
        input_file=str(enterprise_doc),
        output_file=str(out),
        num_topics=5,
        terms_per_topic=15,
    )
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 5

    # Check that topics contain relevant terms
    all_terms = [term for terms in data.values() for term in terms]
    joined_terms = " ".join(all_terms).lower()
    assert any(term in joined_terms for term in ["frontend", "react", "ui", "component"])
    assert any(term in joined_terms for term in ["backend", "service", "api", "microservice"])
    assert any(term in joined_terms for term in ["kubernetes", "cluster", "infra"])
