# Requires: Windows 10/11 with winget

$ErrorActionPreference = "Stop"

# --- Core tools ---

winget install --id Git.Git -e --source winget
winget install --id GitHub.cli -e --source winget
winget install --id Python.Python.3.12 -e --source winget
winget install --id OpenJS.NodeJS.LTS -e --source winget
winget install --id Microsoft.DotNet.SDK.9 -e --source winget
winget install --id BurntSushi.ripgrep.MSVC -e --source winget
winget install --id sharkdp.fd -e --source winget
winget install --id GnuWin32.Make -e --source winget

# Refresh PATH in current session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# --- uv (Python) ---

Invoke-WebRequest https://astral.sh/uv/install.ps1 -UseBasicParsing | Invoke-Expression
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"

# --- GitHub CLI extensions ---

gh extension install github/gh-copilot
gh extension install dlvhdr/gh-dash

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

Write-Host "✅ Windows setup complete."
