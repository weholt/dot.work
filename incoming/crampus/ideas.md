# IDEA-021: Git History Analysis Tool

---
id: "IDEA-021"
title: "Structured Git History Comparison and Analysis"
description: "Compare git branches/commits with detailed change analysis and LLM-powered summaries"
created: 2025-10-15
section: git-tools
tags: [git, analysis, version-control, llm, code-review]
type: enhancement
priority: medium
status: proposed
references: IDEA-019, solace/services/
---

Create a tool for analyzing and comparing git history between branches, commits, or tags with structured, reusable output.

**Core Functionality:**

Compare two git references (branch, commit, tag) and generate:
- Structured JSON output of all changes
- Metadata: author, timestamp, branch, commit hash
- Complexity analysis (lines changed, files affected, impact score)
- LLM-generated natural language summaries
- Incremental, reusable change comparisons

**Architecture:**

```python
# solace/services/git_analysis_service.py

@dataclass
class ChangeAnalysis:
    commit_hash: str
    author: str
    timestamp: datetime
    branch: str
    message: str
    files_changed: list[str]
    lines_added: int
    lines_deleted: int
    complexity_score: float
    summary: str
    tags: list[str]

class GitAnalysisService:
    def compare_refs(
        self,
        from_ref: str,
        to_ref: str,
        repo_path: Path
    ) -> ComparisonResult:
        """
        Compare two git references with detailed analysis.
        
        Process:
        1. Get all commits between references
        2. Analyze each commit individually
        3. Store analysis in cache for reuse
        4. Compare sequential commits
        5. Generate aggregate summary
        6. Return structured results
        """
        ...
    
    def analyze_commit(self, commit: GitCommit) -> ChangeAnalysis:
        """Analyze a single commit with LLM assistance."""
        # Extract commit metadata
        # Calculate complexity metrics
        # Generate LLM summary
        # Extract relevant tags
        # Cache results
        ...
    
    def compare_commits(
        self,
        commit_a: ChangeAnalysis,
        commit_b: ChangeAnalysis
    ) -> ComparisonDiff:
        """Compare two commits and describe differences."""
        # Natural language description
        # Highlight key differences
        # Identify patterns
        ...
```

**Change Complexity Scoring:**

```python
def calculate_complexity(commit: GitCommit) -> float:
    """
    Calculate complexity score (0-100) based on:
    - Number of files changed
    - Lines added/deleted
    - File types affected (config vs code)
    - Commit message indicators (refactor, breaking, etc.)
    - Test coverage changes
    """
    score = 0
    score += min(len(commit.files_changed) * 5, 30)
    score += min((commit.lines_added + commit.lines_deleted) / 100, 40)
    score += 20 if "breaking" in commit.message.lower() else 0
    score += 10 if "refactor" in commit.message.lower() else 0
    return min(score, 100)
```

**Output Format:**

```json
{
  "comparison": {
    "from": "v2025.10.00003",
    "to": "v2025.10.00004",
    "date_range": ["2025-10-10", "2025-10-13"],
    "total_commits": 15,
    "total_complexity": 450
  },
  "commits": [
    {
      "hash": "abc123...",
      "author": "johndoe",
      "timestamp": "2025-10-13T14:30:00Z",
      "branch": "feature/youtube-import",
      "message": "Add YouTube video import support",
      "files_changed": ["solace/services/youtube_service.py", "tests/test_youtube.py"],
      "lines_added": 150,
      "lines_deleted": 5,
      "complexity_score": 45,
      "summary": "Implements YouTube video import with transcript extraction...",
      "tags": ["feature", "youtube", "import"]
    }
  ],
  "aggregate_summary": "This release focuses on content import features...",
  "highlights": [
    "Added YouTube video import (#123)",
    "Performance improvements in indexing (#124)"
  ],
  "contributors": {
    "johndoe": 10,
    "janedoe": 5
  }
}
```

**MCP Tools:**

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
def get_commit_analysis(commit_hash: str, repo_path: str = ".") -> dict:
    """Get detailed analysis of a single commit."""
    ...
```

**Caching Strategy:**

```python
# Cache structure: .git/solace-analysis/
# {commit-hash}.json - Individual commit analysis
# {from-hash}_{to-hash}.json - Comparison results

class AnalysisCache:
    def get_commit_analysis(self, commit_hash: str) -> Optional[ChangeAnalysis]:
        """Retrieve cached commit analysis."""
        ...
    
    def store_commit_analysis(self, analysis: ChangeAnalysis):
        """Store commit analysis for reuse."""
        ...
```

**Use Cases:**

1. **Release Notes Generation:** Automatically generate release notes from git history
2. **Code Review Preparation:** Summarize branch changes before review
3. **Project Timeline:** Visualize project evolution over time
4. **Impact Assessment:** Estimate change impact before merging
5. **Contributor Analysis:** Track individual contributions

**Configuration:**

```env
GIT_ANALYSIS_ENABLED=true
GIT_ANALYSIS_USE_LLM=true
GIT_ANALYSIS_CACHE_DIR=.git/solace-analysis
GIT_ANALYSIS_COMPLEXITY_THRESHOLD=50
```

**Effort Estimate:** 2-3 weeks
