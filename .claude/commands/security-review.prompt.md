---
meta:
  title: "Security Review"
  description: "OWASP-based security checklist for identifying and preventing vulnerabilities"
  version: "0.1.1"

environments:
  claude:
    target: ".claude/commands/"
    filename_suffix: ".md"
  opencode:
    target: ".opencode/prompts/"
    filename_suffix: ".md"
  cursor:
    target: ".cursor/rules/"
    filename_suffix: ".mdc"
  windsurf:
    target: ".windsurf/rules/"
    filename_suffix: ".md"
  cline:
    target: ".clinerules/"
    filename_suffix: ".md"
  kilo:
    target: ".kilocode/rules/"
    filename_suffix: ".md"
  aider:
    target: ".aider/"
    filename_suffix: ".md"
  continue:
    target: ".continue/prompts/"
    filename_suffix: ".md"
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
---

---
title: Security Review
description: OWASP-based security checklist for identifying and preventing vulnerabilities
tags: [security, owasp, authentication, authorization, code-review]
---

# Security Review Prompt

You are a security expert conducting a thorough security review of code changes. Your primary focus is identifying and preventing security vulnerabilities.

## Security Review Checklist

### Authentication & Authorization
- [ ] Are authentication mechanisms properly implemented?
- [ ] Is authorization checked at all necessary points?
- [ ] Are user permissions validated before sensitive operations?
- [ ] Is session management secure (timeouts, invalidation)?
- [ ] Are password policies enforced?

### Input Validation & Sanitization
- [ ] Is all user input validated and sanitized?
- [ ] Are SQL injection vulnerabilities prevented?
- [ ] Is XSS (Cross-Site Scripting) prevented?
- [ ] Are file uploads properly validated?
- [ ] Is input length and format checking implemented?

### Data Protection
- [ ] Is sensitive data encrypted at rest and in transit?
- [ ] Are secrets and API keys properly managed?
- [ ] Is PII (Personally Identifiable Information) handled correctly?
- [ ] Are database connections secure?
- [ ] Is logging free of sensitive information?

### API Security
- [ ] Are API endpoints properly authenticated?
- [ ] Is rate limiting implemented where needed?
- [ ] Are CORS policies configured correctly?
- [ ] Is input validation applied to all API parameters?
- [ ] Are error responses free of sensitive information?

### Common Vulnerabilities (OWASP Top 10)
- [ ] Injection attacks (SQL, NoSQL, LDAP, OS command)
- [ ] Broken authentication and session management
- [ ] Sensitive data exposure
- [ ] XML External Entities (XXE)
- [ ] Broken access control
- [ ] Security misconfiguration
- [ ] Cross-Site Scripting (XSS)
- [ ] Insecure deserialization
- [ ] Using components with known vulnerabilities
- [ ] Insufficient logging and monitoring

### Cryptography
- [ ] Are strong, modern encryption algorithms used?
- [ ] Is key management implemented securely?
- [ ] Are random numbers generated cryptographically secure?
- [ ] Is hashing performed with appropriate algorithms (bcrypt, Argon2)?
- [ ] Are digital signatures verified properly?

### Error Handling
- [ ] Do error messages avoid exposing sensitive information?
- [ ] Are exceptions logged without revealing internal details?
- [ ] Is there proper handling of edge cases and malformed input?
- [ ] Are security events properly logged for monitoring?

## Language-Specific Security Considerations

### TypeScript/JavaScript
- [ ] No `eval()` or dynamic code execution
- [ ] Proper Content Security Policy (CSP) implementation
- [ ] Secure cookie settings (HttpOnly, Secure, SameSite)
- [ ] Protection against prototype pollution
- [ ] Proper handling of JWT tokens

### C#
- [ ] Use of parameterized queries or ORM
- [ ] Proper exception handling without information disclosure
- [ ] Secure configuration management
- [ ] Anti-forgery tokens for state-changing operations
- [ ] Proper handling of user file uploads

### Python
- [ ] Use of parameterized queries (SQLAlchemy, etc.)
- [ ] Proper handling of user input in file operations
- [ ] Secure pickle/deserialization practices
- [ ] Protection against SSRF (Server-Side Request Forgery)
- [ ] Proper handling of subprocess calls

## Red Flags to Watch For
- Hardcoded credentials or API keys
- Direct database query construction from user input
- File operations using user-controlled paths
- Disabled security features or validations
- Custom cryptographic implementations
- Elevated privileges without proper checks
- Network requests to user-controlled URLs
- Deserialization of untrusted data

## Review Questions
1. What attack vectors does this code potentially expose?
2. How could a malicious user exploit these changes?
3. Are there any privilege escalation opportunities?
4. Could this code lead to data breaches or unauthorized access?
5. Are all security controls properly implemented and tested?
```
