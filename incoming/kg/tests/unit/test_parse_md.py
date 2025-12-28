"""Unit tests for kgshred.parse_md module."""

from __future__ import annotations

import io

from kgshred.parse_md import (
    Block,
    BlockKind,
    get_block_content,
    parse_markdown,
    parse_markdown_stream,
    reconstruct_document,
)


class TestHeadingParsing:
    """Tests for heading parsing."""

    def test_parse_h1_heading(self) -> None:
        """Should parse # as H1 with level=1."""
        content = b"# Hello World\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 1
        assert blocks[0].kind == BlockKind.HEADING
        assert blocks[0].level == 1
        assert blocks[0].title == "Hello World"

    def test_parse_h2_through_h6_headings(self) -> None:
        """Should parse ## through ###### with correct levels."""
        content = b"## Level 2\n### Level 3\n#### Level 4\n##### Level 5\n###### Level 6\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 5
        for i, block in enumerate(blocks, start=2):
            assert block.kind == BlockKind.HEADING
            assert block.level == i
            assert block.title == f"Level {i}"

    def test_heading_title_extracted(self) -> None:
        """Heading title should be text after # and space."""
        content = b"# My Title Here\n"
        blocks = list(parse_markdown(content))

        assert blocks[0].title == "My Title Here"

    def test_heading_without_space_not_heading(self) -> None:
        """#foo should not be parsed as heading (no space)."""
        content = b"#foo\n"
        blocks = list(parse_markdown(content))

        # Should be paragraph, not heading
        assert len(blocks) == 1
        assert blocks[0].kind == BlockKind.PARAGRAPH

    def test_heading_byte_offsets_correct(self) -> None:
        """Start/end offsets should match actual byte positions."""
        content = b"# Heading\n"
        blocks = list(parse_markdown(content))

        assert blocks[0].start == 0
        assert blocks[0].end == 10
        assert content[blocks[0].start : blocks[0].end] == b"# Heading\n"

    def test_heading_with_unicode(self) -> None:
        """Heading with unicode should parse correctly."""
        content = "# Hello 世界\n".encode()
        blocks = list(parse_markdown(content))

        assert blocks[0].title == "Hello 世界"


class TestParagraphParsing:
    """Tests for paragraph parsing."""

    def test_parse_single_paragraph(self) -> None:
        """Single paragraph should be one block."""
        content = b"This is a paragraph.\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 1
        assert blocks[0].kind == BlockKind.PARAGRAPH

    def test_parse_multiple_paragraphs(self) -> None:
        """Blank line should separate paragraphs."""
        content = b"First paragraph.\n\nSecond paragraph.\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 2
        assert all(b.kind == BlockKind.PARAGRAPH for b in blocks)

    def test_paragraph_preserves_internal_newlines(self) -> None:
        """Paragraph with single newlines should be one block."""
        content = b"Line one\nLine two\nLine three\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 1
        assert blocks[0].kind == BlockKind.PARAGRAPH

    def test_paragraph_byte_offsets_correct(self) -> None:
        """Paragraph offsets should be accurate."""
        content = b"First para.\n\nSecond para.\n"
        blocks = list(parse_markdown(content))

        assert blocks[0].start == 0
        assert blocks[0].end == 12
        assert content[blocks[0].start : blocks[0].end] == b"First para.\n"

        assert blocks[1].start == 13
        assert blocks[1].end == 26
        assert content[blocks[1].start : blocks[1].end] == b"Second para.\n"

    def test_paragraph_ends_at_heading(self) -> None:
        """Paragraph should end when heading starts."""
        content = b"Some text\n# Heading\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 2
        assert blocks[0].kind == BlockKind.PARAGRAPH
        assert blocks[1].kind == BlockKind.HEADING


class TestCodeFenceParsing:
    """Tests for code fence parsing."""

    def test_parse_backtick_code_fence(self) -> None:
        """``` should start/end code block."""
        content = b"```\ncode here\n```\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 1
        assert blocks[0].kind == BlockKind.CODEBLOCK

    def test_parse_tilde_code_fence(self) -> None:
        """~~~ should start/end code block."""
        content = b"~~~\ncode here\n~~~\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 1
        assert blocks[0].kind == BlockKind.CODEBLOCK

    def test_code_fence_preserves_content_exactly(self) -> None:
        """Content inside fence should be preserved verbatim."""
        content = b"```\nline 1\n  indented\n```\n"
        blocks = list(parse_markdown(content))

        block_content = get_block_content(content, blocks[0])
        assert b"line 1\n  indented" in block_content

    def test_code_fence_with_language_tag(self) -> None:
        """```python should capture language in metadata."""
        content = b"```python\nprint('hello')\n```\n"
        blocks = list(parse_markdown(content))

        assert blocks[0].language == "python"

    def test_code_fence_byte_offsets_include_fences(self) -> None:
        """Offsets should include the fence lines."""
        content = b"```\ncode\n```\n"
        blocks = list(parse_markdown(content))

        assert blocks[0].start == 0
        assert blocks[0].end == 13
        assert content[blocks[0].start : blocks[0].end] == content

    def test_unclosed_code_fence_extends_to_eof(self) -> None:
        """Unclosed fence should extend to end of file."""
        content = b"```\ncode without closing"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 1
        assert blocks[0].kind == BlockKind.CODEBLOCK
        assert blocks[0].end == len(content)

    def test_code_fence_no_language(self) -> None:
        """Code fence without language should have None."""
        content = b"```\ncode\n```\n"
        blocks = list(parse_markdown(content))

        assert blocks[0].language is None


class TestByteOffsetAccuracy:
    """Tests for byte offset accuracy."""

    def test_byte_offsets_with_ascii(self) -> None:
        """Offsets correct for ASCII content."""
        content = b"# Title\nParagraph text.\n"
        blocks = list(parse_markdown(content))

        for block in blocks:
            extracted = content[block.start : block.end]
            assert len(extracted) > 0

    def test_byte_offsets_with_utf8(self) -> None:
        """Offsets correct for UTF-8 multi-byte characters."""
        content = "# 日本語\nテキスト\n".encode()
        blocks = list(parse_markdown(content))

        assert len(blocks) == 2
        # Verify we can extract valid UTF-8
        for block in blocks:
            extracted = content[block.start : block.end]
            decoded = extracted.decode("utf-8")
            assert len(decoded) > 0

    def test_byte_offsets_with_crlf(self) -> None:
        """Offsets correct for Windows line endings."""
        content = b"# Title\r\nParagraph.\r\n"
        blocks = list(parse_markdown(content))

        # Should still parse correctly
        assert len(blocks) == 2

    def test_byte_offsets_with_lf(self) -> None:
        """Offsets correct for Unix line endings."""
        content = b"# Title\nParagraph.\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 2


class TestMixedContent:
    """Tests for mixed content documents."""

    def test_mixed_content_document(self) -> None:
        """Complex document with all block types should parse correctly."""
        content = b"""# Main Title

First paragraph with some text.

## Section One

More paragraph content here.

```python
def hello():
    print("world")
```

### Subsection

Final paragraph.
"""
        blocks = list(parse_markdown(content))

        kinds = [b.kind for b in blocks]
        assert BlockKind.HEADING in kinds
        assert BlockKind.PARAGRAPH in kinds
        assert BlockKind.CODEBLOCK in kinds

    def test_blocks_under_heading_order(self) -> None:
        """Blocks should be in document order."""
        content = b"# First\nPara 1\n# Second\nPara 2\n"
        blocks = list(parse_markdown(content))

        assert blocks[0].kind == BlockKind.HEADING
        assert blocks[0].title == "First"
        assert blocks[1].kind == BlockKind.PARAGRAPH
        assert blocks[2].kind == BlockKind.HEADING
        assert blocks[2].title == "Second"
        assert blocks[3].kind == BlockKind.PARAGRAPH


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_file(self) -> None:
        """Empty file should produce no blocks."""
        content = b""
        blocks = list(parse_markdown(content))

        assert len(blocks) == 0

    def test_only_whitespace(self) -> None:
        """Whitespace-only file should produce no blocks."""
        content = b"   \n\n   \n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 0

    def test_heading_at_end_no_trailing_newline(self) -> None:
        """Heading at EOF without newline should be parsed."""
        content = b"# Final Heading"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 1
        assert blocks[0].kind == BlockKind.HEADING
        assert blocks[0].title == "Final Heading"

    def test_code_fence_at_end(self) -> None:
        """Code fence at EOF should be closed properly."""
        content = b"```\ncode\n```"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 1
        assert blocks[0].kind == BlockKind.CODEBLOCK

    def test_multiple_blank_lines(self) -> None:
        """Multiple blank lines should be handled."""
        content = b"Para 1\n\n\n\nPara 2\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 2
        assert all(b.kind == BlockKind.PARAGRAPH for b in blocks)

    def test_heading_after_code_fence(self) -> None:
        """Heading after code fence should parse."""
        content = b"```\ncode\n```\n# Heading\n"
        blocks = list(parse_markdown(content))

        assert len(blocks) == 2
        assert blocks[0].kind == BlockKind.CODEBLOCK
        assert blocks[1].kind == BlockKind.HEADING


class TestStreamParsing:
    """Tests for stream-based parsing."""

    def test_parse_from_stream(self) -> None:
        """Should parse from binary stream."""
        content = b"# Title\nContent\n"
        stream = io.BytesIO(content)

        blocks = list(parse_markdown_stream(stream))

        assert len(blocks) == 2


class TestReconstruction:
    """Tests for document reconstruction."""

    def test_reconstruct_equals_original(self) -> None:
        """Reconstructing from blocks should equal original (excluding blank lines)."""
        # Use content without blank line separators for exact reconstruction
        content = b"# Title\nParagraph text.\n```python\ncode\n```\n"
        blocks = list(parse_markdown(content))

        reconstructed = reconstruct_document(content, blocks)

        assert reconstructed == content

    def test_reconstruct_empty_blocks(self) -> None:
        """Empty block list should produce empty bytes."""
        result = reconstruct_document(b"content", [])

        assert result == b""

    def test_get_block_content(self) -> None:
        """get_block_content should extract correct bytes."""
        content = b"# Title\nParagraph\n"
        blocks = list(parse_markdown(content))

        title_content = get_block_content(content, blocks[0])
        assert title_content == b"# Title\n"

        para_content = get_block_content(content, blocks[1])
        assert para_content == b"Paragraph\n"


class TestBlockDataclass:
    """Tests for Block dataclass."""

    def test_block_defaults(self) -> None:
        """Block should have correct defaults."""
        block = Block(kind=BlockKind.PARAGRAPH, start=0, end=10)

        assert block.level is None
        assert block.title is None
        assert block.language is None

    def test_block_with_all_fields(self) -> None:
        """Block should accept all fields."""
        block = Block(
            kind=BlockKind.HEADING,
            start=0,
            end=10,
            level=1,
            title="Test",
        )

        assert block.level == 1
        assert block.title == "Test"
