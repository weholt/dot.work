from pathlib import Path

from kgtool.pipeline import extract_chunks


def test_extract_chunks_sample_has_multiple_sections(sample_doc: Path):
    text = sample_doc.read_text(encoding="utf-8")
    chunks = extract_chunks(text)
    assert len(chunks) > 5
    titles = [title for title, _ in chunks]
    assert "Frontend Architecture" in titles
    assert "Backend Architecture" in titles
    assert "Infrastructure & Deployment" in titles


def test_extract_chunks_enterprise_has_frontend_and_backend(enterprise_doc: Path):
    text = enterprise_doc.read_text(encoding="utf-8")
    chunks = extract_chunks(text)
    titles = [title for title, _ in chunks]
    assert any("Frontend" in t or "User Interface" in t for t in titles)
    assert any("Backend" in t or "Application Services" in t for t in titles)
    assert any("Infrastructure" in t for t in titles)


def test_extract_chunks_chaotic_handles_weird_headings(chaotic_doc: Path):
    text = chaotic_doc.read_text(encoding="utf-8")
    chunks = extract_chunks(text)
    assert len(chunks) > 0
    titles = [title for title, _ in chunks]
    assert any("intro" in t.lower() for t in titles)
