# .NET/C# Development Setup

You are a local devops agent on my machine. Install and configure .NET/C# code review and quality tools.

## Tasks

1. Ensure .NET SDK 9.0+ is installed and available as `dotnet`.
2. Install global dotnet tools:
   - `dotnet-format` (code style/format)
   - `dotnet-reportgenerator-globaltool` (coverage reports)
   - `dotnet-outdated-tool` (dependency audit)
   - `dotnet-stryker` (mutation testing)
   - `dotnet-ef` (optional, for EF projects)
   - `dotnet-sonarscanner` (SonarQube/SonarCloud)
3. Create/ensure `Directory.Build.props` with:
   - `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`
   - `<AnalysisLevel>latest</AnalysisLevel>`
   - `<Nullable>enable</Nullable>`
   - Add `Microsoft.CodeAnalysis.NetAnalyzers` and `StyleCop.Analyzers` as PrivateAssets=all
4. Add solution-wide editorconfig enforcing errors for analyzers.
5. Generate a `tools-verify.ps1`/`.sh` that prints versions for all installed tools.
6. Install GitHub CLI and extensions:
   - `gh` + `gh extension install github/gh-copilot`
   - `gh extension install dlvhdr/gh-dash`

## Output

- `dotnet --info`, list of installed dotnet tools, and sample commands:
  - `dotnet format --verify-no-changes`
  - `dotnet test --collect:"XPlat Code Coverage"`
