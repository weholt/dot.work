"""Service layer for the sample project."""


class GreetingService:
    """Coordinates greeting flows for user-facing surfaces."""

    def greet(self, name: str) -> str:
        """Return a greeting string that UIs or bots can render."""
        return f"Hello {name}"
