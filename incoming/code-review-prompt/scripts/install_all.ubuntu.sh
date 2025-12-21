#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
    curl git jq unzip ripgrep fd-find \
    python3 python3-venv python3-pip \
    ca-certificates gnupg lsb-release

# fd binary alias on Ubuntu
if [ ! -e /usr/local/bin/fd ] && command -v fdfind >/dev/null 2>&1; then
    sudo ln -sf "$(command -v fdfind)" /usr/local/bin/fd
fi

# --- uv (Python package manager) ---

curl -fsSL https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# --- Node.js (LTS) via nvm ---

if ! command -v nvm >/dev/null 2>&1; then
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    # shellcheck disable=SC1091
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
fi
nvm install --lts
corepack enable

# --- GitHub CLI ---

type -p curl >/dev/null || sudo apt-get install -y curl
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
sudo apt-get update && sudo apt-get install -y gh

# --- .NET SDK 9 (Microsoft repo) ---

wget https://packages.microsoft.com/config/ubuntu/$(. /etc/os-release; echo $VERSION_ID)/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install -y dotnet-sdk-9.0

# --- GitHub CLI extensions ---

gh extension install github/gh-copilot || true
gh extension install dlvhdr/gh-dash || true

# --- Python tools (global user tools via uv) ---

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

echo "✅ Ubuntu setup complete."
