# GitHub CLI Cross-Platform Setup

You are a local devops agent on my machine. Ensure GitHub CLI tooling is installed and ready across all languages.

## Tasks

1. Install/verify `gh` (GitHub CLI).
2. Log in non-interactively when token provided via `GH_TOKEN` env var.
3. Install the following `gh` extensions:
   - `github/gh-copilot` (AI assistance)
   - `dlvhdr/gh-dash` (dashboard)
4. Configure helpful aliases:
   - `gh alias set prr 'pr review --approve -b "LGTM (automated review)"'`
   - `gh alias set prc 'pr create -f'`
   - `gh alias set prd 'pr diff'`
5. Print versions and confirm extensions installed.

## Output

- `gh --version`, list of installed extensions, and the configured aliases.
