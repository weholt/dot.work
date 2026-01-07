# FEAT-100 Research: Cursor/Windsurf Subagent Support

Research Date: 2026-01-03
Issue: FEAT-100@e5f6a7

---

## Executive Summary

Both Cursor and Windsurf now support **AGENTS.md** files as a standardized format for providing directory-scoped AI instructions. This is simpler than expected - both tools use plain markdown files with minimal or no frontmatter.

---

## Cursor AI Editor

### File Format: `.mdc` (Markdown Cursor)

**Location:** `.cursor/rules/` directory

**Frontmatter Format:**
```yaml
---
description: Brief description under 120 characters
globs: ["pattern/**/*.ts"]  # File pattern matching
---

# Rule Content

Markdown body with instructions...
```

**Key Characteristics:**
- **MDC (Multi-Document Context)** format - markdown with special frontmatter
- `description:` field should be < 120 characters for AI clarity
- `globs:` array for file pattern matching (when rule applies)
- Body content uses structured formatting (some recommend XML tags)
- Can reference other files: `[filename.ext](mdc:filename.ext)`

**Status:**
- `.cursorrules` (legacy) - deprecated, use `.mdc` instead
- `.mdc` is the current standard (2025)
- Active community discussion and ongoing refinement

**Resources:**
- [Cursor Rules Documentation](https://cursor.com/docs/context/rules)
- [Optimal .mdc Structure Discussion](https://forum.cursor.com/t/optimal-structure-for-mdc-rules-files/52260)
- [What is .mdc File Discussion](https://forum.cursor.com/t/what-is-a-mdc-file/50417)
- [Medium: Exploring rules.mdc](https://medium.com/@devlato/a-rule-that-writes-the-rules-exploring-rules-mdc-288dc6cf4092)
- [GitHub: cursor-xml-rules-trial](https://github.com/bmadcode/cursor-xml-rules-trial)

---

## Windsurf AI Editor (Codeium)

### File Format: `AGENTS.md` (Plain Markdown)

**Location:** Any directory in project (auto-discovered)

**Format:**
```markdown
# AGENTS.md

Plain markdown with no frontmatter required.

## Instructions

When working with files in this directory:
- Use TypeScript strict mode
- Follow naming conventions
- etc.
```

**Key Characteristics:**
- **Plain markdown** - NO frontmatter required
- **Auto-discovery** based on file location
- **Directory-scoped** - applies to files in same directory and subdirectories
- Case insensitive: `AGENTS.md` or `agents.md`
- Can place at multiple directory levels for hierarchical rules

**Scoping Behavior:**

| File Location | Scope |
|---------------|-------|
| Workspace root | Applies to all files (global) |
| `/frontend/` | Applies to `/frontend/**` files |
| `/frontend/components/` | Applies to `/frontend/components/**` files |

**Comparison with Windsurf Rules:**

| Feature | AGENTS.md | Windsurf Rules |
|---------|-----------|----------------|
| Location | In project directories | `.windsurf/rules/` or global |
| Scoping | Automatic (location-based) | Manual (glob, always on, etc.) |
| Format | Plain markdown | Markdown with frontmatter |
| Best for | Directory-specific conventions | Cross-cutting concerns |

**Resources:**
- [Windsurf AGENTS.md Documentation](https://docs.windsurf.com/windsurf/cascade/agents-md)
- [Windsurf Cascade Documentation](https://docs.windsurf.com/windsurf/cascade/cascade)
- [Windsurf Rules Discussion (Reddit)](https://www.reddit.com/r/Codeium/comments/1gsl9cv/rules_for_the_ai_in_windsurf_like_the_cursorrules/)
- [Codeium Windsurf Rules Tutorial](https://dev.to/yardenporat/codium-windsurf-ide-rules-file-1hn9)
- [Master File: VS Code, Cursor, Windsurf Rules](https://idavidov.eu/one-file-to-rule-them-all-cursor-windsurf-and-vs-code)

---

## Compatibility Analysis

### VS Code Extension Format Assumption

**Original Assumption (from FEAT-100):**
> "Cursor and Windsurf are popular AI editors that also support custom agents but may have slightly different formats."
> "Whether VS Code extension format is compatible"

**Research Findings:**
- ❌ **NOT compatible** with GitHub Copilot's `.github/agents/` format
- ✅ Both support `AGENTS.md` (plain markdown)
- ⚠️ Cursor uses `.mdc` format in `.cursor/rules/` (different from Copilot)
- ⚠️ Windsurf uses plain `AGENTS.md` (no frontmatter)

### Comparison Table

| Platform | Location | Format | Frontmatter |
|----------|----------|--------|-------------|
| **Claude Code** | `.claude/agents/` | YAML + Markdown | `meta:`, `config:`, `environments:` |
| **GitHub Copilot** | `.github/agents/` | YAML + Markdown | `identifier:`, `name:`, `description:` |
| **OpenCode** | `.opencode/agent/` | YAML + Markdown | `identifier:`, `name:`, `description:` |
| **Cursor** | `.cursor/rules/` | `.mdc` (Markdown + Cursor frontmatter) | `description:`, `globs:` |
| **Windsurf** | `AGENTS.md` (anywhere) | Plain Markdown | **None** |

---

## Implementation Recommendations

### Option 1: Minimal Support (Recommended - Simplest)

Support **AGENTS.md** for both Cursor and Windsurf:

**Pros:**
- Simple format (plain markdown, no frontmatter)
- Works for both Cursor and Windsurf
- Consistent with Windsurf's primary format
- Can be placed at `.cursor/AGENTS.md` for Cursor

**Cons:**
- Doesn't leverage Cursor's `.mdc` capabilities (globs, descriptions)
- Less powerful than Cursor's native `.mdc` format

### Option 2: Full Support

Support both formats:
- `.cursor/rules/*.mdc` for Cursor (with frontmatter)
- `AGENTS.md` for Windsurf (plain markdown)

**Pros:**
- Leverages full capabilities of each platform
- More precise control (globs for Cursor)

**Cons:**
- More complex implementation
- Different formats per platform
- Requires separate adapter logic

### Option 3: Share Copilot Adapter

Validate if Copilot adapter can be reused:

**Analysis:**
- Copilot uses `.github/agents/` with YAML frontmatter
- Cursor uses `.cursor/rules/*.mdc` with different frontmatter structure
- Windsurf uses plain `AGENTS.md` with no frontmatter

**Conclusion:**
- ❌ Copilot adapter **cannot** be directly reused
- Frontmatter structures are incompatible
- Would need new adapter code anyway

---

## Proposed Adapter Implementation

### Cursor Adapter (`cursor.py`)

```python
class CursorAdapter(SubagentEnvironmentAdapter):
    """Adapter for Cursor AI editor .mdc format."""

    DEFAULT_TARGET = ".cursor/rules/"
    DEFAULT_FILENAME_SUFFIX = ".mdc"

    # Frontmatter fields
    FRONTMATTER_DESCRIPTION = "description"
    FRONTMATTER_GLOBS = "globs"

    def generate_native(self, subagent: CanonicalSubagent) -> str:
        """Generate .mdc format file."""
        # Build Cursor-specific frontmatter
        # - description: from subagent.description (truncated to 120 chars)
        # - globs: ["**/*"] for global application
        # Body: subagent.instructions
```

### Windsurf Adapter (`windsurf.py`)

```python
class WindsurfAdapter(SubagentEnvironmentAdapter):
    """Adapter for Windsurf AGENTS.md format."""

    DEFAULT_TARGET = "AGENTS.md"
    DEFAULT_FILENAME = "AGENTS.md"

    # No frontmatter required

    def generate_native(self, subagent: CanonicalSubagent) -> str:
        """Generate plain markdown AGENTS.md."""
        # Just return subagent.instructions as plain markdown
        # No frontmatter processing needed
```

---

## Acceptance Criteria Update

Based on research, the acceptance criteria can be refined:

- [x] Cursor subagent format documented → `.cursor/rules/*.mdc` with frontmatter
- [x] Windsurf subagent format documented → `AGENTS.md` plain markdown
- [x] Adapter implementation approach defined → Separate adapters required (cannot share Copilot)
- [ ] Implement CursorAdapter
- [ ] Implement WindsurfAdapter
- [ ] CLI supports `--env cursor` and `--env windsurf`
- [ ] Tests for both adapters
- [ ] Documentation update

---

## Estimated Effort

**Original Estimate:** 2-4 days (if similar to Copilot)

**Revised Estimate:** 3-5 days

**Reasoning:**
- Cannot reuse Copilot adapter (different frontmatter)
- Need two separate adapters (Cursor + Windsurf)
- Cursor has more complex frontmatter (description, globs)
- Windsurf is simpler (plain markdown, no frontmatter)
- Additional testing for two platforms

---

## Next Steps

1. **Decision Point:** Choose implementation approach
   - Option 1: Minimal (AGENTS.md only for both)
   - Option 2: Full (separate formats for each)
   - Option 3: Hybrid (AGENTS.md + optional .mdc for Cursor)

2. **If approved:**
   - Create `src/dot_work/subagents/environments/cursor.py`
   - Create `src/dot_work/subagents/environments/windsurf.py`
   - Update `src/dot_work/subagents/__init__.py` to register environments
   - Add CLI support for `--env cursor` and `--env windsurf`
   - Write tests
   - Update documentation

---

## Sources

### Cursor
- [Cursor Rules Documentation](https://cursor.com/docs/context/rules)
- [Optimal .mdc Structure Discussion](https://forum.cursor.com/t/optimal-structure-for-mdc-rules-files/52260)
- [What is .mdc File Discussion](https://forum.cursor.com/t/what-is-a-mdc-file/50417)
- [Medium: Exploring rules.mdc](https://medium.com/@devlato/a-rule-that-writes-the-rules-exploring-rules-mdc-288dc6cf4092)
- [GitHub: cursor-xml-rules-trial](https://github.com/bmadcode/cursor-xml-rules-trial)

### Windsurf
- [Windsurf AGENTS.md Documentation](https://docs.windsurf.com/windsurf/cascade/agents-md)
- [Windsurf Cascade Documentation](https://docs.windsurf.com/windsurf/cascade/cascade)
- [Windsurf Changelog](https://windsurf.com/changelog)
- [Windsurf Editor](https://windsurf.com/editor)
- [Windsurf Rules Discussion (Reddit)](https://www.reddit.com/r/Codeium/comments/1gsl9cv/rules_for_the_ai_in_windsurf_like_the_cursorrules/)
- [Codeium Windsurf Rules Tutorial](https://dev.to/yardenporat/codium-windsurf-ide-rules-file-1hn9)
- [Master File: VS Code, Cursor, Windsurf Rules](https://idavidov.eu/one-file-to-rule-them-all-cursor-windsurf-and-vs-code)

### Comparison
- [Cursor vs Windsurf 2025 Comparison](https://dev.to/blamsa0mine/cursor-vs-windsurf-2025-a-deep-dive-into-the-two-fastest-growing-ai-ides-2112)
