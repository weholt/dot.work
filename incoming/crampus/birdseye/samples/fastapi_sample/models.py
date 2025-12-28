"""Domain models for the FastAPI sample project."""

from __future__ import annotations

from datetime import datetime, timezone

try:  # pragma: no cover - optional dependency for this sample
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - minimal fallback to keep sample analyzable

    class BaseModel:  # type: ignore[misc]
        """Lightweight stand-in so static analysis continues without pydantic."""

        def dict(self) -> dict:
            return self.__dict__.copy()

    def Field(  # type: ignore[misc]
        default=..., *, description: str = "", default_factory=None
    ) -> Any:
        return default


class TodoCreate(BaseModel):
    """Incoming payload for creating a to-do item."""

    title: str = Field(..., description="Short headline for the task")
    details: str | None = Field(None, description="Optional extended notes")


class Todo(TodoCreate):
    """Tracked to-do item returned to clients."""

    id: int
    created_at: datetime
    tags: list[str] = Field(default_factory=list)


class HealthStatus(BaseModel):
    """Simple status response for uptime checks."""

    status: str = Field(..., description="Human friendly status text")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
