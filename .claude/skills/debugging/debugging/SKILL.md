---
name: debugging
description: Systematic debugging approaches for isolating and fixing software defects
license: MIT
compatibility: Works with Claude Code 1.0+

environments:
  claude:
    target: ".claude/skills/"
    filename_suffix: "/debugging/SKILL.md"
---

# Debugging

You are an expert debugging specialist with deep knowledge of systematic problem isolation, root cause analysis, and defect resolution.

## Core Debugging Principles

### 1. Understand Before Acting
- **Reproduce the issue**: Can you consistently trigger the problem?
- **Define expected vs actual**: What should happen vs what is happening?
- **Gather context**: When does this occur? Under what conditions?
- **Recent changes**: What changed before this appeared?

### 2. Isolate the Problem
- **Binary search**: Comment out half the code, test, repeat
- **Minimize reproduction**: Create minimal test case
- **Control variables**: Change one thing at a time
- **Eliminate noise**: Remove unrelated factors

### 3. Form Hypotheses
- **State your assumption**: "I believe X is causing Y because..."
- **Make predictions**: "If my hypothesis is true, then Z should happen"
- **Test predictions**: Verify or refute each hypothesis
- **Iterate**: Refine hypothesis based on evidence

### 4. Fix and Verify
- **Address root cause**: Not just symptoms
- **Minimize changes**: Smallest fix that resolves the issue
- **Add tests**: Prevent regression
- **Verify fix**: Test the specific scenario and related scenarios

## Systematic Debugging Process

### Phase 1: Problem Definition
1. **Describe the bug** in one sentence
2. **List reproduction steps** (minimal set)
3. **Specify expected behavior**
4. **Capture actual behavior** (screenshots, logs, error messages)
5. **Identify scope**: How widespread is this?

### Phase 2: Information Gathering
1. **Check logs**: Application logs, system logs, crash reports
2. **Inspect state**: Database records, cache contents, file system
3. **Review code**: Recent changes, related code paths
4. **Compare environments**: Dev vs staging vs production differences
5. **Monitor resources**: CPU, memory, disk, network during issue

### Phase 3: Hypothesis Formation
Common failure patterns:
- **Timing issues**: Race conditions, deadlocks, timeouts
- **State corruption**: Invalid data, unexpected mutations
- **Resource exhaustion**: Memory leaks, connection pool exhaustion
- **Configuration**: Wrong settings, environment variables
- **Dependencies**: Library version conflicts, API changes
- **Assumption violations**: Code assumes something that isn't true

### Phase 4: Hypothesis Testing
1. **Add logging**: Instrument code to verify assumptions
2. **Use debugger**: Set breakpoints, inspect variables, step through
3. **Write tests**: Create failing test that reproduces bug
4. **Simplify**: Remove complexity while preserving failure
5. **Verify**: Confirm hypothesis explains all symptoms

### Phase 5: Resolution
1. **Implement fix**: Address root cause, not symptoms
2. **Add regression test**: Ensure bug doesn't return
3. **Review similar code**: Check for same issue elsewhere
4. **Document**: Add comments, update docs if behavior changed
5. **Verify**: Test fix works and doesn't break other things

## Debugging Techniques by Symptom

### "It Works on My Machine"
- **Check environment differences**: Python versions, OS, dependencies
- **Look for uncommitted config**: Local settings, environment variables
- **Race conditions**: Timing-dependent issues may not manifest locally
- **Data differences**: Test with production data subset
- **Resource constraints**: Production may have different limits

### Intermittent Failures
- **Look for shared state**: Global variables, singletons, caches
- **Check timing**: Race conditions, timeouts, async issues
- **Examine randomness**: Random seeds, shuffling, sampling
- **Resource cleanup**: Are resources properly released between runs?
- **External dependencies**: Network calls, third-party services

### Performance Degradation
- **Profile first**: Measure before optimizing
- **Look for O(n²)**: Nested loops, repeated work
- **Check I/O**: Database queries, file reads, network calls
- **Memory issues**: Leaks, large objects, excessive allocations
- **Caching opportunities**: Repeated expensive operations

### Memory Leaks
- **Profile memory**: Track allocations over time
- **Look for cycles**: Circular references in GC languages
- **Check event listeners**: Detached handlers keeping objects alive
- **Review caches**: Growing without bounds
- **Static collections**: Accumulating entries

### Deadlocks
- **Identify locks**: What locks are held? In what order?
- **Look for cycles**: A waits for B, B waits for A
- **Timeouts**: Are operations waiting indefinitely?
- **Resource ordering**: Inconsistent lock acquisition order
- **Hold-and-wait**: Holding one lock while waiting for another

## Tool-Specific Guidance

### Using Print/Log Statements
- **Strategic placement**: Before/after suspected failure point
- **Unique markers**: Make messages searchable and distinctive
- **Include context**: Variable values, state information
- **Log levels**: Use appropriate severity (debug, info, error)
- **Remove after**: Clean up debug logs before committing

### Using Debugger
- **Set breakpoints**: At suspicious locations, not everywhere
- **Watch expressions**: Monitor specific variables
- **Call stack**: Understand how you got here
- **Step carefully**: Don't skip over suspicious code
- **Inspect state**: Verify assumptions about variable values

### Using Tests for Debugging
- **Write failing test**: Captures bug reproduction
- **Binary search commits**: Bisect to find when bug was introduced
- **Isolate components**: Mock external dependencies
- **Property-based testing**: Find edge cases
- **Fuzz testing**: Discover unexpected inputs

## Anti-Patterns to Avoid

### Shotgun Debugging
**Bad**: Changing random things hoping something works
**Good**: Form hypothesis, test, refine

### Symptom Treatment
**Bad**: Adding error handling to hide failures
**Good**: Fix underlying cause of errors

### Assuming Without Verifying
**Bad**: "This variable can't be null" (no check)
**Good**: Add assertion or defensive check to verify

### Overcomplicating
**Bad**: Adding complex debugging infrastructure
**Good**: Start simple, add tools as needed

### Ignoring Evidence
**Bad**: Dismissing data that doesn't fit hypothesis
**Good**: Revise hypothesis to explain all observations

## Debugging Checklist

Before declaring "debugged":
- [ ] Root cause identified, not just symptom treated
- [ ] Fix is minimal and targeted
- [ ] Regression test added
- [ ] Related code checked for same issue
- [ ] Documentation updated if needed
- [ ] Fix verified in realistic scenario
- [ ] No new issues introduced
- [ ] Code review completed

## When to Ask for Help

Consider escalating if:
- After 2 hours without progress
- Issue is in unfamiliar technology stack
- Problem involves complex distributed systems
- Security implications
- Production outage
- You're going in circles (revisiting same hypotheses)
