# Backlog: Docker & Containerization

Docker/OpenCode container features for containerized development environments.

Issues: FEAT-025, FEAT-026, FEAT-027, FEAT-028
Split from: backlog.md
Created: 2026-01-01

---
id: "FEAT-025@c9d5e1"
title: "Docker image provisioning with OpenCode webui and dynamic port assignment"
description: "Create containerized OpenCode environment with pre-registered providers, safe credential handling, dynamic ports, and optional GitHub repo cloning"
created: 2025-12-30
section: "container/docker"
tags: [feature, docker, containerization, opencode, webui, security, dynamic-ports]
type: enhancement
priority: high
status: proposed
references:
  - README.md
  - src/dot_work/container/
---

### Problem
Developers need a self-contained OpenCode environment that:
1. Runs as a Docker container with webui accessible
2. Has providers pre-registered without exposing credentials in image
3. Uses dynamic port assignment to avoid conflicts
4. Optionally clones a GitHub repo on startup
5. Is secure and reusable across sessions

Current approach requires manual setup of providers, fixed port allocation, and lacks easy container distribution.

### Affected Files
- NEW: `src/dot_work/container/opencode/Dockerfile`
- NEW: `src/dot_work/container/opencode/docker-compose.yml`
- NEW: `src/dot_work/container/opencode/entrypoint.sh`
- NEW: `src/dot_work/container/opencode/.env.example`
- NEW: `src/dot_work/container/opencode/README.md`
- `src/dot_work/container/__init__.py` (add opencode commands)
- `src/dot_work/cli.py` (add container opencode subcommand)

### Importance
**HIGH**: Containerized OpenCode enables:
- Zero-setup environment for new contributors
- Consistent development environments across teams
- Safe credential management (never baked into images)
- Easy distribution of pre-configured OpenCode setups
- Dynamic port assignment prevents conflicts on shared hosts
- Rapid onboarding for new projects via repo cloning

### Proposed Solution

**Phase 1: Docker Infrastructure (2-3 days)**
1. `Dockerfile`:
   - Base: `python:3.11-slim` or official opencode base image if available
   - Install OpenCode via pip/uv from PyPI or from local wheel
   - Copy entrypoint script
   - Set up working directory `/workspace`
   - Expose range of ports (e.g., 8000-9000) for dynamic assignment
   - Configure user permissions (non-root)
   - Add git for repo cloning

2. `entrypoint.sh`:
   - Parse environment variables for provider credentials
   - Dynamically select available port from range (e.g., 8000-9000)
   - Start OpenCode webui with selected port
   - If `GITHUB_REPO_URL` set, clone repo to `/workspace`
   - Health check on startup
   - Graceful shutdown handling

3. `docker-compose.yml`:
   - Service definition for opencode container
   - Volume mounts for workspace persistence
   - Environment variable template
   - Port mapping (dynamic via `--publish` or `8000-9000:8000-9000`)
   - Restart policy (unless-stopped)

**Phase 2: Provider Configuration (2 days)**
1. Provider registration strategy:
   - Create `providers.yaml` template in image
   - Configure provider metadata (name, base_url, models) without secrets
   - Use environment variables for API keys:
     - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
   - Entrypoint reads env vars and injects into OpenCode config
   - Never bake credentials into image layers

2. Config generation in entrypoint:
   ```bash
   # Example: Write OpenCode config file
   cat > ~/.config/opencode/config.yaml <<EOF
   providers:
     openai:
       base_url: https://api.openai.com/v1
       api_key: ${OPENAI_API_KEY}
     anthropic:
       base_url: https://api.anthropic.com
       api_key: ${ANTHROPIC_API_KEY}
   EOF
   ```

3. Validation:
   - Warn if no API keys provided (webui will prompt)
   - Validate API key format before starting
   - Support provider enable/disable via env vars

**Phase 3: Dynamic Port Assignment (1-2 days)**
1. Port selection logic in entrypoint:
   ```bash
   # Find available port in range
   PORT=8000
   while [ $PORT -le 9000 ]; do
     if ! nc -z localhost $PORT 2>/dev/null; then
       break
     fi
     PORT=$((PORT + 1))
   done

   if [ $PORT -gt 9000 ]; then
     echo "Error: No available ports in range 8000-9000"
     exit 1
   fi

   echo "Using port: $PORT" > /tmp/port.txt
   ```

2. Port publishing options:
   - Option A: Publish entire range `docker run -p 8000-9000:8000-9000`
   - Option B: Publish single dynamic port via docker-compose
   - Option C: Use host port specified via `PORT` env var

3. Output port info:
   - Log assigned port to stdout
   - Write port to `/tmp/port.txt` for scripts to read
   - Provide URL: `http://localhost:<PORT>`

**Phase 4: GitHub Repo Cloning (1 day)**
1. Repo cloning in entrypoint:
   ```bash
   if [ -n "$GITHUB_REPO_URL" ]; then
     echo "Cloning repository: $GITHUB_REPO_URL"
     git clone "$GITHUB_REPO_URL" /workspace/repo
     cd /workspace/repo

     if [ -n "$GITHUB_REPO_BRANCH" ]; then
       git checkout "$GITHUB_REPO_BRANCH"
     fi

     # Set as working directory for OpenCode
     ln -sf /workspace/repo /workspace/project
   fi
   ```

2. Authentication options:
   - Public repos: no auth required
   - Private repos: support `GITHUB_TOKEN` env var
   - SSH-based: support `GIT_SSH_COMMAND` or mount SSH keys

3. Environment variables:
   - `GITHUB_REPO_URL`: URL to clone (required for cloning)
   - `GITHUB_REPO_BRANCH`: Branch/commit to checkout (optional)
   - `GITHUB_TOKEN`: Personal access token for private repos

**Phase 5: CLI Integration (1-2 days)**
Add `dot-work container opencode` commands:
```bash
dot-work container opencode build [--tag TAG]           # Build Docker image
dot-work container opencode run [OPTIONS]              # Start container
dot-work container opencode stop [CONTAINER]           # Stop container
dot-work container opencode logs [CONTAINER]           # View logs
dot-work container opencode shell [CONTAINER]          # Open shell in container
```

Run command options:
- `--provider PROVIDER:KEY`: Set provider API key (repeatable)
- `--repo URL`: GitHub repo URL to clone
- `--branch BRANCH`: Branch to checkout
- `--port PORT`: Specific port (overrides dynamic)
- `--volume HOST:CONTAINER`: Additional volume mount
- `--env KEY=VALUE`: Additional environment variables
- `--detach`: Run in background
- `--rm`: Remove container on exit

**Phase 6: Documentation (1 day)**
1. `container/opencode/README.md`:
   - Prerequisites (Docker, Docker Compose)
   - Quick start examples
   - Provider configuration guide
   - GitHub repo cloning guide
   - Troubleshooting common issues
   - Security best practices

2. Examples in README:
   ```bash
   # Basic usage
   dot-work container opencode run

   # With provider keys
   dot-work container opencode run \
     --provider openai:$OPENAI_API_KEY \
     --provider anthropic:$ANTHROPIC_API_KEY

   # Clone GitHub repo
   dot-work container opencode run \
     --repo https://github.com/user/repo

   # Detached mode
   dot-work container opencode run --detach

   # Check logs
   dot-work container opencode logs <container-id>

   # Get assigned port
   docker exec <container-id> cat /tmp/port.txt
   ```

**Phase 7: Security Hardening (1-2 days)**
1. Container security:
   - Run as non-root user
   - Read-only root filesystem (except necessary paths)
   - Drop capabilities (--cap-drop ALL)
   - Use seccomp profiles if available
   - No privileged mode

2. Credential handling:
   - Never log API keys
   - Use Docker secrets or env files for sensitive data
   - Support credential injection via volumes
   - Clear credentials from environment in child processes

3. Network security:
   - Bind to localhost only by default
   - Support `--host 0.0.0.0` for external access with warning
   - Rate limiting suggestions for webui

**Phase 8: Testing (2-3 days)**
1. Unit tests:
   - Port selection logic
   - Provider config generation
   - Repo cloning with various auth methods
   - Entrypoint script validation

2. Integration tests:
   - Build image from Dockerfile
   - Start container and verify webui accessible
   - Test dynamic port assignment
   - Test provider registration with real keys (test only)
   - Test GitHub repo cloning (public and private)
   - Test volume persistence

3. Security tests:
   - Verify no credentials in image layers
   - Verify non-root user
   - Verify read-only paths

### Acceptance Criteria
- [ ] Dockerfile builds successfully
- [ ] Container starts OpenCode webui on dynamic port
- [ ] Provider registration works without hardcoding credentials
- [ ] GitHub repo cloning works with public URLs
- [ ] GitHub repo cloning works with private repos via token
- [ ] Port assignment is dynamic and conflict-free
- [ ] CLI commands: build, run, stop, logs, shell
- [ ] Security: no credentials in image, non-root user
- [ ] Documentation with examples
- [ ] Unit tests for port selection, config gen, cloning
- [ ] Integration tests for container lifecycle
- [ ] .env.example with all supported environment variables

### Notes
- Consider supporting OpenCode webui configuration via env vars (model, temperature, etc.)
- Future: Support MCP server configuration in container
- Future: Support hot-reload of provider credentials without restart
- Future: Multi-container setup with database for persistence
- Consider using Docker secrets for production deployments
- Dynamic port range should be configurable via env var

---
id: "FEAT-026@d0e6f2"
title: "Context and file injection for Dockerized OpenCode containers"
description: "Add support for injecting additional context, files, documentation, and configuration into OpenCode containers at runtime or build time"
created: 2025-12-30
section: "container/docker/context"
tags: [feature, docker, containerization, opencode, context-injection, volumes, configuration]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/backlog.md:FEAT-025@c9d5e1
  - README.md
  - src/dot_work/container/
---

### Problem
After provisioning an OpenCode container (FEAT-025), users need a way to:
1. Add project-specific documentation and context
2. Inject configuration files for tools/providers
3. Supply custom prompts, templates, or skills
4. Load knowledge graph databases or indexes
5. Attach multiple codebases or reference materials
6. Provide working examples or test data

The base Docker image only provides OpenCode itself. Users need flexible mechanisms to add context without rebuilding the image.

### Affected Files
- NEW: `src/dot_work/container/opencode/context-injector.py` (utility script)
- NEW: `src/dot_work/container/opencode/context-layout.md` (directory structure reference)
- MODIFIED: `src/dot_work/container/opencode/entrypoint.sh` (add context loading)
- MODIFIED: `src/dot_work/container/opencode/.env.example` (add context variables)
- MODIFIED: `src/dot_work/container/opencode/README.md` (add context examples)
- `src/dot_work/cli.py` (extend container opencode commands)

### Importance
**MEDIUM**: Context injection enables:
- Tailored OpenCode environments for specific projects
- Pre-loaded knowledge and reference materials
- Multi-repo workspaces
- Consistent context across team containers
- Faster onboarding with pre-baked context
- Template/boilerplate distribution

### Proposed Solution

**Phase 1: Context Directory Structure (1-2 days)**
Define standard context layout in container:
```
/workspace/context/
├── docs/              # Documentation files (.md, .txt, .pdf)
├── prompts/           # Canonical prompt files
├── skills/            # Agent skills directories
├── configs/           # Configuration files (.yaml, .json, .toml)
├── data/              # Data files (CSV, JSON, databases)
├── repos/             # Additional git repositories
├── templates/         # Code templates or snippets
└── manifest.yaml      # Context metadata and loading order
```

`manifest.yaml` format:
```yaml
version: "1.0"
name: "Project Context"
description: "Context for XYZ project"

docs:
  - path: "docs/api-guide.md"
    description: "API documentation"
  - path: "docs/architecture.md"
    description: "System architecture"

prompts:
  - path: "prompts/code-review.md"
    name: "code-review"

configs:
  - path: "configs/providers.yaml"
    target: "~/.config/opencode/providers.yaml"

repos:
  - url: "https://github.com/example/reference-impl"
    path: "repos/reference-impl"
    branch: "main"
```

**Phase 2: Build-Time Context Injection (1-2 days)**
Add `dot-work container opencode build` enhancements:

1. `--context-dir DIR` flag:
   - Copy entire directory to `/workspace/context/`
   - Run context validation
   - Bake context into image layers

2. `--context-file FILE` flag (repeatable):
   - Copy specific files to `/workspace/context/`
   - Auto-detect type based on extension/location

3. `--context-url URL` flag (repeatable):
   - Download file from URL to context directory
   - Support HTTP/HTTPS and raw GitHub URLs

4. `--context-manifest FILE` flag:
   - Load manifest.yaml and follow instructions
   - Clone repos, copy files, apply configs

Examples:
```bash
# Build with context directory
dot-work container opencode build \
  --context-dir ./project-context \
  --tag opencode:my-project

# Build with specific files
dot-work container opencode build \
  --context-file ./docs/api.md \
  --context-file ./prompts/review.md \
  --tag opencode:with-docs

# Build with manifest
dot-work container opencode build \
  --context-manifest ./context-manifest.yaml \
  --tag opencode:full-context

# Build with URL
dot-work container opencode build \
  --context-url https://raw.githubusercontent.com/org/repo/main/docs/spec.md \
  --tag opencode:remote-context
```

**Phase 3: Runtime Context Injection (2-3 days)**
Add `dot-work container opencode run` enhancements:

1. `--context-volume HOST:CONTAINER` flag (repeatable):
   - Mount host directories as read-only volumes
   - Auto-detect context structure

2. `--context-file FILE:DEST` flag (repeatable):
   - Copy files from host to container on startup
   - Use entrypoint script for copying

3. `--context-git URL` flag (repeatable):
   - Clone additional git repos on container startup
   - Support `URL[:DEST[:BRANCH]]` format

4. `--context-archive FILE` flag:
   - Extract tar/zip archive to `/workspace/context/`
   - Support `.tar`, `.tar.gz`, `.zip`

Examples:
```bash
# Run with context volume
dot-work container opencode run \
  --context-volume ./docs:/workspace/context/docs \
  --context-volume ./prompts:/workspace/context/prompts

# Run with file copy
dot-work container opencode run \
  --context-file ./config.yaml:/workspace/context/configs/config.yaml

# Run with additional repo
dot-work container opencode run \
  --context-git https://github.com/example/reference:/workspace/context/repos/ref

# Run with context archive
dot-work container opencode run \
  --context-archive ./context.tar.gz
```

**Phase 4: Context Loading Logic in Entrypoint (1-2 days)**
Extend `entrypoint.sh` to handle context:

1. Context directory setup:
   ```bash
   # Ensure context directory exists
   mkdir -p /workspace/context/{docs,prompts,skills,configs,data,repos,templates}

   # Load manifest if present
   if [ -f /workspace/context/manifest.yaml ]; then
     echo "Loading context manifest..."
     python3 /usr/local/bin/context-injector.py load \
       --manifest /workspace/context/manifest.yaml
   fi
   ```

2. Repo cloning from manifest:
   ```python
   # context-injector.py
   import yaml
   import subprocess

   def load_manifest(manifest_path):
     with open(manifest_path) as f:
       manifest = yaml.safe_load(f)

     for repo in manifest.get('repos', []):
       subprocess.run(['git', 'clone', '-b', repo['branch'],
                       repo['url'], repo['path']])

     for config in manifest.get('configs', []):
       subprocess.run(['cp', config['path'], config['target']])
   ```

3. Integration with OpenCode:
   - Copy prompts to `.work/prompts/`
   - Copy skills to `.skills/`
   - Load configs into OpenCode config dir
   - Index documentation files (optional)

**Phase 5: Context Management CLI (1-2 days)**
Add context-specific commands:

```bash
# List context in running container
dot-work container opencode context list [CONTAINER]

# Show context manifest
dot-work container opencode context show [CONTAINER]

# Add context to running container
dot-work container opencode context add CONTAINER \
  --file ./new-doc.md \
  --git https://github.com/example/repo

# Export context from container
dot-work container opencode context export CONTAINER \
  --output context-export.tar.gz

# Validate context directory
dot-work container opencode context validate [--dir DIR]
```

**Phase 6: Context Packaging and Distribution (1-2 days)**
1. Create context packages:
   - `dot-work container opencode context package DIR output.context`
   - Includes manifest and all referenced files
   - Compressed tarball with metadata

2. Context registry (simple file-based):
   ```bash
   # List available contexts
   dot-work container context list-registry

   # Download and apply context
   dot-work container opencode run \
     --context-registry my-project-context
   ```

3. Shareable context examples:
   - `web-dev.context` - Web development prompts and templates
   - `python-backend.context` - Python backend patterns
   - `ml-project.context` - ML/DS specific prompts and docs
   - `api-design.context` - API design guidelines

**Phase 7: Documentation (1 day)**
1. `container/opencode/context-layout.md`:
   - Directory structure reference
   - Manifest schema reference
   - Best practices for organizing context

2. Extend `container/opencode/README.md`:
   - Context injection examples
   - Build-time vs runtime comparison
   - Context package creation guide
   - Common use cases (multi-repo, docs, templates)

Examples in README:
```bash
# Quick start: Build with context
mkdir my-context
echo "# Project Docs" > my-context/docs/overview.md
dot-work container opencode build --context-dir my-context

# Multi-repo workspace
dot-work container opencode run \
  --context-git https://github.com/user/frontend:/workspace/context/frontend \
  --context-git https://github.com/user/backend:/workspace/context/backend

# Add prompts to existing container
dot-work container opencode context add my-container \
  --file ./prompts/code-review.md

# Export context for sharing
dot-work container opencode context export my-container \
  --output team-context.context

# Validate context before build
dot-work container opencode context validate --dir ./project-context
```

**Phase 8: Testing (2-3 days)**
1. Unit tests:
   - Manifest parsing and validation
   - Context loading logic
   - File copying and repo cloning
   - Archive extraction

2. Integration tests:
   - Build image with context directory
   - Verify files are in container
   - Test runtime context injection
   - Test context export/import
   - Test multi-repo cloning

3. Edge case tests:
   - Invalid manifest formats
   - Missing files in manifest
   - Git clone failures
   - Permission issues
   - Large file handling

### Acceptance Criteria
- [ ] Context directory structure defined and documented
- [ ] `manifest.yaml` schema with validation
- [ ] Build-time context injection: `--context-dir`, `--context-file`, `--context-url`, `--context-manifest`
- [ ] Runtime context injection: `--context-volume`, `--context-file`, `--context-git`, `--context-archive`
- [ ] Entrypoint loads context and applies manifest
- [ ] Context management CLI: list, show, add, export, validate
- [ ] Context packaging: create and distribute `.context` files
- [ ] Documentation: context-layout.md, extended README
- [ ] Integration with prompts, skills, configs
- [ ] Unit tests for context loading and validation
- [ ] Integration tests for build and runtime injection

### Notes
- Context should be optional (container works without it)
- Consider supporting context hot-reload (via webui or signal)
- Future: Context versioning and dependency management
- Future: Context inheritance (base context + overrides)
- Future: Integration with knowledge graph ingestion
- Future: Remote context URLs with authentication
- Consider context size limits and optimization
- Security: Validate file paths (no path traversal attacks)

---
id: "FEAT-027@e1f7g3"
title: "Runtime URL-based context injection for OpenCode containers"
description: "Add support for injecting context files, directories, and archives from remote URLs into running containers"
created: 2025-12-30
section: "container/docker/context"
tags: [feature, docker, containerization, opencode, context-injection, urls, remote-content]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/backlog.md:FEAT-026@d0e6f2
  - README.md
  - src/dot_work/container/
---

### Problem
FEAT-026 adds build-time URL context injection, but runtime containers also need to:
1. Fetch updated documentation from remote URLs
2. Pull latest configuration files from internal servers
3. Download context archives from CI/CD pipelines
4. Fetch prompts/skills from shared repositories
5. Update context without rebuilding or restarting container

Runtime URL injection enables live updates to container context without rebuilding images.

### Affected Files
- MODIFIED: `src/dot_work/container/opencode/entrypoint.sh` (add URL download logic)
- MODIFIED: `src/dot_work/container/opencode/.env.example` (add URL env vars)
- MODIFIED: `src/dot_work/cli.py` (add --context-url to run command)
- NEW: `src/dot_work/container/opencode/url-downloader.py` (downloader utility)
- MODIFIED: `src/dot_work/container/opencode/README.md` (add URL examples)

### Importance
**MEDIUM**: Runtime URL injection enables:
- Live context updates without container restart
- CI/CD integration (inject build artifacts, test results)
- Centralized context management (fetch from shared servers)
- Dynamic prompt/skill distribution
- Zero-downtime context refresh
- Multi-environment consistency (dev/stage/prod from same source)

### Proposed Solution

**Phase 1: URL Download Utility (1-2 days)**
Create `url-downloader.py` script:

1. Supported URL schemes:
   - HTTP/HTTPS: `https://example.com/file.txt`
   - Raw GitHub: `gh://org/repo/path/file.md`
   - GitLab: `gl://org/project/path/file.md`
   - S3: `s3://bucket/path/file.txt` (optional, with boto3)
   - Local file: `file:///path/to/file`

2. Download with validation:
   ```python
   def download_url(url, dest_dir, validate=True):
     """Download URL to destination directory."""
     parsed = urlparse(url)

     if parsed.scheme in ('http', 'https'):
       return download_http(url, dest_dir)
     elif parsed.netloc == 'github.com' or url.startswith('gh://'):
       return download_github(url, dest_dir)
     elif parsed.scheme == 'file':
       return copy_local(url, dest_dir)
     else:
       raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
   ```

3. Validation options:
   - File size limits (e.g., max 100MB)
   - Content type validation (e.g., only text/markdown)
   - Checksum verification (SHA256)
   - SSL certificate validation for HTTPS
   - Auth token injection from env vars

**Phase 2: Runtime URL CLI Flags (1 day)**
Add `--context-url` to `dot-work container opencode run`:

```bash
# Download single file
dot-work container opencode run \
  --context-url https://example.com/api-spec.md \
  --context-dest docs/

# Download manifest from URL
dot-work container opencode run \
  --context-url https://raw.githubusercontent.com/org/repo/main/context.yaml \
  --context-type manifest

# Download archive from URL
dot-work container opencode run \
  --context-url https://releases.example.com/context.tar.gz \
  --context-type archive

# Multiple URLs
dot-work container opencode run \
  --context-url https://example.com/docs/api.md \
  --context-url https://example.com/configs/providers.yaml \
  --context-url gh://org/skills/code-review
```

URL formats:
- `--context-url URL[:DEST][:TYPE]`
  - `URL`: Source URL
  - `DEST`: Destination in context (default: auto-detect)
  - `TYPE`: File type (manifest, archive, file, dir) (default: auto-detect)

**Phase 3: Entrypoint URL Handling (1-2 days)**
Extend `entrypoint.sh` to download URLs on startup:

```bash
# Download context URLs
if [ -n "$CONTEXT_URLS" ]; then
  echo "Downloading context URLs..."
  IFS=';' read -ra URLS <<< "$CONTEXT_URLS"
  for url_spec in "${URLS[@]}"; do
    python3 /usr/local/bin/url-downloader.py download \
      --url "$url_spec" \
      --dest /workspace/context
  done
fi
```

Environment variables:
- `CONTEXT_URLS`: Semicolon-separated URL specs
- `CONTEXT_URL_TIMEOUT`: Download timeout (default: 30s)
- `CONTEXT_URL_MAX_SIZE`: Max file size (default: 100MB)
- `GITHUB_TOKEN`: For private GitHub repos
- `HTTP_AUTH_TOKEN`: Generic HTTP auth token

**Phase 4: Runtime Context Update Command (1-2 days)**
Add CLI command to update context in running container:

```bash
# Update context from URLs
dot-work container opencode context update CONTAINER \
  --url https://example.com/docs/api.md \
  --url https://example.com/config.yaml

# Update from manifest URL
dot-work container opencode context update CONTAINER \
  --manifest-url https://raw.githubusercontent.com/org/repo/main/context.yaml

# Update with force (overwrite existing files)
dot-work container opencode context update CONTAINER \
  --url https://example.com/docs/new.md \
  --force

# Dry run (preview changes)
dot-work container opencode context update CONTAINER \
  --url https://example.com/docs/updated.md \
  --dry-run
```

Update workflow:
1. Download files to temporary location
2. Validate and verify checksums
3. Show diff vs existing files
4. Apply changes (unless dry-run)
5. Trigger OpenCode context reload (if supported)

**Phase 5: URL Authentication Support (1 day)**
Support authenticated URLs:

1. GitHub tokens:
   - Use `GITHUB_TOKEN` env var
   - Inject into GitHub raw content URLs
   - Support private repos

2. HTTP auth:
   - Use `HTTP_AUTH_TOKEN` env var
   - Basic auth via `HTTP_AUTH_USER:HTTP_AUTH_PASS`
   - Bearer token via `HTTP_AUTH_BEARER`

3. Custom headers:
   - `CONTEXT_URL_HEADERS: Authorization=Bearer token,X-Custom=value`
   - Inject into HTTP requests

4. SSH keys for git URLs:
   - Mount SSH key into container
   - Use for git-based URLs (gh://, gl://)

**Phase 6: URL Caching and Versioning (1-2 days)**
Implement caching to avoid redundant downloads:

1. Cache directory:
   - `/workspace/context/.cache/`
   - Store downloaded files by URL hash
   - Cache TTL (configurable via env var)

2. Versioning support:
   ```yaml
   # URL in manifest with version
   urls:
     - url: https://example.com/docs/api-v2.md
       version: "2.1.0"
       checksum: "sha256:abc123..."
       cache_ttl: 3600  # 1 hour
   ```

3. Conditional download:
   - Check if cached file exists
   - Verify checksum matches
   - Skip download if valid and within TTL

**Phase 7: URL Monitoring and Auto-Refresh (2-3 days)**
Optional background monitoring:

1. Watch mode:
   ```bash
   dot-work container opencode context watch CONTAINER \
     --url https://example.com/docs/api.md \
     --interval 300  # check every 5 minutes
   ```

2. Webhook support:
   - Expose endpoint for webhook notifications
   - Trigger context update on webhook call
   - Support GitHub webhooks, CI/CD pipelines

3. Inotify integration:
   - Monitor downloaded files for changes
   - Trigger OpenCode context reload on change

**Phase 8: Documentation and Examples (1 day)**
Extend `container/opencode/README.md`:

```bash
# Quick examples
## Download single file
dot-work container opencode run \
  --context-url https://example.com/api-spec.md

## Download from GitHub
dot-work container opencode run \
  --context-url gh://org/repo/docs/architecture.md

## Download manifest
dot-work container opencode run \
  --context-url https://raw.githubusercontent.com/org/repo/main/context.yaml \
  --context-type manifest

## Multiple URLs with auth
export GITHUB_TOKEN=ghp_xxx
dot-work container opencode run \
  --context-url https://raw.githubusercontent.com/org/repo/main/docs/api.md \
  --context-url https://raw.githubusercontent.com/org/repo/main/configs/providers.yaml

## Update running container
dot-work container opencode context update my-container \
  --url https://example.com/docs/updated-api.md

## Watch for updates
dot-work container opencode context watch my-container \
  --url https://example.com/docs/api.md \
  --interval 600
```

### Acceptance Criteria
- [ ] `url-downloader.py` supports HTTP/HTTPS, GitHub, GitLab URLs
- [ ] Runtime `--context-url` flag works in run command
- [ ] Entrypoint downloads URLs on startup
- [ ] `dot-work container opencode context update` command works
- [ ] URL authentication via env vars (GitHub token, HTTP auth)
- [ ] URL caching with TTL support
- [ ] Dry-run mode for updates
- [ ] Documentation with examples
- [ ] Unit tests for download, validation, caching
- [ ] Integration tests for runtime URL injection
- [ ] Error handling for network failures, invalid URLs, auth failures

### Notes
- URL downloads should be optional (container works without URLs)
- Security: Validate URLs (no SSRF attacks), limit file sizes
- Consider rate limiting for frequent downloads
- Future: Support custom URL handlers via plugins
- Future: URL signing and verification
- Future: Proxy support for corporate environments
- Monitor download sizes to prevent disk exhaustion

---
id: "FEAT-028@f2g8h4"
title: "File upload/download utilities for OpenCode containers"
description: "Add optional file transfer utilities for easy uploading and downloading files to and from running containers"
created: 2025-12-30
section: "container/docker/file-transfer"
tags: [feature, docker, containerization, opencode, file-transfer, upload, download]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/backlog.md:FEAT-025@c9d5e1
  - README.md
  - src/dot_work/container/
---

### Problem
Users working with OpenCode containers need convenient ways to:
1. Upload generated files (code, docs, configs) from container to host
2. Download reference files, datasets, or prompts from host to container
3. Transfer files between containers
4. Bulk upload/download operations
5. Resume interrupted transfers
6. Track transfer history and status

Current approach requires manual `docker cp` commands or volume mounts, which are inconvenient for ad-hoc transfers.

### Affected Files
- NEW: `src/dot_work/container/opencode/file-server.py` (simple HTTP file server)
- NEW: `src/dot_work/container/opencode/file-transfer.sh` (transfer utilities)
- MODIFIED: `src/dot_work/container/opencode/entrypoint.sh` (optional file server)
- MODIFIED: `src/dot_work/container/opencode/Dockerfile` (add curl, transfer tools)
- `src/dot_work/cli.py` (add file transfer commands)
- MODIFIED: `src/dot_work/container/opencode/.env.example` (add file server vars)

### Importance
**MEDIUM**: File transfer utilities enable:
- Ad-hoc file sharing without volume mounts
- Easy backup of container work artifacts
- Transfer files between containers and host
- Integration with CI/CD pipelines
- User-friendly alternative to `docker cp`
- Progress tracking for large transfers

### Proposed Solution

**Phase 1: Simple HTTP File Server (2-3 days)**
Create optional HTTP file server in container:

1. `file-server.py`:
   - Lightweight HTTP server using Flask or FastAPI
   - Endpoints: `/upload`, `/download`, `/list`, `/delete`
   - Authentication (optional token-based)
   - CORS support
   - Chunked upload for large files
   - Progress tracking

2. API design:
   ```python
   # Upload file
   POST /upload
   Query: ?dest=/workspace/uploads/
   Body: multipart/form-data with file

   # Download file
   GET /download
   Query: ?path=/workspace/path/file.txt

   # List files
   GET /list
   Query: ?path=/workspace/

   # Delete file
   DELETE /delete
   Query: ?path=/workspace/path/file.txt

   # Transfer status
   GET /status/:transfer_id
   ```

3. Optional activation via env var:
   - `FILE_SERVER_ENABLED=true`
   - `FILE_SERVER_PORT=9000` (different from webui port)
   - `FILE_SERVER_AUTH_TOKEN=secret` (optional)
   - `FILE_SERVER_MAX_SIZE=1GB` (default)

**Phase 2: File Transfer CLI Commands (2-3 days)**
Add `dot-work container opencode transfer` commands:

```bash
# Upload file to container
dot-work container opencode transfer upload CONTAINER \
  /path/on/host/file.txt \
  --dest /workspace/uploads/

# Upload directory (recursive)
dot-work container opencode transfer upload CONTAINER \
  /path/on/host/dir/ \
  --dest /workspace/context/docs/ \
  --recursive

# Download file from container
dot-work container opencode transfer download CONTAINER \
  /workspace/workspace/generated-code.py \
  --dest ./downloads/

# Download directory
dot-work container opencode transfer download CONTAINER \
  /workspace/context/ \
  --dest ./context-backup/ \
  --recursive

# List files in container
dot-work container opencode transfer list CONTAINER \
  --path /workspace/

# Delete file in container
dot-work container opencode transfer delete CONTAINER \
  /workspace/workspace/temp-file.txt

# Show transfer history
dot-work container opencode transfer status
```

Transfer features:
- Progress bars for large files
- Resume capability (skip if exists and checksum matches)
- Dry-run mode
- Verbose logging
- Checksum verification (SHA256)
- Compression for transfers (`--compress`)
- Parallel transfers (`--jobs 4`)

**Phase 3: Web-Based File Manager (Optional, 2-3 days)**
Simple web UI for file transfers:

1. File upload form:
   - Drag and drop
   - Progress indicators
   - Batch upload
   - Destination selection

2. File browser:
   - Tree view of container files
   - Download buttons
   - Delete confirmation
   - Search/filter

3. Web UI access:
   - `http://localhost:FILE_SERVER_PORT/files/`
   - Authentication via token
   - Responsive design

**Phase 4: Transfer History and Tracking (1-2 days)**
Track file transfers:

1. Transfer log:
   ```yaml
   # /workspace/.transfer-log.yaml
   transfers:
     - id: "tx_001"
       type: "upload"
       timestamp: "2025-12-30T10:00:00Z"
       source: "/host/file.txt"
       dest: "/workspace/uploads/file.txt"
       size: 12345
       checksum: "sha256:abc123..."
       status: "completed"

     - id: "tx_002"
       type: "download"
       timestamp: "2025-12-30T10:05:00Z"
       source: "/workspace/output.txt"
       dest: "/host/downloads/output.txt"
       size: 67890
       status: "failed"
       error: "timeout"
   ```

2. Status command:
   ```bash
   # Show recent transfers
   dot-work container opencode transfer status --recent 10

   # Show specific transfer
   dot-work container opencode transfer status tx_001

   # Filter by status
   dot-work container opencode transfer status --status failed

   # Retry failed transfer
   dot-work container opencode transfer retry tx_002
   ```

**Phase 5: Alternative: SCP/SFTP Mode (Optional, 2 days)**
Enable SCP/SFTP transfers for SSH users:

1. Install OpenSSH server in container (optional)
2. User configuration:
   - `SSH_ENABLED=true` (disabled by default for security)
   - `SSH_USER=opencode`
   - `SSH_KEY_MOUNT=/ssh/keys`

3. SCP usage:
   ```bash
   # Upload via SCP
   scp file.txt opencode@container:/workspace/uploads/

   # Download via SCP
   scp opencode@container:/workspace/output.txt ./downloads/
   ```

**Phase 6: rsync Integration (1-2 days)**
Add rsync for efficient sync:

```bash
# Sync directory (incremental)
dot-work container opencode transfer sync CONTAINER \
  /host/dir/ \
  --dest /workspace/context/ \
  --direction push

# Sync from container
dot-work container opencode transfer sync CONTAINER \
  /workspace/context/ \
  --dest /host/backup/ \
  --direction pull

# Dry-run sync
dot-work container opencode transfer sync CONTAINER \
  /host/dir/ \
  --dest /workspace/ \
  --dry-run
```

Sync features:
- Only transfer changed files (based on checksum)
- Delete extraneous files (`--delete`)
- Exclude patterns (`--exclude .git`)
- Compression (`--compress`)
- Bandwidth limit (`--bwlimit 1M`)

**Phase 7: Entrypoint Integration (1 day)**
Optional file server startup in entrypoint:

```bash
# Start file server if enabled
if [ "$FILE_SERVER_ENABLED" = "true" ]; then
  echo "Starting file server on port $FILE_SERVER_PORT..."
  python3 /usr/local/bin/file-server.py \
    --port "$FILE_SERVER_PORT" \
    --auth-token "$FILE_SERVER_AUTH_TOKEN" \
    --max-size "$FILE_SERVER_MAX_SIZE" \
    --path /workspace \
    &

  echo "File server running on port $FILE_SERVER_PORT"
  echo "Access: http://localhost:$FILE_SERVER_PORT/files/"
fi
```

**Phase 8: Security Hardening (1-2 days)**
1. Authentication:
   - Required auth token for file server
   - Token rotation support
   - HTTPS/TLS (optional, via reverse proxy)

2. Access control:
   - Allowed paths whitelist (e.g., only `/workspace/`)
   - File size limits
   - User-specific permissions

3. Auditing:
   - Log all transfer operations
   - Include source/destination IP
   - Include user/token ID
   - Timestamp and file metadata

**Phase 9: Documentation and Examples (1 day)**
Extend `container/opencode/README.md`:

```bash
# Quick start: Enable file server
export FILE_SERVER_ENABLED=true
export FILE_SERVER_AUTH_TOKEN=my-secret-token
dot-work container opencode run

# Upload file
dot-work container opencode transfer upload my-container \
  ./local-file.txt \
  --dest /workspace/uploads/

# Download generated code
dot-work container opencode transfer download my-container \
  /workspace/workspace/generated.py \
  --dest ./downloads/

# Sync directory
dot-work container opencode transfer sync my-container \
  ./docs/ \
  --dest /workspace/context/docs/ \
  --direction push

# Web UI access
# Open http://localhost:9000/files/
# Enter token: my-secret-token
# Drag and drop files to upload

# Show transfer history
dot-work container opencode transfer status --recent 5
```

### Acceptance Criteria
- [ ] `file-server.py` with upload/download/list/delete endpoints
- [ ] File server optional activation via env vars
- [ ] CLI transfer commands: upload, download, list, delete, sync
- [ ] Progress bars for large file transfers
- [ ] Resume capability and checksum verification
- [ ] Transfer history tracking
- [ ] Optional web UI for file manager
- [ ] Security: auth token, path restrictions, size limits
- [ ] rsync integration for efficient sync
- [ ] Documentation with examples
- [ ] Unit tests for file server and transfer logic
- [ ] Integration tests for file transfers

### Notes
- File server should be optional (disabled by default)
- Security: Never enable file server in production without auth
- Consider rate limiting for transfers
- Future: S3 bucket integration for cloud storage
- Future: Transfer scheduling (upload at specific time)
- Future: Webhook notifications on transfer completion
- Monitor disk usage during transfers

---
