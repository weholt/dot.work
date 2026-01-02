"""Tests for markdown parser."""

from pathlib import Path

from dot_overview.markdown_parser import extract_sections, slugify_fragment


def test_slugify_fragment_basic() -> None:
    assert slugify_fragment("Hello World") == "hello-world"
    assert slugify_fragment("Test Heading") == "test-heading"


def test_slugify_fragment_special_chars() -> None:
    assert slugify_fragment("Hello! World?") == "hello-world"
    # Special characters become dashes
    assert slugify_fragment("Test@Heading#123") == "test-heading-123"


def test_slugify_fragment_empty() -> None:
    assert slugify_fragment("") == "section"


def test_extract_sections_with_headings(tmp_path: Path) -> None:
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """# Main Title

Content under main title.

## Subsection 1

Content for subsection 1.

### Sub-subsection

Deeper content.

## Subsection 2

More content.
"""
    )

    sections = extract_sections(md_file, md_file.read_text())
    assert len(sections) >= 3

    # Check that Main Title section exists
    main_title = [s for s in sections if s.heading == "Main Title"]
    assert len(main_title) == 1
    assert "Content under main title" in main_title[0].content

    # Check subsections
    subsections = [s for s in sections if s.heading.startswith("Subsection")]
    assert len(subsections) >= 2


def test_extract_sections_levels(tmp_path: Path) -> None:
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """# Level 1

Content 1.

## Level 2

Content 2.

### Level 3

Content 3.
"""
    )

    sections = extract_sections(md_file, md_file.read_text())

    level_1 = [s for s in sections if s.level == 1]
    level_2 = [s for s in sections if s.level == 2]
    level_3 = [s for s in sections if s.level == 3]

    assert len(level_1) == 1
    assert len(level_2) == 1
    assert len(level_3) == 1


def test_extract_sections_no_headings(tmp_path: Path) -> None:
    md_file = tmp_path / "test.md"
    content = "Just some content without headings."
    md_file.write_text(content)

    sections = extract_sections(md_file, content)
    assert len(sections) == 1
    assert sections[0].heading == "(no heading)"
    assert sections[0].level == 0
    assert sections[0].content == content


def test_extract_sections_slug_generation(tmp_path: Path) -> None:
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """# Test Heading

Content.
"""
    )

    sections = extract_sections(md_file, md_file.read_text())
    main_section = [s for s in sections if s.heading == "Test Heading"][0]

    assert "test-heading" in main_section.slug


def test_extract_sections_content_extraction(tmp_path: Path) -> None:
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """# Title

First paragraph.

Second paragraph.

## Next Title

Next content.
"""
    )

    sections = extract_sections(md_file, md_file.read_text())
    title_section = [s for s in sections if s.heading == "Title"][0]

    # Content should include both paragraphs
    assert "First paragraph" in title_section.content
    assert "Second paragraph" in title_section.content
    # But not the next heading content
    assert "Next content" not in title_section.content


def test_extract_sections_source_path(tmp_path: Path) -> None:
    md_file = tmp_path / "subdir" / "test.md"
    md_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.write_text("# Test\nContent")

    sections = extract_sections(md_file, md_file.read_text())
    for section in sections:
        assert "subdir/test.md" in section.source_path
