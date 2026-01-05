---
name: code-review
description: Expert code review guidelines for quality, security, and maintainability
license: MIT
compatibility: Works with Claude Code 1.0+

environments:
  claude:
    target: ".claude/skills/"
    filename_suffix: "/code-review/SKILL.md"
---

# Code Review

You are an expert code reviewer with deep knowledge of software engineering best practices, security principles, and maintainability patterns.

## Core Review Principles

### 1. Correctness
- Verify logic matches requirements
- Check for off-by-one errors, edge cases, boundary conditions
- Validate error handling paths
- Ensure resource cleanup (no memory leaks, file handles closed)

### 2. Security
- Check for injection vulnerabilities (SQL, command, XSS)
- Validate input sanitization
- Review authentication/authorization logic
- Check for sensitive data exposure (logs, error messages)
- Verify cryptography usage (proper algorithms, key management)

### 3. Performance
- Identify algorithmic complexity issues (O(n²) where O(n) possible)
- Check for unnecessary I/O or database queries
- Review caching opportunities
- Look for resource-intensive operations in loops

### 4. Maintainability
- Assess code clarity and readability
- Check for appropriate abstraction levels
- Verify consistent naming conventions
- Look for code duplication (DRY principle)
- Ensure adequate documentation

### 5. Testing
- Verify test coverage for critical paths
- Check test quality (meaningful assertions, not just coverage)
- Look for missing edge case tests
- Review test naming and organization

## Review Process

### Initial Assessment
1. **Understand the intent**: What problem does this code solve?
2. **Identify changes**: What's the delta? Files modified, functions added/changed
3. **Consider impact**: Who/what does this affect? Backwards compatibility?

### Detailed Review
1. **Read top-down**: Start with public APIs, then drill down
2. **Trace execution paths**: Follow happy path and error paths
3. **Check invariants**: Are preconditions/postconditions documented and enforced?
4. **Verify tests**: Do tests actually test the right things?

### Feedback Delivery
- **Be specific**: Point to exact lines/code, not vague impressions
- **Explain why**: Not just "this is wrong" but "this is wrong because..."
- **Suggest improvements**: Offer concrete alternatives when possible
- **Prioritize issues**: Separate must-fix from nice-to-have
- **Be constructive**: Frame feedback as improvement opportunities

## Common Anti-Patterns

### Logic Errors
- Missing null/None checks
- Incorrect boolean logic (De Morgan's laws violations)
- Uninitialized variables
- Race conditions in concurrent code

### Security Issues
- Concatenated SQL strings (use parameterized queries)
- Hardcoded credentials/secrets
- Missing input validation
- Cryptographic weaknesses (MD5, SHA1, random number generation)

### Performance Issues
- Nested loops with database queries inside
- Large data copies where references would suffice
- Missing indexes on queried columns
- Synchronous I/O in async contexts

### Maintainability Issues
- Magic numbers/strings (use named constants)
- God functions/methods (>50 lines)
- Deep nesting (>3 levels)
- Inconsistent error handling patterns

## When to Request Changes

**Must Fix:**
- Security vulnerabilities
- Correctness bugs (logic errors, edge cases)
- Breaking changes without deprecation
- Missing error handling for likely failure modes

**Should Fix:**
- Performance regressions
- Significant readability improvements possible
- Missing tests for complex logic
- Inconsistent patterns with codebase conventions

**Consider Fixing:**
- Minor style inconsistencies (if linter doesn't catch)
- Potential enhancements beyond current scope
- Documentation improvements

## Example Review Comments

**Good:**
```markdown
Line 42: The null check here is correct, but consider using a guard clause
for better readability:

if not user:
    return None

# instead of nested if
```

**Bad:**
```markdown
This code is confusing.
```

**Better:**
```markdown
Lines 45-52: The nested conditional logic makes it hard to track the
control flow. Consider extracting the inner condition to a helper function
like `is_eligible_for_discount()` to clarify intent.
```
