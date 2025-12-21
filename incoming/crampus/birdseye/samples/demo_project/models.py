"""Data models used in the sample project."""


class BaseModel:  # pragma: no cover - illustrative stub
    """Minimal stand-in for Pydantic's BaseModel."""


class Profile(BaseModel):
    """Profile details shared with end users."""

    username: str
    bio: str | None = None
