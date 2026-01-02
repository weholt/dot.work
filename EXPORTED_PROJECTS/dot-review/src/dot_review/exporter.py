"""Export review comments for agentic coders."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from dot_review.models import ReviewComment
from dot_review.storage import ensure_store, load_comments


def export_agent_md(root: str, review_id: str) -> Path:
    """Export review comments as agent-friendly markdown.

    Args:
        root: Repository root directory.
        review_id: Review identifier to export.

    Returns:
        Path to the exported markdown file.
    """
    base = ensure_store(root)
    out_dir = base / "exports" / review_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "review.md"

    comments = load_comments(root, review_id)
    by_file: dict[str, list[ReviewComment]] = defaultdict(list)
    for c in comments:
        by_file[c.path].append(c)

    def _fmt_ctx(lines: list[str]) -> str:
        return "\n".join(lines).rstrip("\n")

    md: list[str] = []
    md.append(f"# Review Bundle: {review_id}")
    md.append("")
    md.append("## Instructions")
    md.append("- Apply changes based on comments below.")
    md.append("- Prefer using the provided context and line numbers.")
    md.append("- Re-locate if the file has shifted since the review.")
    md.append("")

    for path in sorted(by_file.keys()):
        md.append(f"## {path}")
        md.append("")
        for c in sorted(by_file[path], key=lambda x: (x.line, x.created_unix)):
            md.append(f"### L{c.line} ({c.side}) — {c.id}")
            md.append("")
            if c.context_before or c.context_after:
                md.append("**Context**")
                md.append("```text")
                if c.context_before:
                    md.append(_fmt_ctx(c.context_before))
                md.append(f">>> TARGET LINE: {c.line} ({c.side})")
                if c.context_after:
                    md.append(_fmt_ctx(c.context_after))
                md.append("```")
                md.append("")
            md.append("**Comment**")
            md.append("")
            md.append(c.message.strip())
            md.append("")
            if c.suggestion:
                md.append("**Suggested change**")
                md.append("```suggestion")
                md.append(c.suggestion.rstrip("\n"))
                md.append("```")
                md.append("")
        md.append("")

    out_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    return out_path
