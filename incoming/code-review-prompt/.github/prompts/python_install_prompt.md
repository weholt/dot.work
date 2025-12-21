# Python Development Setup

You are a local devops agent on my machine. Install and configure Python code review and quality tools. Use uv for tool installation where possible.

## Tasks

1. Ensure Python 3.12+ is installed and available as `python` and `python3`.
2. Install `uv` if missing.
3. Install global user tools with `uv tool install`:
   - ruff, black, isort, mypy, pytest, tox, pre-commit
4. Verify installation by printing versions for each tool.
5. Initialize pre-commit in the current repo if `.git/` exists:
   - Create a minimal `.pre-commit-config.yaml` with ruff, black, isort, mypy hooks.
   - Run `pre-commit install --install-hooks`.
6. Install GitHub CLI and extensions:
   - `gh` + `gh extension install github/gh-copilot`
   - `gh extension install dlvhdr/gh-dash`

## Output

- A concise summary table of tool paths and versions.
- Exit non-zero on failure of any step.
