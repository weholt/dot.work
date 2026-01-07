# Skills and Subagents Related Issues from temp/.work

## Table of Contents

| File | Content Summary |
|------|----------------|
| `skills_spec.md` | Complete specification for Agent Skills integration - data models, parser, validator, discovery, prompt generation, CLI commands |
| `subagents_spec.md` | Complete specification for subagent support - multi-environment agents (Claude, OpenCode, Copilot) with canonical format, adapters, generator |
| `FEAT-023-investigation.md` | Investigation of FEAT-023: Implement Agent Skills support - requirements, implementation plan, acceptance criteria, integration with harness |
| `migrate-db-issues-investigation.md` | Investigation of MIGRATE-034 through MIGRATE-050: Database issues migration from glorious issue-tracker to dot-work - feature inventory, migration issues, recommendations |
| `migration-analysis.md` | Analysis of all migration issues (MIGRATE-001 through MIGRATE-069) - completed vs pending, patterns, recommendations |
| `backlog-pre-split-2026-01-01.md` | Backlog of migration issues before pre-split event in 2026 |
| `shortlist.md` | Shortlist file showing all active skills/subagents related issues (FEAT-023, multiple DOCS issues, backlog items) |

---

# Agent Skills Integration Spec

## Overview

Integrate [Agent Skills](https://agentskills.io/specification) into dot-work, providing a parallel system to existing prompts feature. Skills are reusable agent capability packages with structured metadata, progressive disclosure, and optional bundled resources.

## Directory Structure

```
src/dot_work/
  skills/
    __init__.py          # Public API exports
    models.py            # Skill, SkillMetadata dataclasses
    parser.py            # SKILL.md frontmatter parser
    validator.py         # Skill validation logic
    discovery.py         # Filesystem skill discovery
    prompt_generator.py  # XML prompt generation for agents
```

## Data Models

```python
@dataclass
class SkillMetadata:
    """Lightweight metadata loaded at startup (~100 tokens per skill)."""
    name: str                          # Required:1-64 chars, lowercase + hyphens
    description: str                   # Required:1-1024 chars
    license: str | None = None
    compatibility: str | None = None   # Max 500 chars
    metadata: dict[str, str] | None = None
    allowed_tools: list[str] | None = None  # Experimental

@dataclass
class Skill:
    """Full skill with content and resources."""
    meta: SkillMetadata
    content: str                       # Markdown body (<5000 tokens recommended)
    path: Path                         # Skill directory path
    scripts: list[Path] | None = None  # Optional scripts/
    references: list[Path] | None = None # Optional references/
    assets: list[Path] | None   # Optional assets/
```

## Parser

Mirror existing `CanonicalPromptParser` pattern:

```python
class SkillParser:
    """Parser for SKILL.md files with YAML frontmatter."""
    
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
    
    def parse(self, skill_dir: Path) -> Skill:
        """Parse a skill directory containing SKILL.md."""
        
    def parse_metadata_only(self, skill_dir: Path) -> SkillMetadata:
        """Parse only frontmatter for lightweight discovery."""
```

### Validation Rules

| Field | Constraint |
|-------|-----------|
| `name` | 1-64 chars, `[a-z0-9]`, no leading/trailing/consecutive hyphens |
| `description` | 1-1024 chars, non-empty |
| `compatibility` | 1-500 chars if provided |
| `metadata` | string keys -> string values |
```

## Discovery

```python
class SkillDiscovery:
    """Discover skills from configured directories."""
    
    def __init__(self, search_paths: list[Path]):
        self.search_paths = search_paths
    
    def discover(self) -> list[SkillMetadata]:
        """Scan paths for valid skill directories."""
        
    def load_skill(self, name: str) -> Skill:
        """Load full skill content by name."""
```

Default search paths:
- `.skills/` (project-local)
- `~/.config/dot-work/skills/` (user-global)
- Bundled skills in package

## Prompt Generation

Generate `<available_skills>` XML for agent system prompts:

```python
def generate_skills_prompt(skills: list[SkillMetadata], include_paths: bool = True) -> str:
    """Generate XML prompt section for available skills."""
```

Output format:
```xml
<available_skills>
  <skill>
    <name>pdf-processing</name>
    <description>Extracts text and tables from PDF files...</description>
    <location>/path/to/skills/pdf-processing/SKILL.md</location>
    <license>MIT</license>
  </skill>
</available_skills>
```

## CLI Commands

Add `skills` subcommand group:

```
dot-work skills list              # List discovered skills
dot-work skills validate <path>   # Validate a skill directory
dot-work skills show <name>       # Display full skill content
dot-work skills prompt            # Generate available_skills XML
dot-work skills install <source>  # Copy skill to project .skills/
```

## Integration Points

### With Existing Prompts

Skills complement prompts:
- **Prompts**: Static instructions installed to environment-specific locations
- **Skills**: Dynamic capabilities discovered at runtime, injected into agent context

### With Agent Harness

The existing `harness/` module can inject discovered skills into agent sessions:

```python
# In harness session initialization
discovery = SkillDiscovery(config.skill_paths)
skills = discovery.discover()
system_prompt += generate_skills_prompt(skills)
```

## File Layout

Minimal skill:
```
my-skill/
  SKILL.md
```

Full skill:
```
my-skill/
  SKILL.md
  scripts/
    extract.py
  references/
      REFERENCE.md
  assets/
        template.json
```

## Implementation Order

1. `models.py` - Data classes with validation in `__post_init__`
2. `parser.py` - Frontmatter extraction and parsing
3. `validator.py` - Full validation with error collection
4. `discovery.py` - Filesystem scanning
5. `prompt_generator.py` - XML generation
6. CLI commands in `cli.py`
7. Integration with `harness/`

## Testing

Mirror existing test structure:
```
tests/unit/skills/
  test_models.py
  test_parser.py
  test_validator.py
  test_discovery.py
  test_prompt_generator.py
```

Test fixtures in `tests/fixtures/skills/` with valid and invalid skill directories.

## Differences from Prompts

| Aspect | Prompts | Skills |
|--------|---------|--------|
| Purpose | Environment-specific instructions | Reusable agent capabilities |
| Format | Custom frontmatter with `environments` | Agent Skills spec with `name`/`description` |
| Discovery | Static installation | Runtime discovery |
| Resources | Content only | Scripts, references, assets |
| Output | Installed files | Injected XML in system prompt |

---

# Subagents Integration Spec

## Overview

Integrate subagent/custom agent support into dot-work, enabling users to define specialized AI assistants that can be deployed across multiple AI coding environments (Claude Code, OpenCode, GitHub Copilot).

## Background Research

### Platform Comparison

| Feature | Claude Code | OpenCode | GitHub Copilot |
|---------|-------------|----------|----------------|
| **File Format** | Markdown + YAML frontmatter | Markdown + YAML frontmatter OR JSON | Markdown + YAML frontmatter |
| **Location** | `.claude/agents/`, `~/.claude/agents/` | `.opencode/agent/`, `~/.config/opencode/agent/`, `opencode.json` | `.github/agents/`, org/enterprise `.github-private/agents/` |
| **Agent Types** | Subagents only | Primary + Subagents | Custom agents (single type) |
| **Tools Config** | Comma-separated list | Boolean map or wildcards | String list with aliases |
| **Model Config** | `sonnet`, `opus`, `haiku`, `inherit` | `provider/model-id` format | Not in profile (configured elsewhere) |
| **Permissions** | `permissionMode` field | `permission` object with granular bash rules | `infer` boolean, MCP server config |
| **Invocation** | Auto-delegation + explicit mention | `@mention` + Tab switching | Auto-inference + manual selection |

### Key Differences

1. **Claude Code**: Subagents operate in isolated context windows, support skills loading, resumable sessions
2. **OpenCode**: Distinguishes primary agents (Tab-switchable) from subagents (@-mentionable), supports temperature and maxSteps
3. **GitHub Copilot**: Focuses on repository/org/enterprise hierarchy, MCP server integration, tool aliases

### Design Decision: Separate Feature

Subagents should be a **separate feature** from prompts for these reasons:

1. **Different Purpose**: Prompts are static instructions installed to environments; subagents are dynamic AI personalities with tool/permission configs
2. **Different Lifecycle**: Prompts are deployed once; subagents are discovered at runtime and invoked on-demand
3. **Different Schema**: Subagent frontmatter has tools, model, permissions fields that prompts don't have
4. **Environment-Specific Behaviors**: Each platform handles subagents differently (invocation, model selection, permissions)

## Data Models

```python
@dataclass
class SubagentMetadata:
    """Lightweight metadata for discovery/listing."""
    name: str                            # Required: lowercase + hyphens
    description: str                     # Required: when to use this agent

@dataclass
class SubagentConfig:
    """Full subagent configuration."""
    name: str
    description: str
    prompt: str                          # System prompt (markdown body)
    
    # Tool access (environment-specific interpretation)
    tools: list[str] | None = None       # None = inherit all
    
    # Model selection
    model: str | None = None             # Platform-specific format
    
    # Permissions (Claude Code / OpenCode)
    permission_mode: str | None = None   # Claude: default, acceptEdits, bypassPermissions, plan
    permissions: dict[str, Any] | None = None  # OpenCode: granular bash rules
    
    # OpenCode-specific
    mode: str | None = None              # primary, subagent, all
    temperature: float | None = None
    max_steps: int | None = None
    
    # Claude Code-specific
    skills: list[str] | None = None      # Auto-load skills
    
    # GitHub Copilot-specific
    target: str | None = None            # vscode, github-copilot
    infer: bool | None = None            # Auto-selection
    mcp_servers: dict[str, Any] | None = None  # MCP server config (org/enterprise only)
    
    # Metadata
    source_file: Path | None = None
```

## Directory Structure

```
src/dot_work/
  subagents/
    __init__.py           # Public API exports
    models.py             # Data classes
    parser.py             # Markdown + YAML frontmatter parser
    validator.py          # Validation logic
    discovery.py          # Find subagents in configured paths
    generator.py          # Generate environment-specific files
    environments/
      __init__.py       # Environment registry
      base.py             # Base environment adapter
      claude_code.py      # Claude Code specifics
      opencode.py         # OpenCode specifics
      copilot.py          # GitHub Copilot specifics
```

## Canonical Subagent Format

Similar to canonical prompts, support a canonical format with environment-specific overrides:

```markdown
---
meta:
  name: code-reviewer
  description: Expert code reviewer for quality and security.

environments:
  claude:
    target: ".claude/agents/"
    model: sonnet
    permissionMode: default
    skills:
      - code-review
  
  opencode:
    target: ".opencode/agent/"
    mode: subagent
    temperature: 0.1
  
  copilot:
    target: ".github/agents/"
    infer: true
    tools: ["read", "search", "edit"]

# Common configuration (can be overridden per-environment)
tools:
  - Read
  - Grep
  - Glob
  - Bash
---

You are a senior code reviewer ensuring high standards of code quality and security.

## Review Process

1. Run git diff to see recent changes
2. Focus on modified files
3. Analyze code for:
   - Clarity and readability
   - Security vulnerabilities
   - Performance issues
   - Test coverage

## Output Format

Provide feedback organized by priority:
- **Critical**: Must fix before merge
- **Warning**: Should fix
- **Suggestion**: Consider improving
```

## Parser

```python
class SubagentParser:
    """Parser for subagent definition files."""
    
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
    
    def parse(self, file_path: Path) -> CanonicalSubagent:
        """Parse a canonical subagent file."""
        
    def parse_native(self, file_path: Path, environment: str) -> SubagentConfig:
        """Parse a native environment-specific subagent file."""
```

## Environment Adapters

Each environment has an adapter that handles:
- Native file format parsing
- Canonical to native conversion
- Tool name mapping
- Model name translation

```python
class SubagentEnvironmentAdapter(ABC):
    """Base class for environment-specific subagent handling."""
    
    @abstractmethod
    def get_target_path(self, project_root: Path) -> Path:
        """Get the target directory for subagents."""
    
    @abstractmethod
    def generate_native(self, config: SubagentConfig) -> str:
        """Generate native subagent file content."""
    
    @abstractmethod
    def parse_native(self, content: str) -> SubagentConfig:
        """Parse native subagent file content."""
    
    @abstractmethod
    def map_tools(self, tools: list[str]) -> list[str] | dict[str, bool]:
        """Map canonical tool names to environment-specific format."""
```

### Tool Name Mapping

| Canonical | Claude Code | OpenCode | Copilot |
|-----------|-------------|----------|---------|
| `Read` | `Read` | `read` | `read` |
| `Write` | `Write` | `write` | `edit` |
| `Edit` | `Edit` | `edit` | `edit` |
| `Bash` | `Bash` | `bash` | `execute` |
| `Grep` | `Grep` | `grep` | `search` |
| `Glob` | `Glob` | `glob` | `search` |
| `WebFetch` | `WebFetch` | `webfetch` | `web` |

## CLI Commands

Add `subagents` subcommand group:

```
dot-work subagents list [--env ENV]           # List discovered subagents
dot-work subagents validate <path>            # Validate subagent file
dot-work subagents show <name>                # Display subagent details
dot-work subagents install <file> --env ENV   # Install canonical subagent
dot-work subagents generate <file> --env ENV  # Generate native file (stdout)
dot-work subagents sync <dir>                 # Sync canonical to all environments
dot-work subagents init <name> -d "description"  # Create new canonical template
dot-work subagents envs                           # List supported environments
```

## Discovery

```python
class SubagentDiscovery:
    """Discover subagents from multiple sources."""
    
    def __init__(self, project_root: Path, environment: str):
        self.project_root = project_root
        self.environment = environment
        self.adapter = get_adapter(environment)
    
    def discover_native(self) -> list[SubagentConfig]:
        """Discover native subagents for current environment."""
        
    def discover_canonical(self) -> list[CanonicalSubagent]:
        """Discover canonical subagents in .work/subagents/`."""
```

Search paths:
- Native: Environment-specific directories (`.claude/agents/`, `.opencode/agent/`, `.github/agents/`)
- Canonical: `.work/subagents/` (project), `~/.config/dot-work/subagents/` (user)
- Bundled: Package includes starter subagents

## Bundled Subagents

Include commonly useful subagents:

1. **code-reviewer** - Code quality and security review
2. **test-runner** - Run tests and fix failures
3. **debugger** - Root cause analysis for errors
4. **docs-writer** - Documentation specialist
5. **security-auditor** - Security vulnerability detection
6. **refactorer** - Code refactoring specialist

## Integration with Existing Features

### Relationship to Prompts

- Prompts: Static instructions, always included in agent context
- Subagents: Dynamic agents, invoked on-demand for specific tasks

### Relationship to Skills (skills_spec.md)

Skills and subagents are complementary:
- Skills: Reusable capability packages (instructions + scripts + references)
- Subagents: AI personalities with tool/permission configurations

Claude Code supports auto-loading skills in subagents via the `skills` field.

### Relationship to Harness

The harness module can use subagent discovery for testing:

```python
discovery = SubagentDiscovery(project_root, "claude")
subagents = discovery.discover_native()
# Inject subagent metadata into test prompts
```

## Implementation Order

1. **Phase 1: Core Models** (1-2 days)
   - `models.py` - Data classes with validation
   - `parser.py` - Markdown + YAML frontmatter parsing
   - `validator.py` - Validation rules

2. **Phase 2: Environment Adapters** (2-3 days)
   - Base adapter class
   - Claude Code adapter
   - OpenCode adapter
   - GitHub Copilot adapter

3. **Phase 3: Generator** (1-2 days)
   - Canonical to native conversion
   - Tool/model name mapping
   - File generation

4. **Phase 4: CLI** (1-2 days)
   - Subcommand group
   - List, validate, show, install, generate, sync commands

5. **Phase 5: Bundled Subagents** (1 day)
   - Create canonical definitions
   - Test across environments

## Testing

```
tests/unit/subagents/
  test_models.py
  test_parser.py
  test_validator.py
  test_discovery.py
  environments/
    test_claude_code.py
    test_opencode.py
    test_copilot.py
  tests/fixtures/subagents/
      canonical/
        code-reviewer.md
        test-runner.md
      native/
        claude/
        opencode/
        copilot/
```

## Future Considerations

1. **Cursor/Windsurf Support**: Both use VS Code extension format, may share Copilot adapter
2. **MCP Server Integration**: Support MCP server configuration in subagents
3. **Subagent Marketplace**: Registry of community subagents
4. **Version Management**: Track subagent versions across environments
5. **Metrics/Analytics**: Track subagent usage and effectiveness

---

# FEAT-023: Agent Skills Support

## Problem Statement

dot-work needs to integrate Agent Skills specification for reusable agent capability packages. Currently there is no mechanism for discovering, validating, and injecting skills into agent contexts.

## Requirements (from skills_spec.md)

1. Create data models (SkillMetadata, Skill) with validation
2. Implement SKILL.md parser with YAML frontmatter extraction
3. Build validator with error collection (name format, description length)
4. Implement filesystem discovery (.skills/, ~/.config/dot-work/skills/, bundled)
5. Generate `<available_skills>` XML for agent prompts
6. Add CLI commands: dot-work skills list/validate/show/prompt/install
7. Integrate with harness for session injection

## Affected Files (per spec)

- Create: `src/dot_work/skills/__init__.py`, models.py, parser.py, validator.py, discovery.py, prompt_generator.py
- Modify: `src/dot_work/harness/` (integration point)
- Create: `tests/unit/skills/` (test suite)
- Create: `tests/fixtures/skills/` (test fixtures)

## Implementation Plan (from spec)

1. models.py - Data classes with validation in __post_init__
2. parser.py - Frontmatter extraction and parsing
3. validator.py - Full validation with error collection
4. discovery.py - Filesystem scanning
5. prompt_generator.py - XML generation
6. CLI commands in cli.py
7. Integration with harness/

## Memory.md Context

Key patterns to follow:
- Google-style docstrings
- Type annotations on all functions
- pathlib.Path for file operations
- dataclass.replace() for immutable updates
- __post_init__ for dataclass field validation

## Existing Patterns to Mirror

- CanonicalPromptParser for parser pattern
- Existing prompts/ structure for reference
- Existing prompts/ structure for reference
- Typer CLI patterns
- pytest fixtures for testing

## Validation Plan (from issue)

```bash
# Unit tests
uv run pytest tests/unit/skills/ -v --cov=src/dot_work/skills --cov-report=term-missing

# CLI smoke test
uv run dot-work skills list
uv run dot-work skills validate tests/fixtures/skills/valid
uv run dot-work skills show test-skill

# Integration test
uv run pytest tests/integration/skills/test_skill_injection.py -v
```

## Acceptance Criteria

- [ ] Skill discovery finds valid skills in search paths
- [ ] Parser extracts frontmatter and content with 100% coverage
- [ ] Validator rejects invalid names (format check) and empty descriptions
- [ ] CLI list command shows discovered skills with name/description
- [ ] CLI validate reports specific validation errors
- [ ] generate_skills_prompt() produces valid XML output
- [ ] Harness integration injects skills into agent sessions
- [ ] Unit tests for all modules (≥75% coverage)
- [ ] Integration test for end-to-end skill discovery and injection

---

# Database Issues Migration Investigation

**Investigation started:** 2024-12-22
**Issue reference:** MIGRATE-034 through MIGRATE-050+
**Goal:** 100% feature parity migration from glorious issue-tracker

## Complete Feature Inventory (from source analysis)

### 1. Core Issue Operations
- `create` - Create new issue
- `list` - List issues with filtering
- `show` - Show issue details
- `update` - Update issue fields
- `close` - Close issue
- `reopen` - Reopen issue
- `delete` - Delete issue (with --force flag)
- `restore` - Restore deleted issue

### 2. Issue Status Management
- `ready` - Mark issue as ready
- `blocked` - Mark issue as blocked
- `stale` - Mark issue as stale

### 3. Bulk Operations (CRITICAL)
- `bulk-create` - Create multiple issues from CSV/json
- `bulk-close` - Bulk close multiple issues
- `bulk-update` - Bulk update issue properties
- `bulk-label-add` - Add labels to multiple issues
- `bulk-label-remove` - Remove labels from multiple issues
- `dependencies add` - Add dependency between issues
- `dependencies remove` - Remove dependency
- `dependencies list` - List dependencies for issue
- `dependencies list-all` - List all dependencies globally
- `dependencies tree` - Show dependency tree with visualization
- `dependencies cycles` - Detect and show dependency cycles with fix suggestions

**Dependency Types:** blocks, depends-on, related-to, discovered-from

### 4. Epic Management
- `epics add` - Add issue to epic
- `epics remove` - Remove issue from epic
- `epics list` - List issues in epic
- `epics set` - Assign issue to epic (spec-compliant)
- `epics clear` - Remove issue from epic
- `epics all` - List all epics with counts
- `epics tree` - Show epic hierarchy tree

### 5. Label Management
- `labels add` - Add labels to issue
- `labels remove` - Remove labels from issue
- `labels set` - Set all labels on issue
- `labels list` - List labels (for issue or globally)
- `labels all` - List all unique labels

### 6. Comment Management
- `comments add` - Add comment to issue
- `comments list` - List comments on issue
- `comments delete` - Delete comment (with --force flag)

### 7. JSON Templates System
- `template save` - Save issue template
- `template list` - List available templates
- `template show` - Show template details
- `template delete` - Delete template

### 8. Instruction Templates (MARKDOWN-BASED - MAJOR FEATURE)
- `instructions list` - List instruction templates
- `instructions show` - Display instruction template
- `instructions apply` - Apply template to create multiple issues
- **Instruction Template Features:**
    - Complex task workflows from markdown
    - Multi-issue creation from single template
    - Task definitions with priorities, efforts, subtasks, acceptance criteria
    - Hierarchical template support
    - Epic integration with templates

### 9. Search and Stats
- `search` - Full-text search using FTS5
    - `stats` - Show issue statistics and metrics

### 10. System Operations
- `init` - Initialize issue tracker
- `sync` - Sync with git (JSONL export/import)
- `export` - Export to JSONL format
- `import` - Import from JSONL format
- `rename-prefix` - Rename issue ID prefixes
- `cleanup` - Cleanup operations (archive old issues)
- `duplicates` - Find and manage duplicate issues
- `merge` - Merge duplicate issues
- `edit` - Edit issue in external editor
- `compact` - Compact database
- `info` - Show system information

### 11. Advanced Features
- **Ready Queue Calculation**: Issues with no open blockers
- **Blocker Tracking**: Identify what blocks what
- **Stale Detection**: Automatic stale issue identification
- **Duplicate Detection**: Automatic duplicate finding
- **Visualization**: ASCII tree rendering, Mermaid diagrams
- **Advanced Querying**: Complex filtering, sorting, pagination

### 13. Data Model
- **Status Values**: open, closed, resolved, blocked, in_progress
- **Priority Levels**: critical (0), high (1), medium (2), low (3), backlog (4)
- **Issue Types**: task, bug, feature, epic, story
- **Assignee Support**: Multi-assignee tracking
- **Project Support**: Multi-project issue tracking
- **Time Tracking**: Created, updated, closed timestamps
- **Hash-based IDs**: bd-a1b2 format with child IDs (bd-a1b2.1)

### 14. Database Features
- **SQLite with proper indexing
- Unit of Work pattern
- Transaction management
- FTS5 virtual table for search
- Schema migrations
- Data integrity constraints

### 15. WHAT is EXCLUDED (by user request)
- **daemon/**: Background daemon with IPC/RPC
- **adapters/mcp/**: MCP server for Claude
- **factories/**: Complex DI for daemon
- **CLI commands**: daemon-*, rpc-*, mcp-*

### 14. Migration Issues Analysis

### Current Issues (MIGRATE-034 through MIGRATE-040)
Coverage: ~30% of feature parity

### Additional Issues (MIGRATE-041 through MIGRATE-050)
Coverage: ~60% of feature parity

### STILL MISSING for 100% Parity

The following features are NOT covered by MIGRATE-034 through MIGRATE-050:

1. **Instruction Templates Subsystem** (MAJOR - entire system)
2. **JSON Template Management**

### Phase 5: Data Model Completion (MIGRATE-076 to MIGRATE-080)

- Implement Additional Status Values (resolved, in_progress)
- Implement Additional Priority Values (backlog)
- Implement Time Tracking (created, updated, closed)
- Implement Hash-based ID System with Child IDs
Implement Issue Status Management
Implement Additional Issue Types (story)
```

### Summary

**Total Issues Required for 100% Feature Parity: 52 issues**

---

## Migration Analysis

All migration issues organized by source project, with current status.

### Executive Summary

- **Total migration issues**: 74 (MIGRATE-001 through MIGRATE-069)
- **Completed**: 30 issues (40.5%)
- **Pending**: 44 issues (59.5%)

### Completed Migrations ✅

### 1. **agent-review** (12 issues)
- Source: incoming/review
- Issues: MIGRATE-001 through MIGRATE-012
- Status: All completed
- Result: Review functionality fully integrated

### 2. **kgshred/knowledge_graph** (8 issues)
- Source: incoming/glorious/src/glorious_agents/skills/kgshred/
- Issues: MIGRATE-013 through MIGRATE-020
- Status: All completed
- Result: Knowledge graph functionality fully integrated

### 3. **zipparu** (6 issues)
- Source: incoming/zipparu/
- Issues: MIGRATE-021 through MIGRATE-026
- Status: All completed
- Result: Zip functionality fully integrated

### 4. **version-management** (6 issues)
- Source: incoming/crampus/version-management/
- Issues: MIGRATE-041 through MIGRATE-046
- Status: All completed
- Result: Version module functional, tests need minor fixes
```

### Pending Migrations 📋

### 1. **code-atlas/python-scan** (7 issues)
- Source: incoming/glorious/src/glorious_agents/skills/code-atlas/
- Issues: MIGRATE-027 through MIGRATE-033
- Status: All proposed
- Features: AST parsing, Radon metrics, dependency graphs
- [ ] **issue-tracker/db-issues** (7 issues)
- Status: All proposed
- Features: SQLite-backed issue management
  [ ] **repo-agent/container-provision** (6 issues)
- Status: All proposed
- Features: LLM-powered code agents in Docker
  [ ] **birdseye/overview** (6 issues)
- Status: All proposed
- Features: Project overview analysis and markdown generation
  [ ] **git-analysis/git-history** (6 issues)
- Status: All proposed
  Features: Git repository history analysis

### Recommendation

Start with the smallest remaining project:
- **Python scan (MIGRATE-027)** - 7 issues, features Python code analysis
- Or **Git history (MIGRATE-064)** - 6 issues, provides git analytics

Both provide high value with manageable scope.

### Note on FEAT-002

FEAT-002@b8d4e1 (YAML validation) has been marked as **won't-fix** because:
- YAML specification is too complex for stdlib-only implementation
- PyYAML is already a project dependency
- Current yaml_validator.py using PyYAML is functional
- Cost/benefit of implementing YAML from scratch is prohibitive

---

# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

## Active Work

---

## Skills & Subagents

---

All previous shortlist items (ENH-025, ENH-026, REFACTOR-003, TEST-041, TEST-042, TEST-043, FEAT-023, FEAT-024) have been completed and moved to history.md.

---

## Docker / Containers

All previous shortlist items (ENH-025, ENH-026, REFACTOR-003, TEST-041, TEST-042, TEST-043, FEAT-023, FEAT-024, FEAT-025, FEAT-026, FEAT-027, FEAT-028) have been completed and moved to history.md.

---

## Orchestrator

All previous shortlist items (ENH-025, ENH-026, REFACTOR-003, TEST-041, TEST-042, TEST-043, FEAT-023, FEAT-024, FEAT-025, FEAT-026, FEAT-027, FEAT-028) have been completed and moved to history.md.

---

*Note: This file is a concatenation of all skills/subagents related content found in temp/.work for reference purposes.*
