# Git Analysis Tool

A comprehensive tool for analyzing and comparing git history between branches, commits, or tags with structured, reusable output and LLM-powered summaries.

## Features

- **Structured Analysis** - Detailed analysis of git commits with metadata and metrics
- **Complexity Scoring** - Automated complexity calculation for commits and file changes
- **LLM Integration** - Optional AI-powered summaries and insights
- **Change Impact** - Identify areas of impact and potential regressions
- **Contributor Analytics** - Detailed statistics for all contributors
- **Risk Assessment** - Automated risk evaluation for changes
- **Multiple Output Formats** - Support for table, JSON, and YAML output
- **Caching** - Intelligent caching for fast repeated analysis
- **MCP Integration** - Model Context Protocol tools for AI integration

## Installation

```bash
pip install git-analysis
```

Or for development:

```bash
git clone https://github.com/your-username/git-analysis.git
cd git-analysis
pip install -e ".[dev]"
```

### Optional Dependencies

```bash
# LLM support
pip install git-analysis[llm]

# MCP support
pip install git-analysis[mcp]
```

## Quick Start

### Basic Git Comparison

```bash
# Compare two branches
git-analysis compare main feature/user-auth

# Compare tags
git-analysis compare v1.0.0 v1.1.0

# Compare commit ranges
git-analysis compare HEAD~10 HEAD

# Analyze a single commit
git-analysis analyze abc123def456
```

### Advanced Usage

```bash
# Use LLM for enhanced summaries
git-analysis compare main feature-branch --llm --llm-provider anthropic

# Output to JSON file
git-analysis compare main feature --format json --output analysis.json

# Analyze with custom repository path
git-analysis compare main feature --repo /path/to/repo

# Limit number of commits analyzed
git-analysis compare main feature --max-commits 50
```

## Command Line Interface

### Primary Commands

#### `compare`
Compare two git references with detailed analysis:

```bash
git-analysis compare <from_ref> <to_ref> [options]
```

**Examples:**
```bash
# Compare branches
git-analysis compare main feature/new-feature

# Compare recent commits
git-analysis compare HEAD~20 HEAD

# Compare tags
git-analysis compare v2.0.0 v2.1.0

# With LLM enhancement
git-analysis compare main feature --llm --llm-provider openai

# Custom output
git-analysis compare main feature --format json --output results.json
```

#### `analyze`
Analyze a single commit in detail:

```bash
git-analysis analyze <commit_hash> [options]
```

**Examples:**
```bash
git-analysis analyze abc123def456
git-analysis analyze abc123def456 --llm
git-analysis analyze abc123def456 --format yaml
```

#### `diff-commits`
Compare two commits and describe their differences:

```bash
git-analysis diff-commits <commit_a> <commit_b> [options]
```

**Examples:**
```bash
git-analysis diff-commits HEAD~5 HEAD
git-analysis diff-commits abc123 def456
```

#### `contributors`
Show contributor statistics:

```bash
git-analysis contributors <from_ref> <to_ref> [options]
```

**Examples:**
```bash
git-analysis contributors v1.0.0 v2.0.0
git-analysis contributors main feature-branch
```

#### `complexity`
Show complexity analysis with custom thresholds:

```bash
git-analysis complexity <from_ref> <to_ref> [options]
```

**Examples:**
```bash
git-analysis complexity HEAD~50 HEAD
git-analysis complexity main feature --threshold 30
```

#### `releases`
Analyze recent releases (tags):

```bash
git-analysis releases [options]
```

**Examples:**
```bash
git-analysis releases
git-analysis releases --count 5 --llm
```

### Global Options

- `--repo, -r`: Path to git repository (default: current directory)
- `--format, -f`: Output format (table, json, yaml)
- `--output, -o`: Output file path
- `--llm`: Use LLM for enhanced summaries
- `--llm-provider`: LLM provider (openai, anthropic)
- `--verbose, -v`: Enable verbose logging

## Output Examples

### Table Output (Default)

```
📊 Comparison Summary
────────────────────────────────
Comparison: main → feature/user-auth
Commits: 23
Files: 45
Lines: +1,234 -89
Complexity: 156.7
Time span: 7 days

📝 Aggregate Summary:
Analyzed 23 commits with average complexity of 6.8. Total changes: 1,234 lines added, 89 lines deleted. Main themes: feature (12), auth (8), tests (5)

⭐ Highlights:
• High complexity: Implement JWT authentication (23.4)
• Breaking: Update user model schema (18.7)
• Security: Add password encryption (15.2)
```

### JSON Output

```json
{
  "metadata": {
    "from_ref": "main",
    "to_ref": "feature/user-auth",
    "total_commits": 23,
    "total_files_changed": 45,
    "total_complexity": 156.7
  },
  "commits": [
    {
      "commit_hash": "abc123def456",
      "author": "John Doe",
      "complexity_score": 23.4,
      "summary": "Implements JWT authentication with refresh tokens...",
      "tags": ["feature", "auth", "security"]
    }
  ],
  "aggregate_summary": "Analyzed 23 commits...",
  "highlights": ["High complexity: Implement JWT authentication (23.4)"]
}
```

## Complexity Scoring

The tool automatically calculates complexity scores (0-100) based on:

- **File Changes**: Number and types of files modified
- **Code Volume**: Lines added/deleted
- **File Types**: Higher complexity for config, schema, and deployment files
- **Commit Messages**: Indicators like "breaking", "refactor", "migration"
- **Impact Areas**: Authentication, database, API changes
- **Special Factors**: Breaking changes, security relevance, performance impact

### Complexity Levels

- **0-20**: Low complexity (routine changes)
- **20-40**: Medium complexity (feature additions)
- **40-60**: High complexity (significant changes)
- **60-80**: Very high complexity (major refactoring)
- **80-100**: Critical complexity (breaking changes, migrations)

## LLM Integration

When LLM is enabled, the tool provides enhanced analysis:

### Natural Language Summaries
- Human-readable commit summaries
- Change impact descriptions
- Risk assessments in plain language
- Migration recommendations

### Enhanced Pattern Recognition
- Identify subtle code patterns
- Detect architectural changes
- Surface hidden dependencies
- Suggest testing strategies

### Setup

```bash
# OpenAI (default)
export OPENAI_API_KEY="your-api-key"
git-analysis compare main feature --llm

# Anthropic Claude
export ANTHROPIC_API_KEY="your-api-key"
git-analysis compare main feature --llm --llm-provider anthropic
```

## Configuration

Create a `.git-analysis.toml` file:

```toml
[general]
repo_path = "."
max_commits = 1000
cache_ttl_hours = 24

[llm]
enabled = true
provider = "openai"
model = "gpt-3.5-turbo"
temperature = 0.3
max_tokens = 1000

[complexity]
threshold = 50.0
include_binary_files = false

[output]
format = "table"
include_raw_diff = false
verbose = false

[filtering]
file_ignore_patterns = ["*.log", "*.tmp"]
author_ignore_patterns = ["bot@", "ci@"]
```

## MCP Integration

The tool provides Model Context Protocol tools for AI assistants:

```python
@mcp.tool()
def analyze_git_history(
    from_ref: str,
    to_ref: str,
    repo_path: str = "."
) -> dict:
    """Analyze git history between two references."""
    ...

@mcp.tool()
def compare_git_branches(
    branch_a: str,
    branch_b: str,
    repo_path: str = "."
) -> dict:
    """Compare two git branches with detailed analysis."""
    ...

@mcp.tool()
def get_commit_analysis(
    commit_hash: str,
    repo_path: str = "."
) -> dict:
    """Get detailed analysis of a single commit."""
    ...
```

## Use Cases

### 1. Release Notes Generation
Automatically generate comprehensive release notes:

```bash
git-analysis compare v1.2.0 v1.3.0 --llm --output release-notes.json
```

### 2. Code Review Preparation
Summarize branch changes before code review:

```bash
git-analysis diff-commits main feature-branch
git-analysis complexity main feature-branch --threshold 30
```

### 3. Project Timeline Analysis
Visualize project evolution and contributor activity:

```bash
git-analysis contributors v1.0.0 v2.0.0
git-analysis releases --count 10 --llm
```

### 4. Risk Assessment
Evaluate risk before merging changes:

```bash
git-analysis compare main feature-branch --llm
# Look for:
# - High complexity commits (>70)
# - Breaking changes
# - Security-relevant changes
# - Large file modifications
```

### 5. Impact Analysis
Understand the scope and impact of changes:

```bash
git-analysis analyze abc123def456 --llm
# Review:
# - Impact areas
# - Files affected
# - Dependencies touched
# - Testing implications
```

## API Usage

Use the tool programmatically:

```python
from git_analysis import GitAnalysisService, AnalysisConfig
from pathlib import Path

# Create configuration
config = AnalysisConfig(
    repo_path=Path("."),
    use_llm=True,
    max_commits=100
)

# Create service
service = GitAnalysisService(config)

# Compare branches
result = service.compare_refs("main", "feature-branch")
print(f"Total commits: {result.metadata.total_commits}")
print(f"Average complexity: {result.metadata.total_complexity / result.metadata.total_commits:.1f}")

# Analyze single commit
analysis = service.analyze_commit("abc123def456")
print(f"Commit complexity: {analysis.complexity_score}")
print(f"Summary: {analysis.summary}")
```

## Troubleshooting

### Common Issues

1. **Not a git repository**
   ```
   Error: Invalid git repository at /path/to/dir
   ```
   Ensure you're in a git repository or specify the correct path with `--repo`.

2. **Invalid git reference**
   ```
   Error: Failed to get commits between main and feature
   ```
   Check that the branch, tag, or commit hash exists.

3. **Large repository analysis**
   ```
   Warning: Limiting commits to 1000
   ```
   Use `--max-commits` to adjust the limit or filter the range.

### Debug Mode

Enable verbose logging for detailed output:

```bash
git-analysis compare main feature --verbose
```

Check log files:
```bash
tail -f .git-analysis/logs/git-analysis.log
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/your-username/git-analysis.git
cd git-analysis
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=src/git_analysis
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/git_analysis/
```

### Build and Install

```bash
pip install build
python -m build
pip install dist/git_analysis-*.whl
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Performance Tips

- **Use caching**: Results are cached automatically for fast repeated analysis
- **Limit commits**: Use `--max-commits` for large repositories
- **Filter output**: Use appropriate output format (JSON for machine processing)
- **Repository size**: For very large repositories, consider analyzing specific branches

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: https://github.com/your-username/git-analysis/issues
- **Discussions**: https://github.com/your-username/git-analysis/discussions
- **Documentation**: https://github.com/your-username/git-analysis/wiki

## Acknowledgments

Built with inspiration from:
- Git version control best practices
- Software project analytics
- Code review methodologies
- Machine learning for code analysis