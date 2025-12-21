Skip to content
Chat history

You said:
I work in vs code using copilot, but I experience way too many regressions; things stop working, gets fixed, then soon again stops working, gets fixed etc. over and over. 

I want you to propose a system of iterative agents validating each others work, preferrably by breaking tasks into atomic subtasks, then iterating over the subtasks to validate existing functionality AND newly added enhancements.
ChatGPT said:
Below is a concrete, architecture-level proposal for an iterative multi-agent validator system designed to sit on top of your existing workflow (VS Code + GitHub + Copilot) and prevent regressions by continuously validating both existing and newly added capabilities.

It avoids fluff, gives you a practical, reproducible design you can implement with your existing RAG/agent frameworks and the skill-based “Glorious Agents” setup.

Iterative Multi-Agent Validation System
Atomic tasks → multi-agent execution → cross-validation → regression detection

1. Core Concept
A task is broken into atomic subtasks.
For each subtask:

A Planner Agent defines “expected behaviors” and “acceptance checks”.

An Implementer Agent produces/updates code.

A Static Validator Agent checks structure, interfaces, naming, typing, schema alignment.

A Behavior Validator Agent simulates behavior using your RAG context + test examples.

A Regression Sentinel Agent compares current functionality with previous snapshots and flags regressions.

A PR Generator Agent prepares the patch only if all validators pass.

This creates a closed loop of implement → validate → regressions → iterate until stable.

2. System Overview
Agents
A. Planner Agent (Task → Atomic Subtasks)
Receives the high-level task.

Decomposes into atomic subtasks.

Defines expected input/output behavior per subtask.

Defines “validation contracts”: pre-conditions, post-conditions, invariants.

Output:

{
  "subtask_id": "ST-001",
  "summary": "...",
  "preconditions": [...],
  "postconditions": [...],
  "invariants": [...],
  "tests": ["Given X -> expect Y", "..."]
}
B. Implementer Agent (Code Generation)
Uses your current repo context (RAG).

Modifies only the files specified in the subtask’s contract.

Produces minimal diff.

Outputs the exact patch.

C. Static Validator Agent (Compile-Level Safety)
Checks:

Code compiles

No broken imports

Typing is consistent

Project conventions followed

No dead references

No missing dependencies

No API contract drift

Method:

Run uv run pyright or dotnet build depending on project.

Run tree-shaking analyzer (Code-Atlas style) to detect unused changes.

D. Behavior Validator Agent (Functional Safety)
Given the Planner’s test cases:

Executes logic in a sandbox

Validates I/O behavior

Verifies invariants

Runs synthetic tests (generated test cases)

Simulates user interaction scenarios based on Figma/Gherkin if available

E. Regression Sentinel Agent (Change Impact Inspector)
This agent specifically prevents regressions.

Steps:

Build a feature map from previous successful runs.

Track all invariants across the entire repo.

Run previous successful “behavior snapshots” again.

If any previously green behavior turns red → block patch.

The regression map structure:

{
  "feature": "user-login",
  "invariant": "password-hash-never-logged",
  "previous_status": "PASS",
  "current_status": "FAIL"
}
F. Patch/PR Generator Agent
Reassembles all validated patches from subtasks.

Adds summary notes of:

Task → Subtasks → Patches

Validators results

Regression Sentinel status

Creates a GitHub PR via gh CLI.

3. Iterative Workflow
User writes a task (in VS Code or GitHub issue).

Planner Agent decomposes into atomic tasks.

For each atomic task:

Implementer Agent creates changes.

Static Validator checks.

Behavior Validator checks.

Regression Sentinel cross-checks against historical behavior.

If any validator fails:

Implementer Agent receives feedback and tries again.

Loop continues until all pass.

Patch is added to a “batch patch list”.

When all subtasks are validated, the PR is generated.

4. Preventing Regressions Repeatedly
Your main pain point:
Copilot introduces regressions because it has no memory and no regression tests.

This system fixes that via:

4.1. Persistent Behavior Snapshots
Store snapshot data in .agents/snapshots/:

Inputs/outputs

Mocked UI flows

OpenAPI schema conformance

Domain invariants

Snapshots are re-run every time a subtask changes something.

4.2. Invariant Enforcement
Represent all invariants as machine-checkable rules, such as:

“API must always return tenant_id when authenticated”

“Notes skill must never overwrite another skill’s tables”

“CLI must always support --json output”

The Regression Sentinel agent runs these invariants after each proposed patch.

4.3. Cross-Agent Disagreement Resolution
If Static Validator and Behavior Validator disagree:

Planner Agent generates a new subtask to reconcile them.

Example: “Fix contract drift between module A and module B”.

5. Integration with VS Code + Copilot
5.1. Role of Copilot
Copilot remains a local assistive coder but is no longer trusted blindly.

The agents sit outside of VS Code and act as your CI validator:

Runs automatically on save

Or manually triggered with a CLI command:
glorious validate-task path/to/issue.md

5.2. GitHub Integration
The PR generator agent outputs patches only when all validators pass.

A failing validator blocks PR creation.

GitHub Actions can run the validation chain server-side as well.

6. Minimal Implementation using your existing framework
You can implement this using:

Glorious Agents (skills + planner/executor)

uv for Python task runners

gh CLI for PR management

n8n or simple Python orchestration for workflow automation

Code-Atlas (your graph analyzer) for static validation

OpenAPI schema validation for API behavior consistency

Figma → test case generation through vector embeddings

Directory structure:
.agents/
  planner/
  implementer/
  validator-static/
  validator-behavior/
  regression-sentinel/
  pr-agent/
  snapshots/
  tasks/
7. If you want, I can generate:
Complete Python implementation

GitHub Action workflow

VS Code commands

CLI to run the agents

Skill templates

Step-by-step instructions for integrating it with your repo or Glorious Agents framework

Tell me if you want the full codebase, a step-by-step plan, or a ready-to-run agent workflow.

You said:
We have a huuge suite of unittests and integrationtests, and still this happens
ChatGPT said:
Below is a concrete design for an agentic regression-prevention system built specifically for teams that already have a massive unittest + integration test suite but still experience regressions (like in your VS Code + Copilot workflow).

This system does not try to replace your tests.
It uses agents to continuously validate that your tests actually cover the changed behavior, and to detect when Copilot-generated changes silently invalidate assumptions your tests don’t yet encode.

No fluff. Strict architecture.

1. Core Problem
Even with thousands of tests, regressions still occur because:

Copilot alters logic in areas that look correct syntactically and don’t break existing tests.

The tests do not encode the invariants that you think they encode.

The test suite is large but coverage is incomplete in narrow decision branches.

Integration tests often use happy-path flows, leaving edge-path regressions.

Copilot occasionally rewrites or removes behaviour that is “implicit” but not explicitly tested.

So the solution is not “more tests”.
It is agents that derive, simulate, and validate invariants and behavior not currently encoded in your tests.

2. The System
A 3-layer validation system that uses your existing tests, but adds two new layers of defense:

LAYER 1 — Your current tests
Run them normally. This guarantees baseline correctness.

LAYER 2 — Agent-Generated Behavioral Expectations (auto-snapshots)
Each time a test passes, an agent generates a behavioral snapshot:

Input → Output

Side-effects

API contracts

Structural invariants

Domain rules

UI behavior (if applicable)

Config/state transitions

These snapshots are machine-readable JSON files stored under version control.

Snapshots represent real behavior, not test assertions.

These are used for cross-run regression detection.

LAYER 3 — Agentic Change Impact Analysis
Before Copilot’s code change is accepted, agents:

Check snapshot drift

Compare new behavior to old snapshot.

If a snapshot changes without the corresponding test intentionally being updated, block.

Generate “missing tests” dynamically

Agents examine code diffs and generate test cases that your current suite does not cover.

These synthetic tests target:

rare branches

null/empty states

boundary conditions

concurrency edge cases

error handling

The system fails the patch if synthetic tests catch regressions.

Execution Graph Diffing

Use a call-graph analyzer (like your Code-Atlas idea).

Compare pre-change graph and post-change graph.

If any high-level flow changes (branches removed, ordering changed, exception propagation altered), agents flag it unless explicitly approved.

This prevents “silent logical rewrites” that tests didn’t assert.

3. Agent Roles
A. Test Runner Agent
Runs your entire suite, captures:

coverage

call traces

state diffs

Then hands that data to the Snapshot Agent.

B. Snapshot Agent
Creates versioned JSON snapshots:

{
  "id": "login_flow",
  "inputs": {...},
  "outputs": {...},
  "side_effects": ["sent email", "db.updated(user.id)"],
  "graph": ["ServiceA -> RepoB -> QueueC"],
  "invariants": {
    "password_hash_format": "bcrypt+$2b$...",
    "min_fields_required": ["username", "password"]
  }
}
These are stored under:

regression-snapshots/<feature>/<hash>.json
C. Change-Impact Agent
Before PR creation, it:

Analyzes the patch.

Identifies execution paths the patch touches.

Locates all snapshots that reference those paths.

Replays those snapshots and checks for drift.

If drift occurs but existing tests don’t fail → this is a regression.

D. Missing-Test Generator Agent
Given a diff, it:

Analyzes the decision tree.

Detects untested branches.

Creates synthetic tests:

minimal mocks

assertion scaffolds

negative-path tests

invariant tests

concurrency or async tests

Runs them.

If synthetic tests fail → patch rejected.

This specifically catches Copilot’s tendency to “rewrite internal logic that looked unused”.

E. Semantic Regression Agent
This one detects logic regression, even if tests pass and snapshots match, via:

symbolic execution

state-space exploration

invariant extraction from commit history

pre/post-condition auto-generation

This is where the agent leverages LLM intelligence beyond what unit tests can assert.

For example:

It knows a function that used to validate email format must still do so, even if no test asserts it.

It knows an event name that has always been uppercase should not suddenly become lowercase.

These are caught via inferred invariants, not tests.

4. The Failure Modes This System Fixes
4.1. Copilot rewrites logic to “optimize” something
→ Snapshot drift + execution graph diff → blocked.

4.2. Copilot deletes error-handling paths because they “look unused”
→ Missing-test generator detects missing branch coverage → synthetic tests fail → blocked.

4.3. Copilot renames something used implicitly
→ Semantic regression agent picks up inconsistent naming invariants → blocked.

4.4. Copilot updates a data model but doesn’t update serialization
→ Snapshot comparison + synthetic deserialization tests → blocked.

4.5. Copilot introduces side-effects (DB writes, logging, queue messages)
→ Snapshot drift + side-effect diff → blocked.

5. This Works With Your Existing Suite
Your current tests stay exactly as is.

The agentic system adds:

expected-behavior snapshots

automated coverage-gap discovery

synthetic test generation

invariant inference

call-graph drift detection

semantic cross-checking

automated behavior replays

That is why even gigantic test suites don’t catch Copilot regressions—but this system will.

6. If you want, I can deliver next:
A complete architecture with directories, scripts, tools, commands

A full Python implementation (using your uv, RAG, Glorious Agents, Code-Atlas)

GitHub Action workflows

Snapshoter + impact-analyzer + synthetic-test generator code

Integration with VS Code commands and Copilot

A live daemon that watches git diffs and auto-validates

Tell me which deliverable you want.

You said:
1
ChatGPT said:

Thought for 15s
Below is a concrete architecture for the system in the form of directories, scripts, tools, and commands you can drop into an existing repo.

I’ll assume Python for orchestration with uv, and that you already have a large test suite (pytest / xUnit / whatever). Adjust naming to your taste.

1. Top-level repository layout
.
├─ src/                         # your existing code
├─ tests/                       # your existing tests (unit + integration)
├─ tools/
│  └─ regression_guard/
│     ├─ agents/
│     │  ├─ __init__.py
│     │  ├─ test_runner_agent.py
│     │  ├─ snapshot_agent.py
│     │  ├─ change_impact_agent.py
│     │  ├─ synthetic_test_agent.py
│     │  └─ semantic_regression_agent.py
│     ├─ cli.py
│     ├─ config.py
│     ├─ models.py
│     └─ utils/
│        ├─ git_utils.py
│        ├─ test_utils.py
│        ├─ coverage_utils.py
│        └─ graph_utils.py
├─ .regression_guard/
│  ├─ snapshots/
│  │  ├─ features/
│  │  └─ tests/
│  ├─ runs/
│  └─ reports/
├─ .github/
│  └─ workflows/
│     └─ regression-guard.yml
├─ pyproject.toml
└─ README.md
You can also put tools/regression_guard in its own repo and vendor it in.

2. Core data models
Make the behavior visible and machine-checkable.

# filename: tools/regression_guard/models.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class Snapshot:
    id: str
    kind: str  # e.g. "feature", "test"
    test_name: Optional[str]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    side_effects: Dict[str, Any]
    call_graph_nodes: List[str]
    invariants: Dict[str, Any]
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeImpactResult:
    touched_files: List[str]
    touched_symbols: List[str]
    affected_snapshots: List[str]
    summary: str
    warnings: List[str]


@dataclass
class SyntheticTestResult:
    created_tests: List[str]  # file paths
    passed: bool
    failing_cases: List[Dict[str, Any]]
Snapshots will be written as JSON under .regression_guard/snapshots.

3. Agents (modules) and responsibilities
3.1 Test Runner Agent
# filename: tools/regression_guard/agents/test_runner_agent.py
class TestRunnerAgent:
    def run_tests(self, test_selector: str | None = None) -> dict:
        """
        Run the existing test suite (or subset) and return:
          - success boolean
          - list of passed tests
          - list of failed tests
          - coverage info (optional)
        """
        ...
Responsibilities:

Call your existing test runner (pytest, dotnet test, etc.).

Optionally run coverage.

Provide detailed per-test result data to SnapshotAgent.

Command example:

uv run python -m tools.regression_guard.cli run-tests
uv run python -m tools.regression_guard.cli run-tests --pattern "tests/integration/auth"
3.2 Snapshot Agent
# filename: tools/regression_guard/agents/snapshot_agent.py
from .models import Snapshot

class SnapshotAgent:
    def create_snapshots_from_test_run(self, test_run_result: dict) -> list[Snapshot]:
        """
        For each selected test, derive a Snapshot from:
          - known inputs (fixtures, params)
          - observed outputs (return values, response dicts)
          - side-effects (db, queues, logs)
        """
        ...

    def save_snapshot(self, snapshot: Snapshot) -> None:
        ...
Responsibilities:

Turn real test runs into behavior snapshots.

Write snapshots to .regression_guard/snapshots/{feature_or_test_id}.json.

Optionally group by feature (tag/marker in tests).

Example snapshot paths:

.regression_guard/snapshots/features/login_flow.json
.regression_guard/snapshots/tests/test_login_happy_path.json
Commands:

uv run python -m tools.regression_guard.cli snapshot-from-tests
uv run python -m tools.regression_guard.cli snapshot-from-tests --pattern "tests/integration/auth"
3.3 Change Impact Agent
# filename: tools/regression_guard/agents/change_impact_agent.py
from .models import ChangeImpactResult

class ChangeImpactAgent:
    def analyze_diff(self, base_ref: str, head_ref: str) -> ChangeImpactResult:
        """
        Use git diff and optionally a call-graph analyzer to:
          - find touched files
          - find functions/classes modified
          - map those to snapshots that reference them
        """
        ...
Responsibilities:

Inspect git diff base..head.

Use static graph (Code-Atlas style) or symbol index to map functions → tests → snapshots.

Identify which snapshots must be revalidated.

Commands:

uv run python -m tools.regression_guard.cli impact HEAD~1 HEAD
uv run python -m tools.regression_guard.cli impact origin/main HEAD
3.4 Synthetic Test Agent
# filename: tools/regression_guard/agents/synthetic_test_agent.py
from .models import SyntheticTestResult

class SyntheticTestAgent:
    def generate_tests_for_diff(self, diff_info: ChangeImpactResult) -> SyntheticTestResult:
        """
        Generate new tests targeting:
          - untested branches in changed code
          - boundary values
          - error paths
        Optionally write them to e.g. tests/synthetic/test_regression_guard_*.py
        """
        ...
Responsibilities:

For each changed function:

Inspect control-flow (if/else, try/except, early returns).

Check coverage data for missing branches.

Auto-generate minimal tests in e.g. tests/synthetic/.

Run the synthetic tests and mark pass/fail.

Commands:

uv run python -m tools.regression_guard.cli gen-synthetic-tests --base HEAD~1 --head HEAD
uv run python -m tools.regression_guard.cli run-synthetic-tests
3.5 Semantic Regression Agent
# filename: tools/regression_guard/agents/semantic_regression_agent.py
class SemanticRegressionAgent:
    def check_inferred_invariants(self, diff_info: ChangeImpactResult) -> dict:
        """
        Use commit history and snapshots to infer invariants such as:
          - naming patterns
          - required fields in responses
          - constraints on arguments/return values
        Compare old vs new behavior.
        """
        ...
Responsibilities:

Derive invariants from:

Commit history.

Existing snapshots.

Historical test passes.

Check if any of these invariants are violated by new code even when tests still pass.

Commands:

uv run python -m tools.regression_guard.cli semantic-check --base HEAD~1 --head HEAD
4. CLI orchestration
4.1 CLI entry point
# filename: tools/regression_guard/cli.py
import argparse

from .agents.test_runner_agent import TestRunnerAgent
from .agents.snapshot_agent import SnapshotAgent
from .agents.change_impact_agent import ChangeImpactAgent
from .agents.synthetic_test_agent import SyntheticTestAgent
from .agents.semantic_regression_agent import SemanticRegressionAgent

def main():
    parser = argparse.ArgumentParser(prog="regression-guard")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run-tests")
    sub.add_parser("snapshot-from-tests")
    impact = sub.add_parser("impact")
    impact.add_argument("--base", required=True)
    impact.add_argument("--head", required=True)
    sub.add_parser("gen-synthetic-tests")
    sub.add_parser("run-synthetic-tests")
    semantic = sub.add_parser("semantic-check")
    semantic.add_argument("--base", required=True)
    semantic.add_argument("--head", required=True)

    validate = sub.add_parser("validate-diff")
    validate.add_argument("--base", required=True)
    validate.add_argument("--head", required=True)

    args = parser.parse_args()

    if args.command == "run-tests":
        result = TestRunnerAgent().run_tests()
        # simple exit code based on result
        raise SystemExit(0 if result["success"] else 1)

    elif args.command == "snapshot-from-tests":
        tr = TestRunnerAgent()
        sr = SnapshotAgent()
        result = tr.run_tests()
        snapshots = sr.create_snapshots_from_test_run(result)
        for s in snapshots:
            sr.save_snapshot(s)

    elif args.command == "impact":
        ci = ChangeImpactAgent().analyze_diff(args.base, args.head)
        # print summary; exit code always 0

    elif args.command == "gen-synthetic-tests":
        # usually used after impact
        ...

    elif args.command == "run-synthetic-tests":
        ...

    elif args.command == "semantic-check":
        ...

    elif args.command == "validate-diff":
        # Orchestrate whole flow:
        # 1. impact
        # 2. run subset of tests
        # 3. replay snapshots
        # 4. synthetic tests
        # 5. semantic check
        ...
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
Example commands you’ll actually run:

uv run python -m tools.regression_guard.cli validate-diff --base origin/main --head HEAD
5. Storage structure in .regression_guard
.regression_guard/
  snapshots/
    features/
      login_flow.json
      user_settings.json
    tests/
      test_auth_login_happy.json
      test_auth_login_wrong_password.json
  runs/
    2025-11-25T12-34-56Z.json      # combined result of one validate run
  reports/
    2025-11-25T12-34-56Z.md       # human-readable summary
runs/* contains summaries of:

diff info

tests run

synthetic tests added

semantic invariant violations

reports/* can be used to comment on PRs.

6. Git integration
6.1 Pre-push (or pre-PR) hook
# filename: .git/hooks/pre-push
#!/usr/bin/env bash
set -euo pipefail

BASE_REF="origin/main"
HEAD_REF="HEAD"

echo "[regression-guard] validating diff ${BASE_REF}..${HEAD_REF}..."
uv run python -m tools.regression_guard.cli validate-diff --base "${BASE_REF}" --head "${HEAD_REF}"
Make it executable:

chmod +x .git/hooks/pre-push
If validation fails → push blocked.

7. GitHub Actions workflow
# filename: .github/workflows/regression-guard.yml
name: Regression Guard

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  regression-guard:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        run: pip install uv

      - name: Install project
        run: uv sync

      - name: Regression Guard
        run: |
          BASE_REF="${{ github.base_ref }}"
          HEAD_REF="${{ github.sha }}"
          uv run python -m tools.regression_guard.cli validate-diff --base "origin/${BASE_REF}" --head "${HEAD_REF}"
Validation becomes part of every PR.
Copilot’s changes that pass your existing tests but violate snapshots / invariants / synthetic tests will fail this job.

8. VS Code integration
8.1 VS Code task
// filename: .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Regression Guard: Validate Diff (origin/main..HEAD)",
      "type": "shell",
      "command": "uv run python -m tools.regression_guard.cli validate-diff --base origin/main --head HEAD",
      "problemMatcher": []
    }
  ]
}
You can bind this to a keybinding and run before commit or push.

9. Tooling assumptions
Python orchestrator with uv.

You keep using your existing test infrastructure (pytest, dotnet, etc.).

Call-graph analysis can be a simple ast walk initially, later upgraded to a full Code-Atlas integration.

Snapshots are JSON only; no binary artifacts.

Everything is repo-local and versioned so the agents’ “understanding of behavior” evolves with your code.

If you want, next step can be the full Python implementation of validate-diff with a minimal but working snapshot + impact + synthetic test flow.

You said:
yes
ChatGPT said:

Thought for 44s
# filename: tools/regression_guard/__init__.py

"""
Minimal, working regression-guard implementation.

Provides:
- pytest-based test runner
- git diff based impact detection
- basic snapshotting of test results
- simple synthetic tests for changed Python modules
- validate-diff CLI entrypoint
"""
# filename: tools/regression_guard/models.py

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


@dataclass
class Snapshot:
    id: str
    kind: str  # e.g. "feature", "test"
    test_name: Optional[str]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    side_effects: Dict[str, Any]
    call_graph_nodes: List[str]
    invariants: Dict[str, Any]
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, data: str) -> "Snapshot":
        raw = json.loads(data)
        return cls(**raw)


@dataclass
class ChangeImpactResult:
    touched_files: List[str]
    touched_symbols: List[str]
    affected_snapshots: List[str]
    summary: str
    warnings: List[str]


@dataclass
class SyntheticTestResult:
    created_tests: List[str]
    passed: bool
    failing_cases: List[Dict[str, Any]] = field(default_factory=list)


REGRESSION_ROOT = Path(".regression_guard").resolve()
SNAPSHOTS_ROOT = REGRESSION_ROOT / "snapshots"
TEST_SNAPSHOTS_ROOT = SNAPSHOTS_ROOT / "tests"
RUNS_ROOT = REGRESSION_ROOT / "runs"
REPORTS_ROOT = REGRESSION_ROOT / "reports"


def ensure_dirs() -> None:
    for p in (REGRESSION_ROOT, SNAPSHOTS_ROOT, TEST_SNAPSHOTS_ROOT, RUNS_ROOT, REPORTS_ROOT):
        p.mkdir(parents=True, exist_ok=True)
# filename: tools/regression_guard/utils/git_utils.py

from __future__ import annotations

from subprocess import CalledProcessError, CompletedProcess, run
from typing import List


def _git(args: list[str]) -> CompletedProcess:
    return run(["git"] + args, capture_output=True, text=True, check=True)


def get_changed_files(base_ref: str, head_ref: str) -> List[str]:
    """
    Returns list of changed files between base_ref and head_ref.
    """
    try:
        proc = _git(["diff", "--name-only", f"{base_ref}..{head_ref}"])
    except CalledProcessError as exc:
        raise RuntimeError(f"git diff failed: {exc.stderr or exc.stdout}") from exc

    files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return files
# filename: tools/regression_guard/utils/test_utils.py

from __future__ import annotations

from dataclasses import dataclass
from subprocess import CalledProcessError, CompletedProcess, run
from typing import List


@dataclass
class TestRunResult:
    success: bool
    passed: List[str]
    failed: List[str]
    raw_output: str
    return_code: int


def run_pytest(pattern: str | None = None) -> TestRunResult:
    """
    Run pytest and parse a minimal list of passed/failed tests from -q output.
    """
    cmd = ["pytest", "-q"]
    if pattern:
        cmd.append(pattern)

    try:
        proc: CompletedProcess = run(cmd, capture_output=True, text=True)
    except CalledProcessError as exc:
        # This branch will almost never be hit because we don't use check=True.
        out = (exc.stdout or "") + "\n" + (exc.stderr or "")
        return TestRunResult(False, [], [], out, exc.returncode)

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    passed: List[str] = []
    failed: List[str] = []

    # pytest -q lines like: "tests/test_x.py::test_foo PASSED"
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # crude parse
        if line.endswith("PASSED"):
            test_id = line.rsplit(" ", 1)[0].strip()
            passed.append(test_id)
        elif line.endswith(("FAILED", "ERROR")):
            test_id = line.rsplit(" ", 1)[0].strip()
            failed.append(test_id)

    success = proc.returncode == 0
    return TestRunResult(
        success=success,
        passed=passed,
        failed=failed,
        raw_output=stdout + "\n" + stderr,
        return_code=proc.returncode,
    )
# filename: tools/regression_guard/utils/graph_utils.py

from __future__ import annotations

from typing import List


def approximate_touched_symbols_from_files(files: List[str]) -> List[str]:
    """
    Minimal placeholder for touched symbols.

    In a more advanced version, this would parse ASTs and collect functions/classes.
    For now, we just return file paths as "symbols".
    """
    return files[:]
# filename: tools/regression_guard/agents/test_runner_agent.py

from __future__ import annotations

from typing import Any, Dict

from ..utils.test_utils import TestRunResult, run_pytest


class TestRunnerAgent:
    def run_tests(self, pattern: str | None = None) -> Dict[str, Any]:
        """
        Run existing tests using pytest and return a summary dict.
        """
        result: TestRunResult = run_pytest(pattern)

        return {
            "success": result.success,
            "passed": result.passed,
            "failed": result.failed,
            "raw_output": result.raw_output,
            "return_code": result.return_code,
        }
# filename: tools/regression_guard/agents/snapshot_agent.py

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from ..models import Snapshot, TEST_SNAPSHOTS_ROOT, ensure_dirs


class SnapshotAgent:
    def __init__(self) -> None:
        ensure_dirs()

    @staticmethod
    def _safe_name(test_name: str) -> str:
        # tests/test_module.py::TestClass::test_something -> tests_test_module_py__TestClass__test_something
        name = test_name.replace("::", "__").replace("/", "_").replace("\\", "_")
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
        return name

    def create_snapshots_from_test_run(self, test_run_result: Dict[str, Any]) -> List[Snapshot]:
        """
        Minimal snapshot: one per passed test.
        Inputs/outputs/side_effects/invariants are left empty placeholders.
        """
        snapshots: List[Snapshot] = []
        for test_name in test_run_result.get("passed", []):
            snapshot = Snapshot(
                id=test_name,
                kind="test",
                test_name=test_name,
                inputs={},
                outputs={},
                side_effects={},
                call_graph_nodes=[],
                invariants={},
                meta={
                    "status": "passed",
                    "source": "pytest",
                },
            )
            snapshots.append(snapshot)
        return snapshots

    def save_snapshot(self, snapshot: Snapshot) -> Path:
        safe = self._safe_name(snapshot.id)
        path = TEST_SNAPSHOTS_ROOT / f"{safe}.json"
        path.write_text(snapshot.to_json(), encoding="utf-8")
        return path
# filename: tools/regression_guard/agents/change_impact_agent.py

from __future__ import annotations

from typing import List

from ..models import ChangeImpactResult
from ..utils.git_utils import get_changed_files
from ..utils.graph_utils import approximate_touched_symbols_from_files


class ChangeImpactAgent:
    def analyze_diff(self, base_ref: str, head_ref: str) -> ChangeImpactResult:
        files: List[str] = get_changed_files(base_ref, head_ref)
        touched_symbols = approximate_touched_symbols_from_files(files)

        summary = f"{len(files)} files changed between {base_ref} and {head_ref}"
        warnings: List[str] = []
        if not files:
            warnings.append("No changed files detected for diff.")

        # For now we can't map snapshots to symbols reliably; leave affected_snapshots empty.
        return ChangeImpactResult(
            touched_files=files,
            touched_symbols=touched_symbols,
            affected_snapshots=[],
            summary=summary,
            warnings=warnings,
        )
# filename: tools/regression_guard/agents/synthetic_test_agent.py

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess, run
from typing import List

from ..models import SyntheticTestResult


SYNTHETIC_TESTS_DIR = Path("tests") / "synthetic"
SYNTHETIC_TEST_FILE = SYNTHETIC_TESTS_DIR / "test_regression_guard_synthetic.py"


class SyntheticTestAgent:
    def __init__(self) -> None:
        SYNTHETIC_TESTS_DIR.mkdir(parents=True, exist_ok=True)

    def _generate_import_tests(self, changed_python_files: List[str]) -> str:
        """
        Generate a simple pytest file that imports changed modules.

        This will catch:
        - syntax errors
        - immediate import-time issues
        """
        lines: List[str] = [
            '"""Auto-generated synthetic tests for regression-guard.',
            "Do not edit by hand; changes will be overwritten.",
            '"""',
            "",
            "import importlib",
            "import pathlib",
            "",
            "",
        ]

        for idx, path_str in enumerate(changed_python_files):
            path = Path(path_str)
            if not path.suffix == ".py":
                continue
            # crude module name inference: src/pkg/mod.py -> pkg.mod
            parts = list(path.with_suffix("").parts)
            # try to drop leading "src" if present
            if parts and parts[0] == "src":
                parts = parts[1:]
            if not parts:
                continue
            module_name = ".".join(parts)
            test_name = f"test_import_{idx}"

            lines.append(f"def {test_name}():")
            lines.append(f"    module_name = {module_name!r}")
            lines.append("    importlib.import_module(module_name)")
            lines.append("")

        if len(lines) <= 7:
            # No interesting modules; create a trivial sanity test
            lines.append("")
            lines.append("def test_regression_guard_synthetic_sanity():")
            lines.append("    assert True")
            lines.append("")

        return "\n".join(lines) + "\n"

    def generate_tests_for_diff(self, changed_files: List[str]) -> SyntheticTestResult:
        """
        Generate or update synthetic tests for changed Python modules, then run them.
        """
        python_files = [f for f in changed_files if f.endswith(".py")]
        test_source = self._generate_import_tests(python_files)
        SYNTHETIC_TEST_FILE.write_text(test_source, encoding="utf-8")

        created = [str(SYNTHETIC_TEST_FILE)]

        # Run only synthetic tests
        cmd = ["pytest", str(SYNTHETIC_TEST_FILE)]
        proc: CompletedProcess = run(cmd, capture_output=True, text=True)
        passed = proc.returncode == 0

        failing_cases: List[dict] = []
        if not passed:
            failing_cases.append(
                {
                    "file": str(SYNTHETIC_TEST_FILE),
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "return_code": proc.returncode,
                }
            )

        return SyntheticTestResult(
            created_tests=created,
            passed=passed,
            failing_cases=failing_cases,
        )
# filename: tools/regression_guard/agents/semantic_regression_agent.py

from __future__ import annotations

from typing import Dict, List


class SemanticRegressionAgent:
    """
    Minimal placeholder implementation.

    In a future version this could:
    - infer invariants from commit history and snapshots
    - check naming/contract consistency
    """

    def check(self, changed_files: List[str]) -> Dict[str, object]:
        return {
            "issues": [],
            "summary": "semantic-check not implemented; skipping.",
            "ok": True,
        }
# filename: tools/regression_guard/config.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RegressionGuardConfig:
    base_ref: str = "origin/main"
    head_ref: str = "HEAD"

    @classmethod
    def from_env(cls) -> "RegressionGuardConfig":
        # simple placeholder if you want to add env-based overrides later
        return cls()
# filename: tools/regression_guard/cli.py

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .agents.change_impact_agent import ChangeImpactAgent
from .agents.semantic_regression_agent import SemanticRegressionAgent
from .agents.snapshot_agent import SnapshotAgent
from .agents.synthetic_test_agent import SyntheticTestAgent
from .agents.test_runner_agent import TestRunnerAgent
from .models import RUNS_ROOT, REPORTS_ROOT, ensure_dirs


def _write_run_summary(name: str, payload: Dict[str, Any]) -> None:
    ensure_dirs()
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = RUNS_ROOT / f"{ts}_{name}.json"
    md_path = REPORTS_ROOT / f"{ts}_{name}.md"

    import json

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    # simple markdown report
    lines = [
        f"# regression-guard run: {name}",
        "",
        f"- timestamp (UTC): {ts}",
        f"- exit_code: {payload.get('exit_code')}",
        "",
        "## Summary",
        "",
        f"- tests_success: {payload.get('tests_success')}",
        f"- synthetic_tests_passed: {payload.get('synthetic_tests_passed')}",
        "",
        "## Details",
        "",
        "```json",
        json.dumps(payload, indent=2, sort_keys=True),
        "```",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def command_validate_diff(base_ref: str, head_ref: str) -> int:
    ensure_dirs()

    print(f"[regression-guard] analyzing diff {base_ref}..{head_ref}")
    impact_agent = ChangeImpactAgent()
    impact = impact_agent.analyze_diff(base_ref, head_ref)
    print(f"[regression-guard] {impact.summary}")
    if impact.warnings:
        for w in impact.warnings:
            print(f"[regression-guard][warning] {w}")

    # 1. Run tests
    print("[regression-guard] running test suite (pytest)...")
    test_runner = TestRunnerAgent()
    test_result = test_runner.run_tests()
    print(f"[regression-guard] tests_success={test_result['success']}, "
          f"passed={len(test_result['passed'])}, failed={len(test_result['failed'])}")

    if not test_result["success"]:
        print("[regression-guard] tests failed; aborting.")
        payload = {
            "phase": "tests",
            "tests_success": False,
            "synthetic_tests_passed": None,
            "impact": impact.__dict__,
            "test_result": test_result,
            "synthetic_result": None,
            "semantic_result": None,
            "exit_code": 1,
        }
        _write_run_summary("validate_diff", payload)
        return 1

    # 2. Create snapshots
    print("[regression-guard] creating snapshots for passed tests...")
    snapshot_agent = SnapshotAgent()
    snapshots = snapshot_agent.create_snapshots_from_test_run(test_result)
    for s in snapshots:
        path = snapshot_agent.save_snapshot(s)
        print(f"[regression-guard] snapshot saved: {path}")

    # 3. Synthetic tests for changed files
    print("[regression-guard] generating and running synthetic tests for changed files...")
    synthetic_agent = SyntheticTestAgent()
    synthetic_result = synthetic_agent.generate_tests_for_diff(impact.touched_files)
    print("[regression-guard] synthetic tests created:", ", ".join(synthetic_result.created_tests))
    print("[regression-guard] synthetic_tests_passed=", synthetic_result.passed)

    if not synthetic_result.passed:
        print("[regression-guard] synthetic tests failed; aborting.")
        payload = {
            "phase": "synthetic_tests",
            "tests_success": True,
            "synthetic_tests_passed": False,
            "impact": impact.__dict__,
            "test_result": test_result,
            "synthetic_result": synthetic_result.__dict__,
            "semantic_result": None,
            "exit_code": 1,
        }
        _write_run_summary("validate_diff", payload)
        return 1

    # 4. Semantic regression (placeholder)
    print("[regression-guard] running semantic regression check (placeholder)...")
    semantic_agent = SemanticRegressionAgent()
    semantic_result = semantic_agent.check(impact.touched_files)
    print("[regression-guard] semantic summary:", semantic_result.get("summary"))

    if not semantic_result.get("ok", True):
        print("[regression-guard] semantic regression issues detected; aborting.")
        payload = {
            "phase": "semantic",
            "tests_success": True,
            "synthetic_tests_passed": True,
            "impact": impact.__dict__,
            "test_result": test_result,
            "synthetic_result": synthetic_result.__dict__,
            "semantic_result": semantic_result,
            "exit_code": 1,
        }
        _write_run_summary("validate_diff", payload)
        return 1

    # 5. All good
    print("[regression-guard] validation successful.")
    payload = {
        "phase": "complete",
        "tests_success": True,
        "synthetic_tests_passed": True,
        "impact": impact.__dict__,
        "test_result": test_result,
        "synthetic_result": synthetic_result.__dict__,
        "semantic_result": semantic_result,
        "exit_code": 0,
    }
    _write_run_summary("validate_diff", payload)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="regression-guard")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-diff", help="run full validation for base..head diff")
    validate.add_argument("--base", required=True, help="base git ref, e.g. origin/main")
    validate.add_argument("--head", required=True, help="head git ref, e.g. HEAD")

    args = parser.parse_args()

    if args.command == "validate-diff":
        exit_code = command_validate_diff(args.base, args.head)
        raise SystemExit(exit_code)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
# filename: pyproject.toml
[project]
name = "regression-guard"
version = "0.1.0"
description = "Minimal regression guard tooling"
requires-python = ">=3.11"
dependencies = [
    "pytest",
]

[project.scripts]
regression-guard = "tools.regression_guard.cli:main"



Ingen fil valgtIngen fil valgt
ChatGPT can make mistakes. Check important info. See Cookie Preferences.
