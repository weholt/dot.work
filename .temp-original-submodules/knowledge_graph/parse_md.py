"""Streaming Markdown parser for kgshred.

Parses Markdown into structural blocks with byte offsets for lossless reconstruction.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from typing import BinaryIO


class BlockKind(Enum):
    """Types of Markdown blocks."""

    DOC = "doc"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CODEBLOCK = "codeblock"


@dataclass
class Block:
    """A parsed Markdown block with byte offsets."""

    kind: BlockKind
    start: int
    end: int
    level: int | None = None
    title: str | None = None
    language: str | None = None  # For code blocks


# Regex patterns
HEADING_PATTERN = re.compile(rb"^(#{1,6}) (.+)$")
CODE_FENCE_BACKTICK = re.compile(rb"^```(.*)$")
CODE_FENCE_TILDE = re.compile(rb"^~~~(.*)$")


def parse_markdown(content: bytes) -> Iterator[Block]:
    """Parse Markdown content into blocks with byte offsets.

    This is a streaming parser that yields blocks as they complete.
    Tracks exact byte offsets for lossless reconstruction.

    Args:
        content: Raw Markdown content as bytes.

    Yields:
        Block objects with kind, start, end, and optional metadata.
    """
    if not content:
        return

    lines = _split_lines_with_offsets(content)
    yield from _parse_blocks(lines, len(content))


def parse_markdown_stream(stream: BinaryIO) -> Iterator[Block]:
    """Parse Markdown from a binary stream.

    Reads the entire stream into memory, then parses.
    For truly streaming parsing of very large files, use parse_markdown_chunked.

    Args:
        stream: Binary file-like object.

    Yields:
        Block objects.
    """
    content = stream.read()
    yield from parse_markdown(content)


def _split_lines_with_offsets(content: bytes) -> list[tuple[bytes, int, int]]:
    """Split content into lines with byte offsets.

    Args:
        content: Raw bytes.

    Returns:
        List of (line_content, start_offset, end_offset) tuples.
        Line content excludes the newline, but end_offset includes it.
    """
    lines: list[tuple[bytes, int, int]] = []
    start = 0

    while start < len(content):
        # Find next newline
        newline_pos = content.find(b"\n", start)

        if newline_pos == -1:
            # Last line without trailing newline
            line = content[start:]
            lines.append((line, start, len(content)))
            break

        # Check for CRLF
        if newline_pos > 0 and content[newline_pos - 1 : newline_pos] == b"\r":
            line = content[start : newline_pos - 1]
            end = newline_pos + 1
        else:
            line = content[start:newline_pos]
            end = newline_pos + 1

        lines.append((line, start, end))
        start = end

    return lines


def _parse_blocks(
    lines: list[tuple[bytes, int, int]],
    content_length: int,
) -> Iterator[Block]:
    """Parse lines into blocks.

    Args:
        lines: List of (line, start, end) tuples.
        content_length: Total content length.

    Yields:
        Block objects.
    """
    if not lines:
        return

    i = 0
    n = len(lines)

    while i < n:
        line, line_start, line_end = lines[i]
        stripped = line.strip()

        # Check for heading
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).decode("utf-8", errors="replace")
            yield Block(
                kind=BlockKind.HEADING,
                start=line_start,
                end=line_end,
                level=level,
                title=title,
            )
            i += 1
            continue

        # Check for code fence
        backtick_match = CODE_FENCE_BACKTICK.match(line)
        tilde_match = CODE_FENCE_TILDE.match(line)

        if backtick_match or tilde_match:
            match = backtick_match or tilde_match
            fence_char = b"```" if backtick_match else b"~~~"
            language_raw = match.group(1) if match else b""
            language = language_raw.decode("utf-8", errors="replace").strip() or None

            block_start = line_start
            i += 1

            # Find closing fence
            while i < n:
                close_line, _, close_end = lines[i]
                if close_line.strip().startswith(fence_char):
                    yield Block(
                        kind=BlockKind.CODEBLOCK,
                        start=block_start,
                        end=close_end,
                        language=language or None,
                    )
                    i += 1
                    break
                i += 1
            else:
                # Unclosed fence extends to EOF
                yield Block(
                    kind=BlockKind.CODEBLOCK,
                    start=block_start,
                    end=content_length,
                    language=language or None,
                )
            continue

        # Check for blank line (paragraph separator)
        if not stripped:
            i += 1
            continue

        # Start of paragraph
        para_start = line_start
        para_end = line_end
        i += 1

        # Consume lines until blank line, heading, or code fence
        while i < n:
            next_line, next_start, next_end = lines[i]
            next_stripped = next_line.strip()

            # Blank line ends paragraph
            if not next_stripped:
                break

            # Heading ends paragraph
            if HEADING_PATTERN.match(next_line):
                break

            # Code fence ends paragraph
            if CODE_FENCE_BACKTICK.match(next_line) or CODE_FENCE_TILDE.match(next_line):
                break

            para_end = next_end
            i += 1

        yield Block(
            kind=BlockKind.PARAGRAPH,
            start=para_start,
            end=para_end,
        )


def get_block_content(content: bytes, block: Block) -> bytes:
    """Extract raw content bytes for a block.

    Args:
        content: Original document content.
        block: Block with start/end offsets.

    Returns:
        Raw bytes from content[block.start:block.end].
    """
    return content[block.start : block.end]


def reconstruct_document(content: bytes, blocks: list[Block]) -> bytes:
    """Reconstruct document from blocks.

    This is the inverse of parsing - should produce identical bytes.

    Args:
        content: Original document content.
        blocks: List of blocks from parsing.

    Returns:
        Reconstructed content (should equal original).
    """
    if not blocks:
        return b""

    # Sort blocks by start offset
    sorted_blocks = sorted(blocks, key=lambda b: b.start)

    result = bytearray()
    for block in sorted_blocks:
        result.extend(content[block.start : block.end])

    return bytes(result)
