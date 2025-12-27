# AUDIT-GAP-008 Investigation: MCP tools not migrated from git-analysis

**Issue:** AUDIT-GAP-008@e5f6a7
**Started:** 2025-12-27T05:00:00Z
**Completed:** 2025-12-27T05:00:00Z
**Status**: Documented - Intentional Exclusion

---

## Investigation Summary

During AUDIT-GIT-003, it was discovered that MCP (Model Context Protocol) tools (26K, 659 lines) from git-analysis were NOT migrated to the git module.

**Source:** `incoming/crampus/git-analysis/src/git_analysis/mcp/tools.py`
**Destination:** NOT found in `src/dot_work/git/`

---

## What MCP Tools Provide

The MCP tools file provides:
- `GitAnalysisMCPServer` - MCP server wrapper
- `analyze_git_history` - Git history analysis with metrics
- `compare_git_branches` - Branch comparison with risk assessment
- `get_commit_analysis` - Single commit analysis
- `get_complexity_report` - Complexity analysis and risk identification
- `list_repository_tags` - Repository tag listing

**Purpose:** These tools enable **external AI systems** to call git-analysis functionality via the Model Context Protocol (MCP).

---

## Analysis: Does dot-work need MCP?

### MCP in dot-work

**Dependencies:**
- No `mcp` package in pyproject.toml dependencies
- No MCP-related optional dependencies

**Code:**
- No MCP code in `src/dot_work/git/`
- No MCP servers in any dot-work module
- No MCP integration in CLI or services

### Architecture Mismatch

**dot-work is:** A CLI tool for developers
- Primary interface: `dot-work` CLI command
- Usage: Developers run commands directly in terminal
- Target user: Human developers using AI coding tools (Claude Code, Cursor)

**MCP is for:** External AI system integration
- Primary interface: MCP server (stdio or SSE)
- Usage: Other AI systems call tools via MCP protocol
- Target user: Other AI agents/services

**Verdict:** Architectural mismatch. dot-work is a CLI tool, not an MCP server.

---

## Core Git Migration Status

**Excellent:** The git module migration was fully successful:
- 101 tests passing
- Zero errors
- All core functionality migrated:
  - `GitService` - Main git operations
  - `ComplexityCalculator` - Change complexity scoring
  - `FileAnalyzer` - File change categorization
  - `TagGenerator` - Automated tag generation
  - `LLMSummarizer` - AI-powered commit summaries (optional)

**MCP tools were NOT part of core functionality** - they were optional external integration.

---

## Decision: Intentional Exclusion

**MCP tools were intentionally NOT migrated** because:

1. **No MCP integration in dot-work**: The project has no MCP dependencies or infrastructure
2. **CLI architecture**: dot-work is a CLI tool, not an MCP server
3. **Core functionality complete**: All git analysis features are available via CLI
4. **Source preserved**: `incoming/crampus/git-analysis/` contains the source if needed later

---

## If MCP is Needed Later

If dot-work adds MCP integration in the future:

1. **Source available**: `incoming/crampus/git-analysis/src/git_analysis/mcp/tools.py` (26K)
2. **Migration path**: Would need to:
   - Add `mcp` dependency to pyproject.toml
   - Create `src/dot_work/git/mcp/tools.py`
   - Update imports for new module structure
   - Add CLI command to run MCP server (e.g., `dot-work git mcp-server`)

3. **Code quality**: The source code is well-designed and production-ready

---

## Acceptance Criteria

- [x] Decision made: Document intentional exclusion
- [x] Documentation added explaining rationale
- [x] No ambiguity about MCP status

---

## Notes

- MCP (Model Context Protocol) is the standard for AI tool integration
- Claude Code, Cursor, and other AI IDEs use MCP to call external tools
- dot-work itself is used BY these tools, not AS an MCP server
- The git migration was excellent without MCP tools
- This is LOW priority - MCP is optional enhancement, not core functionality
