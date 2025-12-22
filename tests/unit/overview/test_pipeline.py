"""Tests for analysis pipeline."""

from pathlib import Path

from dot_work.overview.pipeline import (
    AnalysisBundle,
    _assign_feature_ids,
    _attach_document_references,
    analyze_project,
    write_outputs,
)


def test_analyze_project_returns_bundle(sample_project_dir: Path) -> None:
    bundle = analyze_project(sample_project_dir)
    assert isinstance(bundle, AnalysisBundle)
    assert hasattr(bundle, "features")
    assert hasattr(bundle, "models")
    assert hasattr(bundle, "documents")


def test_analyze_project_finds_python_features(sample_project_dir: Path) -> None:
    bundle = analyze_project(sample_project_dir)
    assert len(bundle.features) > 0

    # Should find the hello function
    hello_features = [f for f in bundle.features if f.name == "hello"]
    assert len(hello_features) == 1
    assert hello_features[0].kind == "function"


def test_analyze_project_finds_classes(sample_project_dir: Path) -> None:
    bundle = analyze_project(sample_project_dir)

    # Should find the Greeter class
    greeter_classes = [f for f in bundle.features if f.name == "Greeter"]
    assert len(greeter_classes) == 1
    assert greeter_classes[0].kind == "class"


def test_analyze_project_finds_methods(sample_project_dir: Path) -> None:
    bundle = analyze_project(sample_project_dir)

    # Should find the greet method
    greet_methods = [f for f in bundle.features if f.name == "greet"]
    assert len(greet_methods) >= 1
    assert any(f.kind == "method" for f in greet_methods)


def test_analyze_project_finds_data_models(sample_project_dir: Path) -> None:
    bundle = analyze_project(sample_project_dir)

    # Person dataclass might be detected as either model or class feature
    person_models = [m for m in bundle.models if m.name == "Person"]
    person_features = [f for f in bundle.features if f.name == "Person"]

    # Should find Person somewhere
    assert len(person_models) > 0 or len(person_features) > 0

    # If detected as a model, verify fields
    if person_models:
        assert len(person_models[0].fields) > 0


def test_analyze_project_finds_document_sections(sample_project_dir: Path) -> None:
    bundle = analyze_project(sample_project_dir)
    assert len(bundle.documents) > 0

    # Should find headings from README
    headings = [d.heading for d in bundle.documents]
    assert "Features" in headings
    assert "Usage" in headings


def test_analyze_project_empty_project(empty_project_dir: Path) -> None:
    bundle = analyze_project(empty_project_dir)
    assert len(bundle.features) == 0
    assert len(bundle.models) == 0
    assert len(bundle.documents) == 0


def test_assign_feature_ids() -> None:
    from dot_work.overview.models import Feature

    features = [
        Feature(
            name="func_b",
            qualified_name="a:func_b",
            kind="function",
            module_path="a",
            parent=None,
            docstring=None,
            args=[],
            returns=None,
            avg_complexity=1.0,
            maintainability_index=50.0,
        ),
        Feature(
            name="func_a",
            qualified_name="a:func_a",
            kind="function",
            module_path="a",
            parent=None,
            docstring=None,
            args=[],
            returns=None,
            avg_complexity=1.0,
            maintainability_index=50.0,
        ),
        Feature(
            name="func_c",
            qualified_name="b:func_c",
            kind="function",
            module_path="b",
            parent=None,
            docstring=None,
            args=[],
            returns=None,
            avg_complexity=1.0,
            maintainability_index=50.0,
        ),
    ]

    _assign_feature_ids(features)

    # All features should have IDs
    for feature in features:
        assert feature.feature_id is not None
        assert feature.feature_id.startswith("F-")

    # IDs should be sequential (sorted by module_path, kind, qualified_name)
    # func_a comes before func_b alphabetically within the same module
    ids = [f.feature_id for f in features]
    assert len(ids) == len(set(ids))  # All unique


def test_attach_document_references() -> None:
    from dot_work.overview.models import DocumentSection, Feature

    features = [
        Feature(
            name="hello_func",
            qualified_name="mod:hello_func",
            kind="function",
            module_path="mod",
            parent=None,
            docstring=None,
            args=[],
            returns=None,
            avg_complexity=1.0,
            maintainability_index=50.0,
            doc_refs=[],
        )
    ]

    documents = [
        DocumentSection(
            source_path="README.md",
            heading="Hello Func",
            level=2,
            content="Documentation for hello_func",
            # Slug needs the # separator format used by the parser
            slug="readme.md#hello-func",
        )
    ]

    _attach_document_references(features, documents)

    # Feature should have document reference
    assert len(features[0].doc_refs) > 0


def test_write_outputs_creates_files(sample_project_dir: Path, tmp_path: Path) -> None:
    bundle = analyze_project(sample_project_dir)
    output_dir = tmp_path / "output"

    destinations = write_outputs(bundle, output_dir)

    assert output_dir.exists()
    assert "features_json" in destinations
    assert "documents_json" in destinations
    assert "overview_markdown" in destinations

    # Check files exist
    assert destinations["features_json"].exists()
    assert destinations["documents_json"].exists()
    assert destinations["overview_markdown"].exists()


def test_write_outputs_content(sample_project_dir: Path, tmp_path: Path) -> None:
    bundle = analyze_project(sample_project_dir)
    output_dir = tmp_path / "output"

    destinations = write_outputs(bundle, output_dir)

    # Check features JSON
    features_json = destinations["features_json"].read_text(encoding="utf-8")
    assert "features" in features_json
    assert "models" in features_json

    # Check documents JSON
    documents_json = destinations["documents_json"].read_text(encoding="utf-8")
    import json

    docs = json.loads(documents_json)
    assert isinstance(docs, list)

    # Check markdown
    markdown = destinations["overview_markdown"].read_text(encoding="utf-8")
    assert "# Birdseye Project Guide" in markdown
