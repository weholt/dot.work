# Migration Guide: dot-work Plugin Architecture

This guide helps you migrate from the monolithic dot-work to the new plugin-based architecture.

## What Changed?

The dot-work project has been split into:
- **Core package**: Essential functionality (prompt installation, environment detection, validation)
- **Plugin packages**: Specialized features (issue tracking, knowledge graph, code review, etc.)

## Why the Change?

The plugin architecture provides:

1. **Smaller dependencies**: Install only what you need
2. **Faster installs**: Smaller packages download and install faster
3. **Independent updates**: Plugins can be updated independently
4. **Modular development**: Easier to contribute to specific features

## Affected Commands

The following commands now require installing the corresponding plugin:

| Command | Plugin | Installation |
|---------|--------|--------------|
| `dot-work db-issues` | dot-issues | `pip install dot-issues` |
| `dot-work kg` | dot-kg | `pip install dot-kg` |
| `dot-work review` | dot-review | `pip install dot-review` |
| `dot-work container` | dot-container | `pip install dot-container` |
| `dot-work git` | dot-git | `pip install dot-git` |
| `dot-work harness` | dot-harness | `pip install dot-harness` |
| `dot-work overview` | dot-overview | `pip install dot-overview` |
| `dot-work python` | dot-python | `pip install dot-python` |
| `dot-work version` | dot-version | `pip install dot-version` |

### Unchanged Commands

These core commands work without any plugins:

- `dot-work install` - Install prompts to AI environments
- `dot-work list` - List supported environments
- `dot-work detect` - Detect AI environment
- `dot-work validate` - Validate JSON/YAML files
- `dot-work prompt` - Generate prompts
- `dot-work plugins` - List installed plugins

## Migration Steps

### Step 1: Check Your Current Usage

Identify which dot-work commands you use:

```bash
# Check your command history for dot-work usage
history | grep "dot-work"

# Or check if you use specific subcommands
dot-work --help | grep -E "db-issues|kg|review|container|git|harness|overview|python|version"
```

### Step 2: Install Required Plugins

Install the plugins corresponding to the commands you use:

```bash
# Issue tracking
pip install dot-issues

# Knowledge graph
pip install dot-kg

# Code review
pip install dot-review

# Docker containers
pip install dot-container

# Git analysis
pip install dot-git

# Claude Agent SDK
pip install dot-harness

# Codebase overview
pip install dot-overview

# Python build/scan
pip install dot-python

# Version management
pip install dot-version
```

### Step 3: Verify Installation

Check that plugins are installed and registered:

```bash
dot-work plugins
```

Expected output:

```
Installed Plugins:
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Name       ┃ Command   ┃ Version ┃ Module           ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ dot-issues │ db-issues │ 0.1.0   │ dot_issues      │
│ dot-kg     │ kg        │ 0.1.0   │ dot_kg          │
│ dot-review │ review    │ 0.1.0   │ dot_review      │
└────────────┴───────────┴─────────┴─────────────────┘

✓ 3 plugin(s) installed
```

### Step 4: Update Scripts and Workflows

Replace direct command calls with plugin commands:

**Before:**
```bash
# Old: Command bundled with dot-work
dot-work db-issues create --title "Fix bug"
dot-work kg init
dot-work review start
```

**After:**
```bash
# New: Plugin commands (after installing plugins)
dot-work db-issues create --title "Fix bug"  # Requires dot-issues
dot-work kg init                              # Requires dot-kg
dot-work review start                          # Requires dot-review
```

Or use standalone plugin commands:

```bash
dot-issues create --title "Fix bug"
kg init
dot-review start
```

### Step 5: Update Dependencies

**If you use dot-work as a dependency:**

Update your `pyproject.toml` or `requirements.txt`:

**Before:**
```toml
dependencies = [
    "dot-work>=0.1.0",
]
```

**After:**
```toml
dependencies = [
    "dot-work>=0.1.0",
    # Add plugins you need
    "dot-issues>=0.1.0",
    "dot-kg>=0.1.0",
    "dot-review>=0.1.0",
]
```

**For development:**

```toml
dependencies = [
    "dot-work>=0.1.0",
]

[project.optional-dependencies]
# All plugins
plugins = [
    "dot-issues>=0.1.0",
    "dot-kg>=0.1.0",
    "dot-review>=0.1.0",
    "dot-container>=0.1.0",
    "dot-git>=0.1.0",
    "dot-harness>=0.1.0",
    "dot-overview>=0.1.0",
    "dot-python>=0.1.0",
    "dot-version>=0.1.0",
]

# Install with: pip install -e ".[plugins]"
```

## Rollback Plan

If you encounter issues with the plugin architecture, you can temporarily use the old monolithic version:

```bash
# Uninstall current version
pip uninstall dot-work

# Install specific monolithic version (if available)
pip install dot-work==0.1.0
```

Note: The monolithic version will be deprecated after a transition period.

## Common Issues

### Issue: "Command not found"

**Problem:**
```bash
$ dot-work db-issues create --title "Test"
error: No such command 'db-issues'
```

**Solution:**
Install the required plugin:
```bash
pip install dot-issues
```

### Issue: Missing dependencies

**Problem:**
```bash
$ dot-work kg init
error: Module 'numpy' not found
```

**Solution:**
The plugin requires additional dependencies. Reinstall with extras:
```bash
pip install --force-reinstall "dot-kg[all]"
```

### Issue: Plugin not discovered

**Problem:**
```bash
$ dot-work plugins
⚠ No plugins installed
```

But you just installed a plugin.

**Solution:**
1. Check that the plugin was installed correctly:
   ```bash
   pip list | grep dot-
   ```

2. Try reinstalling:
   ```bash
   pip install --force-reinstall dot-issues
   ```

3. Check entry points:
   ```bash
   python -c "from importlib.metadata import entry_points; print(list(entry_points(group='dot_work.plugins')))"
   ```

## Support

If you encounter issues during migration:

1. **Check the [plugins documentation](plugins.md)** for plugin-specific information
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - Your dot-work version: `dot-work --version`
   - Your Python version: `python --version`
   - Installed plugins: `pip list | grep dot-`
   - Error message and steps to reproduce

## Timeline

- **Current status**: Migration in progress, backward compatibility maintained
- **Near future**: Plugins will be published to PyPI
- **Future**: Monolithic version will be deprecated

## Summary

1. Install core dot-work: `pip install dot-work`
2. Install required plugins: `pip install dot-issues dot-kg dot-review`
3. Verify installation: `dot-work plugins`
4. Update scripts and dependencies as needed
5. Report issues if you encounter problems

The plugin architecture provides a more modular and maintainable dot-work ecosystem while preserving all existing functionality.
