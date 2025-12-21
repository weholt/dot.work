param(
    [Parameter(Mandatory = $true)][string]$RepoUrl,
    [Parameter(Mandatory = $true)][string]$LanguageCsv
)

$ErrorActionPreference = "Stop"

function ConvertTo-OwnerRepo([string]$url) {
    $u = $url.TrimEnd(".git")
    $u = $u -replace "^git@github.com:", ""
    $u = $u -replace "^https://github.com/", ""
    return $u
}

$Workspace = (Get-Location).Path
$CacheRoot = Join-Path $Workspace ".repo_cache"
New-Item -ItemType Directory -Force -Path $CacheRoot | Out-Null

# gh setup
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Warning "gh not found. Install GitHub CLI for best experience."
} else {
    if ($env:GH_TOKEN) {
        try { gh auth status | Out-Null } catch { Write-Output $env:GH_TOKEN | gh auth login --with-token }
        try { gh extension list | Select-String "gh-copilot" -Quiet | Out-Null } catch { gh extension install github/gh-copilot }
        try { gh extension list | Select-String "gh-dash" -Quiet | Out-Null } catch { gh extension install dlvhdr/gh-dash }
    }
}

$OwnerRepo = ConvertTo-OwnerRepo $RepoUrl
$SafeName = if ($OwnerRepo) { $OwnerRepo -replace "/", "__" } else { "repo_$((Get-Date).ToFileTime())" }
$CacheDir = Join-Path $CacheRoot $SafeName

# clone or update
if (-not (Test-Path (Join-Path $CacheDir ".git"))) {
    Write-Host "⏬ Cloning $RepoUrl -> $CacheDir"
    if ((Get-Command gh -ErrorAction SilentlyContinue) -and ($RepoUrl -match "github.com")) {
        gh repo clone $OwnerRepo $CacheDir -- --depth=1
    } else {
        git clone --depth=1 $RepoUrl $CacheDir
    }
} else {
    Write-Host "🔄 Updating cache at $CacheDir"
    git -C $CacheDir fetch --all --prune
    try {
        $defaultBranch = git -C $CacheDir symbolic-ref refs/remotes/origin/HEAD | ForEach-Object { $_ -replace "^refs/remotes/origin/", "" }
    } catch { $defaultBranch = "HEAD" }
    git -C $CacheDir reset --hard "origin/$defaultBranch" 2>$null
}

$OutRoot = Join-Path $Workspace "project-docs"
New-Item -ItemType Directory -Force -Path (Join-Path $OutRoot "_shared") | Out-Null

# Copy shared files using robocopy
$sharedPatterns = @("README*", "LICENSE*", "CONTRIBUTING*", "CODE_OF_CONDUCT*", "SECURITY*", "CHANGELOG*")
$sharedFiles = @(".editorconfig", ".gitattributes", ".gitignore", ".gitmodules")

foreach ($pattern in $sharedPatterns) {
    robocopy $CacheDir (Join-Path $OutRoot "_shared") $pattern /S /NFL /NDL /NJH /NJS /NC /NS /NP /XD ".git" "node_modules" "dist" "build" "coverage" ".venv" ".tox" "__pycache__" ".mypy_cache" ".pytest_cache" ".ruff_cache" ".idea" "bin" "obj" 2>$null | Out-Null
}

foreach ($file in $sharedFiles) {
    if (Test-Path (Join-Path $CacheDir $file)) {
        Copy-Item (Join-Path $CacheDir $file) (Join-Path $OutRoot "_shared") -Force -ErrorAction SilentlyContinue
    }
}

# Copy directories
$sharedDirs = @(".docker", ".devcontainer", ".vscode", ".github")
foreach ($dir in $sharedDirs) {
    $sourcePath = Join-Path $CacheDir $dir
    if (Test-Path $sourcePath) {
        robocopy $sourcePath (Join-Path $OutRoot "_shared" $dir) /E /NFL /NDL /NJH /NJS /NC /NS /NP 2>$null | Out-Null
    }
}

# Language include maps
$LangMap = @{
    "python" = @(
        "**/*.py", "pyproject.toml", "poetry.lock", "poetry.toml", "requirements*.txt",
        "Pipfile", "Pipfile.lock", "setup.py", "setup.cfg", "tox.ini", "noxfile.py",
        ".python-version", "ruff.toml", ".ruff.toml", ".flake8", ".pylintrc",
        "mypy.ini", ".mypy.ini", "bandit.yaml", "pytest.ini", "conftest.py"
    );
    "javascript" = @(
        "**/*.js", "**/*.jsx", "package.json", "package-lock.json", "pnpm-lock.yaml",
        "yarn.lock", "tsconfig*.json", "jsconfig*.json", "eslint.*", ".eslintrc*",
        ".prettierrc*", "prettier.*", "vitest.config.*", "jest.config.*",
        "babel.config.*", "webpack.*", "rollup.*", "vite.*", "turbo.*"
    );
    "typescript" = @(
        "**/*.ts", "**/*.tsx", "package.json", "package-lock.json", "pnpm-lock.yaml",
        "yarn.lock", "tsconfig*.json", "jsconfig*.json", "eslint.*", ".eslintrc*",
        ".prettierrc*", "prettier.*", "vitest.config.*", "jest.config.*",
        "babel.config.*", "webpack.*", "rollup.*", "vite.*", "turbo.*"
    );
    "csharp" = @(
        "**/*.cs", "**/*.csx", "**/*.razor", "**/*.cshtml", "*.sln", "*.csproj",
        "*.props", "*.targets", "Directory.Build.props", "Directory.Build.targets",
        "global.json", "NuGet.config", "appsettings*.json", "launchSettings.json",
        "stylecop.json", "ruleset*.json", ".editorconfig*"
    );
    "go" = @("**/*.go", "go.mod", "go.sum", ".golangci.yml", ".golangci.yaml", "Makefile*");
    "java" = @("**/*.java", "pom.xml", "build.gradle*", "gradle.properties", "settings.gradle*", "*.iml");
    "rust" = @("**/*.rs", "Cargo.toml", "Cargo.lock", "rust-toolchain*", "clippy.toml", ".rustfmt.toml");
    "php" = @("**/*.php", "composer.json", "composer.lock", "phpunit.xml*", ".psalm.xml*", "phpstan*.neon*");
    "ruby" = @("**/*.rb", "Gemfile", "Gemfile.lock", ".rubocop.yml", ".rspec");
    "kotlin" = @("**/*.kt", "**/*.kts", "build.gradle*", "settings.gradle*", "gradle.properties");
    "swift" = @("**/*.swift", "Package.swift", "Package.resolved");
    "scala" = @("**/*.scala", "build.sbt");
}

# Add aliases
$LangMap["cs"] = $LangMap["csharp"]
$LangMap["dotnet"] = $LangMap["csharp"]
$LangMap["js"] = $LangMap["javascript"]
$LangMap["ts"] = $LangMap["typescript"]

$Langs = $LanguageCsv.Split(",") | ForEach-Object { $_.Trim().ToLower() }

foreach ($lang in $Langs) {
    $outDir = Join-Path $OutRoot $lang
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $patterns = $LangMap[$lang]

    if (-not $patterns) {
        Write-Warning "Language '$lang' not supported. Skipping."
        continue
    }

    # Copy base files
    $basePatterns = @("README*", "LICENSE*", "CONTRIBUTING*", "CODE_OF_CONDUCT*", "SECURITY*", "CHANGELOG*")
    $baseFiles = @(".editorconfig", ".gitattributes", ".gitignore", ".gitmodules")

    foreach ($pattern in $basePatterns) {
        robocopy $CacheDir $outDir $pattern /NFL /NDL /NJH /NJS /NC /NS /NP /XD ".git" "node_modules" "dist" "build" "coverage" ".venv" ".tox" "__pycache__" ".mypy_cache" ".pytest_cache" ".ruff_cache" ".idea" "bin" "obj" 2>$null | Out-Null
    }

    foreach ($file in $baseFiles) {
        if (Test-Path (Join-Path $CacheDir $file)) {
            Copy-Item (Join-Path $CacheDir $file) $outDir -Force -ErrorAction SilentlyContinue
        }
    }

    # Copy language-specific patterns
    foreach ($pat in $patterns) {
        if ($pat.StartsWith("**/")) {
            # Handle recursive patterns
            $extension = $pat.Substring(3)
            Get-ChildItem -Path $CacheDir -Recurse -Include $extension -ErrorAction SilentlyContinue | ForEach-Object {
                $relativePath = $_.FullName.Substring($CacheDir.Length + 1)
                $targetPath = Join-Path $outDir $relativePath
                $targetDir = Split-Path $targetPath -Parent
                if (-not (Test-Path $targetDir)) {
                    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
                }
                Copy-Item $_.FullName $targetPath -Force -ErrorAction SilentlyContinue
            }
        } else {
            # Handle file patterns
            robocopy $CacheDir $outDir $pat /S /NFL /NDL /NJH /NJS /NC /NS /NP /XD ".git" "node_modules" "dist" "build" "coverage" ".venv" ".tox" "__pycache__" ".mypy_cache" ".pytest_cache" ".ruff_cache" ".idea" "bin" "obj" 2>$null | Out-Null
        }
    }

    # counts
    $files = Get-ChildItem -Path $outDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
    $codeFiles = Get-ChildItem -Path $outDir -Recurse -Include "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.cs", "*.go", "*.java", "*.rs", "*.php", "*.rb", "*.kt", "*.swift", "*.scala" -ErrorAction SilentlyContinue
    $loc = if ($codeFiles) { ($codeFiles | Get-Content -ErrorAction SilentlyContinue | Measure-Object -Line).Lines } else { 0 }

    # Create README
    @"
# Extracted Code Snapshot

* **Repository:** $OwnerRepo
* **Language:** $lang
* **Files:** $files
* **Total LOC (approx):** $loc

## Next Steps

### Python

``````bash
uv sync || pip install -r requirements.txt || true
ruff check .
pytest -q
``````

### JavaScript / TypeScript

``````bash
npm i
npm run lint && npm run typecheck && npm test
``````

### C# / .NET

``````bash
dotnet restore
dotnet build -warnaserror
dotnet test --collect:"XPlat Code Coverage"
dotnet format --verify-no-changes
``````

> Note: Only the relevant files and key project configs were copied to this snapshot. See ``project-docs/_shared`` for repo-wide docs, CI, and prompts.
"@ | Out-File -Encoding UTF8 (Join-Path $outDir "README.md")

    Write-Host "✅ Extracted $lang`: $outDir (files=$files, loc≈$loc)"
}

Write-Host "📦 Cache: $CacheDir"
Write-Host "📂 Shared materials: $(Join-Path $OutRoot "_shared")"
