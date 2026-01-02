"""Tests for overview data models."""

from dot_overview.models import (
    AnalysisBundle,
    Argument,
    DocumentSection,
    Feature,
    ModelDef,
    ModelField,
)


def test_argument_to_dict() -> None:
    arg = Argument(name="foo", annotation="str")
    assert arg.to_dict() == {"name": "foo", "type": "str"}


def test_argument_to_dict_no_annotation() -> None:
    arg = Argument(name="foo", annotation=None)
    assert arg.to_dict() == {"name": "foo", "type": None}


def test_feature_short_doc_with_docstring() -> None:
    # The short_doc function splits on ".\n" (period + newline), not just "."
    # So it will return the full docstring if there's no period followed by newline
    feature = Feature(
        name="test",
        qualified_name="module:test",
        kind="function",
        module_path="module",
        parent=None,
        docstring="This is a test.\nWith more details.",
        args=[],
        returns=None,
        avg_complexity=1.0,
        maintainability_index=50.0,
    )
    assert feature.short_doc() == "This is a test."


def test_feature_short_doc_without_docstring() -> None:
    feature = Feature(
        name="test",
        qualified_name="module:test",
        kind="function",
        module_path="module",
        parent=None,
        docstring=None,
        args=[],
        returns=None,
        avg_complexity=1.0,
        maintainability_index=50.0,
    )
    assert feature.short_doc() == "No description provided."


def test_feature_to_dict() -> None:
    feature = Feature(
        name="test_func",
        qualified_name="module:test_func",
        kind="function",
        module_path="module",
        parent=None,
        docstring="Test function",
        args=[Argument(name="x", annotation="int")],
        returns="str",
        avg_complexity=2.0,
        maintainability_index=75.0,
        api=True,
    )
    result = feature.to_dict()
    assert result["name"] == "test_func"
    assert result["args"] == [{"name": "x", "type": "int"}]
    assert result["api"] is True


def test_model_field_to_dict() -> None:
    field = ModelField(name="id", annotation="int", default=None)
    assert field.to_dict() == {"name": "id", "annotation": "int", "default": None}


def test_model_def_to_dict() -> None:
    model = ModelDef(
        name="User",
        qualified_name="models:User",
        bases=["BaseModel"],
        docstring="User model",
        fields=[ModelField(name="id", annotation="int", default=None)],
        module_path="models",
    )
    result = model.to_dict()
    assert result["name"] == "User"
    assert result["fields"] == [{"name": "id", "annotation": "int", "default": None}]


def test_document_section_summary_short_content() -> None:
    section = DocumentSection(
        source_path="README.md",
        heading="Introduction",
        level=1,
        content="This is short content.",
        slug="readme-introduction",
    )
    assert section.summary() == "This is short content."


def test_document_section_summary_long_content() -> None:
    long_content = "This is a very long content that should be truncated. " * 10
    section = DocumentSection(
        source_path="README.md",
        heading="Introduction",
        level=1,
        content=long_content,
        slug="readme-introduction",
    )
    summary = section.summary()
    assert len(summary) <= 223  # 220 + "..."
    assert summary.endswith("…")


def test_document_section_to_dict() -> None:
    section = DocumentSection(
        source_path="README.md",
        heading="Introduction",
        level=1,
        content="Content here",
        slug="readme-introduction",
    )
    result = section.to_dict()
    assert result["source_path"] == "README.md"
    assert result["heading"] == "Introduction"


def test_analysis_bundle_to_dict() -> None:
    bundle = AnalysisBundle(
        features=[
            Feature(
                name="func",
                qualified_name="mod:func",
                kind="function",
                module_path="mod",
                parent=None,
                docstring=None,
                args=[],
                returns=None,
                avg_complexity=1.0,
                maintainability_index=50.0,
            )
        ],
        models=[
            ModelDef(
                name="Model",
                qualified_name="mod:Model",
                bases=[],
                docstring=None,
                fields=[],
                module_path="mod",
            )
        ],
        documents=[
            DocumentSection(
                source_path="README.md",
                heading="Intro",
                level=1,
                content="Content",
                slug="readme-intro",
            )
        ],
    )
    result = bundle.to_dict()
    assert "features" in result
    assert "models" in result
    assert "documents" in result
    assert len(result["features"]) == 1
    assert len(result["models"]) == 1
    assert len(result["documents"]) == 1
