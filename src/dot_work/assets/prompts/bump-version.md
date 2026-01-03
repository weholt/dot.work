---
meta:
  title: "Bump Version"
  description: "Semantic versioning management for any project"
  version: "0.1.1"
---

# 🔢 Bump Version

This prompt manages semantic versioning for any project.

---

## 🧠 Step 0: Check Memory First

**Before investigating the codebase**, check `memory.md` for existing version management rules:

```markdown
Look for:
  - "Version Management" section in memory.md
  - Previously documented version file locations
  - Project-specific versioning scheme (SemVer, CalVer, custom)
```

- **Found** → Follow documented rules, skip investigation
- **Not found** → Proceed to Step 1 (Investigation)

---

## 🔍 Step 1: Investigate Version Management

Scan the codebase for version definitions:

```bash
# Common version file patterns
grep -r "version" --include="*.toml" --include="*.json" --include="*.yaml" .
grep -r "__version__\|VERSION\|version =" --include="*.py" --include="*.js" .
```

### Common Version Locations by Ecosystem

| Ecosystem | Primary File | Format |
|-----------|-------------|--------|
| Python (modern) | `pyproject.toml` | `version = "X.Y.Z"` |
| Python (legacy) | `setup.py` | `version="X.Y.Z"` |
| Node.js | `package.json` | `"version": "X.Y.Z"` |
| Rust | `Cargo.toml` | `version = "X.Y.Z"` |
| Go | `go.mod` or git tags | `vX.Y.Z` |
| Ruby | `*.gemspec` | `version = "X.Y.Z"` |
| .NET | `*.csproj` | `<Version>X.Y.Z</Version>` |
| Java/Gradle | `build.gradle` | `version = 'X.Y.Z'` |
| Java/Maven | `pom.xml` | `<version>X.Y.Z</version>` |

### After Investigation

1. Identify the **single source of truth** for version
2. List any **secondary locations** that must stay in sync
3. **Document findings in memory.md** (Step 2)

### Investigation Outcomes

After scanning, you will encounter one of these scenarios:

| Outcome | Action |
|---------|--------|
| ✅ Single version found | Proceed to Step 2 (document in memory) |
| ⚠️ Multiple versions found | Go to **Ambiguous Version Handling** |
| ❌ No version found | Go to **No Version Found Handling** |

---

## ❌ No Version Found Handling

If investigation finds **no version definition**, STOP and ask the user:

```markdown
🔍 **No version management detected in this project.**

I scanned for version definitions but found none. How would you like to proceed?

**Option 1: Add version to existing config file**
Best for projects that already have a manifest file.

| If you have... | I'll add version to... |
|----------------|------------------------|
| `pyproject.toml` | `[project]` section: `version = "0.1.0"` |
| `package.json` | Root object: `"version": "0.1.0"` |
| `Cargo.toml` | `[package]` section: `version = "0.1.0"` |
| `*.csproj` | `<PropertyGroup>`: `<Version>0.1.0</Version>` |

**Option 2: Use git tags only**
No file changes. Version tracked via `git tag vX.Y.Z`.
Good for: Go projects, scripts, simple tools.

**Option 3: Create a VERSION file**
Simple text file containing just the version string.
Good for: Shell scripts, polyglot projects, CI/CD pipelines.

**Option 4: Skip versioning**
This project doesn't need version management.

---

Please choose an option (1-4) or describe your preferred approach:
```

### After User Chooses

1. Implement the chosen approach
2. Set initial version (suggest `0.1.0` for new projects, `1.0.0` for stable)
3. Document in memory.md
4. Confirm the setup

---

## ⚠️ Ambiguous Version Handling

If investigation finds **multiple version definitions**, STOP and ask the user:

```markdown
⚠️ **Multiple version definitions found!**

I found version strings in multiple locations:

| Location | Version | Last Modified |
|----------|---------|---------------|
| `pyproject.toml` | `0.1.0` | 2024-12-15 |
| `src/__init__.py` | `0.1.1` | 2024-12-18 |
| `package.json` | `1.0.0` | 2024-11-01 |

**This creates sync problems.** We need to establish a single source of truth.

---

### Recommended Approaches

**Option A: Single source of truth (RECOMMENDED)**
Choose ONE file as the source. Remove version from others.

Example for Python:
- Keep: `pyproject.toml` → `version = "X.Y.Z"`
- Remove: `__version__` from `__init__.py`
- At runtime, use: `importlib.metadata.version("package-name")`

**Option B: Primary + synced secondaries**
One source, others explicitly synced.

Example:
- Source: `pyproject.toml`
- Synced: `__init__.py` (must update both on every bump)

**Option C: Different versions for different purposes**
Rare, but sometimes needed (e.g., API version vs package version).

---

### Questions to resolve:

1. **Which version is correct right now?**
   - `0.1.0` (pyproject.toml)
   - `0.1.1` (__init__.py)
   - Other: ___

2. **Which file should be the source of truth?**
   - `pyproject.toml` (recommended for Python)
   - Other: ___

3. **What should happen to the other locations?**
   - Remove them (cleanest)
   - Keep in sync (more maintenance)

Please answer these questions so I can set up proper version management.
```

### Resolution Steps

Once the user clarifies:

1. **Set correct version** in the chosen source of truth
2. **Handle secondary locations**:
   - If removing: Delete the version lines, update code to use runtime lookup
   - If syncing: Update to match, document sync requirement
3. **Document in memory.md** with clear rules
4. **Verify** no version mismatches remain

---

## 📝 Step 2: Save to Memory (First Time Only)

After initial investigation, **add to memory.md**:

```markdown
## Version Management
- **Scheme:** [SemVer | CalVer | Custom]
- **Source of truth:** [primary file path]
- **Sync locations:** [list any secondary files, or "none"]
- **Notes:** [any project-specific rules]
- **Added:** [date]
```

This ensures future bumps skip investigation.

---

## 📋 Semantic Versioning Rules

Version format: `MAJOR.MINOR.PATCH`

| Bump Type | When to Use | Example |
|-----------|-------------|---------|
| **patch** | Bug fixes, minor improvements, no API changes | `0.1.0` → `0.1.1` |
| **minor** | New features, backward-compatible changes | `0.1.5` → `0.2.0` |
| **major** | Breaking changes, incompatible API changes | `0.9.3` → `1.0.0` |

### Bump Behavior

| Command | Action |
|---------|--------|
| `bump version` (no arg) | Increment **patch**: `0.1.0` → `0.1.1` |
| `bump version patch` | Increment **patch**: `0.1.0` → `0.1.1` |
| `bump version minor` | Increment **minor**, reset patch: `0.1.5` → `0.2.0` |
| `bump version major` | Increment **major**, reset minor and patch: `0.9.3` → `1.0.0` |

---

## 🔄 Bump Procedure

### Step 3: Read Current Version

Read version from the documented source of truth.

If multiple locations documented, verify they match:
- **Match** → Proceed with bump
- **Mismatch** → STOP, use the mismatch resolution dialog:

```markdown
⚠️ **Version mismatch detected!**

The documented version locations are out of sync:

| Location | Version |
|----------|---------|
| `pyproject.toml` (source) | `0.2.0` |
| `__init__.py` (synced) | `0.1.9` |

**Before bumping, we need to sync these.**

Which version is correct?
1. `0.2.0` (from pyproject.toml)
2. `0.1.9` (from __init__.py)
3. Neither - the correct version is: ___

After you confirm, I'll:
1. Sync all locations to the correct version
2. Then perform the requested bump
```

### Step 4: Calculate New Version

```
patch bump (default): X.Y.Z → X.Y.(Z+1)
minor bump:           X.Y.Z → X.(Y+1).0
major bump:           X.Y.Z → (X+1).0.0
```

### Step 5: Update All Locations

Update the source of truth and any documented sync locations atomically.

### Step 6: Verify and Report

```markdown
✅ Version bumped: X.Y.Z → A.B.C (type)

Updated files:
  - [list of files updated]

Next steps:
  - Run build/tests to verify
  - Commit: `git commit -am "chore: bump version to A.B.C"`
  - Tag (optional): `git tag vA.B.C`
```

---

## ⚠️ Pre-Bump Checklist

Before bumping version:

```
□ All tests pass?
□ Build succeeds?
□ CHANGELOG updated? (if maintained)
□ Version files in sync? (if multiple)
□ Working directory clean?
```

---

## 🚫 Anti-Patterns

| Don't | Do |
|-------|-----|
| Update only one version file | Update all documented locations together |
| Bump during active development | Bump before release/commit |
| Skip verification | Always verify versions match after bump |
| Investigate every time | Check memory.md first |
| Forget to document | Save version rules to memory.md on first use |

---

## 🎯 Usage Triggers

When the user says:
- "bump version" → patch bump
- "bump version patch" → patch bump
- "bump version minor" → minor bump  
- "bump version major" → major bump
- "release X.Y.Z" → set specific version
- "what version are we on?" → read and report current version

---

## 📚 Examples by Ecosystem

### Python (pyproject.toml)

**Source of truth:** `pyproject.toml`

```toml
[project]
name = "my-package"
version = "0.1.1"
```

**Memory entry:**
```markdown
## Version Management
- Scheme: SemVer (MAJOR.MINOR.PATCH)
- Source of truth: pyproject.toml
- Sync locations: none
- Added: 2024-12-20
```

**Commands:**
```bash
# Read version
grep 'version = ' pyproject.toml | head -1

# Verify build after bump
uv run python scripts/build.py
```

---

### Node.js (package.json)

**Source of truth:** `package.json`

```json
{
  "name": "my-package",
  "version": "1.2.3"
}
```

**Memory entry:**
```markdown
## Version Management
- Scheme: SemVer
- Source of truth: package.json
- Sync locations: package-lock.json (auto-updated on npm install)
- Added: 2024-12-20
```

**Commands:**
```bash
npm version patch  # or minor, major
# Or manually edit package.json
```

---

### Rust (Cargo.toml)

**Source of truth:** `Cargo.toml`

```toml
[package]
name = "my-crate"
version = "0.1.0"
```

**Memory entry:**
```markdown
## Version Management
- Scheme: SemVer
- Source of truth: Cargo.toml
- Sync locations: Cargo.lock (auto-updated)
- Added: 2024-12-20
```

---

### Go (git tags)

**Source of truth:** Git tags

```bash
git tag v1.2.3
git push origin v1.2.3
```

**Memory entry:**
```markdown
## Version Management
- Scheme: SemVer with v prefix
- Source of truth: git tags (vX.Y.Z format)
- Sync locations: none (Go modules use tags)
- Notes: Must push tags to origin
- Added: 2024-12-20
```

---

### .NET (csproj)

**Source of truth:** `*.csproj`

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <Version>1.0.0</Version>
  </PropertyGroup>
</Project>
```

**Memory entry:**
```markdown
## Version Management
- Scheme: SemVer
- Source of truth: MyProject.csproj
- Sync locations: none (or Directory.Build.props for multi-project)
- Added: 2024-12-20
```

---

## 🔀 Alternative Versioning Schemes

If the project uses non-SemVer versioning:

### CalVer (Calendar Versioning)
Format: `YYYY.MM.DD` or `YY.MM.PATCH`

```markdown
## Version Management
- Scheme: CalVer (YYYY.MM.PATCH)
- Source of truth: pyproject.toml
- Bump rules: Year.Month auto-set, patch increments within month
- Added: 2024-12-20
```

### Custom Scheme
Document the specific rules in memory.md and follow them.

---

## 📝 Memory Template

Copy this to memory.md after investigating a new project:

```markdown
## Version Management
- **Scheme:** [SemVer | CalVer | Custom: describe]
- **Source of truth:** [file path]
- **Sync locations:** [file paths, or "none"]
- **Notes:** [any special rules]
- **Added:** [date]
```
