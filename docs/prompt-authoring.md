# Prompt Authoring Guide

## Quick Start (5 Minutes)

The dot-work system uses a **single canonical prompt file** per AI tool integration, eliminating duplication and drift across environments.

### The Problem (Before)
```
prompts/
├── copilot-prompt.md        ← Manual copy
├── claude-prompt.md         ← Manual copy
└── opencode-prompt.md       ← Manual copy (out of sync!)
```
**Issues:** Drift, maintenance burden, inconsistency

### The Solution (After)
```
prompts/
└── my-agent.canon.md        ← Single source of truth
```
**Benefits:** One file, multiple targets, deterministic generation

### Create Your First Canonical Prompt

**Step 1:** Create a file named `my-agent.canon.md`:

```markdown
---
meta:
  title: "My Agent"
  description: "An AI agent that does XYZ"
  version: "1.0.0"

environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
  
  claude:
    target: ".claude/"
    filename: "system-prompt.md"

---

# System Instructions for My Agent

Your actual prompt content goes here.
You can use markdown, code blocks, etc.

## Key Behaviors
- Behavior 1
- Behavior 2
```

**Step 2:** Install it:
```bash
dot-work prompts install my-agent.canon.md --target copilot
dot-work prompts install my-agent.canon.md --target claude
```

**Step 3:** Done! Generated files:
- `.github/prompts/my-agent.prompt.md` (for Copilot)
- `.claude/system-prompt.md` (for Claude)

---

## Canonical Prompt Format

Every canonical prompt file has two sections:

### 1. Frontmatter (YAML)

The frontmatter is delimited by `---` markers and contains metadata and environment configuration.

#### Required Sections

**`meta:`** - Metadata about the prompt
```yaml
meta:
  title: "Agent Name"           # Human-readable title
  description: "Purpose"         # What this prompt does
  version: "1.0.0"              # Semantic version (optional but recommended)
```

**`environments:`** - Configuration for each target AI tool
```yaml
environments:
  copilot:                       # Environment identifier (copilot, claude, etc.)
    target: ".github/prompts/"   # Output directory (required)
    filename_suffix: ".prompt.md" # OR filename (see below)
```

#### Target Path Options

**Relative paths** (recommended):
```yaml
environments:
  copilot:
    target: ".github/prompts/"          # Relative to project root
  claude:
    target: ".claude/"
```

**Absolute paths:**
```yaml
environments:
  custom:
    target: "/etc/ai/prompts/"          # Absolute path
```

### 2. Prompt Body

After the closing `---`, add your actual prompt content:

```markdown
---
meta:
  title: "My Prompt"
environments:
  copilot:
    target: ".github/prompts/"
    filename: "my-prompt.md"

---

# Your Prompt Title

Start writing your prompt here. It can be:

- Multi-line
- With **markdown** formatting
- Including code blocks
- Anything else your AI tool accepts
```

---

## Filename Configuration

Each environment specifies **either** `filename` **or** `filename_suffix`, not both:

### Option 1: Fixed Filename

Use `filename` when you want a specific name for each environment:

```yaml
environments:
  copilot:
    target: ".github/prompts/"
    filename: "agent-system.md"     # Always generates this name
  
  claude:
    target: ".claude/"
    filename: "instructions.txt"    # Different name, same source
```

### Option 2: Dynamic Filename (from Title)

Use `filename_suffix` to generate names automatically from the `meta.title`:

```yaml
meta:
  title: "Code Review Agent"

environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"   # Generates: code-review-agent.prompt.md
  
  opencode:
    target: ".opencode/"
    filename_suffix: ".md"          # Generates: code-review-agent.md
```

**Transformation Rules:**
- Title: `"Code Review Agent"` → Base: `code-review-agent`
- Spaces → hyphens
- Special chars removed
- Lowercase
- Append suffix

---

## Supported Environments

### GitHub Copilot

**Use Case:** VS Code extension configuration  
**Directory:** `.github/prompts/`  
**File Pattern:** `*.prompt.md`

```yaml
copilot:
  target: ".github/prompts/"
  filename_suffix: ".prompt.md"
```

### Anthropic Claude

**Use Case:** Claude Code or API integration  
**Directory:** `.claude/` or `.anthropic/`  
**File Pattern:** Usually `instructions.md` or similar

```yaml
claude:
  target: ".claude/"
  filename: "instructions.md"
```

### OpenCode (OpenCode Agent)

**Use Case:** Custom AI agent framework  
**Directory:** `.opencode/`  
**File Pattern:** `*.md`

```yaml
opencode:
  target: ".opencode/"
  filename_suffix: ".md"
```

### Custom Environments

Add any custom environment:

```yaml
environments:
  my_custom_tool:
    target: "./custom/prompts/"
    filename: "my-prompt.txt"
```

---

## Complete Example

Here's a real-world example with multiple environments:

```markdown
---
meta:
  title: "Code Review Expert"
  description: "Analyzes pull requests and provides detailed code review feedback"
  version: "2.1.0"

environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
  
  claude:
    target: ".claude/"
    filename: "pr-review.md"
  
  opencode:
    target: ".opencode/"
    filename_suffix: ".md"

---

# Code Review Expert

You are an expert code reviewer with deep knowledge of software engineering best practices.

## Your Role

When analyzing a pull request, you:

1. **Check correctness** - Does the code do what it intends?
2. **Review design** - Is the design sound and maintainable?
3. **Verify testing** - Are tests adequate and correct?
4. **Ensure documentation** - Is the code documented?
5. **Performance** - Are there performance concerns?

## Feedback Format

For each issue found:

```
**Issue:** [Category] - [Brief title]
**Location:** [File:Line]
**Severity:** [Critical/High/Medium/Low]
**Details:** [Explanation]
**Suggestion:** [How to fix]
```

## Rules

- Be respectful and constructive
- Explain the "why" not just the "what"
- Suggest solutions, not just problems
- Consider context and constraints
```

---

## Migration from Legacy Format

If you have separate prompt files for each environment, here's how to migrate:

### Before: Multiple Files

```
prompts/
├── copilot-prompt.md   (content A)
├── claude-prompt.md    (content A with tweaks)
└── opencode-prompt.md  (content A with tweaks)
```

### Migration Steps

**1. Identify common content:**
- Open all existing prompt files
- Find the base content (usually ~80% similar)
- Note the environment-specific tweaks

**2. Create canonical file:**
- Use the base content as the prompt body
- Create the YAML frontmatter
- Add each environment to `environments:` block

**3. Handle environment-specific variations:**

**Option A: Same content, different names**
```yaml
environments:
  copilot:
    target: ".github/prompts/"
    filename: "prompt.md"
  claude:
    target: ".claude/"
    filename: "instructions.md"
```

**Option B: If content must differ:**
- For now: Use separate canonical files
- Future: System may support per-environment content overrides

**4. Test the migration:**
```bash
# Generate and inspect output
dot-work prompts install prompts/my-prompt.canon.md --target copilot

# Compare with original
diff .github/prompts/my-prompt.md prompts/original-copilot.md

# Repeat for other environments
dot-work prompts install prompts/my-prompt.canon.md --target claude
diff .claude/instructions.md prompts/original-claude.md
```

**5. Deploy:**
- Remove old separate prompt files
- Commit the new canonical file
- Update documentation pointing to new location

### Migration Example

**Original Files:**

`prompts/copilot.md`:
```markdown
# Code Review Guide
Review code carefully.
```

`prompts/claude.md`:
```markdown
# Code Review Guide
Review code carefully.
```

**Migrated Canonical File:**

`prompts/code-review.canon.md`:
```yaml
---
meta:
  title: "Code Review Guide"
environments:
  copilot:
    target: ".github/prompts/"
    filename: "review.md"
  claude:
    target: ".claude/"
    filename: "review.md"
---

# Code Review Guide

Review code carefully.
```

---

## FAQ & Troubleshooting

### Q: How do I update a canonical prompt?

**A:** Edit the single `.canon.md` file and reinstall:
```bash
# Edit the file
vim prompts/my-prompt.canon.md

# Reinstall to all environments
dot-work prompts install prompts/my-prompt.canon.md --all-environments
```

All environments get the updated content immediately.

### Q: Generated file says "Environment 'xyz' not found"

**A:** The environment key doesn't exist in your canonical file:

```yaml
# ✗ This won't work:
environments:
  copilot: ...

# Then try to install for 'claude':
dot-work prompts install file.canon.md --target claude  # ERROR!

# ✓ Fix: Add the environment:
environments:
  copilot: ...
  claude: ...    # Add this
```

### Q: Error: "target path is empty"

**A:** The `target:` field must have a value:

```yaml
# ✗ Wrong:
environments:
  copilot:
    target: ""           # Empty!

# ✓ Correct:
environments:
  copilot:
    target: ".github/prompts/"
```

### Q: Error: "must specify either filename or filename_suffix"

**A:** Each environment needs exactly one of these:

```yaml
# ✗ Wrong - has neither:
environments:
  copilot:
    target: ".github/prompts/"

# ✗ Wrong - has both:
environments:
  copilot:
    target: ".github/prompts/"
    filename: "prompt.md"
    filename_suffix: ".prompt.md"

# ✓ Right - has exactly one:
environments:
  copilot:
    target: ".github/prompts/"
    filename: "prompt.md"
```

### Q: Can I have environment-specific content?

**A:** Not yet. Canonical files currently generate the same body for all environments. 

Workarounds:
- Create separate canonical files for different content:
  - `review-detailed.canon.md` (for Copilot)
  - `review-brief.canon.md` (for Claude)
- Use conditional content blocks (documented separately)
- Set different expectations in the prompt text itself

### Q: How do I version my prompts?

**A:** Use semantic versioning in `meta.version`:

```yaml
meta:
  title: "My Prompt"
  version: "1.0.0"    # MAJOR.MINOR.PATCH
  # 1.0.0 → 1.0.1 (fix), 1.1.0 (feature), 2.0.0 (breaking)
```

Track versions in git tags:
```bash
git tag -a v1.0.0-my-prompt -m "Initial prompt release"
```

### Q: Are generated files safe to edit?

**A:** No. Generated files are **disposable**:
- Regenerate them by reinstalling
- Never commit edited generated files
- Always edit the `.canon.md` source instead
- Generated files are git-ignored (recommended)

Add to `.gitignore`:
```
.github/prompts/*.md
.claude/
.opencode/
```

### Q: How do I validate my canonical file?

**A:** The system validates automatically, but you can test:

```bash
# This will error if the file is invalid:
dot-work prompts install my-prompt.canon.md --target copilot

# Check for issues without installing:
dot-work prompts validate my-prompt.canon.md
```

### Q: Can I reference other files in my prompt?

**A:** Not automatically. Options:

1. **Include content directly** in the canonical file (simpler)
2. **Reference paths** in the prompt text for humans to include:
   ```markdown
   See also: docs/guidelines.md
   ```
3. **Generate aggregate files** as part of your build process

### Q: What if I need prompt variations per environment?

**A:** Create multiple canonical files:

```
prompts/
├── review-detailed.canon.md    # Longer, detailed version
├── review-brief.canon.md       # Concise version
└── review-strict.canon.md      # Strict rules version
```

Then install the right one:
```bash
dot-work prompts install prompts/review-detailed.canon.md --target copilot
dot-work prompts install prompts/review-brief.canon.md --target claude
```

---

## Best Practices

### ✅ Do

- **Keep one source of truth** - Maintain a single `.canon.md` file
- **Use descriptive titles** - `"Code Review Expert"` not `"prompt1"`
- **Version your prompts** - Use semantic versioning
- **Document changes** - Include why you updated the prompt
- **Git-ignore generated files** - Don't track `.github/prompts/`, `.claude/`, etc.
- **Test after changes** - Verify generated output is correct
- **Use consistent naming** - Pick a convention and stick to it

### ❌ Don't

- **Manually edit generated files** - They're regenerated when the source changes
- **Keep separate `.md` files** for each environment - That defeats the purpose
- **Hard-code full paths** in prompts - Use relative references instead
- **Share environment configs** between files - One canonical file per logical prompt
- **Ignore validation errors** - Fix them before installing

---

## Deterministic Generation

The system guarantees deterministic output:

**Same input + Same target = Identical output**

This means:
- You can safely regenerate files anytime
- Output is reproducible in CI/CD
- Files can be cached or deleted safely
- No hidden random elements

Generated frontmatter includes only the selected environment's configuration:

```markdown
---
meta:
  title: "My Prompt"
  description: "..."
  version: "1.0.0"

environment:
  filename_suffix: ".prompt.md"   # Only the selected environment
---

# Prompt body
```

Notice: No `environments:` block (that's canonical only), just `environment:` with the selected one.

---

## Next Steps

- Read the [Unified Multi-Environment Prompt Specification](./Unified%20Multi-Environment%20Prompt%20Specification.md) for formal details
- Create your first canonical prompt
- Install it to your environments
- Commit the `.canon.md` file (and `.gitignore` generated output)

**Questions?** Check the FAQ section above or review the test examples in `tests/unit/test_installer_canonical.py`.
