# AI-Powered Code Review Setup

This repository provides a comprehensive VS Code setup for AI-assisted code reviews using GitHub Copilot and other modern development tools. It includes configurations for TypeScript/JavaScript, C#/.NET, and Python development with enterprise-grade quality gates, plus powerful repository extraction tools.

## 🎯 Get This Setup in Your Project

### Option 1: AI Agent Prompt (Recommended)
Copy and paste this prompt to any AI coding assistant (GitHub Copilot, Claude, ChatGPT, etc.):

```
Clone and extract the comprehensive VS Code setup for AI-assisted code reviews:

repo_url=https://github.com/weholt/code-review-prompt
language=typescript,csharp,python

This repository contains:
- Complete VS Code configuration with curated extensions for AI development
- AI review prompts for code quality, security, and performance
- Repository extraction tools supporting 11+ programming languages
- Cross-platform setup scripts for Windows, macOS, and Ubuntu
- Enterprise-grade quality gates and linting configurations

Extract all the configuration files, prompts, and scripts to integrate into the current project.
```

### Option 2: Manual Clone
```bash
# Clone the repository
git clone https://github.com/weholt/code-review-prompt.git

# Copy the setup to your project
cp -r code-review-prompt/.vscode ./
cp -r code-review-prompt/.github ./
cp -r code-review-prompt/prompts ./
cp -r code-review-prompt/scripts ./
cp code-review-prompt/.editorconfig ./
cp code-review-prompt/.copilotignore ./
cp code-review-prompt/eslint.config.js ./
cp code-review-prompt/tsconfig.json ./
cp code-review-prompt/Directory.Build.props ./
cp code-review-prompt/global.json ./
cp code-review-prompt/NuGet.config ./
cp code-review-prompt/package.json ./

# Install dependencies
npm install
```

### Option 3: Use Repository Extraction Tool
If you already have this setup, you can extract it into any project:

```powershell
# PowerShell
.\scripts\repo_extract.ps1 "https://github.com/weholt/code-review-prompt" "typescript,csharp,python"

# Bash
./scripts/repo_extract.sh "https://github.com/weholt/code-review-prompt" "typescript,csharp,python"
```

## 🚀 Quick Start

1. **Get this setup** using one of the methods above
2. **Install recommended extensions** when prompted by VS Code
3. **Run setup scripts** for your platform:
   - **Windows**: `.\scripts\install_all.windows.ps1`
   - **macOS**: `./scripts/install_all.macos.sh`
   - **Ubuntu**: `./scripts/install_all.ubuntu.sh`
4. **Configure project-specific settings** (update paths in `launch.json`, solution name in `settings.json`)
5. **Start using AI-assisted code reviews** with the prompts in `.github/prompts/`

## 📁 What's Included

### VS Code Configuration (`.vscode/`)
- **`extensions.json`**: Curated extensions for AI-powered development
- **`settings.json`**: Optimized settings for code quality and AI assistance
- **`tasks.json`**: Build and test tasks for multiple languages + repository extraction
- **`launch.json`**: Debug configurations for Node.js and .NET

### Cross-Platform Setup Scripts (`scripts/`)
- **`install_all.windows.ps1`**: Complete Windows setup with Chocolatey, .NET, Node.js, Python
- **`install_all.macos.sh`**: Complete macOS setup with Homebrew
- **`install_all.ubuntu.sh`**: Complete Ubuntu/Debian setup with apt
- **`repo_extract.ps1`**: PowerShell repository extraction tool
- **`repo_extract.sh`**: Bash repository extraction tool

### Project Configuration
- **`package.json`**: Node.js/TypeScript project setup with modern tooling
- **`tsconfig.json`**: Strict TypeScript configuration
- **`eslint.config.js`**: ESLint 9+ flat config with comprehensive rules
- **`Directory.Build.props`**: C# project settings with strict analysis
- **`.editorconfig`**: Consistent code formatting across languages
- **`global.json`**: .NET SDK version pinning
- **`NuGet.config`**: NuGet package source configuration
- **`.copilotignore`**: Exclude sensitive files from AI context
- **`.gitignore`**: Comprehensive ignore patterns for all supported languages

### AI Review Prompts (`.github/prompts/`)
- **`code-review.md`**: General code quality and best practices
- **`security-review.md`**: Security vulnerability assessment
- **`performance-review.md`**: Performance optimization guidelines
- **`all_platforms_gh_prompt.md`**: Cross-platform GitHub CLI setup
- **`dotnet_install_prompt.md`**: .NET development environment setup
- **`js_ts_install_prompt.md`**: JavaScript/TypeScript environment setup
- **`python_install_prompt.md`**: Python development environment setup
- **`README.md`**: How to use the review prompts

### Repository Extraction System (`prompts/`)
- **`repo_extract_prompt.md`**: AI agent specification for repository extraction

## 🛠️ Extensions Included

### AI & Collaboration
- **GitHub Copilot**: AI code suggestions and completions
- **GitHub Copilot Chat**: Interactive AI assistance
- **GitHub Pull Requests**: Integrated PR management
- **GitLens**: Enhanced Git capabilities

### Language Support
- **C# Dev Kit**: Complete C# development environment
- **TypeScript/JavaScript**: Enhanced language support
- **Python**: Comprehensive Python tooling with Pylance and Ruff

### Quality & Security
- **SonarLint**: Code quality and security analysis
- **CodeQL**: GitHub's semantic code analysis
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting

## 🔧 Automated Setup Scripts

This repository includes comprehensive setup scripts that automatically install and configure everything you need for multi-language development.

### Windows Setup (`scripts/install_all.windows.ps1`)
**Installs via Chocolatey:**
- **.NET SDK**: Latest version with all required workloads
- **Node.js**: LTS version with npm
- **Python**: Latest stable with pip and essential packages
- **Git**: With GitHub CLI and extensions
- **PowerShell**: Latest version with execution policy configuration
- **Visual Studio Code**: With recommended extensions auto-install

### macOS Setup (`scripts/install_all.macos.sh`)
**Installs via Homebrew:**
- **Xcode Command Line Tools**: For native compilation
- **Git & GitHub CLI**: With Copilot and dashboard extensions
- **.NET SDK**: Latest version
- **Node.js**: LTS version via nodenv
- **Python**: Latest version via pyenv with development tools
- **VS Code**: With settings sync

### Ubuntu Setup (`scripts/install_all.ubuntu.sh`)
**Installs via apt and official sources:**
- **Build essentials**: gcc, make, and development headers
- **.NET SDK**: Microsoft's official repository
- **Node.js**: NodeSource LTS repository
- **Python**: System python with pip, venv, and dev packages
- **Git & GitHub CLI**: Latest versions
- **VS Code**: Microsoft's official repository

### Running Setup Scripts
```powershell
# Windows (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\install_all.windows.ps1

# macOS
chmod +x ./scripts/install_all.macos.sh
./scripts/install_all.macos.sh

# Ubuntu/Debian
chmod +x ./scripts/install_all.ubuntu.sh
sudo ./scripts/install_all.ubuntu.sh
```

Each script is idempotent and can be run multiple times safely. They automatically detect existing installations and skip unnecessary steps.

## 🔧 Configuration Highlights

### Code Quality
- **Strict TypeScript** configuration with comprehensive type checking
- **ESLint 9+** flat config with modern rules
- **Prettier** integration for consistent formatting
- **EditorConfig** for cross-editor consistency

### C# Development
- **Warnings as errors** enforcement
- **Nullable reference types** enabled
- **Latest analysis level** with StyleCop and Roslyn analyzers
- **Code style enforcement** in build

### Python Development
- **Strict type checking** with Pylance
- **Ruff** for fast linting and formatting
- **Black** formatter integration
- **Pytest** configuration

### Security
- **SonarLint** connected mode for enterprise security scanning
- **Telemetry disabled** across all extensions
- **Copilot ignore** file to protect sensitive data

## 🤖 Using AI-Assisted Code Reviews

### Basic Usage
```bash
# In GitHub Copilot Chat or your AI assistant:
@copilot Review this pull request using the guidelines in .github/prompts/code-review.md

[Paste your code changes]
```

### Security Review
```bash
@copilot Perform a security review using .github/prompts/security-review.md

[Paste your code changes]
```

### Performance Review
```bash
@copilot Analyze performance implications using .github/prompts/performance-review.md

[Paste your code changes]
```

### Environment Setup Prompts
The repository includes specialized prompts for setting up development environments:

- **`.github/prompts/all_platforms_gh_prompt.md`**: Cross-platform GitHub CLI setup
- **`.github/prompts/dotnet_install_prompt.md`**: Complete .NET development environment
- **`.github/prompts/js_ts_install_prompt.md`**: JavaScript/TypeScript development setup
- **`.github/prompts/python_install_prompt.md`**: Python development environment

These can be used with AI assistants to automatically configure development environments on any platform.

## 📦 Repository Extraction

This setup includes powerful repository extraction tools to clone and analyze external GitHub repositories. This is useful for code reviews, learning from other projects, or migrating code between repositories.

### Quick Start

1. **Run via VS Code Task**:
   - Open Command Palette (`Ctrl+Shift+P`)
   - Type "Tasks: Run Task"
   - Select "repo:extract" (PowerShell) or "repo:extract-bash" (Bash)
   - Enter the GitHub repository URL
   - Enter comma-separated languages (e.g., `typescript,python`)

2. **Run via Command Line**:
   ```powershell
   # PowerShell (Windows)
   .\scripts\repo_extract.ps1 "https://github.com/owner/repo" "typescript,python"
   ```

   ```bash
   # Bash (Linux/macOS/WSL)
   ./scripts/repo_extract.sh "https://github.com/owner/repo" "typescript,python"
   ```

### Supported Languages

- **`python`** - Python files and ecosystem (pip, poetry, ruff, pytest configs)
- **`javascript`** / **`js`** - JavaScript files and tooling
- **`typescript`** / **`ts`** - TypeScript files and configurations
- **`csharp`** / **`cs`** / **`dotnet`** - C# files and .NET project structure
- **`go`** - Go files and modules
- **`java`** - Java files and build configurations
- **`rust`** - Rust files and Cargo configuration
- **`php`** - PHP files and Composer setup
- **`ruby`** - Ruby files and Gem configuration
- **`kotlin`** - Kotlin files and Gradle setup
- **`swift`** - Swift files and Package manager
- **`scala`** - Scala files and SBT configuration

### What Gets Extracted

#### For Each Language:
- **Source files** (`.py`, `.ts`, `.cs`, etc.)
- **Build configurations** (`package.json`, `*.csproj`, `Cargo.toml`)
- **Dependency manifests** (`requirements.txt`, `yarn.lock`, `go.mod`)
- **Linting/formatting configs** (ESLint, Prettier, Ruff, StyleCop)
- **Testing configurations** (Jest, Pytest, xUnit settings)

#### Shared Materials (Always Included):
- **Documentation** (`README*`, `LICENSE*`, `CONTRIBUTING*`)
- **CI/CD workflows** (`.github/workflows/**`)
- **Development containers** (`.devcontainer/**`, `Dockerfile*`)
- **Editor configuration** (`.vscode/**`, `.editorconfig`)

### Output Structure

```
project-docs/
├── _shared/           # Repository-wide documentation and CI
├── typescript/        # TypeScript-specific files and configs
├── python/           # Python-specific files and configs
└── csharp/           # C#-specific files and configs
```

Each language folder includes:
- **Extracted source code** matching the language
- **Related configuration files** (build, lint, test)
- **`README.md`** with extraction summary and next steps

### Caching

- Repositories are cached in `.repo_cache/<owner>__<repo>/`
- Subsequent extractions update the cache instead of re-cloning
- Cache persists across VS Code sessions for faster re-extraction

### Example Workflows

#### Learning from Popular Projects
```powershell
# Extract React's TypeScript patterns
.\scripts\repo_extract.ps1 "https://github.com/facebook/react" "typescript"

# Study Django's Python structure
.\scripts\repo_extract.ps1 "https://github.com/django/django" "python"

# Analyze ASP.NET Core patterns
.\scripts\repo_extract.ps1 "https://github.com/dotnet/aspnetcore" "csharp"
```

#### Multi-Language Analysis
```powershell
# Extract both frontend and backend from a full-stack repo
.\scripts\repo_extract.ps1 "https://github.com/owner/fullstack-app" "typescript,python,csharp"
```

#### Code Migration
```powershell
# Extract specific components for migration
.\scripts\repo_extract.ps1 "https://github.com/old-company/legacy-app" "javascript"
# Review extracted code in project-docs/javascript/
# Adapt and integrate into current project
```

### Integration with AI Reviews

After extraction, you can use the extracted code with AI-assisted reviews:

```bash
@copilot Review the extracted TypeScript code in project-docs/typescript/ using our coding standards from .github/prompts/code-review.md

# Analyze architecture patterns
@copilot Analyze the project structure in project-docs/_shared/ and suggest improvements for our current architecture

# Security assessment
@copilot Perform a security review of the extracted Python code using .github/prompts/security-review.md
```

## 📋 Customization Checklist

### Required Updates
- [ ] Update `dotnet.defaultSolution` in `.vscode/settings.json`
- [ ] Update project paths in `.vscode/launch.json`
- [ ] Configure SonarLint connection in `.vscode/settings.json`
- [ ] Add your enterprise NuGet feeds to `NuGet.config`
- [ ] Update Python virtual environment path if needed
- [ ] Run the appropriate setup script for your platform

### Optional Customizations
- [ ] Modify ESLint rules in `eslint.config.js`
- [ ] Adjust TypeScript compiler options in `tsconfig.json`
- [ ] Customize C# analyzer rules in `Directory.Build.props`
- [ ] Add project-specific VS Code tasks to `.vscode/tasks.json`
- [ ] Create custom AI review prompts in `.github/prompts/`
- [ ] Extend repository extraction patterns in scripts for additional languages
- [ ] Customize `.copilotignore` for your project's sensitive files

### Platform-Specific Setup
- [ ] **Windows**: Run `.\scripts\install_all.windows.ps1` as Administrator
- [ ] **macOS**: Run `./scripts/install_all.macos.sh` and install Xcode CLI tools
- [ ] **Ubuntu**: Run `sudo ./scripts/install_all.ubuntu.sh` for system packages

## 🚦 Quality Gates

This setup enforces several quality gates:

### Build-Time
- **TypeScript**: Strict type checking, no implicit any
- **C#**: Warnings as errors, nullable reference types
- **Python**: Type checking with mypy/pylance
- **Linting**: ESLint, Ruff, StyleCop enforcement

### Editor-Time
- **Format on save** with Prettier/Black
- **Organize imports** automatically
- **Fix all auto-fixable issues** on save
- **Real-time linting** feedback

### AI-Assisted
- **Code review prompts** for comprehensive analysis
- **Security checklists** for vulnerability assessment
- **Performance guidelines** for optimization

## 📚 Additional Resources

### Documentation
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [VS Code Extensions API](https://code.visualstudio.com/api)
- [ESLint Flat Config](https://eslint.org/docs/latest/use/configure/configuration-files)
- [SonarLint Connected Mode](https://docs.sonarsource.com/sonarlint/vs-code/team-features/connected-mode/)

### Best Practices
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [C# Coding Conventions](https://docs.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [Python PEP 8](https://peps.python.org/pep-0008/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

## 🤝 Contributing

This setup is actively maintained and designed to be shared across development teams. We welcome contributions!

### How to Contribute

1. **Fork this repository** on GitHub
2. **Create a feature branch** for your improvements
3. **Test your changes** across multiple platforms if possible
4. **Submit a pull request** with clear description of changes

### Types of Contributions Welcome

- **New language support** for repository extraction
- **Additional platform setup scripts** (e.g., Arch Linux, Alpine)
- **Enhanced AI review prompts** for specialized domains
- **VS Code extension recommendations** for emerging tools
- **Configuration improvements** for better development experience
- **Documentation updates** and examples

### Development Guidelines

- **Test setup scripts** in clean environments (containers/VMs recommended)
- **Follow existing patterns** for consistency
- **Update documentation** for any new features
- **Keep cross-platform compatibility** in mind

### Issues and Feedback

- **Report bugs** via GitHub Issues
- **Request features** with use case descriptions
- **Share success stories** of using this setup in your projects
- **Ask questions** in GitHub Discussions

## 🌟 Star This Repository

If this setup has been helpful for your development workflow, please consider starring the repository to help others discover it!

## 📄 License

This configuration setup is provided as-is for educational and professional use. Individual tools and extensions are subject to their respective licenses.
