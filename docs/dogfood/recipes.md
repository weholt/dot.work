# Dogfooding Recipes: How to Use dot-work Today

**Generated:** 2024-12-28
**Source:** Documentation analysis – all recipes use documented behavior only

---

## Recipe Selection Rules

These recipes:
- ✅ Match the baseline mission
- ✅ Use only documented behavior
- ✅ Are realistic and end-to-end
- ✅ Include explicit commands/config snippets

---

## Recipe 1: New Python Project with AI Workflow

**Goal:** Create a new Python project with full AI-assisted workflow support

**Preconditions:**
- Python 3.11+ installed
- `uv` package manager installed
- GitHub Copilot (or other AI tool) installed

**Inputs needed:**
- Project idea/description

**Step-by-step procedure:**

```bash
# 1. Create project directory
mkdir my-cli-tool && cd my-cli-tool

# 2. Initialize git
git init

# 3. Install dot-work prompts
uvx dot-work install --env copilot

# 4. Use AI prompt to scaffold project
# In GitHub Copilot, type:
/python-project-from-discussion

I want to build a CLI tool that processes CSV files and generates statistics.
It should have commands for:
- stats: Show summary statistics
- filter: Filter rows by criteria
- export: Export to different formats
Use typer for CLI, pandas for processing, and pytest for testing.

# 5. Initialize issue tracking
/setup-issue-tracker

# 6. Generate baseline
/generate-baseline

# 7. Start working
/do-work
```

**Expected outputs:**
- Project structure with `src/`, `tests/`, `pyproject.toml`
- Prompts installed in `.github/prompts/`
- `.work/` directory with `baseline.md`, `focus.md`, `priority files`
- AI agent begins first iteration

**Validation steps:**
```bash
# Verify structure
ls -la src/
ls -la tests/
ls -la .github/prompts/
ls -la .work/agent/

# Verify tests pass
uv run pytest

# Verify linting
uv run ruff check .
```

**Variations:**
- Use `--env claude` for Claude Code
- Use `--env cursor` for Cursor
- Skip `uvx` if dot-work already installed: `dot-work install`

**Failure modes (documented):**
- None documented

---

## Recipe 2: Setup Issue Tracking for Existing Project

**Goal:** Add file-based issue tracking to existing codebase

**Preconditions:**
- Existing Python project
- Git repository

**Inputs needed:**
- Project directory path

**Step-by-step procedure:**

```bash
# 1. Navigate to project
cd /path/to/existing-project

# 2. Install prompts (if not already)
dot-work install --env copilot

# 3. Initialize .work/ structure
dot-work init-work

# 4. Generate baseline (CRITICAL before any code changes)
/generate-baseline

# 5. Verify setup
cat .work/agent/focus.md
cat .work/agent/memory.md
```

**Expected outputs:**
```
.work/
├── baseline.md
└── agent/
    ├── focus.md
    ├── memory.md
    ├── notes/
    └── issues/
        ├── critical.md
        ├── high.md
        ├── medium.md
        ├── low.md
        ├── backlog.md
        ├── shortlist.md
        ├── history.md
        └── references/
```

**Validation steps:**
```bash
# Check .work/ exists
test -d .work/ && echo "OK"

# Check all files exist
test -f .work/agent/focus.md && echo "focus.md OK"
test -f .work/agent/memory.md && echo "memory.md OK"
test -f .work/agent/issues/shortlist.md && echo "shortlist.md OK"
```

**Variations:**
- Add `--force` to overwrite existing `.work/`

**Failure modes:**
- If `.work/` exists: Use `--force` to overwrite

---

## Recipe 3: Quality-Controlled Feature Development

**Goal:** Implement a new feature with regression prevention

**Preconditions:**
- Project with `.work/` initialized
- Baseline already generated

**Inputs needed:**
- Feature description

**Step-by-step procedure:**

```bash
# 1. Create prioritized issue
/focus on "Add user authentication with OAuth2"

# This creates issue in shortlist.md:
# id: FEAT-001@<hash>
# title: Add user authentication with OAuth2
# priority: high
# status: proposed

# 2. Start iteration loop
/do-work

# AI will:
# - Check baseline exists
# - Select issue from shortlist.md
# - Create investigation notes
# - Implement feature
# - Run validation
# - Compare to baseline
# - Complete or fix regressions
```

**What the AI does internally:**
```markdown
[BASELINE]
Verify .work/baseline.md exists and is current

[SELECT]
Select FEAT-001@<hash> from shortlist.md
Update focus.md:
  - Current: FEAT-001@<hash>
  - Next: (select next)

[INVESTIGATE]
Create .work/agent/notes/FEAT-001-investigation.md
Research OAuth2 providers
Determine implementation approach

[IMPLEMENT]
Add authentication code
Add tests
Update documentation

[VALIDATE]
Run tests: uv run pytest
Check coverage: uv run pytest --cov
Run lint: uv run ruff check .
Run types: uv run mypy src/

Compare to .work/baseline.md:
- No new errors in previously clean files
- No increased errors in problematic files

[COMPLETE]
Move FEAT-001 to .work/agent/issues/history.md
Update focus.md: Current → Previous
Extract lessons to memory.md
```

**Expected outputs:**
- Feature implemented with tests
- No regressions vs baseline
- Issue in history.md
- Lessons in memory.md

**Validation steps:**
```bash
# Check tests pass
uv run pytest

# Check coverage maintained
uv run pytest --cov --cov-report=term-missing

# Verify issue completed
grep "FEAT-001" .work/agent/issues/history.md

# Verify focus updated
cat .work/agent/focus.md
```

**Variations:**
- Use `/new-issue` to create issue in specific priority file
- Use `generate-baseline` if baseline is stale

**Failure modes (from do-work prompt):**
- Validation fails: AI creates issues for regressions, fixes them, re-validates
- New errors in modified files: Must fix before completion
- Coverage regression: Must add tests

---

## Recipe 4: Interactive Code Review Workflow

**Goal:** Review code changes and export feedback for AI fixes

**Preconditions:**
- Git repository with changes
- Browser installed

**Inputs needed:**
- Base commit to compare against

**Step-by-step procedure:**

```bash
# 1. Make your changes
# (edit files)
git add .
git commit -m "WIP: Feature changes"

# 2. Start review server
dot-work review start --base HEAD~1

# Server starts at http://localhost:8765
# Browser opens automatically

# 3. In browser:
# - View file tree with changed files
# - Click files to see diff (side-by-side or unified)
# - Click any line to add comment
# - Add suggestions for improvements

# 4. Export comments
dot-work review export --output review-feedback.md

# 5. Pass to AI agent for fixes
# In GitHub Copilot:
I've made some changes. Please review the feedback in review-feedback.md
and implement the suggested fixes.

# 6. Clear reviews when done
dot-work review clear --force
```

**Expected outputs:**
- Web UI at `http://localhost:8765`
- `review-feedback.md` with:
  - File paths
  - Line numbers
  - Comment text
  - Suggestions

**Sample export format:**
```markdown
# Code Review Feedback

## src/auth.py:45
**Issue:** Security - Plain text storage
**Severity:** High
**Comment:** Password stored in plain text. Use hashing.

## src/auth.py:72
**Suggestion:** Add type hints
```python
def authenticate(user: str, password: str) -> bool:
```

## tests/test_auth.py:23
**Comment:** Add test for invalid credentials
```

**Validation steps:**
```bash
# Check export created
test -f .work/reviews/review.md || test -f review-feedback.md

# View export
cat review-feedback.md
```

**Variations:**
- Custom port: `dot-work review start --port 3000`
- Custom base: `dot-work review start --base main`
- Export specific review: `dot-work review export --review-id 20241221-143500`

**Failure modes:**
- Port 8765 in use: Use `--port` to specify different port
- No changes found: Check base commit

---

## Recipe 5: Database Issue Tracking for Team

**Goal:** Setup SQLite-based issue tracking for team collaboration

**Preconditions:**
- Python 3.11+ installed
- dot-work installed

**Inputs needed:**
- Project directory

**Step-by-step procedure:**

```bash
# 1. Initialize database
dot-work db-issues init

# Creates .work/db-issues/issues.db

# 2. Create labels for organization
dot-work db-issues labels create "bug" --color red --description "Bug reports"
dot-work db-issues labels create "feature" --color blue --description "New features"
dot-work db-issues labels create "urgent" --color "#ff4444" --description "Urgent items"

# 3. Create epic for feature
EPIC_ID=$(dot-work db-issues epic create "User Authentication" \
  --description "Implement login, signup, password reset")

# 4. Create child issues
dot-work db-issues create "OAuth2 login" \
  --type feature \
  --priority high \
  --epic $EPIC_ID \
  --labels "feature,backend"

dot-work db-issues create "Signup form" \
  --type feature \
  --priority high \
  --epic $EPIC_ID \
  --labels "feature,frontend"

dot-work db-issues create "Password reset" \
  --type feature \
  --priority medium \
  --epic $EPIC_ID \
  --labels "feature,backend"

# 5. Setup dependencies
LOGIN_ID=$(dot-work db-issues list --epic $EPIC_ID --limit 1 --output json | jq -r '.[0].id')
SESSION_ID=$(dot-work db-issues list --epic $EPIC_ID --output json | jq -r '.[1].id')

dot-work db-issues deps add $SESSION_ID $LOGIN_ID --type depends-on

# 6. Assign work
dot-work db-issues update $LOGIN_ID --assignee alice
dot-work db-issues update $SESSION_ID --assignee bob

# 7. Start work
dot-work db-issues update $LOGIN_ID --status in-progress

# 8. Add progress comment
dot-work db-issues comment $LOGIN_ID "Started OAuth2 implementation using authlib"

# 9. Complete and close
dot-work db-issues close $LOGIN_ID

# 10. Sync to git
dot-work db-issues io sync --message "Completed OAuth2 login" --push
```

**Expected outputs:**
- `.work/db-issues/issues.db` with all issues
- Git commits for each sync

**Validation steps:**
```bash
# Show epic progress
dot-work db-issues epic show $EPIC_ID

# List children
dot-work db-issues child list $EPIC_ID

# Check dependencies
dot-work db-issues deps tree $LOGIN_ID --direction down

# Export backup
dot-work db-issues io export --output backup.jsonl
```

**Variations:**
- Use `--output json` for scripting
- Use `--assignee` for team assignment
- Use `labels` for categorization

**Failure modes:**
- Circular dependency: `deps check-all` will detect
- Missing epic: Check epic ID with `epic list`

---

## Recipe 6: Multi-Environment Prompt Installation

**Goal:** Install prompts for multiple AI tools in same project

**Preconditions:**
- Project that uses multiple AI tools

**Inputs needed:**
- Project directory

**Step-by-step procedure:**

```bash
# 1. Navigate to project
cd /path/to/project

# 2. Install for Copilot (primary)
dot-work install --env copilot

# 3. Install for Claude (secondary)
dot-work install --env claude

# 4. Install for Cursor (tertiary)
dot-work install --env cursor
```

**Expected outputs:**
```
.github/
└── prompts/
    ├── do-work.prompt.md
    ├── setup-issue-tracker.prompt.md
    └── ...

.claude/
└── (claude-specific files)

.cursor/
└── rules/
    └── (cursor-specific files)
```

**Validation steps:**
```bash
# Check each environment
ls -la .github/prompts/
ls -la .claude/
ls -la .cursor/rules/

# Verify prompts exist
test -f .github/prompts/do-work.prompt.md
```

**Variations:**
- Use `--dry-run` to preview all installations first

**Failure modes:**
- Conflicting files: Use `--force` to overwrite

---

## Recipe 7: Codebase Overview for New Team Member

**Goal:** Generate overview of existing codebase for understanding

**Preconditions:**
- Existing Python project with documentation

**Inputs needed:**
- Source directory
- Output directory

**Step-by-step procedure:**

```bash
# 1. Generate overview
dot-work overview src/ docs/overview/

# 2. Read human-friendly guide
cat docs/overview/birdseye_overview.md

# 3. Use structured data for AI
# In AI prompt:
"Use docs/overview/features.json and docs/overview/documents.json
to understand the codebase structure."
```

**Expected outputs:**
```
docs/overview/
├── birdseye_overview.md    # Human-readable
├── features.json           # Structured for LLMs
└── documents.json          # Cross-referenceable
```

**Validation steps:**
```bash
# Check files created
ls -la docs/overview/

# View overview
less docs/overview/birdseye_overview.md

# Check JSON valid
jq . docs/overview/features.json
```

**Variations:**
- Run from project root: `dot-work overview . .work/overview/`

**Failure modes:**
- No Python files found: Check directory path
- No documentation found: Overview still generated

---

## Recipe 8: Version Management with Changelog

**Goal:** Set up date-based versioning with automatic changelog

**Preconditions:**
- Git repository
- dot-work installed

**Inputs needed:**
- Initial version number

**Step-by-step procedure:**

```bash
# 1. Initialize version management
dot-work version init --version 2025.01.001

# 2. Make changes
# (develop features, fix bugs)

# 3. Commit changes
git add .
git commit -m "Add feature X, fix bug Y"

# 4. Freeze version (generates changelog)
dot-work version freeze

# 5. Show current version
dot-work version show

# 6. View history
dot-work version history

# 7. View commits since last version
dot-work version commits
```

**Expected outputs:**
- Git tag: `v2025.01.001`
- `CHANGELOG.md` with entry

**Sample CHANGELOG.md:**
```markdown
# Changelog

## [2025.01.001] - 2025-01-15
### Added
- Feature X implementation

### Fixed
- Bug Y fix
```

**Validation steps:**
```bash
# Check tag created
git tag | grep 2025.01.001

# Check changelog
cat CHANGELOG.md | head -20

# Show version
dot-work version show
```

**Variations:**
- Auto-generate version: `dot-work version init` (no --version)

**Failure modes:**
- No commits since last version: changelog will be empty

---

## Recipe 9: Knowledge Graph for Documentation

**Goal:** Build searchable knowledge graph from markdown docs

**Preconditions:**
- Markdown documentation files

**Inputs needed:**
- Documentation files

**Step-by-step procedure:**

```bash
# 1. Ingest documentation
dot-work kg ingest docs/*.md

# 2. Check database stats
dot-work kg stats

# 3. Search for content
dot-work kg search "authentication"

# 4. Show document outline
DOC_ID=$(dot-work kg search "api" | head -1)
dot-work kg outline $DOC_ID

# 5. Expand specific node
dot-work kg expand <node-id>

# 6. Export as JSON
dot-work kg export > knowledge-graph.json

# 7. Create project for organization
dot-work kg project create "API Documentation"

# 8. Create topics for tagging
dot-work kg topic create "authentication"
dot-work kg topic create "database"
```

**Expected outputs:**
- SQLite database with documents
- Search results with relevance
- Tree outlines
- JSON exports

**Validation steps:**
```bash
# Check database
dot-work kg status

# Test search
dot-work kg search "test query"

# View outline
dot-work kg outline <doc-id>
```

**Variations:**
- Ingest recursively: `dot-work kg ingest docs/**/*.md`
- Export filtered: `dot-work kg render <doc-id> --topic authentication`

**Failure modes:**
- No markdown files found: Check path
- Database locked: Close other connections

---

## Recipe 10: Custom Prompt Authoring

**Goal:** Create custom AI prompt for team workflow

**Preconditions:**
- Understanding of team workflow
- Target AI tool known

**Inputs needed:**
- Prompt content

**Step-by-step procedure:**

```bash
# 1. Create canonical prompt (interactive)
dot-work prompts create

# Follow wizard:
# - Enter title: "Team Code Review"
# - Enter description: "Our team's code review process"
# - Add environments: copilot, claude
# - Enter prompt content...

# 2. Or create manually
cat > team-review.canon.md << 'EOF'
---
meta:
  title: "Team Code Review"
  description: "Our team's code review process"
  version: "1.0.0"

environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
  claude:
    target: ".claude/"
    filename: "team-review.md"

---

# Team Code Review Process

When reviewing PRs:

1. Check test coverage is >= 80%
2. Verify no new security issues
3. Ensure documentation updated
4. Check type hints added
EOF

# 3. Install to environments
dot-work prompts install team-review.canon.md --target copilot
dot-work prompts install team-review.canon.md --target claude

# 4. Verify installation
cat .github/prompts/team-review.prompt.md
cat .claude/team-review.md
```

**Expected outputs:**
- `team-review.canon.md` (source)
- `.github/prompts/team-review.prompt.md` (generated)
- `.claude/team-review.md` (generated)

**Validation steps:**
```bash
# Check source exists
test -f team-review.canon.md

# Check generated files
test -f .github/prompts/team-review.prompt.md
test -f .claude/team-review.md

# Test in AI tool
# In Copilot: /team-code-review
```

**Variations:**
- Use fixed filename: `filename: "custom.md"`
- Add more environments to frontmatter

**Failure modes:**
- Environment not in frontmatter: Add to `environments:` block
- Target path empty: Must specify `target:` for each environment

---

## Symbiosis: Composing Features

### Small Compositions (2 components)

**1. Install + Detect**
```bash
# Auto-detect and install appropriate environment
ENV=$(dot-work detect | awk '{print $1}')
dot-work install --env $ENV
```

**2. init-work + generate-baseline**
```bash
# Setup tracking and quality floor
dot-work init-work
/generate-baseline
```

### Medium Compositions (3-4 components)

**1. New project workflow**
```bash
mkdir new-project && cd new-project
git init
dot-work install --env copilot
/python-project-from-discussion < project-description.txt
/setup-issue-tracker
/generate-baseline
```

**2. Review + Fix loop**
```bash
dot-work review start --base main
# (add comments in browser)
dot-work review export
# (pass to AI for fixes)
dot-work review clear --force
```

### Large Composition (5+ components)

**1. Complete development workflow**
```bash
# SETUP
dot-work install --env claude
dot-work init-work
/generate-baseline

# DEVELOPMENT
/focus on "Implement feature X"
/do-work
# (AI: baseline → select → investigate → implement → validate → complete)

# REVIEW
dot-work review start --base main
dot-work review export

# FIXES
/do-work  # AI addresses review feedback

# RELEASE
dot-work version freeze
git tag -l | tail -1
```

---

## Parameter Interplay Analysis

### Key Parameter Relationships

**install --env + --target:**
- `--env` determines file format and location
- `--target` changes where files are written
- Safe defaults: `--target .` (current directory)

**init-work --force:**
- Overwrites existing `.work/` directory
- Use with caution: destroys existing issues/history
- Default: safe (aborts if exists)

**review start --base + --head:**
- `--base` is the starting point (usually main or HEAD~1)
- `--head` is the endpoint (default: working tree)
- Common: `--base main` to compare against main branch

**db-issues create --type + --priority:**
- Independent but often correlated
- Common combos: `--type bug --priority critical`
- Less common: `--type docs --priority critical`

---

## Decision Guides

| If you want... | Choose... | Why |
|---------------|-----------|-----|
| Start new Python project | Recipe 1 | Full scaffolding with AI workflow |
| Add tracking to existing project | Recipe 2 | Non-destructive setup |
| Quality-controlled development | Recipe 3 | Regression prevention |
| Manual code review | Recipe 4 | Interactive + AI export |
| Team issue tracking | Recipe 5 | SQLite + dependencies |
| Multiple AI tools | Recipe 6 | Multi-environment install |
| Understand codebase | Recipe 7 | Auto-generated overview |
| Version management | Recipe 8 | Date-based + changelog |
| Searchable docs | Recipe 9 | Knowledge graph |
| Custom workflows | Recipe 10 | Canonical prompts |
| File-based issues | `init-work` + AI prompts | Simple, git-tracked |
| Database issues | `db-issues init` | Complex queries, teams |

---

## Success Criteria

Each recipe succeeds when:

1. **Commands execute without error** – All documented commands run successfully
2. **Expected files exist** – Outputs are in documented locations
3. **Validation passes** – Verification steps confirm correct state
4. **Next step possible** - Recipe enables following workflow

---

## Common Gotchas

1. **Forgetting `generate-baseline`** – Always generate before code changes
2. **Editing priority files manually** – Let AI agents manage issues
3. **Not installing prompts first** – Must `install` before using AI prompts
4. **Conflicting review servers** – Only one review server at a time (port 8765)
5. **Mixing issue systems** – Choose file-based OR db-issues, not both (for now)
