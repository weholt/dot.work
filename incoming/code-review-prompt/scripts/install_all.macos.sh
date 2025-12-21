#!/usr/bin/env bash
set -euo pipefail

# --- Homebrew & core ---

if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

brew update
brew install \
    git gh jq ripgrep fd \
    python node \
    uv \
    dotnet-sdk \
    pre-commit

# Enable Corepack (yarn/pnpm shims)
corepack enable

# --- GitHub CLI & extensions ---

gh extension install github/gh-copilot || true
gh extension install dlvhdr/gh-dash || true

# --- Python toolchain (global user tools via uv) ---

uv tool install ruff
uv tool install black
uv tool install isort
uv tool install mypy
uv tool install pytest
uv tool install tox
uv tool install pre-commit

# --- JavaScript / TypeScript global utilities ---

npm install -g @sonarsource/sonar-scanner-cli

# --- .NET / C# global tools ---

dotnet tool install -g dotnet-format
dotnet tool install -g dotnet-reportgenerator-globaltool
dotnet tool install -g dotnet-outdated-tool
dotnet tool install -g dotnet-stryker
dotnet tool install -g dotnet-ef
dotnet tool install -g dotnet-sonarscanner

echo "✅ macOS setup complete."
