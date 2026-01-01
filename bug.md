FEAT-025 | Q1: Credential handling approach: - Volume mount ~/.local/share/opencode/auth.json into container (recommended)
FEAT-025 | Q2: Port range: Dynamic: 8000-9000 (search for available) But range can be overriden using .env
FEAT-025 | Q3: Container lifecycle: Always background, print container ID
FEAT-026 | Q1: Auto-detection scope_: - Configurable allowlist/denylist with .claude, .opencode and github copilot cli as defaults
FEAT-026 | Q2: Conflict handling: User flag --override to control behavior
FEAT-026 | Q3: Build-time approach: Build custom images with docker build before provisioning
FEAT-027 | Q1: Archive support: support .zip only
FEAT-027 | Q2: Cache policy: ETag/Last-Modified support (HTTP conditional GET)
FEAT-027 | Q3: Authentication: Bearer token via --url-token or env var
FEAT-028 | Q1: Implementation approach: Wrapper around docker cp (simple, recommended)
FEAT-028 | Q2: Container ID specification: Require full container ID (exact match)
FEAT-028 | Q3: Default paths: No defaults, require both paths
FEAT-029 | Q1: State schema: Minimal: {"step": 5, "last_issue": "FEAT-025", "cycles": 1}
FEAT-029 | Q2: Loop termination: Stop when all issues completed (natural termination) or Stop after N cycles (configurable via flag)
FEAT-029 | Q3: Error recovery: Abort on error (fail-fast) or Skip failed step, continue to next (resilient), configurable with fail-fast as default
FEAT-030 | Q1: Required vs optional checks: Configurable via --strict and --lenient flags
FEAT-030 | Q2: Git state handling: Require clean git (abort if dirty) if --strict flag applied
 FEAT-030 | Q3: Auto-fix capability: Auto-fix ALL fixable issues 
FEAT-031 | Q1: Error classification: use critical, high, medium, low
FEAT-031 | Q2: Retry behavior: Exponential backoff (1s, 2s, 4s)
FEAT-031 | Q3: Escalation destination: Append to error log file
FEAT-032 | Q1: Issue selection: all three options with CLI arguments
FEAT-032 | Q2: Ambiguity handling: Refuse underspecified issues (require issue-readiness first)
FEAT-032 | Q3: Output format: Both (stdout + file)
FEAT-033 | Q1: Marker format: YAML frontmatter: progressive: true
FEAT-033 | Q2: Priority levels: 5 levels: critical, high, medium, low, discard
FEAT-033 | Q3: Estimation method: Actual tokenizer (tiktoken, slow but accurate)
FEAT-034 | Q1: Document location: .work/prompts-symbiosis.md (project documentation)
FEAT-034 | Q2: Format style: Both (graph + table fallback)
FEAT-034 | Q3: Workflow scope: 10 workflows covering all agent-loop scenarios

