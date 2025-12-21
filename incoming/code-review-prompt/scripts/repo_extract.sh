#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/repo_extract.sh <repo_url> <language_csv>
# Example: ./scripts/repo_extract.sh https://github.com/org/repo typescript,python

REPO_URL="${1:-}"
LANGS_CSV="${2:-}"

if [[ -z "$REPO_URL" || -z "$LANGS_CSV" ]]; then
    echo "Usage: $0 <repo_url> <language_csv>"
    exit 1
fi

WORKSPACE_ROOT="$(pwd)"
CACHE_ROOT="${WORKSPACE_ROOT}/.repo_cache"
mkdir -p "${CACHE_ROOT}"

# --- gh setup (optional) ---

if ! command -v gh >/dev/null 2>&1; then
    echo "⚠️  gh not found. Install GitHub CLI for best experience."
else
    if [[ -n "${GH_TOKEN:-}" ]]; then
        gh auth status >/dev/null 2>&1 || echo "$GH_TOKEN" | gh auth login --with-token
        gh extension list | grep -q gh-copilot || gh extension install github/gh-copilot || true
        gh extension list | grep -q gh-dash || gh extension install dlvhdr/gh-dash || true
    fi
fi

# --- derive local path ---

# Normalize "owner/repo" from URL
to_owner_repo() {
    local url="$1"
    url="${url%.git}"
    url="${url#git@github.com:}"
    url="${url#https://github.com/}"
    echo "$url"
}

OWNER_REPO="$(to_owner_repo "$REPO_URL" || true)"
SAFE_NAME="${OWNER_REPO//\//__}"
[[ -z "$SAFE_NAME" ]] && SAFE_NAME="repo_$(date +%s)"
CACHE_DIR="${CACHE_ROOT}/${SAFE_NAME}"

# --- clone or update ---

if [[ ! -d "${CACHE_DIR}/.git" ]]; then
    echo "⏬ Cloning ${REPO_URL} -> ${CACHE_DIR}"
    if command -v gh >/dev/null 2>&1 && [[ "$REPO_URL" == https://github.com/* || "$REPO_URL" == git@github.com:* ]]; then
        gh repo clone "${OWNER_REPO}" "${CACHE_DIR}" -- --depth=1
    else
        git clone --depth=1 "${REPO_URL}" "${CACHE_DIR}"
    fi
else
    echo "🔄 Updating cache at ${CACHE_DIR}"
    git -C "${CACHE_DIR}" fetch --all --prune

    # Try default branch; fall back to origin/HEAD
    DEFAULT_BRANCH="$(git -C "${CACHE_DIR}" symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@' || true)"
    [[ -z "$DEFAULT_BRANCH" ]] && DEFAULT_BRANCH="HEAD"
    git -C "${CACHE_DIR}" reset --hard "origin/${DEFAULT_BRANCH}" || git -C "${CACHE_DIR}" reset --hard origin/HEAD || true
fi

OUT_ROOT="${WORKSPACE_ROOT}/project-docs"
mkdir -p "${OUT_ROOT}/_shared"

# --- shared includes copied once ---

rsync -a --prune-empty-dirs \
    --include="/README*" \
    --include="/LICENSE*" \
    --include="/CONTRIBUTING*" \
    --include="/CODE_OF_CONDUCT*" \
    --include="/SECURITY*" \
    --include="/CHANGELOG*" \
    --include="/.editorconfig" \
    --include="/.gitattributes" \
    --include="/.gitignore" \
    --include="/.gitmodules" \
    --include="/Makefile*" \
    --include="/Dockerfile*" \
    --include="/docker-compose*.y*ml" \
    --include="/.docker/***" \
    --include="/.devcontainer/***" \
    --include="/.vscode/***" \
    --include="/.github/***" \
    --exclude="**/.git/**" \
    --exclude="**/node_modules/**" \
    --exclude="**/dist/**" \
    --exclude="**/build/**" \
    --exclude="**/coverage/**" \
    --exclude="**/.venv/**" \
    --exclude="**/.tox/**" \
    --exclude="**/__pycache__/**" \
    --exclude="**/.mypy_cache/**" \
    --exclude="**/.pytest_cache/**" \
    --exclude="**/.ruff_cache/**" \
    --exclude="**/.idea/**" \
    --exclude="**/bin/**" \
    --exclude="**/obj/**" \
    "${CACHE_DIR}/" "${OUT_ROOT}/_shared/" || true

# Helper: build rsync include list per language
add_includes_for_lang() {
    local lang="$1"
    case "$lang" in
        python)
            cat <<'PAT'
**/*.py
pyproject.toml
poetry.lock
poetry.toml
requirements*.txt
requirements/**/*.txt
Pipfile
Pipfile.lock
setup.py
setup.cfg
tox.ini
noxfile.py
.python-version
ruff.toml
.ruff.toml
.flake8
.pylintrc
mypy.ini
.mypy.ini
bandit.yaml
pytest.ini
conftest.py
PAT
            ;;
        javascript|js)
            cat <<'PAT'
**/*.js
**/*.jsx
package.json
package-lock.json
pnpm-lock.yaml
yarn.lock
tsconfig*.json
jsconfig*.json
eslint.*
.eslintrc*
.prettierrc*
prettier.*
vitest.config.*
jest.config.*
babel.config.*
webpack.*
rollup.*
vite.*
turbo.*
PAT
            ;;
        typescript|ts)
            cat <<'PAT'
**/*.ts
**/*.tsx
package.json
package-lock.json
pnpm-lock.yaml
yarn.lock
tsconfig*.json
jsconfig*.json
eslint.*
.eslintrc*
.prettierrc*
prettier.*
vitest.config.*
jest.config.*
babel.config.*
webpack.*
rollup.*
vite.*
turbo.*
PAT
            ;;
        csharp|cs|dotnet)
            cat <<'PAT'
**/*.cs
**/*.csx
**/*.razor
**/*.cshtml
*.sln
*.csproj
*.props
*.targets
Directory.Build.props
Directory.Build.targets
global.json
NuGet.config
appsettings*.json
launchSettings.json
stylecop.json
ruleset*.json
.editorconfig*
PAT
            ;;
        go)
            cat <<'PAT'
**/*.go
go.mod
go.sum
.golangci.yml
.golangci.yaml
Makefile*
PAT
            ;;
        java)
            cat <<'PAT'
**/*.java
pom.xml
build.gradle*
gradle.properties
settings.gradle*
*.iml
PAT
            ;;
        rust)
            cat <<'PAT'
**/*.rs
Cargo.toml
Cargo.lock
rust-toolchain*
clippy.toml
.rustfmt.toml
PAT
            ;;
        php)
            cat <<'PAT'
**/*.php
composer.json
composer.lock
phpunit.xml*
.psalm.xml*
phpstan*.neon*
PAT
            ;;
        ruby)
            cat <<'PAT'
**/*.rb
Gemfile
Gemfile.lock
.rubocop.yml
.rspec
PAT
            ;;
        kotlin)
            cat <<'PAT'
**/*.kt
**/*.kts
build.gradle*
settings.gradle*
gradle.properties
PAT
            ;;
        swift)
            cat <<'PAT'
**/*.swift
Package.swift
Package.resolved
.xcworkspace/**/*
.xcodeproj/**/*
PAT
            ;;
        scala)
            cat <<'PAT'
**/*.scala
build.sbt
project/**/*
PAT
            ;;
        *)
            ;;
    esac
}

# Iterate requested languages
IFS=',' read -r -a LANGS <<< "$LANGS_CSV"

for RAW_LANG in "${LANGS[@]}"; do
    LANG="$(echo "$RAW_LANG" | tr '[:upper:]' '[:lower:]' | sed 's/^[ \t]*//;s/[ \t]*$//')"
    OUT_DIR="${OUT_ROOT}/${LANG}"
    mkdir -p "${OUT_DIR}"

    # build a temporary include file
    INC_FILE="$(mktemp)"

    # Always include shared top-level docs for context in each language folder
    cat <<'BASE' > "$INC_FILE"
README*
LICENSE*
CONTRIBUTING*
CODE_OF_CONDUCT*
SECURITY*
CHANGELOG*
.editorconfig
.gitattributes
.gitignore
.gitmodules
Makefile*
Dockerfile*
docker-compose*.y*ml
.github/***
.vscode/***
.devcontainer/***
BASE
    add_includes_for_lang "$LANG" >> "$INC_FILE"

    # rsync with include list
    RSYNC_FILTERS=()
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        RSYNC_FILTERS+=("--include=$line")
    done < "$INC_FILE"
    RSYNC_FILTERS+=(
        "--exclude=**/.git/**"
        "--exclude=**/node_modules/**"
        "--exclude=**/dist/**"
        "--exclude=**/build/**"
        "--exclude=**/coverage/**"
        "--exclude=**/.venv/**"
        "--exclude=**/.tox/**"
        "--exclude=**/__pycache__/**"
        "--exclude=**/.mypy_cache/**"
        "--exclude=**/.pytest_cache/**"
        "--exclude=**/.ruff_cache/**"
        "--exclude=**/.idea/**"
        "--exclude=**/bin/**"
        "--exclude=**/obj/**"
    )

    rsync -a --prune-empty-dirs "${RSYNC_FILTERS[@]}" "${CACHE_DIR}/" "${OUT_DIR}/" || true
    rm -f "$INC_FILE"

    # counts
    FILE_COUNT="$(find "${OUT_DIR}" -type f ! -path '*/.git/*' | wc -l | tr -d ' ')"
    LINE_COUNT="$((find "${OUT_DIR}" -type f -name '*.py' -o -name '*.js' -o -name '*.jsx' -o -name '*.ts' -o -name '*.tsx' -o -name '*.cs' -o -name '*.go' -o -name '*.java' -o -name '*.rs' -o -name '*.php' -o -name '*.rb' -o -name '*.kt' -o -name '*.swift' -o -name '*.scala' | xargs -r wc -l | awk 'END{print $1}') 2>/dev/null || echo 0)"

    # README
    cat > "${OUT_DIR}/README.md" <<MD

# Extracted Code Snapshot

* **Repository:** ${OWNER_REPO:-${REPO_URL}}
* **Language:** ${LANG}
* **Files:** ${FILE_COUNT}
* **Total LOC (approx):** ${LINE_COUNT}

## Next Steps

### Python

\`\`\`bash
uv sync || pip install -r requirements.txt || true
ruff check .
pytest -q
\`\`\`

### JavaScript / TypeScript

\`\`\`bash
npm i
npm run lint && npm run typecheck && npm test
\`\`\`

### C# / .NET

\`\`\`bash
dotnet restore
dotnet build -warnaserror
dotnet test --collect:"XPlat Code Coverage"
dotnet format --verify-no-changes
\`\`\`

> Note: Only the relevant files and key project configs were copied to this snapshot. See \`project-docs/_shared\` for repo-wide docs, CI, and prompts.
MD

    echo "✅ Extracted ${LANG}: ${OUT_DIR} (files=${FILE_COUNT}, loc≈${LINE_COUNT})"
done

echo "📦 Cache: ${CACHE_DIR}"
echo "📂 Shared materials: ${OUT_ROOT}/_shared"
