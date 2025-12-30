"""Core functionality for repo-agent.

This module contains the main logic for configuring and running LLM-powered
code agents in Docker containers. It handles configuration resolution, Docker
command building, and orchestrating the full workflow from cloning repositories
to creating pull requests.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter  # type: ignore[import-untyped]

# Module logger
logger = logging.getLogger(__name__)

# Default values for configuration
DEFAULT_DOCKER_IMAGE = "repo-agent:latest"
DEFAULT_GIT_USER_NAME = "repo-agent"
DEFAULT_GIT_USER_EMAIL = "repo-agent@example.com"
DEFAULT_BRANCH_PREFIX = "auto/repo-agent-"
DEFAULT_PR_TITLE = "Automated changes via repo-agent"
DEFAULT_PR_BODY = (
    "This PR was generated automatically by repo-agent using a configurable code tool."
)
DEFAULT_COMMIT_MESSAGE = "chore: automated changes via repo-agent"

# OpenCode configuration paths
OPENCODE_CONFIG_FILENAME = "opencode.json"
OPENCODE_CONFIG_CONTAINER_PATH = "/root/.config/opencode/opencode.json"
OPENCODE_AUTH_PATH = "~/.local/share/opencode/auth.json"

# Boolean string values
BOOL_TRUE = "1"
BOOL_FALSE = "0"


# Docker image name validation pattern
# Pattern: [registry/][namespace/]name[:tag|@digest]
# Simplified for common cases: registry.io/namespace/image:tag
DOCKER_IMAGE_PATTERN = re.compile(
    r"^("
    r"(localhost/|[^/]+/|)"  # optional registry (localhost/ or registry.io/)
    r"[a-z0-9]+([._-][a-z0-9]+)*"  # first component (namespace or image)
    r"(/[a-z0-9]+([._-][a-z0-9]+)*)*"  # optional additional components
    r"(:[a-zA-Z0-9]+([._-][a-zA-Z0-9]+)*)?"  # optional tag
    r")$"
)


def validate_docker_image(image: str) -> None:
    """Validate Docker image name format.

    Args:
        image: Docker image name to validate.

    Raises:
        ValueError: If image name is invalid.
    """
    logger.debug(f"Validating Docker image: {image}")
    if not DOCKER_IMAGE_PATTERN.match(image):
        logger.error(f"Invalid Docker image name: {image}")
        raise ValueError(
            f"Invalid docker image name: {image}. Expected format: [registry/]namespace/image[:tag]"
        )
    logger.debug(f"Docker image validation passed: {image}")


def validate_dockerfile_path(dockerfile: Path | None, project_root: Path) -> None:
    """Validate Dockerfile path is within project directory.

    Args:
        dockerfile: Path to Dockerfile (or None).
        project_root: Root directory of the project.

    Raises:
        ValueError: If dockerfile path escapes project directory.
    """
    if dockerfile is None:
        logger.debug("No Dockerfile specified, using default")
        return

    logger.debug(f"Validating Dockerfile path: {dockerfile} within {project_root}")
    try:
        resolved = dockerfile.resolve().relative_to(project_root.resolve())
        logger.debug(f"Dockerfile path validation passed: {resolved}")
    except ValueError:
        logger.error(f"Dockerfile outside project directory: {dockerfile}")
        raise ValueError(f"Dockerfile must be within project directory: {dockerfile}") from None


class RepoAgentError(Exception):
    """Base exception for repo-agent failures.

    This exception is raised for any configuration errors, validation failures,
    or runtime errors specific to repo-agent operations.
    """


@dataclass
class RunConfig:
    """Configuration for a repo-agent run.

    This dataclass holds all configuration values needed to execute a repo-agent
    workflow, including repository settings, Docker configuration, authentication,
    LLM parameters, and tool settings. Values are resolved from frontmatter and
    CLI overrides.

    Attributes:
        instructions_path: Path to the markdown instructions file.
        repo_url: Git repository URL (HTTPS or SSH).
        base_branch: Base branch to branch from (e.g., 'main'), or None for auto-detect.
        branch: Target branch name for changes.
        docker_image: Docker image to use for running the tool.
        dockerfile: Optional path to Dockerfile to build before running.
        use_ssh: Whether to use SSH authentication instead of HTTPS.
        ssh_key_dir: Directory containing SSH keys to mount, if use_ssh is True.
        github_token: GitHub personal access token for API operations.
        api_key: API key for LLM provider (e.g., OpenRouter).
        git_user_name: Git user.name for commits.
        git_user_email: Git user.email for commits.
        model: LLM model identifier (e.g., 'openai/gpt-4').
        strategy: Execution strategy, either 'agentic' or 'direct'.
        pr_title: Title for the pull request.
        pr_body: Description/body for the pull request.
        auto_commit: Whether to automatically commit and push changes.
        create_pr: Whether to create a pull request after pushing.
        create_repo_if_missing: Whether to create the GitHub repo if it doesn't exist.
        commit_message: Message for automatic commits.
        tool_name: Name of the code tool (e.g., 'opencode', 'claude-code').
        tool_entrypoint: Command to run the tool (e.g., 'opencode run').
        tool_args: Additional arguments to pass to the tool.
        prompt_header_agentic: Prompt header for agentic strategy.
        prompt_header_direct: Prompt header for direct strategy.
        dry_run: If True, print Docker command instead of executing.
    """

    # Core
    instructions_path: Path
    repo_url: str
    base_branch: str | None
    branch: str

    # Docker
    docker_image: str
    dockerfile: Path | None

    # Auth / git
    use_ssh: bool
    ssh_key_dir: Path | None
    github_token: str | None
    api_key: str | None
    git_user_name: str
    git_user_email: str

    # LLM / strategy
    model: str
    strategy: str  # "agentic" or "direct"

    # PR / commit
    pr_title: str
    pr_body: str
    auto_commit: bool
    create_pr: bool
    create_repo_if_missing: bool
    commit_message: str

    # Tool config (generic, not tied to opencode)
    tool_name: str
    tool_entrypoint: str
    tool_args: dict[str, Any]
    prompt_header_agentic: str
    prompt_header_direct: str

    # Misc
    dry_run: bool


def _bool_meta(meta: Mapping[str, Any], key: str, default: bool) -> bool:
    """Parse a boolean value from frontmatter metadata.

    Handles multiple boolean representations: native bools, numeric strings
    ('1', '0'), and text values ('true', 'false', 'yes', 'no', 'on', 'off').
    Case-insensitive for string values.

    Args:
        meta: Metadata dictionary from frontmatter.
        key: Key to look up in metadata.
        default: Default value if key is missing.

    Returns:
        Boolean value parsed from metadata, or default if key not found.
    """
    if key not in meta:
        return default
    v = meta[key]
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in {"1", "true", "yes", "on"}
    return bool(v)


def _load_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    """Load and parse a markdown file with YAML frontmatter.

    Args:
        path: Path to the markdown file.

    Returns:
        A tuple of (metadata dict, content string). The content is stripped
        of leading/trailing whitespace. If metadata is None, returns empty dict.
    """
    post = frontmatter.load(path)
    meta = dict(post.metadata or {})
    content = post.content or ""
    return meta, content.strip()


def _resolve_config(
    instructions_path: Path,
    cli_overrides: Mapping[str, Any],
) -> tuple[RunConfig, str]:
    """Resolve final configuration by merging frontmatter and CLI overrides.

    Loads the instruction file frontmatter, applies CLI overrides, resolves
    environment variables, validates required fields, and constructs a complete
    RunConfig object with all necessary defaults filled in.

    CLI overrides take precedence over frontmatter values when both are provided.

    Args:
        instructions_path: Path to the markdown instructions file.
        cli_overrides: Dictionary of command-line parameter overrides.

    Returns:
        A tuple of (RunConfig object, instructions body text).

    Raises:
        RepoAgentError: If required fields (repo_url, model) are missing,
            strategy is invalid, or other configuration errors occur.
    """
    logger.info(f"Resolving configuration from: {instructions_path}")
    logger.debug(f"CLI overrides: {list(cli_overrides.keys())}")
    meta, content = _load_frontmatter(instructions_path)
    logger.debug(f"Loaded frontmatter with keys: {list(meta.keys())}")

    def get(key: str, default: Any = None) -> Any:
        if key in cli_overrides and cli_overrides[key] is not None:
            return cli_overrides[key]
        return meta.get(key, default)

    # Required: repo_url
    repo_url = get("repo_url")
    if not repo_url:
        raise RepoAgentError("repo_url must be provided via frontmatter or --repo-url")

    # Branching
    base_branch = get("base_branch")
    branch = get("branch") or f"{DEFAULT_BRANCH_PREFIX}{os.getpid()}"

    # Docker
    docker_image = get("docker_image", DEFAULT_DOCKER_IMAGE)
    dockerfile_val = get("dockerfile")
    dockerfile = cli_overrides.get("dockerfile") or dockerfile_val
    if isinstance(dockerfile, str):
        dockerfile = (instructions_path.parent / dockerfile).resolve()
    elif isinstance(dockerfile, Path):
        dockerfile = dockerfile.resolve()
    else:
        dockerfile = None

    # Auth / SSH
    use_ssh = bool(get("use_ssh", False) or get("auth") == "ssh" or cli_overrides.get("use_ssh"))
    ssh_key_dir_val = cli_overrides.get("ssh_key_dir") or get("ssh_key_dir")
    ssh_key_dir: Path | None = None
    if ssh_key_dir_val:
        ssh_key_dir = Path(ssh_key_dir_val).expanduser().resolve()

    # Model
    model = get("model")
    if not model:
        raise RepoAgentError("model must be provided via frontmatter or --model")

    # Strategy (generic, but we support legacy opencode_strategy key)
    strategy_val = (
        cli_overrides.get("strategy") or meta.get("strategy") or meta.get("opencode_strategy")
    )
    strategy = (strategy_val or "agentic").lower()
    if strategy not in {"agentic", "direct"}:
        raise RepoAgentError("strategy must be 'agentic' or 'direct'")

    # PR / commit
    pr_title = get("pr_title", DEFAULT_PR_TITLE)
    pr_body = get("pr_body", DEFAULT_PR_BODY)

    # auto_commit
    ac_override = cli_overrides.get("auto_commit")
    if ac_override is not None:
        auto_commit = bool(ac_override)
    else:
        auto_commit = _bool_meta(meta, "auto_commit", True)

    # create_pr
    cp_override = cli_overrides.get("create_pr")
    if cp_override is not None:
        create_pr = bool(cp_override)
    else:
        create_pr = _bool_meta(meta, "create_pr", True)

    # create_repo_if_missing
    cr_override = cli_overrides.get("create_repo_if_missing")
    if cr_override is not None:
        create_repo_if_missing = bool(cr_override)
    else:
        create_repo_if_missing = _bool_meta(meta, "create_repo_if_missing", False)

    commit_message = get("commit_message", DEFAULT_COMMIT_MESSAGE)

    # Git identity
    git_user_name = get("git_user_name", DEFAULT_GIT_USER_NAME)
    git_user_email = get("git_user_email", DEFAULT_GIT_USER_EMAIL)

    # GitHub token resolution (frontmatter + env indirection)
    github_token: str | None = None
    raw_token = get("github_token")
    token_env_name = get("github_token_env")
    if raw_token:
        github_token = str(raw_token)
    elif token_env_name and os.getenv(str(token_env_name)):
        github_token = os.getenv(str(token_env_name))
    elif os.getenv("GITHUB_TOKEN"):
        github_token = os.getenv("GITHUB_TOKEN")
    elif os.getenv("GH_TOKEN"):
        github_token = os.getenv("GH_TOKEN")

    # API key resolution (for LLM providers like OpenRouter)
    api_key: str | None = None
    raw_api_key = get("api_key")
    api_key_env_name = get("api_key_env")
    if raw_api_key:
        api_key = str(raw_api_key)
    elif api_key_env_name and os.getenv(str(api_key_env_name)):
        api_key = os.getenv(str(api_key_env_name))

    # Tool config
    tool_meta = meta.get("tool", {}) or {}
    tool_name = tool_meta.get("name") or "opencode"
    tool_entrypoint = (
        cli_overrides.get("tool_entrypoint") or tool_meta.get("entrypoint") or "opencode run"
    )
    tool_args = tool_meta.get("args") or {}

    header_agentic = tool_meta.get("prompt_header_agentic") or (
        "You are an autonomous coding agent working on this repository. "
        "Plan your approach, then execute the necessary edits to implement "
        "the requested changes, keeping commits logical and cohesive."
    )
    header_direct = tool_meta.get("prompt_header_direct") or (
        "Apply the following changes directly to this repository. "
        "Make minimal, focused edits and keep the diff small and coherent."
    )

    dry_run = bool(cli_overrides.get("dry_run") or False)

    cfg = RunConfig(
        instructions_path=instructions_path,
        repo_url=str(repo_url),
        base_branch=str(base_branch) if base_branch else None,
        branch=str(branch),
        docker_image=str(docker_image),
        dockerfile=dockerfile,
        use_ssh=use_ssh,
        ssh_key_dir=ssh_key_dir,
        github_token=github_token,
        api_key=api_key,
        git_user_name=str(git_user_name),
        git_user_email=str(git_user_email),
        model=str(model),
        strategy=strategy,
        pr_title=str(pr_title),
        pr_body=str(pr_body),
        auto_commit=auto_commit,
        create_pr=create_pr,
        create_repo_if_missing=create_repo_if_missing,
        commit_message=str(commit_message),
        tool_name=str(tool_name),
        tool_entrypoint=str(tool_entrypoint),
        tool_args=dict(tool_args),
        prompt_header_agentic=str(header_agentic),
        prompt_header_direct=str(header_direct),
        dry_run=dry_run,
    )
    # Log final configuration (with sensitive values masked)
    logger.info(
        f"Configuration resolved: repo_url={cfg.repo_url}, model={cfg.model}, strategy={cfg.strategy}"
    )
    logger.debug(f"Branch configuration: base_branch={cfg.base_branch}, target_branch={cfg.branch}")
    logger.debug(f"Docker configuration: image={cfg.docker_image}, dockerfile={cfg.dockerfile}")
    logger.debug(
        f"Authentication: use_ssh={cfg.use_ssh}, has_github_token={bool(cfg.github_token)}, has_api_key={bool(cfg.api_key)}"
    )
    return cfg, content


def _docker_build_if_needed(cfg: RunConfig) -> None:
    """Build a Docker image from a Dockerfile if one is specified.

    If cfg.dockerfile is set, executes `docker build` to create the image
    tagged with cfg.docker_image. If dockerfile is None, this is a no-op.

    Args:
        cfg: Configuration object containing dockerfile path and image tag.

    Raises:
        subprocess.CalledProcessError: If docker build command fails.
        ValueError: If docker image name or dockerfile path is invalid.
    """
    if not cfg.dockerfile:
        logger.debug("No Dockerfile specified, skipping build")
        return

    logger.info(f"Building Docker image: {cfg.docker_image} from {cfg.dockerfile}")
    # Validate docker image name
    validate_docker_image(cfg.docker_image)

    # Validate dockerfile path is within project
    project_root = cfg.instructions_path.parent
    validate_dockerfile_path(cfg.dockerfile, project_root)

    build_cmd = [
        "docker",
        "build",
        "-t",
        cfg.docker_image,
        "-f",
        str(cfg.dockerfile),
        str(cfg.dockerfile.parent),
    ]
    logger.debug(f"Running: {' '.join(build_cmd)}")
    subprocess.run(build_cmd, check=True)
    logger.info(f"Docker image built successfully: {cfg.docker_image}")


def _build_env_args(cfg: RunConfig) -> list[str]:
    """Build Docker environment variable arguments from configuration.

    Creates environment variables for repository, model, strategy, git config,
    tool settings, and authentication tokens.

    Args:
        cfg: Configuration object with all settings.

    Returns:
        List of Docker CLI arguments in format ['-e', 'KEY=value', '-e', 'KEY2=value2', ...].
    """
    env_map: dict[str, str] = {
        "REPO_URL": cfg.repo_url,
        "BASE_BRANCH": cfg.base_branch or "",
        "TARGET_BRANCH": cfg.branch,
        "MODEL": cfg.model,
        "STRATEGY": cfg.strategy,
        "AUTO_COMMIT": BOOL_TRUE if cfg.auto_commit else BOOL_FALSE,
        "CREATE_PR": BOOL_TRUE if cfg.create_pr else BOOL_FALSE,
        "CREATE_REPO_IF_MISSING": BOOL_TRUE if cfg.create_repo_if_missing else BOOL_FALSE,
        "COMMIT_MESSAGE": cfg.commit_message,
        "PR_TITLE": cfg.pr_title,
        "PR_BODY": cfg.pr_body,
        "GIT_USER_NAME": cfg.git_user_name,
        "GIT_USER_EMAIL": cfg.git_user_email,
        "TOOL_NAME": cfg.tool_name,
        "TOOL_ENTRYPOINT": cfg.tool_entrypoint,
        "PROMPT_HEADER_AGENTIC": cfg.prompt_header_agentic,
        "PROMPT_HEADER_DIRECT": cfg.prompt_header_direct,
    }

    if cfg.github_token:
        env_map["GITHUB_TOKEN"] = cfg.github_token
        env_map["GH_TOKEN"] = cfg.github_token

    # Pass API key to Docker if provided (for LLM providers)
    if cfg.api_key:
        env_map["OPENROUTER_API_KEY"] = cfg.api_key

    # Serialize tool_args into CLI-style arguments
    if cfg.tool_args:
        pieces: list[str] = []
        for k, v in cfg.tool_args.items():
            flag = "--" + str(k).replace("_", "-")
            pieces.append(flag)
            if not isinstance(v, bool):
                pieces.append(str(v))
        env_map["TOOL_EXTRA_ARGS"] = " ".join(shlex.quote(p) for p in pieces)
    else:
        env_map["TOOL_EXTRA_ARGS"] = ""

    env_args: list[str] = []
    for k, v in env_map.items():
        env_args.extend(["-e", f"{k}={v}"])

    return env_args


def _build_volume_args(
    cfg: RunConfig,
    workdir: Path,
    instructions_body_path: Path,
) -> list[str]:
    """Build Docker volume mount arguments.

    Creates volume mounts for workspace, instruction files, optional SSH keys,
    and optional OpenCode configuration.

    Args:
        cfg: Configuration object with all settings.
        workdir: Temporary directory for the workspace.
        instructions_body_path: Path to the instructions content file.

    Returns:
        List of Docker CLI volume arguments in format ['-v', 'host:container', ...].
    """
    volume_args = [
        "-v",
        f"{workdir}:/workspace",
        "-v",
        f"{instructions_body_path}:/workspace/instructions_body.md:ro",
    ]

    # Mount opencode.json config if it exists
    opencode_config = cfg.instructions_path.parent / OPENCODE_CONFIG_FILENAME
    if opencode_config.exists():
        volume_args.extend(
            [
                "-v",
                f"{opencode_config}:{OPENCODE_CONFIG_CONTAINER_PATH}:ro",
            ]
        )

    if cfg.use_ssh:
        ssh_dir = cfg.ssh_key_dir or Path.home() / ".ssh"
        volume_args.extend(
            ["-v", f"{ssh_dir}:/root/.ssh:ro"],
        )

    return volume_args


def _generate_inner_script() -> str:
    """Generate the bash script that runs inside the Docker container.

    This script handles the complete workflow:
    1. Validates required environment variables
    2. Optionally creates the GitHub repository if it doesn't exist
    3. Clones the repository
    4. Configures git credentials and identity
    5. Creates/checks out the target branch
    6. Constructs and runs the tool prompt
    7. Commits and pushes changes if auto_commit is enabled
    8. Creates a pull request if create_pr is enabled

    Returns:
        Complete bash script as a string.
    """
    # Load the bash script from docker-entrypoint.sh
    # This allows independent maintenance and testing
    script_path = Path(__file__).parent / "docker-entrypoint.sh"
    if not script_path.exists():
        raise FileNotFoundError(f"Docker entrypoint script not found: {script_path}")
    return script_path.read_text(encoding="utf-8")


def _build_docker_run_cmd(
    cfg: RunConfig,
    workdir: Path,
    instructions_body_path: Path,
) -> list[str]:
    """Build the complete Docker run command with all environment variables and volumes.

    Constructs a Docker run command that:
    - Sets up environment variables for the tool
    - Mounts workspace and instruction files
    - Optionally mounts SSH keys and OpenCode config
    - Executes a bash script that clones the repo, runs the tool, and creates a PR

    Args:
        cfg: Configuration object with all settings.
        workdir: Temporary directory for the workspace.
        instructions_body_path: Path to the instructions content file.

    Returns:
        Complete Docker run command as a list of strings.

    Raises:
        ValueError: If docker image name is invalid.
    """
    logger.info("Building Docker run command")
    env_args = _build_env_args(cfg)
    volume_args = _build_volume_args(cfg, workdir, instructions_body_path)
    inner_script = _generate_inner_script()

    # Add OpenCode config environment variable if the config file exists
    opencode_config = cfg.instructions_path.parent / OPENCODE_CONFIG_FILENAME
    if opencode_config.exists():
        logger.debug(f"Found OpenCode config at: {opencode_config}")
        env_args.extend(["-e", f"OPENCODE_CONFIG={OPENCODE_CONFIG_CONTAINER_PATH}"])

    # Validate docker image name before using in command
    validate_docker_image(cfg.docker_image)

    cmd = [
        "docker",
        "run",
        "--rm",
        *env_args,
        *volume_args,
        cfg.docker_image,
        "bash",
        "-lc",
        inner_script,
    ]
    return cmd


def run_from_markdown(
    instructions_path: Path,
    *,
    repo_url: str | None = None,
    branch: str | None = None,
    base_branch: str | None = None,
    docker_image: str | None = None,
    dockerfile: Path | None = None,
    use_ssh: bool | None = None,
    ssh_key_dir: Path | None = None,
    model: str | None = None,
    strategy: str | None = None,
    pr_title: str | None = None,
    pr_body: str | None = None,
    github_token: str | None = None,
    auto_commit: bool | None = None,
    create_pr: bool | None = None,
    create_repo_if_missing: bool | None = None,
    commit_message: str | None = None,
    git_user_name: str | None = None,
    git_user_email: str | None = None,
    tool_entrypoint: str | None = None,
    dry_run: bool = False,
) -> None:
    """Execute the full repo-agent workflow from a markdown instruction file.

    This is the main entry point for running repo-agent. It:
    1. Loads and parses the instruction file with frontmatter
    2. Merges configuration from frontmatter and CLI overrides
    3. Builds Docker image if needed
    4. Constructs and executes Docker run command
    5. The Docker container handles: cloning, running the tool, committing, and creating PR

    All parameters are optional and override corresponding frontmatter values when provided.

    Args:
        instructions_path: Path to markdown file with YAML frontmatter and instructions.
        repo_url: Override repository URL.
        branch: Override target branch name.
        base_branch: Override base branch to branch from.
        docker_image: Override Docker image to use.
        dockerfile: Override Dockerfile to build.
        use_ssh: Override SSH authentication setting.
        ssh_key_dir: Override SSH key directory path.
        model: Override LLM model identifier.
        strategy: Override strategy ('agentic' or 'direct').
        pr_title: Override pull request title.
        pr_body: Override pull request body/description.
        github_token: Override GitHub token (otherwise uses env vars).
        auto_commit: Override auto-commit setting.
        create_pr: Override PR creation setting.
        create_repo_if_missing: Override repository auto-creation setting.
        commit_message: Override commit message.
        git_user_name: Override git user.name.
        git_user_email: Override git user.email.
        tool_entrypoint: Override tool entrypoint command.
        dry_run: If True, prints Docker command without executing.

    Raises:
        RepoAgentError: If instructions file is not found, required configuration
            is missing, or validation fails.
        subprocess.CalledProcessError: If Docker build or run commands fail.
    """
    logger.info(f"Starting repo-agent workflow for: {instructions_path}")
    instructions_path = instructions_path.expanduser().resolve()
    if not instructions_path.is_file():
        logger.error(f"Instructions file not found: {instructions_path}")
        raise RepoAgentError(f"Instructions markdown not found: {instructions_path}")

    overrides: dict[str, Any] = {
        "repo_url": repo_url,
        "branch": branch,
        "base_branch": base_branch,
        "docker_image": docker_image,
        "dockerfile": dockerfile,
        "use_ssh": use_ssh,
        "ssh_key_dir": ssh_key_dir,
        "model": model,
        "strategy": strategy,
        "pr_title": pr_title,
        "pr_body": pr_body,
        "github_token": github_token,
        "auto_commit": auto_commit,
        "create_pr": create_pr,
        "create_repo_if_missing": create_repo_if_missing,
        "commit_message": commit_message,
        "git_user_name": git_user_name,
        "git_user_email": git_user_email,
        "tool_entrypoint": tool_entrypoint,
        "dry_run": dry_run,
    }

    cfg, body = _resolve_config(instructions_path, overrides)
    logger.info(f"Configuration resolved, repo: {cfg.repo_url}, model: {cfg.model}")

    _docker_build_if_needed(cfg)

    with tempfile.TemporaryDirectory(prefix="repo-agent-") as td:
        workdir = Path(td).resolve()
        logger.debug(f"Created temporary workspace: {workdir}")
        instructions_body_path = workdir / "instructions_body.md"
        instructions_body_path.write_text(body, encoding="utf-8")

        docker_cmd = _build_docker_run_cmd(cfg, workdir, instructions_body_path)

        if cfg.dry_run:
            logger.info("Dry run mode - printing Docker command")
            print("# repo-agent dry run")
            print("# Working directory:", workdir)
            print("# Docker command:")
            print(" ".join(shlex.quote(p) for p in docker_cmd))
            return

        logger.info(f"Running Docker container with image: {cfg.docker_image}")
        logger.debug(f"Full command: {' '.join(shlex.quote(p) for p in docker_cmd)}")

        # Run Docker command without suppressing output so errors are visible
        subprocess.run(docker_cmd, check=True)
        logger.info(f"repo-agent workflow completed successfully for {cfg.repo_url}")
