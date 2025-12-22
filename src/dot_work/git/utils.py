"""Utility functions for git analysis."""

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    # Create logs directory
    logs_dir = Path(".git-analysis/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(logs_dir / "git-analysis.log"),
            logging.StreamHandler(sys.stdout) if verbose else logging.NullHandler(),
        ],
    )

    # Set specific logger levels
    if not verbose:
        # Suppress noisy loggers
        logging.getLogger("git").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


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


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_data = {"args": args, "kwargs": sorted(kwargs.items())}
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(key_str.encode()).hexdigest()


def get_env_var(key: str, default: Any = None, var_type: type = str) -> Any:
    """Get environment variable with type conversion."""
    value = os.getenv(key, default)

    if value is None:
        return default

    try:
        if var_type is bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif var_type is int:
            return int(value)
        elif var_type is float:
            return float(value)
        elif var_type is list:
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
        sanitized = re.sub(
            pattern, lambda m: m.group(0).split("=")[0] + "=***", sanitized, flags=re.IGNORECASE
        )

    return sanitized


def is_valid_git_ref(ref: str) -> bool:
    """Check if a git reference is valid."""
    import re

    # Basic validation for git refs
    if not ref or len(ref) > 255:
        return False

    # Check for invalid characters
    if re.search(r"[~^:?*\[\\]", ref):
        return False

    # Cannot start with dot
    if ref.startswith("."):
        return False

    # Cannot end with .lock
    if ref.endswith(".lock"):
        return False

    return True


def parse_commit_range(range_str: str) -> tuple[str, str]:
    """Parse commit range string like 'main..feature' or 'HEAD~5..HEAD'."""
    if ".." not in range_str:
        raise ValueError("Invalid range format. Expected 'from..to'")

    from_ref, to_ref = range_str.split("..", 1)
    return from_ref.strip(), to_ref.strip()


def calculate_time_ago(timestamp: datetime) -> str:
    """Calculate human-readable time ago string."""
    now = datetime.now()
    diff = now - timestamp

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(weeks=1):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"


def get_git_config_value(key: str, repo_path: Path | None = None) -> str | None:
    """Get git configuration value."""
    try:
        import subprocess

        cmd = ["git", "config", "--get", key]
        if repo_path:
            cmd.extend(["-C", str(repo_path)])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def is_git_repository(path: Path) -> bool:
    """Check if path is a git repository."""
    try:
        import git

        git.Repo(path)
        return True
    except Exception:
        return False


def get_repository_root(path: Path | None = None) -> Path | None:
    """Get the root directory of the git repository."""
    try:
        if path is None:
            path = Path.cwd()

        import git

        repo = git.Repo(path, search_parent_directories=True)
        return Path(repo.git_dir).parent
    except Exception:
        return None


def detect_encoding(file_path: Path) -> str:
    """Detect file encoding."""
    try:
        import chardet  # type: ignore[import-not-found]

        with open(file_path, "rb") as f:
            raw_data = f.read(10000)  # Read first 10KB
        result = chardet.detect(raw_data)
        return result["encoding"] or "utf-8"
    except ImportError:
        # Fallback to utf-8 if chardet is not available
        return "utf-8"
    except (OSError, ValueError):
        return "utf-8"


class ProgressTracker:
    """Simple progress tracker for long-running operations."""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()

    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        self._print_progress()

    def set_current(self, current: int):
        """Set current progress."""
        self.current = current
        self._print_progress()

    def _print_progress(self):
        """Print progress to console."""
        percentage = (self.current / self.total) * 100
        elapsed = datetime.now() - self.start_time

        if self.current > 0:
            eta = elapsed * (self.total - self.current) / self.current
            eta_str = f" ETA: {format_duration(eta.total_seconds())}"
        else:
            eta_str = ""

        print(
            f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%)"
            f" Elapsed: {format_duration(elapsed.total_seconds())}{eta_str}",
            end="",
        )

        if self.current >= self.total:
            print()  # New line when complete


class Timer:
    """Simple timer context manager."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        logging.debug(f"Starting {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        logging.debug(f"Completed {self.name} in {format_duration(duration.total_seconds())}")

    @property
    def duration(self) -> float:
        """Get the duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


def merge_dicts(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries."""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def validate_email(email: str) -> bool:
    """Validate email address format."""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def extract_emoji_indicators(text: str) -> list[str]:
    """Extract emoji indicators from text."""
    # Common emoji patterns in commit messages
    emoji_patterns = [
        "🚀",
        "✨",
        "🐛",
        "💥",
        "🔥",
        "⚡",
        "🎉",
        "🔒",
        "🔑",
        "🔧",
        "📝",
        "📚",
        "🏗️",
        "🎨",
        "♻️",
        "♿",
        "🌐",
        "📊",
        "🔬",
        "🧪",
        "⚠️",
        "❗",
        "❓",
        "➕",
        "➖",
        "🔄",
        "🔀",
        "🔁",
        "🔂",
        "⏪",
        "⏩",
        "⏭",
        "⏹️",
        "⏯️",
        "⏮️",
        "⏸️",
        "⏹️",
        "🏁",
    ]

    found = []
    for emoji in emoji_patterns:
        if emoji in text:
            found.append(emoji)

    return found


def normalize_branch_name(branch: str) -> str:
    """Normalize branch name."""
    # Remove remote prefix (origin/main -> main)
    if "/" in branch:
        parts = branch.split("/")
        if parts[0] in ["origin", "upstream", "fork", "remote"]:
            branch = "/".join(parts[1:])

    # Remove common prefixes
    prefixes_to_remove = ["feature/", "feat/", "bugfix/", "fix/", "hotfix/", "release/", "rel/"]
    for prefix in prefixes_to_remove:
        if branch.startswith(prefix):
            branch = branch[len(prefix) :]
            break

    return branch


def get_file_extension_stats(file_paths: list[str]) -> dict[str, int]:
    """Get statistics of file extensions."""
    extensions: dict[str, int] = {}

    for file_path in file_paths:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext:
            extensions[ext] = extensions.get(ext, 0) + 1
        else:
            extensions["(no extension)"] = extensions.get("(no extension)", 0) + 1

    return dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True))


def calculate_commit_velocity(commits: list, time_window_days: int = 30) -> float:
    """Calculate commit velocity (commits per day) over a time window."""
    if not commits:
        return 0.0

    cutoff_date = datetime.now() - timedelta(days=time_window_days)
    recent_commits = [c for c in commits if c.timestamp >= cutoff_date]

    return len(recent_commits) / time_window_days


def identify_commit_patterns(commits: list) -> dict[str, int]:
    """Identify common patterns in commit messages."""
    patterns = {
        "fix": 0,
        "feature": 0,
        "refactor": 0,
        "test": 0,
        "docs": 0,
        "chore": 0,
        "perf": 0,
        "style": 0,
        "build": 0,
        "ci": 0,
        "revert": 0,
        "merge": 0,
        "initial": 0,
    }

    for commit in commits:
        message = commit.message.lower()

        if any(keyword in message for keyword in ["fix", "bug", "error", "issue"]):
            patterns["fix"] += 1
        if any(keyword in message for keyword in ["feature", "feat", "add", "new", "implement"]):
            patterns["feature"] += 1
        if any(keyword in message for keyword in ["refactor", "refact", "restructure"]):
            patterns["refactor"] += 1
        if any(keyword in message for keyword in ["test", "spec", "testing"]):
            patterns["test"] += 1
        if any(keyword in message for keyword in ["doc", "readme", "documentation"]):
            patterns["docs"] += 1
        if any(keyword in message for keyword in ["chore", "maintenance", "update"]):
            patterns["chore"] += 1
        if any(keyword in message for keyword in ["perf", "performance", "optimize"]):
            patterns["perf"] += 1
        if any(keyword in message for keyword in ["style", "format", "lint"]):
            patterns["style"] += 1
        if any(keyword in message for keyword in ["build", "compile", "makefile"]):
            patterns["build"] += 1
        if any(keyword in message for keyword in ["ci", "cd", "pipeline", "workflow"]):
            patterns["ci"] += 1
        if "revert" in message:
            patterns["revert"] += 1
        if "merge" in message:
            patterns["merge"] += 1
        if any(keyword in message for keyword in ["initial", "first", "skeleton", "setup"]):
            patterns["initial"] += 1

    return patterns
