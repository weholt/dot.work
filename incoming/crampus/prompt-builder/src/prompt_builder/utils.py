"""Utility functions for the prompt-builder package."""

import logging
import os
import sys
from pathlib import Path
from typing import Any

import toml


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    # Create logs directory
    logs_dir = Path(".prompt-builder/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(logs_dir / "prompt-builder.log"),
            logging.StreamHandler(sys.stdout) if verbose else logging.NullHandler(),
        ],
    )

    # Set specific logger levels
    if not verbose:
        # Suppress noisy loggers
        logging.getLogger("git").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def load_config(config_file: str = "prompt-builder.toml") -> dict[str, Any]:
    """Load configuration from file."""
    config_path = Path(config_file)

    if not config_path.exists():
        return get_default_config()

    try:
        with open(config_path) as f:
            return toml.load(f)
    except Exception as e:
        logging.warning(f"Failed to load config from {config_path}: {e}")
        return get_default_config()


def save_config(config: dict[str, Any], config_file: str = "prompt-builder.toml"):
    """Save configuration to file."""
    config_path = Path(config_file)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w") as f:
            toml.dump(config, f)
    except Exception as e:
        logging.error(f"Failed to save config to {config_path}: {e}")


def get_default_config() -> dict[str, Any]:
    """Get default configuration."""
    return {
        "agents": {
            "planner": {"enabled": True, "timeout": 300, "max_retries": 3},
            "static_validator": {"enabled": True, "timeout": 180, "max_retries": 3},
            "behavior_validator": {"enabled": True, "timeout": 600, "max_retries": 3},
            "regression_sentinel": {"enabled": True, "timeout": 240, "max_retries": 3},
            "synthetic_test": {"enabled": True, "timeout": 300, "max_retries": 3},
            "pr_generator": {"enabled": True, "timeout": 120, "max_retries": 3},
        },
        "git": {"auto_push": False, "pr_auto_merge": False, "default_base": "main"},
        "notifications": {"on_failure": True, "on_success": False, "webhook_url": None},
        "paths": {
            "tasks_dir": ".prompt-builder/tasks",
            "snapshots_dir": ".prompt-builder/snapshots",
            "synthetic_tests_dir": "tests/synthetic",
            "logs_dir": ".prompt-builder/logs",
        },
    }


def ensure_directories():
    """Ensure all necessary directories exist."""
    config = load_config()
    paths = config.get("paths", {})

    for path_key, path_value in paths.items():
        Path(path_value).mkdir(parents=True, exist_ok=True)


def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path.cwd()

    # Look for common project indicators
    indicators = [".git", "pyproject.toml", "setup.py", "requirements.txt", "prompt-builder.toml"]

    while current != current.parent:
        for indicator in indicators:
            if (current / indicator).exists():
                return current
        current = current.parent

    # Fallback to current directory
    return Path.cwd()


def is_git_repository() -> bool:
    """Check if current directory is a git repository."""
    try:
        import subprocess

        result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        import subprocess

        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def get_changed_files(base_ref: str = "HEAD~1", head_ref: str = "HEAD") -> list[str]:
    """Get list of files changed between git references."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}..{head_ref}"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def validate_agent_config(agent_name: str, config: dict[str, Any]) -> bool:
    """Validate agent configuration."""
    required_fields = ["enabled", "timeout", "max_retries"]

    for field in required_fields:
        if field not in config:
            logging.error(f"Agent {agent_name} missing required field: {field}")
            return False

    # Validate values
    if not isinstance(config["enabled"], bool):
        logging.error(f"Agent {agent_name} 'enabled' must be boolean")
        return False

    if not isinstance(config["timeout"], (int, float)) or config["timeout"] <= 0:
        logging.error(f"Agent {agent_name} 'timeout' must be positive number")
        return False

    if not isinstance(config["max_retries"], int) or config["max_retries"] < 0:
        logging.error(f"Agent {agent_name} 'max_retries' must be non-negative integer")
        return False

    return True


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def safe_filename(filename: str) -> str:
    """Convert string to safe filename."""
    import re

    # Remove invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Replace spaces with underscores
    safe_name = re.sub(r"\s+", "_", safe_name)
    # Remove leading/trailing underscores
    safe_name = safe_name.strip("_")
    # Limit length
    if len(safe_name) > 255:
        safe_name = safe_name[:255]
    return safe_name


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def merge_dicts(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries."""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def get_env_var(key: str, default: Any = None, var_type: type = str) -> Any:
    """Get environment variable with type conversion."""
    value = os.getenv(key, default)

    if value is None:
        return default

    try:
        if var_type == bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif var_type == int:
            return int(value)
        elif var_type == float:
            return float(value)
        elif var_type == list:
            return [item.strip() for item in value.split(",")]
        else:
            return var_type(value)
    except (ValueError, TypeError):
        logging.warning(f"Failed to convert env var {key} to {var_type}, using default")
        return default


def sanitize_log_message(message: str) -> str:
    """Sanitize log message by removing sensitive information."""
    import re

    # Remove common sensitive patterns
    patterns = [
        r"password[=:]\s*[^\s]+",
        r"token[=:]\s*[^\s]+",
        r"key[=:]\s*[^\s]+",
        r"secret[=:]\s*[^\s]+",
        r"api[_-]?key[=:]\s*[^\s]+",
        r"auth[=:]\s*[^\s]+",
        r"ghp_[a-zA-Z0-9]{36}",  # GitHub personal access tokens
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email addresses
    ]

    sanitized = message
    for pattern in patterns:
        sanitized = re.sub(pattern, lambda m: m.group(0).split("=")[0] + "=***", sanitized, flags=re.IGNORECASE)

    return sanitized


class Timer:
    """Simple timer context manager."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = logging.time.time()
        logging.debug(f"Starting {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = logging.time.time()
        duration = self.end_time - self.start_time
        logging.debug(f"Completed {self.name} in {format_duration(duration)}")

    @property
    def duration(self) -> float:
        """Get the duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
