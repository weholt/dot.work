# Enable AI Agent Autopilot Mode

You are an AI coding assistant working in VS Code. Your task is to enable maximum autonomy for AI agents by merging autonomous settings into the current workspace's `.vscode/settings.json` file.

## Instructions

Merge the following autonomous agent settings into the current workspace's `.vscode/settings.json` file. These settings eliminate confirmation prompts, enable auto-replies, and optimize the development environment for AI agent workflows.

## Settings to Merge

```json
{
    // AI & Quality - Enable maximum AI assistance
    "github.copilot.enable": {
        "*": true,
        "yaml": false,
        "plaintext": false
    },
    "github.copilot.editor.enableAutoCompletions": true,

    // Terminal Autonomy - Eliminate all confirmation prompts
    "terminal.integrated.shellIntegration.enabled": true,
    "terminal.integrated.shellIntegration.showWelcome": false,
    "terminal.integrated.enableMultiLinePasteWarning": "never",
    "terminal.integrated.confirmOnExit": "never",
    "terminal.integrated.confirmOnKill": "never",
    "terminal.integrated.fontFamily": "'JetBrainsMono Nerd Font','JetBrainsMono Nerd Font Mono','JetBrains Mono',Consolas,'Courier New',monospace",

    // Windows Terminal Profile - Use Git Bash for consistency
    "terminal.integrated.defaultProfile.windows": "Git Bash",
    "terminal.integrated.profiles.windows": {
        "Git Bash": {
            "source": "Git Bash",
            "icon": "terminal-bash"
        }
    },

    // Auto-Reply Configuration - Approve all common development commands
    "terminal.integrated.autoReplies": {
        // Node.js/JavaScript/TypeScript
        "npm run build": "y",
        "npm run dev": "y",
        "npm run start": "y",
        "npm run test": "y",
        "npm install": "y",
        "npm ci": "y",
        "pnpm build": "y",
        "pnpm dev": "y",
        "pnpm start": "y",
        "pnpm test": "y",
        "pnpm install": "y",

        // Python Development
        "python -m pip install": "y",
        "pip install -r requirements.txt": "y",
        "python setup.py install": "y",
        "python -m pytest": "y",
        "uv pip install": "y",
        "uv pip sync": "y",
        "uv run": "y",

        // .NET Development
        "dotnet build": "y",
        "dotnet run": "y",
        "dotnet test": "y",
        "dotnet restore": "y",
        "dotnet clean": "y",
        "dotnet publish": "y",
        "dotnet new": "y",
        "dotnet add": "y",
        "dotnet remove": "y",
        "dotnet list": "y",
        "dotnet pack": "y",
        "dotnet nuget": "y",
        "dotnet tool": "y",
        "dotnet format": "y",
        "dotnet watch": "y",
        "dotnet dev-certs": "y",
        "dotnet ef": "y",

        // Docker & Containers
        "docker build": "y",
        "docker run": "y",
        "docker-compose up": "y",
        "docker-compose down": "y",

        // Git Operations
        "git add .": "y",
        "git status": "y",
        "git pull": "y",
        "git push": "y",

        // File System Operations
        "mkdir": "y",

        // PowerShell Core Commands
        "New-Item": "y",
        "Copy-Item": "y",
        "Remove-Item": "y",
        "Move-Item": "y",
        "Rename-Item": "y",
        "Get-ChildItem": "y",
        "Set-Location": "y",
        "Get-Location": "y",
        "Push-Location": "y",
        "Pop-Location": "y",
        "Test-Path": "y",
        "Get-Content": "y",
        "Set-Content": "y",
        "Add-Content": "y",
        "Out-File": "y",
        "Select-String": "y",
        "Where-Object": "y",
        "Sort-Object": "y",
        "Measure-Object": "y",
        "Group-Object": "y",
        "Format-Table": "y",
        "Format-List": "y",
        "Get-Process": "y",
        "Stop-Process": "y",
        "Start-Process": "y",
        "Get-Service": "y",
        "Start-Service": "y",
        "Stop-Service": "y",
        "Restart-Service": "y",
        "Get-Command": "y",
        "Get-Help": "y",
        "Get-Module": "y",
        "Import-Module": "y",
        "Install-Module": "y",
        "Update-Module": "y",
        "Uninstall-Module": "y",
        "Get-Variable": "y",
        "Set-Variable": "y",
        "Clear-Variable": "y",
        "Remove-Variable": "y",
        "Write-Host": "y",
        "Write-Output": "y",
        "Write-Verbose": "y",
        "Write-Debug": "y",
        "Write-Warning": "y",
        "Write-Error": "y",
        "Invoke-WebRequest": "y",
        "Invoke-RestMethod": "y",
        "ConvertTo-Json": "y",
        "ConvertFrom-Json": "y",
        "ConvertTo-Csv": "y",
        "ConvertFrom-Csv": "y",
        "Export-Csv": "y",
        "Import-Csv": "y"
    },

    // File Management - Enable auto-save and eliminate prompts
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,

    // Editor Behavior - Optimize for autonomous coding
    "editor.formatOnSave": true,
    "editor.fontFamily": "'JetBrainsMono Nerd Font','JetBrainsMono Nerd Font Mono','JetBrains Mono',Consolas,'Courier New',monospace",
    "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.fixAll.eslint": "explicit",
        "source.organizeImports": "explicit"
    },
    "editor.rulers": [100],

    // Language Intelligence - Enable auto-imports and suggestions
    "typescript.preferences.importModuleSpecifier": "relative",
    "typescript.suggest.autoImports": true,
    "javascript.suggest.autoImports": true,

    // Development Environment Optimization
    "files.exclude": {
        "**/node_modules": true,
        "**/.git": true,
        "**/.DS_Store": true,
        "**/Thumbs.db": true,
        "**/dist": true,
        "**/build": true,
        "**/bin": true,
        "**/obj": true,
        "**/.venv": true,
        "**/venv": true,
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/.mypy_cache": true,
        "**/.ruff_cache": true,
        "**/.repo_cache": true
    },

    "search.exclude": {
        "**/node_modules": true,
        "**/bower_components": true,
        "**/*.code-search": true,
        "**/dist": true,
        "**/build": true,
        "**/bin": true,
        "**/obj": true,
        "**/.venv": true,
        "**/venv": true,
        "**/__pycache__": true
    }
}
```

## Merge Instructions

1. **Read the current `.vscode/settings.json`** in the workspace
2. **Intelligently merge** the above settings with existing settings:
   - **Preserve existing settings** that don't conflict
   - **Add new autopilot settings** that aren't present
   - **Merge objects and arrays** rather than replacing them completely
   - **Prioritize autonomy** - if there's a conflict, choose the setting that enables more autonomous operation
3. **Maintain proper JSON formatting** with comments where appropriate
4. **Test the configuration** by verifying the file is valid JSON

## Key Autonomy Features

### 🚀 Terminal Autonomy
- **No confirmation prompts** for exit, kill, or paste operations
- **Auto-approval** for 100+ common development commands
- **Consistent shell environment** with Git Bash on Windows

### 🤖 AI Enhancement
- **Maximum Copilot integration** enabled across all file types
- **Auto-completions** enabled for faster coding
- **Intelligent suggestions** for imports and code actions

### ⚡ Workflow Optimization
- **Auto-save** with 1-second delay for immediate persistence
- **Format on save** with automatic import organization
- **Auto-fix** for linting issues on save
- **Clean workspace** with comprehensive file exclusions

### 🔧 Development Tools
- **Multi-language support** with optimized settings for:
  - TypeScript/JavaScript (Node.js, npm, pnpm)
  - Python (pip, uv, pytest)
  - .NET (dotnet CLI, Entity Framework)
  - Docker and containerization
  - Git version control

## Usage Example

```
Enable autopilot mode by merging the autonomous agent settings from .github/prompts/enable_autopilot.prompt.md into the current workspace's .vscode/settings.json. This will eliminate confirmation prompts and enable maximum autonomy for AI coding assistants.
```

## Benefits

- **Reduced friction** - No manual approvals needed for common commands
- **Faster development** - Automatic formatting, saving, and import organization
- **Consistent environment** - Standardized terminal and editor behavior
- **AI-optimized** - Settings specifically chosen to enhance AI agent performance
- **Cross-platform** - Works on Windows, macOS, and Linux development environments

## Notes

- These settings are designed for **trusted development environments**
- Review the auto-reply list and customize for your specific workflow
- Some organizations may have security policies that conflict with these settings
- Consider using a separate workspace or profile for AI agent development
- The font family assumes JetBrains Mono Nerd Font is installed (fallbacks provided)

---

**Generated from**: AI-Powered Code Review Setup
**Source**: [weholt/code-review-prompt](https://github.com/weholt/code-review-prompt)
**Purpose**: Maximum autonomy for AI coding agents in VS Code
