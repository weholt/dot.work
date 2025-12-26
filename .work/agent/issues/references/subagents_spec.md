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

## Design Decision: Separate Feature

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
    mcp_servers: dict[str, Any] | None = None  # MCP config (org/enterprise only)
    
    # Metadata
    source_file: Path | None = None

@dataclass
class CanonicalSubagent:
    """Canonical subagent with multi-environment support."""
    meta: SubagentMetadata
    config: SubagentConfig
    environments: dict[str, SubagentEnvironmentConfig]  # Environment-specific overrides
```

## Directory Structure

```
src/dot_work/
  subagents/
    __init__.py           # Public API
    models.py             # Data classes
    parser.py             # Markdown + YAML frontmatter parser
    validator.py          # Validation logic
    discovery.py          # Find subagents in configured paths
    generator.py          # Generate environment-specific files
    environments/
      __init__.py
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
  description: Expert code reviewer for quality and security

environments:
  claude:
    target: ".claude/agents/"
    model: sonnet
    permission_mode: default
    
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
        """Discover canonical subagents in .work/subagents/."""
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
   - List, validate, show, install, generate commands

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
