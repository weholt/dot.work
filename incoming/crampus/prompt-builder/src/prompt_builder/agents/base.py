"""Base agent class and common utilities."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ..models import (
    AgentConfig,
    Subtask,
    Task,
    ValidationResult,
    ValidationType,
)


class BaseAgent(ABC):
    """Base class for all validation agents."""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig(name=self.__class__.__name__)
        self.logger = logging.getLogger(f"prompt_builder.{self.config.name}")

    @abstractmethod
    async def execute(
        self, task: Task, subtask: Subtask | None = None, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """Execute the agent's primary function."""
        pass

    @abstractmethod
    def get_validation_type(self) -> ValidationType:
        """Return the type of validation this agent performs."""
        pass

    def _create_validation_result(
        self,
        subtask_id: str,
        passed: bool,
        issues: list[str] = None,
        warnings: list[str] = None,
        metrics: dict[str, Any] = None,
        execution_time: float = 0.0,
    ) -> ValidationResult:
        """Create a standardized validation result."""
        return ValidationResult(
            validator_type=self.get_validation_type(),
            subtask_id=subtask_id,
            passed=passed,
            issues=issues or [],
            warnings=warnings or [],
            metrics=metrics or {},
            execution_time=execution_time,
            timestamp=datetime.now(),
        )

    async def _execute_with_timeout(self, coro, timeout: float | None = None) -> Any:
        """Execute a coroutine with timeout and retry logic."""
        timeout = timeout or self.config.timeout
        max_retries = self.config.max_retries

        for attempt in range(max_retries + 1):
            try:
                return await asyncio.wait_for(coro, timeout=timeout)
            except asyncio.TimeoutError:
                if attempt == max_retries:
                    raise
                self.logger.warning(
                    f"Attempt {attempt + 1} timed out after {timeout}s, "
                    f"retrying... ({max_retries - attempt} attempts left)"
                )
                await asyncio.sleep(2**attempt)  # Exponential backoff
            except Exception as e:
                if attempt == max_retries:
                    raise
                self.logger.warning(
                    f"Attempt {attempt + 1} failed with {e}, retrying... ({max_retries - attempt} attempts left)"
                )
                await asyncio.sleep(1)

    def _log_start(self, subtask: Subtask | None = None):
        """Log the start of agent execution."""
        if subtask:
            self.logger.info(f"Starting {self.config.name} for subtask {subtask.id}")
        else:
            self.logger.info(f"Starting {self.config.name}")

    def _log_success(self, result: ValidationResult, subtask: Subtask | None = None):
        """Log successful execution."""
        status = "PASSED" if result.passed else "FAILED"
        if subtask:
            self.logger.info(
                f"Completed {self.config.name} for subtask {subtask.id}: {status} ({result.execution_time:.2f}s)"
            )
        else:
            self.logger.info(f"Completed {self.config.name}: {status} ({result.execution_time:.2f}s)")

        if result.issues:
            self.logger.warning(f"Issues found: {result.issues}")
        if result.warnings:
            self.logger.warning(f"Warnings: {result.warnings}")

    def _log_error(self, error: Exception, subtask: Subtask | None = None):
        """Log execution errors."""
        if subtask:
            self.logger.error(f"Error in {self.config.name} for subtask {subtask.id}: {error}")
        else:
            self.logger.error(f"Error in {self.config.name}: {error}")


class AgentError(Exception):
    """Base exception for agent-related errors."""

    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""

    pass


class AgentConfigurationError(AgentError):
    """Raised when agent configuration is invalid."""

    pass


def measure_execution_time(func):
    """Decorator to measure execution time of functions."""

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Add execution time to result if it's a ValidationResult
            if hasattr(result, "execution_time"):
                result.execution_time = execution_time

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            # Log execution time even on failure
            logging.getLogger(__name__).warning(f"Function {func.__name__} failed after {execution_time:.2f}s: {e}")
            raise

    return wrapper
