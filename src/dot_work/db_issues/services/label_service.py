"""Label service for label management and color utilities.

Provides operations for:
- Label CRUD operations (create, update, delete, list)
- Color format conversion (named colors, hex, RGB)
- Label usage tracking

Source reference: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/
"""

import logging
import re
from dataclasses import dataclass

from dot_work.db_issues.adapters import UnitOfWork
from dot_work.db_issues.domain.entities import (
    Clock,
    IdentifierService,
    Label,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Color Utilities
# =============================================================================


# Named color mapping to hex codes
NAMED_COLORS: dict[str, str] = {
    # Basic colors
    "black": "#000000",
    "white": "#ffffff",
    "red": "#ff0000",
    "green": "#00ff00",
    "blue": "#0000ff",
    "yellow": "#ffff00",
    "orange": "#ff8800",
    "purple": "#8800ff",
    "pink": "#ff00ff",
    "cyan": "#00ffff",
    "magenta": "#ff00ff",
    # Variants
    "darkred": "#8b0000",
    "darkgreen": "#006400",
    "darkblue": "#00008b",
    "darkyellow": "#8b8b00",
    "darkorange": "#ff8c00",
    "darkpurple": "#5d008b",
    "lightred": "#ff6b6b",
    "lightgreen": "#90ee90",
    "lightblue": "#add8e6",
    "lightyellow": "#ffffe0",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "gray": "#808080",
    "grey": "#808080",
    # Additional useful colors
    "brown": "#a52a2a",
    "beige": "#f5f5dc",
    "lime": "#00ff00",
    "maroon": "#800000",
    "navy": "#000080",
    "olive": "#808000",
    "teal": "#008080",
    "silver": "#c0c0c0",
    "urgent": "#ff4444",  # Red-orange for urgency
    "bug": "#ff0000",  # Red for bugs
    "feature": "#0000ff",  # Blue for features
    "enhancement": "#008800",  # Green for enhancements
    "docs": "#888888",  # Gray for documentation
    "refactor": "#8800ff",  # Purple for refactoring
    "test": "#ff8800",  # Orange for testing
    "security": "#ff00ff",  # Magenta for security
}


def parse_color(color: str | None) -> str | None:
    """Parse color from various formats to hex.

    Supports:
    - Named colors: "red", "blue", "green", etc.
    - Hex colors: "#ff0000", "ff0000", "00ff00", "0000ff"
    - RGB format: "rgb(255, 0, 0)", "RGB(255, 0, 0)"

    Args:
        color: Color string in any supported format

    Returns:
        Hex color string with "#" prefix (e.g., "#ff0000"), or None if input is None

    Raises:
        ValueError: If color format is invalid

    Examples:
        >>> parse_color("red")
        "#ff0000"
        >>> parse_color("#00ff00")
        "#00ff00"
        >>> parse_color("rgb(0, 0, 255)")
        "#0000ff"
        >>> parse_color(None)
        None
    """
    if color is None:
        return None

    color = color.strip()

    # Check for named color
    if color.lower() in NAMED_COLORS:
        return NAMED_COLORS[color.lower()]

    # Check for hex format (with or without #)
    hex_match = re.match(r"^#?([0-9a-fA-F]{6})$", color)
    if hex_match:
        return f"#{hex_match.group(1).lower()}"

    # Check for short hex format (#rgb)
    short_hex_match = re.match(r"^#?([0-9a-fA-F]{3})$", color)
    if short_hex_match:
        expanded = "".join(c * 2 for c in short_hex_match.group(1))
        return f"#{expanded.lower()}"

    # Check for RGB format
    rgb_match = re.match(
        r"^rgb\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$",
        color,
        re.IGNORECASE,
    )
    if rgb_match:
        r, g, b = rgb_match.groups()
        # Validate ranges
        if not (0 <= int(r) <= 255 and 0 <= int(g) <= 255 and 0 <= int(b) <= 255):
            raise ValueError(f"RGB values must be between 0 and 255: {color}")
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    raise ValueError(
        f"Invalid color format: {color}. Use named color (red), hex (#ff0000), or RGB (rgb(255, 0, 0))"
    )


def get_terminal_color_code(hex_color: str | None) -> str:
    """Convert hex color to nearest terminal color code.

    Args:
        hex_color: Hex color string (e.g., "#ff0000")

    Returns:
        Rich color style string (e.g., "[red]", "[#ff0000]")
    """
    if not hex_color:
        return ""

    # Remove # if present
    hex_color = hex_color.lstrip("#")

    # For rich, we can use hex colors directly
    return f"#{hex_color}"


# =============================================================================
# Label Service
# =============================================================================


@dataclass(frozen=True)
class LabelInfo:
    """Summary information about a label.

    Attributes:
        name: The label name
        count: Number of issues with this label
        color: Optional label color
    """

    name: str
    count: int
    color: str | None


class LabelService:
    """Service for label management operations.

    Coordinates between repositories and enforces business rules.
    All operations use UnitOfWork for transaction management.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        id_service: IdentifierService,
        clock: Clock,
    ) -> None:
        """Initialize label service.

        Args:
            uow: Unit of work for transaction management
            id_service: Service for generating unique identifiers
            clock: Time provider for timestamps
        """
        self.uow = uow
        self.id_service = id_service
        self.clock = clock

    def create_label(
        self,
        name: str,
        color: str | None = None,
        description: str | None = None,
    ) -> Label:
        """Create a new label.

        Args:
            name: Label name (must be unique)
            color: Optional color (named, hex, or RGB format)
            description: Optional label description

        Returns:
            Created label entity

        Raises:
            ValueError: If label name already exists or color is invalid
        """
        logger.debug("Creating label: name=%s, color=%s", name, color)

        # Check if label already exists
        existing = self.uow.labels.get_by_name(name)
        if existing:
            raise ValueError(f"Label already exists: {name}")

        # Parse color
        parsed_color = parse_color(color) if color else None

        label = Label(
            id=self.id_service.generate("label"),
            name=name,
            color=parsed_color,
            description=description,
        )

        saved = self.uow.labels.save(label)
        logger.info("Created label: %s", name)
        return saved

    def update_label(
        self,
        label_id: str,
        color: str | None = None,
        description: str | None = None,
    ) -> Label:
        """Update an existing label.

        Args:
            label_id: Label identifier
            color: New color (named, hex, or RGB format)
            description: New description

        Returns:
            Updated label entity

        Raises:
            ValueError: If label not found or color is invalid
        """
        logger.debug("Updating label: id=%s", label_id)

        label = self.uow.labels.get(label_id)
        if not label:
            raise ValueError(f"Label not found: {label_id}")

        # Parse color if provided
        if color:
            label = Label(
                id=label.id,
                name=label.name,
                color=parse_color(color),
                description=description or label.description,
                created_at=label.created_at,
                updated_at=self.clock.now(),
            )
        else:
            label = Label(
                id=label.id,
                name=label.name,
                color=label.color,
                description=description or label.description,
                created_at=label.created_at,
                updated_at=self.clock.now(),
            )

        saved = self.uow.labels.save(label)
        logger.info("Updated label: %s", label_id)
        return saved

    def rename_label(self, label_id: str, new_name: str) -> Label:
        """Rename a label.

        Args:
            label_id: Label identifier
            new_name: New label name

        Returns:
            Updated label entity

        Raises:
            ValueError: If label not found or name already exists
        """
        logger.debug("Renaming label: id=%s, new_name=%s", label_id, new_name)

        # Check if new name already exists
        existing = self.uow.labels.get_by_name(new_name)
        if existing:
            raise ValueError(f"Label already exists: {new_name}")

        # Get current label
        label = self.uow.labels.get(label_id)
        if not label:
            raise ValueError(f"Label not found: {label_id}")

        # Create updated label with new name
        updated = Label(
            id=label.id,
            name=new_name,
            color=label.color,
            description=label.description,
            created_at=label.created_at,
            updated_at=self.clock.now(),
        )

        # Update via repository rename method
        result = self.uow.labels.rename(label_id, new_name)
        if result:
            logger.info("Renamed label: %s -> %s", label_id, new_name)
            return updated
        raise ValueError(f"Failed to rename label: {label_id}")

    def delete_label(self, label_id: str) -> bool:
        """Delete a label.

        Args:
            label_id: Label identifier

        Returns:
            True if deleted, False if not found
        """
        logger.debug("Deleting label: id=%s", label_id)

        result = self.uow.labels.delete(label_id)
        if result:
            logger.info("Deleted label: %s", label_id)
        else:
            logger.warning("Label not found for deletion: %s", label_id)
        return result

    def list_labels(self, include_unused: bool = False) -> list[Label]:
        """List all labels.

        Args:
            include_unused: If True, only return unused labels

        Returns:
            List of label entities
        """
        logger.debug("Listing labels: unused_only=%s", include_unused)

        if include_unused:
            return self.uow.labels.list_unused()
        return self.uow.labels.list_all()

    def get_label(self, label_id: str) -> Label | None:
        """Get label by ID.

        Args:
            label_id: Label identifier

        Returns:
            Label entity if found, None otherwise
        """
        return self.uow.labels.get(label_id)

    def get_all_labels_with_counts(self, include_unused: bool = False) -> list[LabelInfo]:
        """Get all unique labels with usage counts.

        Scans all issues to collect unique labels and count their usage.
        Optionally includes only unused labels (count = 0).

        Args:
            include_unused: If True, only return unused labels (count = 0)

        Returns:
            List of LabelInfo objects with name, count, and color

        Examples:
            >>> infos = service.get_all_labels_with_counts()
            >>> for info in infos:
            ...     print(f"{info.name}: {info.count} issues")
            bug: 15 issues
            feature: 8 issues
        """
        logger.debug("Getting all labels with counts: include_unused=%s", include_unused)

        # Get all defined labels (from Label repository)
        defined_labels = self.uow.labels.list_all()
        defined_label_map = {label.name: label for label in defined_labels}

        # Get all issues and count label usage
        all_issues = self.uow.issues.list_all(limit=1000000)

        # Count label usage across all issues
        label_counts: dict[str, int] = {}
        for issue in all_issues:
            for label_name in issue.labels:
                label_counts[label_name] = label_counts.get(label_name, 0) + 1

        # Build result list
        results: list[LabelInfo] = []

        if include_unused:
            # Only show unused labels (count = 0)
            for label in defined_labels:
                count = label_counts.get(label.name, 0)
                if count == 0:
                    results.append(
                        LabelInfo(
                            name=label.name,
                            count=0,
                            color=label.color,
                        )
                    )
        else:
            # Show all labels, with usage counts
            # First, add labels that were found in issues
            for label_name, count in label_counts.items():
                label = defined_label_map.get(label_name)
                results.append(
                    LabelInfo(
                        name=label_name,
                        count=count,
                        color=label.color if label else None,
                    )
                )

            # Then add defined labels that have no usage (unused)
            for label in defined_labels:
                if label.name not in label_counts:
                    results.append(
                        LabelInfo(
                            name=label.name,
                            count=0,
                            color=label.color,
                        )
                    )

        # Sort by count descending, then by name
        results.sort(key=lambda x: (-x.count, x.name))

        return results


__all__ = [
    "LabelService",
    "LabelInfo",
    "parse_color",
    "get_terminal_color_code",
    "NAMED_COLORS",
]
