# AI-Assisted Pull Request Review Prompt

You are an AI assistant helping with pull request reviews. Use this prompt to get comprehensive, structured feedback on code changes.

## How to Use This Prompt

1. **Copy the relevant prompt** from the `.github/prompts/` folder
2. **Paste it into GitHub Copilot Chat** or your AI assistant
3. **Include the specific code changes** you want reviewed
4. **Ask specific questions** about areas of concern

## Available Review Types

### 🔍 General Code Review
**File**: `.github/prompts/code-review.md`
**Use for**: Overall code quality, best practices, maintainability
```
@copilot Review this pull request using the code review guidelines in .github/prompts/code-review.md
```

### 🔒 Security Review
**File**: `.github/prompts/security-review.md`
**Use for**: Security vulnerabilities, authentication, data protection
```
@copilot Perform a security review of these changes using .github/prompts/security-review.md
```

### ⚡ Performance Review
**File**: `.github/prompts/performance-review.md`
**Use for**: Performance optimization, algorithm efficiency, resource usage
```
@copilot Analyze the performance implications using .github/prompts/performance-review.md
```

## Example Usage

### Full PR Review
```
@copilot Please review this entire pull request focusing on:
1. Security implications (use security-review.md)
2. Performance impact (use performance-review.md)
3. General code quality (use code-review.md)

[Paste your code changes here]
```

### Specific Code Block Review
```
@copilot Review this specific function for security issues:

```typescript
// Your code here
```

Use the security checklist from .github/prompts/security-review.md
```

### Targeted Review
```
@copilot I'm concerned about the performance of this database query.
Can you review it using the database performance guidelines from performance-review.md?

[Your database code here]
```

## Tips for Better Reviews

1. **Be specific**: Mention what type of review you want
2. **Provide context**: Include relevant background information
3. **Ask targeted questions**: "Is this secure?" vs "Are there SQL injection vulnerabilities?"
4. **Include test cases**: Show how the code is tested
5. **Mention constraints**: Performance requirements, browser support, etc.

## Custom Review Prompts

You can also create custom prompts by combining elements:

```
@copilot Review this code for:
- TypeScript type safety
- React performance best practices
- Accessibility compliance
- Testing coverage

[Your code here]
```
