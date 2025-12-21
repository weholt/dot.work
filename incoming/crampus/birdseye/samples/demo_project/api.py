"""HTTP surface for the sample project."""

from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable[..., object])


class APIRouter:
    """Minimal stub to mimic a router decorator for static analysis."""

    def get(self, _path: str) -> Callable[[F], F]:  # pragma: no cover - placeholder
        def decorator(func: F) -> F:
            return func

        return decorator


router = APIRouter()


@router.get("/greet")
def read_greeting(name: str) -> dict[str, str]:
    """Return a greeting payload for web clients."""
    return {"message": f"Hello {name}"}
