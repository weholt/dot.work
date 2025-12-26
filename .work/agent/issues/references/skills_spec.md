# Agent Skills Integration Spec

## Overview

Integrate [Agent Skills](https://agentskills.io/specification) into dot-work, providing a parallel system to the existing prompts feature. Skills are reusable agent capability packages with structured metadata, progressive disclosure, and optional bundled resources.

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
    name: str                          # Required: 1-64 chars, lowercase + hyphens
    description: str                   # Required: 1-1024 chars
    license: str | None = None
    compatibility: str | None = None   # Max 500 chars
    metadata: dict[str, str] | None = None
    allowed_tools: list[str] | None = None  # Experimental

@dataclass
class Skill:
    """Full skill with content and resources."""
    meta: SkillMetadata
    content: str                       # Markdown body (< 5000 tokens recommended)
    path: Path                         # Skill directory path
    scripts: list[Path] | None = None  # Optional scripts/
    references: list[Path] | None = None  # Optional references/
    assets: list[Path] | None = None   # Optional assets/
```

## Parser

Mirror the existing `CanonicalPromptParser` pattern:

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
| `name` | 1-64 chars, `[a-z0-9-]`, no leading/trailing/consecutive hyphens, must match parent directory name |
| `description` | 1-1024 chars, non-empty |
| `compatibility` | 1-500 chars if provided |
| `metadata` | string keys -> string values |

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
