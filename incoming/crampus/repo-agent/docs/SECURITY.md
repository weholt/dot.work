# Security Policy

## Supported Versions

Currently supported versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email the maintainer directly with details of the vulnerability
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Initial Response**: Within 48 hours of report
- **Status Updates**: Every 7 days until resolved
- **Resolution Timeline**: 
  - Critical vulnerabilities: 7 days
  - High severity: 30 days
  - Medium/Low severity: 90 days

### Disclosure Policy

- We will acknowledge receipt of your vulnerability report
- We will provide regular updates on the fix progress
- We will notify you when the vulnerability is fixed
- We will publicly disclose the vulnerability after a fix is released (with credit to the reporter if desired)

## Security Best Practices for Users

### Credential Management

**✅ DO:**
- Store secrets in environment variables
- Use `.env` files locally (never commit them)
- Use GitHub Secrets in CI/CD pipelines
- Rotate tokens regularly
- Use tokens with minimal required permissions

**❌ DON'T:**
- Hardcode tokens in instruction files
- Commit `.env` files to git
- Share tokens in public channels
- Use personal tokens in shared environments

### GitHub Token Permissions

For this tool, your GitHub token needs:
- `repo` scope - for repository access and PR creation

Optional scopes:
- `workflow` - if modifying GitHub Actions workflows
- `read:org` - if working with organization repositories

### Example Secure Configuration

```yaml
# ✅ SECURE: Use environment variable
github_token_env: "GITHUB_TOKEN"
api_key_env: "OPENROUTER_API_KEY"

# ❌ INSECURE: Don't hardcode tokens
# github_token: "ghp_xxxxxxxxxxxx"
# api_key: "sk-xxxxxxxxxxxx"
```

### Docker Security Considerations

This tool runs code in Docker containers. Be aware:

1. **Environment Variables**: Secrets are passed to containers via environment variables
   - They are visible via `docker inspect` (requires Docker daemon access)
   - Containers are ephemeral and deleted after use
   - Suitable for most CI/CD and local development scenarios

2. **Git Credentials**: The tool uses git credential helper to store credentials temporarily
   - Credentials stored in `~/.git-credentials` inside container
   - File is deleted when container exits
   - Standard git practice for HTTPS authentication

3. **SSH Keys**: If using SSH authentication
   - Keys are mounted read-only into containers
   - Original keys on host are never modified
   - Ensure your SSH keys have proper permissions (600)

### CI/CD Security

When using in GitHub Actions:

```yaml
- name: Run repo-agent
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # ✅ Use GitHub secrets
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  run: |
    uvx repo-agent run instructions.md
```

**Never** put secrets directly in workflow files:
```yaml
# ❌ NEVER DO THIS
env:
  GITHUB_TOKEN: ghp_hardcoded_token_here
```

### Local Development Security

1. **Create `.env` file** (gitignored):
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   OPENROUTER_API_KEY=sk-or-v1-your_key_here
   ```

2. **Load environment variables**:
   ```bash
   # Linux/Mac
   source <(cat .env | sed 's/^/export /')
   
   # Windows PowerShell
   . .\load-env.ps1
   ```

3. **Never commit `.env` file** - it's already in `.gitignore`

## Security Features

### Built-in Protections

1. **No Credential Storage**: Credentials are never written to disk except in ephemeral containers
2. **Environment Variable Isolation**: Each container run has isolated environment
3. **Git Ignore**: Template `.gitignore` excludes sensitive files
4. **Template Files**: Sensitive configs use templates (e.g., `auth.json.template`)
5. **Documentation**: Clear examples of secure vs insecure practices

### Audit Trail

- All git operations are logged in container output
- Docker run commands can be reviewed with `--dry-run` flag
- PR descriptions provide visibility into automated changes

## Known Limitations

1. **Docker Inspect**: Environment variables visible to anyone with Docker daemon access
   - Mitigation: Run in trusted environments
   - Consider: Docker secrets for production environments

2. **Credential Helper**: Uses standard git credential helper (plaintext in memory)
   - Mitigation: Ephemeral containers automatically clean up
   - Alternative: Use SSH keys instead of HTTPS tokens

3. **LLM Provider Tokens**: API keys passed to LLM tool containers
   - Mitigation: Only passed at runtime, never stored
   - Consider: Using provider-specific authentication methods when available

## Security Updates

Security patches and updates will be released as:
- Patch versions for security fixes (e.g., 0.1.1 → 0.1.2)
- With clear changelog entries marked as [SECURITY]
- With GitHub Security Advisory for critical issues

Subscribe to repository releases for security notifications.

## Compliance

This tool follows security best practices for:
- OWASP Top 10 (credential management, logging)
- GitHub Security Best Practices
- Docker Security Guidelines
- Python Packaging Security Standards

## Additional Resources

- [GitHub Token Security](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

**Last Updated**: 2025-11-20  
**Policy Version**: 1.0
