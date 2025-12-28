# CR-001 Investigation: Plaintext Git Credentials in Container

**Issue:** CR-001@f8a2c1
**Started:** 2025-12-27T14:15:00Z
**Status:** In Progress

---

## Problem Analysis

**Location:** `src/dot_work/container/provision/core.py:591-592`

```bash
git config --global credential.helper store
echo "https://x-access-token:${GITHUB_TOKEN}@github.com" > ~/.git-credentials
```

### Root Cause
The embedded bash script writes GitHub credentials to `~/.git-credentials` in plaintext:
- Uses `credential.helper store` which writes credentials to disk
- Writes token directly to `~/.git-credentials` file
- Token is visible in plaintext to anyone with read access
- File persists in container filesystem

### Security Risks
While the container is ephemeral, this is a security concern because:
1. **Image commits** - If the Docker image is saved/committed, credentials are baked in
2. **Container logs** - Logs may capture file contents during debugging
3. **Container inspection** - `docker exec` or `docker cp` can expose the file
4. **Core dumps** - Process memory dumps may contain file contents
5. **Volume mounts** - If home directory is mounted, credentials persist on host

### Current Code Flow
1. Container starts with `GITHUB_TOKEN` environment variable
2. Bash script runs `git config --global credential.helper store`
3. Script writes `https://x-access-token:${GITHUB_TOKEN}@github.com` to `~/.git-credentials`
4. Git reads from this file for authentication
5. File remains on disk until container is destroyed

---

## Proposed Solution

### Option 1: Use GIT_ASKPASS with echo (Recommended)

Use `GIT_ASKPASS` environment variable with a helper script that echoes the token:

```bash
# Don't write credentials to disk
# git config --global credential.helper store  # REMOVE THIS

# Use GIT_ASKPASS for authentication
export GITHUB_TOKEN  # Already set as environment variable

# Create a temporary askpass script that echoes the token
cat > /tmp/git-askpass.sh << 'EOF'
#!/bin/sh
echo "${GITHUB_TOKEN}"
EOF
chmod +x /tmp/git-askpass.sh

# Configure git to use the askpass helper
export GIT_ASKPASS=/tmp/git-askpass.sh
export GIT_TERMINAL_PROMPT=0  # Don't prompt interactively

# Git will now call the askpass script when credentials are needed
# No credentials written to disk
```

### Option 2: Use credential.helper with memory cache

Use git's in-memory credential helper:

```bash
# Use memory-only credential helper (timeout in seconds)
git config --global credential.helper 'cache --timeout=3600'

# Feed credentials to the cache once
echo "url=https://github.com" | git credential approve << EOF
protocol=https
host=github.com
username=x-access-token
password=${GITHUB_TOKEN}
EOF

# Credentials cached in memory only, not written to disk
# Expires after 3600 seconds (1 hour)
```

### Option 3: Pass credentials via environment (Simplest)

Many git commands accept credentials via environment variables:

```bash
# No git config needed - git reads from environment
export GIT_USERNAME="x-access-token"
export GIT_PASSWORD="${GITHUB_TOKEN}"

# Use in git URLs: https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/...
```

### Trade-offs
- **Option 1 (GIT_ASKPASS):**
  - Pros: No credentials on disk, secure, works with all git operations
  - Cons: Requires temporary script file

- **Option 2 (memory cache):**
  - Pros: Standard git mechanism, no disk writes
  - Cons: Credentials in process memory (still vulnerable to core dumps)

- **Option 3 (environment):**
  - Pros: Simplest approach
  - Cons: Need to update all git URLs, environment still visible in /proc

**Recommendation:** Option 1 (GIT_ASKPASS) because:
- No credentials written to disk
- Works with existing git commands without URL changes
- Temporary script can be deleted after use
- Industry-standard approach for CI/CD environments

---

## Affected Code
- `src/dot_work/container/provision/core.py:591-592` (credential writing)

---

## Acceptance Criteria
- [ ] No plaintext credentials written to `~/.git-credentials`
- [ ] Git operations still work with GitHub authentication
- [ ] Credentials not visible in container filesystem
- [ ] Solution documented in code comments
- [ ] Test verifies git clone/push still works

---

## Next Steps
1. Implement Option 1 (GIT_ASKPASS approach)
2. Remove lines 591-592 (credential.helper store and echo to file)
3. Add askpass script creation
4. Test git operations work without credential file
5. Document the security improvement
