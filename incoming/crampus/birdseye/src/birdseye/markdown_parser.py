"""Minimal markdown section extraction."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from pathlib import Path

from .models import DocumentSection

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def slugify_fragment(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    slug = slug.strip("-")
    return slug or "section"


def extract_sections(path: Path, text: str) -> list[DocumentSection]:
    """Split markdown into sections keyed by headings."""

    matches = list(_HEADING_PATTERN.finditer(text))
    sections: list[DocumentSection] = []
    normalized_path = path.as_posix()
    hierarchy: list[tuple[int, str]] = []

    if not matches:
        content = text.strip("\n")
        if content:
            slug = f"{normalized_path}#root"
            sections.append(
                DocumentSection(source_path=str(path), heading="(no heading)", level=0, content=content, slug=slug)
            )
        return sections

    preamble = text[: matches[0].start()].strip("\n")
    if preamble:
        sections.append(
            DocumentSection(
                source_path=str(path),
                heading="Preamble",
                level=0,
                content=preamble,
                slug=f"{normalized_path}#preamble",
            )
        )

    for idx, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()
        heading_slug = slugify_fragment(heading)
        while hierarchy and hierarchy[-1][0] >= level:
            hierarchy.pop()
        hierarchy.append((level, heading_slug))
        anchor_slug = "-".join(segment for _, segment in hierarchy)
        slug = f"{normalized_path}#{anchor_slug}"
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end]
        body = body.lstrip("\n").rstrip("\n")
        sections.append(
            DocumentSection(
                source_path=str(path),
                heading=heading,
                level=level,
                content=body,
                slug=slug,
            )
        )
    return sections


def export_sections(sections: Iterable[DocumentSection]) -> Iterator[dict[str, object]]:
    for section in sections:
        yield section.to_dict()
