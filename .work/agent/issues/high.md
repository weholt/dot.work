# High Priority Issues (P1)

Core functionality broken or missing documented features.

---

---
id: "PERF-010@3d8a2f"
title: "N+1 query in _get_commit_tags causes O(n*m) tag lookups"
description: "Each commit iteration loops through all repo tags to find matches"
created: 2025-12-31
section: "git"
tags: [performance, n+1-query, algorithm]
type: performance
priority: high
status: proposed
references:
  - src/dot_work/git/services/git_service.py
---

### Problem
In `git_service.py:668-679`, `_get_commit_tags()` iterates through ALL repository tags for each commit to find matches. For a repo with C commits and T tags, this is O(C*T) instead of O(C).

```python
def _get_commit_tags(self, commit: gitpython.Commit) -> list[str]:
    """Get tags pointing to this commit."""
    if self.repo is None:
        return []
    try:
        tags = []
        for tag in self.repo.tags:  # ← Iterates ALL tags per commit
            if tag.commit.hexsha == commit.hexsha:
                tags.append(tag.name)
        return tags
    except Exception:
        return []
```

This is called in `analyze_commit()` which is already inside a loop over commits.

### Affected Files
- `src/dot_work/git/services/git_service.py` (lines 668-679)
- Called from `analyze_commit()` (line 212)

### Impact
For a typical repo with 1000 commits and 100 tags:
- Current: 100,000 tag comparisons
- Optimized: 1,000 tag comparisons (100x faster)

With large repos (e.g., linux kernel: 1M+ commits, 40k tags), this becomes prohibitive.

### Proposed Solution
Build a tag-to-commit mapping cache once, similar to `_commit_to_branch_cache`:

```python
def _build_tag_commit_mapping(self) -> dict[str, list[str]]:
    """Build mapping of commit SHAs to tag names.

    Returns:
        Dictionary mapping commit SHA to list of tag names
    """
    if self.repo is None:
        return {}

    mapping: dict[str, list[str]] = {}
    for tag in self.repo.tags:
        sha = tag.commit.hexsha
        if sha not in mapping:
            mapping[sha] = []
        mapping[sha].append(tag.name)

    return mapping

def _get_commit_tags(self, commit: gitpython.Commit) -> list[str]:
    """Get tags pointing to this commit using cache.

    O(1) lookup instead of O(T) iteration.
    """
    return self._tag_to_commit_cache.get(commit.hexsha, [])
```

Build the cache in `compare_refs()` alongside `_build_commit_branch_mapping()`.

### Acceptance Criteria
- [ ] Tag-to-commit mapping built once per comparison
- [ ] `_get_commit_tags()` uses O(1) dictionary lookup
- [ ] All existing tests pass
- [ ] No regression in tag detection

---

id: "PERF-011@7b2c9e"
title: "Repeated regex compilation in FileAnalyzer.categorize_file()"
description: "Category patterns recompiled on every file categorization"
created: 2025-12-31
section: "git"
tags: [performance, regex, compilation]
type: performance
priority: high
status: proposed
references:
  - src/dot_work/git/services/file_analyzer.py
---

### Problem
In `file_analyzer.py:32-73`, `categorize_file()` uses `re.search()` on patterns that are compiled on every call. For F files and P patterns, this compiles patterns F*P times instead of P times.

```python
def categorize_file(self, file_path: str) -> FileCategory:
    # ...
    for category, patterns in self.file_category_patterns.items():
        for pattern in patterns:
            if re.search(pattern, file_path, re.IGNORECASE):  # ← Compiles pattern every time
                return category
```

The `file_category_patterns` dict has ~50 regex patterns across 7 categories.

### Affected Files
- `src/dot_work/git/services/file_analyzer.py` (lines 32-73, 128-224)

### Impact
For scanning 10,000 files:
- Current: 10,000 files × ~50 patterns = 500,000 regex compilations
- Optimized: 50 regex compilations once at initialization

Regex compilation is expensive; this wastes significant CPU time during large scans.

### Proposed Solution
Pre-compile all patterns in `_initialize_category_patterns()`:

```python
def _initialize_category_patterns(self) -> dict[FileCategory, list[re.Pattern]]:
    """Initialize file category patterns with pre-compiled regex."""
    return {
        FileCategory.CODE: [
            re.compile(pattern, re.IGNORECASE)
            for pattern in [
                r"\.(py|js|ts|jsx|tsx|java|go|rs|c|cpp|cc|cxx|h|hpp|cs|php|rb|kt|scala|swift|dart|lua|perl|r|sql)$",
                r"^src/",
                # ... etc
            ]
        ],
        # ... other categories
    }
```

And update `categorize_file()` to use pre-compiled patterns directly.

### Acceptance Criteria
- [ ] All category patterns pre-compiled at initialization
- [ ] `categorize_file()` uses compiled patterns directly
- [ ] Existing tests pass
- [ ] Performance improvement measurable on large repos

---

id: "PERF-012@1e5f8d"
title: "Jinja2 environment created repeatedly in installer"
description: "create_jinja_env() creates new environment for each file render"
created: 2025-12-31
section: "installer"
tags: [performance, memory, jinja2]
type: performance
priority: high
status: proposed
references:
  - src/dot_work/installer.py
---

### Problem
In `installer.py:153-156`, `render_prompt()` calls `create_jinja_env()` which creates a new Jinja2 environment for EACH prompt file. This creates unnecessary overhead:

```python
def render_prompt(prompts_dir: Path, prompt_file: Path, env_config: Environment) -> str:
    jinja_env = create_jinja_env(prompts_dir)  # ← New environment per file
    template = jinja_env.get_template(prompt_file.name)
    context = build_template_context(env_config)
    return template.render(**context)
```

Each Jinja2 Environment:
- Loads templates from disk
- Compiles loaders and filters
- Allocates memory for caching structures

### Affected Files
- `src/dot_work/installer.py` (lines 93-112, 134-156)
- Called from `install_prompts_generic()` in loops

### Impact
For installing 50 prompt files:
- Creates 50 separate Jinja2 environments
- 50x template loading overhead
- Unnecessary memory allocations

### Proposed Solution
Pass Jinja2 environment as parameter or cache at module level:

```python
def render_prompt(
    prompts_dir: Path,
    prompt_file: Path,
    env_config: Environment,
    jinja_env: JinjaEnvironment | None = None,
) -> str:
    if jinja_env is None:
        jinja_env = create_jinja_env(prompts_dir)
    template = jinja_env.get_template(prompt_file.name)
    context = build_template_context(env_config)
    return template.render(**context)
```

Or use a module-level cache:
```python
_jinja_env_cache: dict[Path, JinjaEnvironment] = {}

def get_jinja_env(prompts_dir: Path) -> JinjaEnvironment:
    if prompts_dir not in _jinja_env_cache:
        _jinja_env_cache[prompts_dir] = create_jinja_env(prompts_dir)
    return _jinja_env_cache[prompts_dir]
```

### Acceptance Criteria
- [ ] Jinja2 environment created once per prompts_dir
- [ ] Environment reused across all files in installation
- [ ] Existing tests pass
- [ ] No memory leaks from cached environments

---

id: "PERF-013@6a9d4b"
title: "Inefficient project context detection with repeated file reads"
description: "detect_project_context() reads same files multiple times"
created: 2025-12-31
section: "installer"
tags: [performance, io, file-operations]
type: performance
priority: high
status: proposed
references:
  - src/dot_work/installer.py
---

### Problem
In `installer.py:904-972`, `detect_project_context()` reads `pyproject.toml` or `package.json` once to check existence, then reads it AGAIN to parse content:

```python
# Detect Python
if (target / "pyproject.toml").exists():  # ← Read #1 (stat)
    # ...
    pyproject_content = (target / "pyproject.toml").read_text(encoding="utf-8")  # ← Read #2
```

This doubles I/O for files that exist.

### Affected Files
- `src/dot_work/installer.py` (lines 904-972)
- Called from `initialize_work_directory()`

### Impact
- Unnecessary I/O operations
- Blocking on disk access twice
- Particularly slow on network filesystems

### Proposed Solution
Read file once and cache content, or use exception handling:

```python
def detect_project_context(target: Path) -> dict[str, str]:
    context = { /* defaults */ }

    # Detect Python - read once
    try:
        pyproject_content = (target / "pyproject.toml").read_text(encoding="utf-8")
        context["language"] = "Python"
        context["package_manager"] = "uv or pip"
        # ... parse content
    except FileNotFoundError:
        pass

    # Detect Node.js - read once
    try:
        pkg_content = (target / "package.json").read_text(encoding="utf-8")
        context["language"] = "JavaScript/TypeScript"
        # ... parse content
    except FileNotFoundError:
        pass

    return context
```

### Acceptance Criteria
- [ ] Each file read at most once
- [ ] Existing tests pass
- [ ] No functional regression in context detection

---
